from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
from datetime import datetime, timezone

from .config import KNOWN_POOLS
from .db import Database
from .event_parser import parse_swap_event
from .graphql_client import query_swap_events
from .ohlcv import aggregate_swaps, INTERVAL_SECONDS
from .poller import run_poller, _build_pool_configs


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cetus-indexer",
        description="Cetus CLMM on-chain OHLCV indexer",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # poll
    p_poll = sub.add_parser("poll", help="Start continuous polling")
    p_poll.add_argument("--pool", help="Pool ID to index (default: all known)")
    p_poll.add_argument(
        "--interval", type=int, default=60, help="Poll interval seconds"
    )
    p_poll.add_argument(
        "--no-backfill", action="store_true", help="Skip initial backfill"
    )

    # query
    p_query = sub.add_parser("query", help="Single query test (no storage)")
    p_query.add_argument(
        "--limit", type=int, default=10, help="Number of events"
    )

    # status
    sub.add_parser("status", help="Show indexer status")

    # export
    p_export = sub.add_parser("export", help="Export OHLCV to CSV")
    p_export.add_argument("--pool", required=True, help="Pool ID")
    p_export.add_argument(
        "--interval",
        default="1h",
        choices=list(INTERVAL_SECONDS.keys()),
        help="OHLCV interval",
    )
    p_export.add_argument("--output", "-o", default="-", help="Output file")

    # rebuild
    p_rebuild = sub.add_parser(
        "rebuild-ohlcv", help="Rebuild OHLCV from stored swap events"
    )
    p_rebuild.add_argument("--pool", help="Pool ID (default: all)")
    p_rebuild.add_argument(
        "--interval",
        default="1h",
        choices=list(INTERVAL_SECONDS.keys()),
        help="OHLCV interval",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    asyncio.run(_dispatch(args))


async def _dispatch(args: argparse.Namespace) -> None:
    if args.command == "poll":
        pool_ids = [args.pool] if args.pool else None
        await run_poller(
            pool_ids=pool_ids,
            interval=args.interval,
            backfill=not args.no_backfill,
        )

    elif args.command == "query":
        await _cmd_query(args.limit)

    elif args.command == "status":
        await _cmd_status()

    elif args.command == "export":
        await _cmd_export(args.pool, args.interval, args.output)

    elif args.command == "rebuild-ohlcv":
        await _cmd_rebuild(args.pool, args.interval)


async def _cmd_query(limit: int) -> None:
    """Single query test — fetch and print swap events without storing."""
    pool_configs = _build_pool_configs()

    events, cursor, has_next = await query_swap_events(limit=limit)
    print(f"Fetched {len(events)} events (has_next: {has_next})\n")

    for ev in events:
        record = parse_swap_event(ev, pool_configs)
        if record:
            ts = datetime.fromtimestamp(
                record.timestamp_ms / 1000, tz=timezone.utc
            )
            direction = "A→B" if record.atob else "B→A"
            pool_sym = KNOWN_POOLS.get(record.pool_id, {}).get(
                "symbol", record.pool_id[:16] + "..."
            )
            print(
                f"  {ts:%Y-%m-%d %H:%M:%S} | {pool_sym} | "
                f"${record.price:.6f} | {direction} | "
                f"vol_a={record.volume_a:.4f} vol_b={record.volume_b:.4f} | "
                f"tx={record.tx_digest[:16]}..."
            )
        else:
            pool_id = ev.get("json", {}).get("pool", "?")
            print(f"  [skipped] unknown pool: {pool_id}")

    print(f"\nCursor: {cursor}")


async def _cmd_status() -> None:
    """Show indexer status."""
    async with Database() as db:
        stats = await db.get_stats()

    print("=== Cetus Indexer Status ===\n")
    print(f"Total swap events: {stats['total_events']}")

    if stats["earliest_ms"]:
        earliest = datetime.fromtimestamp(
            stats["earliest_ms"] / 1000, tz=timezone.utc
        )
        latest = datetime.fromtimestamp(
            stats["latest_ms"] / 1000, tz=timezone.utc
        )
        print(f"Time range: {earliest:%Y-%m-%d %H:%M} → {latest:%Y-%m-%d %H:%M}")

    if stats["pools"]:
        print("\nEvents by pool:")
        for pid, count in stats["pools"].items():
            sym = KNOWN_POOLS.get(pid, {}).get("symbol", pid[:20] + "...")
            print(f"  {sym}: {count}")

    print(f"\nCursor: {stats['cursor'] or '(none)'}")


async def _cmd_export(pool_id: str, interval: str, output: str) -> None:
    """Export OHLCV bars to CSV."""
    async with Database() as db:
        bars = await db.get_ohlcv(pool_id, interval)

    if not bars:
        print("No OHLCV data found. Run 'poll' first to index events.")
        return

    out = sys.stdout if output == "-" else open(output, "w", newline="")
    try:
        writer = csv.writer(out)
        writer.writerow(
            ["open_time", "open_time_utc", "open", "high", "low", "close", "volume", "trades"]
        )
        for b in bars:
            ts = datetime.fromtimestamp(b.open_time / 1000, tz=timezone.utc)
            writer.writerow(
                [
                    b.open_time,
                    ts.strftime("%Y-%m-%d %H:%M:%S"),
                    f"{b.open:.8f}",
                    f"{b.high:.8f}",
                    f"{b.low:.8f}",
                    f"{b.close:.8f}",
                    f"{b.volume:.4f}",
                    b.trade_count,
                ]
            )
        print(f"Exported {len(bars)} bars", file=sys.stderr)
    finally:
        if out is not sys.stdout:
            out.close()


async def _cmd_rebuild(pool_id: str | None, interval: str) -> None:
    """Rebuild OHLCV from stored swap events."""
    pool_configs = _build_pool_configs()
    pools = [pool_id] if pool_id else list(pool_configs.keys())

    async with Database() as db:
        for pid in pools:
            sym = KNOWN_POOLS.get(pid, {}).get("symbol", pid[:20])
            swaps = await db.get_swaps(pid)
            if not swaps:
                print(f"{sym}: no events")
                continue

            bars = aggregate_swaps(swaps, interval, forward_fill=True)
            await db.upsert_ohlcv(bars)
            print(f"{sym}: rebuilt {len(bars)} bars ({interval})")


if __name__ == "__main__":
    main()
