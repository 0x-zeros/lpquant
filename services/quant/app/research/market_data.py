from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd

from app.research.types import PairSpec, PriceDataset, SourceMode

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
MAX_LIMIT = 1000
STABLE_QUOTES = ("USDT", "USDC", "FDUSD", "BUSD")
KNOWN_QUOTES = ("USDC", "USDT", "FDUSD", "BUSD", "BTC", "ETH", "SOL", "SUI")


class MarketDataUnavailable(RuntimeError):
    """当请求的交易对无法从已配置数据源解析时抛出。"""


def parse_pair(raw_pair: str) -> PairSpec:
    cleaned = raw_pair.strip().upper().replace(" ", "")
    if not cleaned:
        raise ValueError("必须提供交易对")

    for delimiter in ("/", "-", "_", ":"):
        if delimiter in cleaned:
            base, quote = cleaned.split(delimiter, 1)
            if not base or not quote:
                break
            return PairSpec(base=base, quote=quote)

    for quote in sorted(KNOWN_QUOTES, key=len, reverse=True):
        if cleaned.endswith(quote) and cleaned != quote:
            base = cleaned[: -len(quote)]
            if base:
                return PairSpec(base=base, quote=quote)

    raise ValueError(
        "无法解析交易对，请使用 BTC/USDC、SUI-USDC 或 BTCUSDC 这类格式"
    )


def fetch_binance_klines(
    symbol: str,
    interval: str,
    start_ms: int,
    end_ms: int,
) -> pd.DataFrame:
    all_rows: list[dict[str, float | int]] = []
    current_start = start_ms

    with httpx.Client(timeout=20.0, headers={"User-Agent": "lpquant-research/0.1"}) as client:
        while current_start < end_ms:
            response = client.get(
                BINANCE_KLINES_URL,
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": current_start,
                    "endTime": end_ms,
                    "limit": MAX_LIMIT,
                },
            )
            if response.status_code != 200:
                raise MarketDataUnavailable(
                    f"Binance 拒绝了 {symbol} {interval} 请求：{response.status_code} {response.text}"
                )

            payload = response.json()
            if not payload:
                break

            for row in payload:
                all_rows.append(
                    {
                        "timestamp": int(row[0]),
                        "open": float(row[1]),
                        "high": float(row[2]),
                        "low": float(row[3]),
                        "close": float(row[4]),
                        "volume": float(row[5]),
                    }
                )

            last_open_time = int(payload[-1][0])
            if len(payload) < MAX_LIMIT or last_open_time >= end_ms:
                break
            current_start = last_open_time + 1

    if not all_rows:
        raise MarketDataUnavailable(f"Binance 没有返回 {symbol} 的任何数据")

    frame = pd.DataFrame.from_records(all_rows)
    frame = (
        frame.drop_duplicates(subset="timestamp")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    return frame


def _build_ratio_frame(
    base_frame: pd.DataFrame,
    quote_frame: pd.DataFrame,
) -> pd.DataFrame:
    merged = base_frame.merge(
        quote_frame,
        on="timestamp",
        suffixes=("_base", "_quote"),
        how="inner",
    )
    if merged.empty:
        raise MarketDataUnavailable("比价构造后的合并结果为空")

    for column in ("open", "high", "low", "close"):
        quote_col = f"{column}_quote"
        if (merged[quote_col] <= 0).any():
            raise MarketDataUnavailable("比价构造过程中出现了非正数的报价价格")

    return pd.DataFrame(
        {
            "timestamp": merged["timestamp"],
            "open": merged["open_base"] / merged["open_quote"],
            "high": merged["high_base"] / merged["high_quote"],
            "low": merged["low_base"] / merged["low_quote"],
            "close": merged["close_base"] / merged["close_quote"],
            "volume": merged["volume_base"],
        }
    ).reset_index(drop=True)


def _build_dataset(
    pair: PairSpec,
    interval: str,
    source: SourceMode,
    frame: pd.DataFrame,
    notes: list[str],
) -> PriceDataset:
    min_required = 50
    if len(frame) < min_required:
        raise MarketDataUnavailable(
            f"{pair.symbol} 只拿到了 {len(frame)} 条数据，至少需要 {min_required} 条"
        )
    return PriceDataset(pair=pair, interval=interval, source=source, frame=frame, notes=notes)


def load_price_history(
    raw_pair: str,
    interval: str,
    days: int,
    end_time: datetime | None = None,
) -> PriceDataset:
    pair = parse_pair(raw_pair)
    end_dt = end_time or datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    errors: list[str] = []

    direct_symbol = f"{pair.base}{pair.quote}"
    try:
        direct_frame = fetch_binance_klines(direct_symbol, interval, start_ms, end_ms)
        return _build_dataset(pair, interval, "binance-direct", direct_frame, [])
    except MarketDataUnavailable as exc:
        errors.append(f"直连 {direct_symbol}: {exc}")

    if pair.quote != "USDT":
        base_usdt = f"{pair.base}USDT"
        quote_usdt = f"{pair.quote}USDT"
        try:
            base_frame = fetch_binance_klines(base_usdt, interval, start_ms, end_ms)
            quote_frame = fetch_binance_klines(quote_usdt, interval, start_ms, end_ms)
            ratio_frame = _build_ratio_frame(base_frame, quote_frame)
            notes = [
                f"Binance 没有直接提供 {pair.symbol}，当前使用 {base_usdt} / {quote_usdt} 的比价结果。",
            ]
            return _build_dataset(pair, interval, "binance-ratio", ratio_frame, notes)
        except MarketDataUnavailable as exc:
            errors.append(f"比价 {base_usdt}/{quote_usdt}: {exc}")

    if pair.quote in STABLE_QUOTES and pair.quote != "USDT":
        proxy_symbol = f"{pair.base}USDT"
        try:
            proxy_frame = fetch_binance_klines(proxy_symbol, interval, start_ms, end_ms)
            notes = [
                f"{pair.symbol} 既没有直连数据，也没有可用的稳定币比价数据，当前使用 {proxy_symbol} 作为稳定币代理。",
            ]
            return _build_dataset(pair, interval, "binance-proxy", proxy_frame, notes)
        except MarketDataUnavailable as exc:
            errors.append(f"稳定币代理 {proxy_symbol}: {exc}")

    joined_errors = "; ".join(errors) if errors else "没有找到可用的 Binance 路径"
    raise MarketDataUnavailable(f"{pair.symbol} 当前无法从 Binance 路径获取：{joined_errors}")
