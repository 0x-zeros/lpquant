from __future__ import annotations

import math

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "trend_pct",
    "realized_vol_pct",
    "downside_vol_pct",
    "distance_to_sma_pct",
    "drawdown_pct",
    "rsi",
]


def interval_to_hours(interval: str) -> float:
    token = interval.strip()
    if not token:
        raise ValueError("interval is required")

    unit = token[-1]
    value = int(token[:-1])
    if unit == "m":
        return value / 60.0
    if unit == "h":
        return float(value)
    if unit == "d":
        return float(value * 24)
    if unit == "w":
        return float(value * 24 * 7)

    raise ValueError(f"unsupported interval {interval!r}; use m/h/d/w intervals")


def bars_per_year(interval: str) -> float:
    hours = interval_to_hours(interval)
    return 24.0 * 365.0 / hours


def build_feature_frame(
    frame: pd.DataFrame,
    lookback_bars: int,
    interval: str,
) -> pd.DataFrame:
    if lookback_bars < 5:
        raise ValueError("lookback_bars must be at least 5")

    feature_frame = frame.copy()
    close = feature_frame["close"].astype(float)
    log_return = np.log(close).diff()
    annualizer = math.sqrt(bars_per_year(interval))

    feature_frame["log_return"] = log_return
    feature_frame["trend_pct"] = close.pct_change(lookback_bars) * 100.0
    feature_frame["realized_vol_pct"] = log_return.rolling(lookback_bars).std() * annualizer * 100.0
    feature_frame["downside_vol_pct"] = (
        log_return.where(log_return < 0).rolling(lookback_bars).std() * annualizer * 100.0
    ).fillna(0.0)
    sma = close.rolling(lookback_bars).mean()
    feature_frame["distance_to_sma_pct"] = (close / sma - 1.0) * 100.0
    rolling_max = close.rolling(lookback_bars).max()
    feature_frame["drawdown_pct"] = (close / rolling_max - 1.0) * 100.0

    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.rolling(lookback_bars).mean()
    avg_loss = losses.rolling(lookback_bars).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss > 0, 100.0)
    rsi = rsi.where(avg_gain > 0, 0.0)
    feature_frame["rsi"] = rsi.where((avg_gain > 0) | (avg_loss > 0), 50.0)

    return feature_frame


def describe_current_regime(feature_frame: pd.DataFrame) -> dict[str, float | str]:
    valid = feature_frame.dropna(subset=FEATURE_COLUMNS)
    if valid.empty:
        raise ValueError("not enough feature history to describe the current regime")

    latest = valid.iloc[-1]
    vol_rank = float(valid["realized_vol_pct"].rank(pct=True).iloc[-1])

    if latest["trend_pct"] >= 5:
        trend_label = "bullish"
    elif latest["trend_pct"] <= -5:
        trend_label = "bearish"
    else:
        trend_label = "sideways"

    if vol_rank >= 0.66:
        vol_label = "high-vol"
    elif vol_rank <= 0.33:
        vol_label = "low-vol"
    else:
        vol_label = "mid-vol"

    rsi = float(latest["rsi"])
    if rsi >= 60:
        momentum_label = "overbought"
    elif rsi <= 40:
        momentum_label = "oversold"
    else:
        momentum_label = "balanced"

    return {
        "regime_label": f"{trend_label} / {vol_label} / {momentum_label}",
        "trend_pct": round(float(latest["trend_pct"]), 2),
        "realized_vol_pct": round(float(latest["realized_vol_pct"]), 2),
        "downside_vol_pct": round(float(latest["downside_vol_pct"]), 2),
        "distance_to_sma_pct": round(float(latest["distance_to_sma_pct"]), 2),
        "drawdown_pct": round(float(latest["drawdown_pct"]), 2),
        "rsi": round(rsi, 2),
        "vol_rank": round(vol_rank, 3),
        "current_price": round(float(latest["close"]), 6),
    }


def select_similar_windows(
    feature_frame: pd.DataFrame,
    horizon_bars: int,
    neighbors: int,
) -> pd.DataFrame:
    current_row = feature_frame.iloc[-1]
    candidates = feature_frame.iloc[:-horizon_bars].dropna(subset=FEATURE_COLUMNS).copy()
    if candidates.empty:
        raise ValueError("not enough fully-featured historical windows to compare against")

    feature_slice = candidates[FEATURE_COLUMNS]
    means = feature_slice.mean()
    stds = feature_slice.std().replace(0, 1.0)
    scaled = (feature_slice - means) / stds
    current_scaled = (current_row[FEATURE_COLUMNS] - means) / stds
    distances = np.sqrt(((scaled - current_scaled) ** 2).sum(axis=1))

    candidates["distance"] = distances
    candidates["entry_index"] = candidates.index
    candidates["entry_time"] = pd.to_datetime(candidates["timestamp"], unit="ms", utc=True)
    limit = max(1, min(int(neighbors), len(candidates)))
    candidates = candidates.nsmallest(limit, "distance").reset_index(drop=True)
    candidates["similarity_rank"] = np.arange(1, len(candidates) + 1)
    return candidates
