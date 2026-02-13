from __future__ import annotations

from dataclasses import dataclass

from .event_parser import SwapRecord

INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


@dataclass(slots=True)
class OhlcvBar:
    pool_id: str
    interval: str
    open_time: int  # epoch ms, aligned to interval start
    open: float
    high: float
    low: float
    close: float
    volume: float  # quote currency volume
    trade_count: int


def aggregate_swaps(
    swaps: list[SwapRecord],
    interval: str = "1h",
    forward_fill: bool = True,
) -> list[OhlcvBar]:
    """Aggregate swap records into OHLCV bars.

    Args:
        swaps: Sorted by timestamp_ms.
        interval: One of "1m", "5m", "15m", "1h", "4h", "1d".
        forward_fill: Fill empty bars with previous close.

    Returns:
        List of OhlcvBar sorted by open_time.
    """
    if not swaps:
        return []

    interval_ms = INTERVAL_SECONDS[interval] * 1000
    pool_id = swaps[0].pool_id

    # Group swaps into time buckets
    buckets: dict[int, list[SwapRecord]] = {}
    for s in swaps:
        bucket_start = (s.timestamp_ms // interval_ms) * interval_ms
        buckets.setdefault(bucket_start, []).append(s)

    # Build bars from buckets
    bars: list[OhlcvBar] = []
    for open_time in sorted(buckets):
        bucket = buckets[open_time]
        prices = [s.price for s in bucket]
        bars.append(
            OhlcvBar(
                pool_id=pool_id,
                interval=interval,
                open_time=open_time,
                open=prices[0],
                high=max(prices),
                low=min(prices),
                close=prices[-1],
                volume=sum(s.volume_b for s in bucket),
                trade_count=len(bucket),
            )
        )

    if not forward_fill or len(bars) < 2:
        return bars

    # Forward-fill empty bars
    filled: list[OhlcvBar] = [bars[0]]
    for i in range(1, len(bars)):
        prev = filled[-1]
        curr = bars[i]
        # Fill gaps between prev and curr
        gap_start = prev.open_time + interval_ms
        while gap_start < curr.open_time:
            filled.append(
                OhlcvBar(
                    pool_id=pool_id,
                    interval=interval,
                    open_time=gap_start,
                    open=prev.close,
                    high=prev.close,
                    low=prev.close,
                    close=prev.close,
                    volume=0.0,
                    trade_count=0,
                )
            )
            gap_start += interval_ms
        filled.append(curr)

    return filled
