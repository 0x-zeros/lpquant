from __future__ import annotations

from pathlib import Path

import aiosqlite

from .config import DB_PATH
from .event_parser import SwapRecord
from .ohlcv import OhlcvBar

SCHEMA = """
CREATE TABLE IF NOT EXISTS swap_events (
    tx_digest TEXT NOT NULL,
    event_seq INTEGER NOT NULL,
    pool_id TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL,
    price REAL NOT NULL,
    volume_a REAL,
    volume_b REAL,
    atob INTEGER NOT NULL,
    sqrt_price_x64 TEXT,
    PRIMARY KEY (tx_digest, event_seq)
);

CREATE INDEX IF NOT EXISTS idx_swap_pool_ts
    ON swap_events (pool_id, timestamp_ms);

CREATE TABLE IF NOT EXISTS ohlcv (
    pool_id TEXT NOT NULL,
    interval TEXT NOT NULL,
    open_time INTEGER NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    trade_count INTEGER,
    PRIMARY KEY (pool_id, interval, open_time)
);

CREATE TABLE IF NOT EXISTS poller_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    def __init__(self, db_path: str | Path = DB_PATH):
        self._db_path = str(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def __aenter__(self) -> Database:
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._conn is not None, "Database not connected"
        return self._conn

    async def insert_swaps(self, swaps: list[SwapRecord]) -> int:
        """Insert swap records, ignoring duplicates. Returns count inserted."""
        if not swaps:
            return 0
        inserted = 0
        for s in swaps:
            try:
                await self.conn.execute(
                    """INSERT INTO swap_events
                       (tx_digest, event_seq, pool_id, timestamp_ms,
                        price, volume_a, volume_b, atob, sqrt_price_x64)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        s.tx_digest,
                        s.event_seq,
                        s.pool_id,
                        s.timestamp_ms,
                        s.price,
                        s.volume_a,
                        s.volume_b,
                        int(s.atob),
                        s.sqrt_price_x64,
                    ),
                )
                inserted += 1
            except aiosqlite.IntegrityError:
                pass  # duplicate
        await self.conn.commit()
        return inserted

    async def upsert_ohlcv(self, bars: list[OhlcvBar]) -> None:
        """Upsert OHLCV bars."""
        if not bars:
            return
        await self.conn.executemany(
            """INSERT INTO ohlcv
               (pool_id, interval, open_time, open, high, low, close, volume, trade_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (pool_id, interval, open_time)
               DO UPDATE SET
                   open = excluded.open,
                   high = excluded.high,
                   low = excluded.low,
                   close = excluded.close,
                   volume = excluded.volume,
                   trade_count = excluded.trade_count""",
            [
                (
                    b.pool_id,
                    b.interval,
                    b.open_time,
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                    b.trade_count,
                )
                for b in bars
            ],
        )
        await self.conn.commit()

    async def get_ohlcv(
        self,
        pool_id: str,
        interval: str,
        start_ms: int | None = None,
        end_ms: int | None = None,
    ) -> list[OhlcvBar]:
        """Retrieve OHLCV bars for a pool/interval, optionally filtered by time."""
        query = "SELECT * FROM ohlcv WHERE pool_id = ? AND interval = ?"
        params: list = [pool_id, interval]
        if start_ms is not None:
            query += " AND open_time >= ?"
            params.append(start_ms)
        if end_ms is not None:
            query += " AND open_time <= ?"
            params.append(end_ms)
        query += " ORDER BY open_time"

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [
            OhlcvBar(
                pool_id=r[0],
                interval=r[1],
                open_time=r[2],
                open=r[3],
                high=r[4],
                low=r[5],
                close=r[6],
                volume=r[7],
                trade_count=r[8],
            )
            for r in rows
        ]

    async def get_swaps(
        self,
        pool_id: str,
        start_ms: int | None = None,
        end_ms: int | None = None,
    ) -> list[SwapRecord]:
        """Retrieve swap events for a pool, optionally filtered by time."""
        query = "SELECT * FROM swap_events WHERE pool_id = ?"
        params: list = [pool_id]
        if start_ms is not None:
            query += " AND timestamp_ms >= ?"
            params.append(start_ms)
        if end_ms is not None:
            query += " AND timestamp_ms < ?"
            params.append(end_ms)
        query += " ORDER BY timestamp_ms"

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [
            SwapRecord(
                tx_digest=r[0],
                event_seq=r[1],
                pool_id=r[2],
                timestamp_ms=r[3],
                price=r[4],
                volume_a=r[5],
                volume_b=r[6],
                atob=bool(r[7]),
                sqrt_price_x64=r[8],
            )
            for r in rows
        ]

    async def get_cursor(self) -> str | None:
        """Get the last stored pagination cursor."""
        async with self.conn.execute(
            "SELECT value FROM poller_state WHERE key = 'cursor'"
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else None

    async def set_cursor(self, cursor: str) -> None:
        """Store the pagination cursor."""
        await self.conn.execute(
            """INSERT INTO poller_state (key, value) VALUES ('cursor', ?)
               ON CONFLICT (key) DO UPDATE SET value = excluded.value""",
            (cursor,),
        )
        await self.conn.commit()

    async def get_stats(self) -> dict:
        """Get indexer statistics."""
        stats: dict = {}

        async with self.conn.execute(
            "SELECT COUNT(*) FROM swap_events"
        ) as c:
            stats["total_events"] = (await c.fetchone())[0]

        async with self.conn.execute(
            "SELECT MIN(timestamp_ms), MAX(timestamp_ms) FROM swap_events"
        ) as c:
            row = await c.fetchone()
            stats["earliest_ms"] = row[0]
            stats["latest_ms"] = row[1]

        async with self.conn.execute(
            "SELECT pool_id, COUNT(*) FROM swap_events GROUP BY pool_id"
        ) as c:
            stats["pools"] = {r[0]: r[1] for r in await c.fetchall()}

        async with self.conn.execute(
            "SELECT value FROM poller_state WHERE key = 'cursor'"
        ) as c:
            row = await c.fetchone()
            stats["cursor"] = row[0] if row else None

        return stats
