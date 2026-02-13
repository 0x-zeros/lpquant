import pytest
import pytest_asyncio

from cetus_indexer.db import Database
from cetus_indexer.event_parser import SwapRecord
from cetus_indexer.ohlcv import OhlcvBar

POOL = "0xpool_test"


@pytest_asyncio.fixture
async def db(tmp_path):
    db_path = tmp_path / "test.db"
    d = Database(db_path)
    await d.connect()
    yield d
    await d.close()


def _swap(ts_ms: int, price: float, tx: str = "tx1", seq: int = 0) -> SwapRecord:
    return SwapRecord(
        tx_digest=tx,
        event_seq=seq,
        pool_id=POOL,
        timestamp_ms=ts_ms,
        price=price,
        volume_a=1.0,
        volume_b=price,
        atob=True,
        sqrt_price_x64="0",
    )


@pytest.mark.asyncio
async def test_insert_and_query_swaps(db: Database):
    swaps = [
        _swap(1000, 3.50, "tx1"),
        _swap(2000, 3.55, "tx2"),
    ]
    inserted = await db.insert_swaps(swaps)
    assert inserted == 2

    result = await db.get_swaps(POOL)
    assert len(result) == 2
    assert result[0].price == 3.50
    assert result[1].price == 3.55


@pytest.mark.asyncio
async def test_insert_duplicates_ignored(db: Database):
    swaps = [_swap(1000, 3.50, "tx1", 0)]
    await db.insert_swaps(swaps)
    inserted = await db.insert_swaps(swaps)  # duplicate
    assert inserted == 0


@pytest.mark.asyncio
async def test_upsert_ohlcv(db: Database):
    bars = [
        OhlcvBar(POOL, "1h", 0, 3.50, 3.55, 3.45, 3.52, 100.0, 5),
    ]
    await db.upsert_ohlcv(bars)

    result = await db.get_ohlcv(POOL, "1h")
    assert len(result) == 1
    assert result[0].open == 3.50

    # Upsert with updated values
    bars[0].close = 3.60
    await db.upsert_ohlcv(bars)
    result = await db.get_ohlcv(POOL, "1h")
    assert result[0].close == 3.60


@pytest.mark.asyncio
async def test_cursor(db: Database):
    assert await db.get_cursor() is None

    await db.set_cursor("abc123")
    assert await db.get_cursor() == "abc123"

    await db.set_cursor("def456")
    assert await db.get_cursor() == "def456"


@pytest.mark.asyncio
async def test_get_stats_empty(db: Database):
    stats = await db.get_stats()
    assert stats["total_events"] == 0
    assert stats["earliest_ms"] is None


@pytest.mark.asyncio
async def test_get_stats_with_data(db: Database):
    swaps = [
        _swap(1000, 3.50, "tx1"),
        _swap(5000, 3.55, "tx2"),
    ]
    await db.insert_swaps(swaps)
    stats = await db.get_stats()
    assert stats["total_events"] == 2
    assert stats["earliest_ms"] == 1000
    assert stats["latest_ms"] == 5000
    assert POOL in stats["pools"]
