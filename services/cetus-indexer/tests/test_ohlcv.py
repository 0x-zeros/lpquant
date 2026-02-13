from cetus_indexer.event_parser import SwapRecord
from cetus_indexer.ohlcv import aggregate_swaps, OhlcvBar

POOL = "0xpool"


def _swap(ts_ms: int, price: float, vol_b: float = 100.0) -> SwapRecord:
    return SwapRecord(
        tx_digest=f"tx_{ts_ms}",
        event_seq=0,
        pool_id=POOL,
        timestamp_ms=ts_ms,
        price=price,
        volume_a=vol_b / price,
        volume_b=vol_b,
        atob=True,
        sqrt_price_x64="0",
    )


def test_aggregate_single_bar():
    """Multiple swaps in the same hour → one bar."""
    base = 1700000000000  # some epoch ms
    swaps = [
        _swap(base, 3.50, 100),
        _swap(base + 60_000, 3.55, 200),
        _swap(base + 120_000, 3.45, 150),
    ]
    bars = aggregate_swaps(swaps, "1h", forward_fill=False)

    assert len(bars) == 1
    bar = bars[0]
    assert bar.open == 3.50
    assert bar.high == 3.55
    assert bar.low == 3.45
    assert bar.close == 3.45
    assert bar.volume == 450.0
    assert bar.trade_count == 3


def test_aggregate_multiple_bars():
    """Swaps in different hours → separate bars."""
    hour_ms = 3600_000
    base = (1700000000000 // hour_ms) * hour_ms  # align to hour

    swaps = [
        _swap(base + 1000, 3.50),
        _swap(base + hour_ms + 1000, 3.60),
        _swap(base + 2 * hour_ms + 1000, 3.55),
    ]
    bars = aggregate_swaps(swaps, "1h", forward_fill=False)

    assert len(bars) == 3
    assert bars[0].open == 3.50
    assert bars[1].open == 3.60
    assert bars[2].open == 3.55


def test_forward_fill():
    """Empty bars between trades should be filled with previous close."""
    hour_ms = 3600_000
    base = (1700000000000 // hour_ms) * hour_ms

    swaps = [
        _swap(base + 1000, 3.50),
        _swap(base + 3 * hour_ms + 1000, 3.60),  # skip 2 hours
    ]
    bars = aggregate_swaps(swaps, "1h", forward_fill=True)

    assert len(bars) == 4  # hour 0, 1 (fill), 2 (fill), 3
    assert bars[1].open == 3.50
    assert bars[1].close == 3.50
    assert bars[1].volume == 0.0
    assert bars[1].trade_count == 0
    assert bars[2].open == 3.50
    assert bars[3].open == 3.60


def test_empty_swaps():
    bars = aggregate_swaps([], "1h")
    assert bars == []


def test_single_swap():
    base = 1700000000000
    swaps = [_swap(base, 3.50)]
    bars = aggregate_swaps(swaps, "1h")
    assert len(bars) == 1
    assert bars[0].open == bars[0].close == bars[0].high == bars[0].low == 3.50
