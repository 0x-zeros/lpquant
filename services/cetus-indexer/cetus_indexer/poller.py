from __future__ import annotations

import asyncio
import logging

from .config import KNOWN_POOLS, POLL_INTERVAL, PAGE_SIZE
from .db import Database
from .event_parser import PoolInfo, SwapRecord, parse_swap_event
from .graphql_client import query_swap_events
from .ohlcv import aggregate_swaps, INTERVAL_SECONDS

logger = logging.getLogger(__name__)


def _build_pool_configs(
    pool_ids: list[str] | None = None,
) -> dict[str, PoolInfo]:
    """Build pool_id → PoolInfo mapping from KNOWN_POOLS."""
    pools = KNOWN_POOLS
    if pool_ids:
        pools = {k: v for k, v in pools.items() if k in pool_ids}
    return {
        pid: PoolInfo(
            decimals_a=cfg["decimals_a"],
            decimals_b=cfg["decimals_b"],
            invert_price=cfg.get("invert_price", False),
        )
        for pid, cfg in pools.items()
    }


async def fetch_and_store(
    db: Database,
    pool_configs: dict[str, PoolInfo],
    cursor: str | None,
    limit: int = PAGE_SIZE,
) -> tuple[str | None, int, bool]:
    """Fetch one page of events, parse, store, and update OHLCV.

    Returns:
        (next_cursor, num_inserted, has_next_page)
    """
    events, next_cursor, has_next = await query_swap_events(
        after_cursor=cursor,
        limit=limit,
    )

    swaps: list[SwapRecord] = []
    for ev in events:
        record = parse_swap_event(ev, pool_configs)
        if record is not None:
            swaps.append(record)

    inserted = await db.insert_swaps(swaps)

    # Update OHLCV for affected pools/time ranges
    if swaps:
        await _update_ohlcv(db, swaps)

    if next_cursor:
        await db.set_cursor(next_cursor)

    return next_cursor, inserted, has_next


async def _update_ohlcv(db: Database, swaps: list[SwapRecord]) -> None:
    """Incrementally update OHLCV bars for the time ranges affected by new swaps."""
    by_pool: dict[str, list[SwapRecord]] = {}
    for s in swaps:
        by_pool.setdefault(s.pool_id, []).append(s)

    for pool_id, pool_swaps in by_pool.items():
        ts_min = min(s.timestamp_ms for s in pool_swaps)
        ts_max = max(s.timestamp_ms for s in pool_swaps)

        for interval in INTERVAL_SECONDS:
            interval_ms = INTERVAL_SECONDS[interval] * 1000
            start = (ts_min // interval_ms) * interval_ms
            end = ((ts_max // interval_ms) + 1) * interval_ms

            all_swaps = await db.get_swaps(pool_id, start_ms=start, end_ms=end)
            if all_swaps:
                bars = aggregate_swaps(all_swaps, interval, forward_fill=False)
                await db.upsert_ohlcv(bars)


async def run_poller(
    pool_ids: list[str] | None = None,
    interval: int = POLL_INTERVAL,
    backfill: bool = True,
) -> None:
    """Main polling loop.

    1. On first start: backfill all available history.
    2. Then: poll for new events every `interval` seconds.
    """
    pool_configs = _build_pool_configs(pool_ids)
    if not pool_configs:
        logger.error("No known pools to index")
        return

    logger.info(
        "Starting poller for pools: %s",
        ", ".join(pool_configs.keys()),
    )

    async with Database() as db:
        cursor = await db.get_cursor()

        if backfill or cursor is None:
            logger.info("Starting backfill (cursor: %s)...", cursor or "none")
            total = 0
            while True:
                cursor, inserted, has_next = await fetch_and_store(
                    db, pool_configs, cursor
                )
                total += inserted
                if inserted > 0:
                    logger.info(
                        "Backfill: +%d events (total: %d)", inserted, total
                    )
                if not has_next:
                    break
            logger.info("Backfill complete: %d events indexed", total)

        # Continuous polling
        logger.info("Entering polling loop (interval: %ds)...", interval)
        while True:
            try:
                cursor, inserted, _ = await fetch_and_store(
                    db, pool_configs, cursor
                )
                if inserted > 0:
                    logger.info("Poll: +%d new events", inserted)
            except Exception:
                logger.exception("Poll error")
            await asyncio.sleep(interval)
