"""Range candidate generation strategies for CLMM positions."""

import numpy as np


def generate_quantile_ranges(closes: np.ndarray) -> list[tuple[float, float, str]]:
    """Generate candidate ranges based on historical price percentiles.

    Creates three ranges using (P5,P95), (P10,P90), and (P25,P75) quantile
    pairs of the close price series.
    """
    if len(closes) == 0:
        return []
    ranges: list[tuple[float, float, str]] = []
    for lo_q, hi_q in [(5, 95), (10, 90), (25, 75)]:
        pa = float(np.percentile(closes, lo_q))
        pb = float(np.percentile(closes, hi_q))
        if pa >= pb:
            # Degenerate case -- skip
            continue
        ranges.append((pa, pb, f"quantile_P{lo_q}_P{hi_q}"))
    return ranges


def generate_volband_ranges(
    closes: np.ndarray, window: int = 24
) -> list[tuple[float, float, str]]:
    """Generate candidate ranges using SMA +/- k * std (volatility bands).

    Uses the last *window* data points to compute mean and standard deviation,
    then creates bands at 1x, 1.5x, and 2x sigma.
    """
    if len(closes) == 0:
        return []
    tail = closes[-window:]
    sma = float(np.mean(tail))
    std = float(np.std(tail))
    if std == 0:
        # No volatility -- fallback to a tiny band around SMA
        std = sma * 0.001

    ranges: list[tuple[float, float, str]] = []
    for k in [1.0, 1.5, 2.0]:
        pa = sma - k * std
        pb = sma + k * std
        ranges.append((max(pa, 1e-8), pb, f"volband_{k}x"))
    return ranges


def generate_swing_ranges(closes: np.ndarray) -> list[tuple[float, float, str]]:
    """Generate ranges based on local min/max swing points.

    Scans the close price series for local extrema using a rolling window,
    then constructs a *recent* range (median of last few swings) and a *full*
    range (absolute min/max of all detected swings).
    """
    if len(closes) < 10:
        return []

    window = max(5, len(closes) // 20)
    ranges: list[tuple[float, float, str]] = []

    # Detect local minima and maxima
    local_mins: list[float] = []
    local_maxs: list[float] = []
    for i in range(window, len(closes) - window):
        segment = closes[i - window : i + window + 1]
        if closes[i] == float(np.min(segment)):
            local_mins.append(float(closes[i]))
        if closes[i] == float(np.max(segment)):
            local_maxs.append(float(closes[i]))

    # Recent swings -- tight range
    if local_mins and local_maxs:
        pa = (
            float(np.median(local_mins[-3:]))
            if len(local_mins) >= 3
            else float(min(local_mins))
        )
        pb = (
            float(np.median(local_maxs[-3:]))
            if len(local_maxs) >= 3
            else float(max(local_maxs))
        )
        if pa < pb:
            ranges.append((pa, pb, "swing_recent"))

    # Full swings -- wide range
    if local_mins and local_maxs:
        pa = float(min(local_mins))
        pb = float(max(local_maxs))
        if pa < pb:
            ranges.append((pa, pb, "swing_full"))

    return ranges


def generate_extreme_ranges(
    current_price: float,
) -> list[tuple[float, float, str]]:
    """Generate narrow extreme ranges centred on the current price.

    Creates fixed-width ranges of 2% and 5% around *current_price*.
    """
    ranges: list[tuple[float, float, str]] = []
    for width_pct in [2.0, 5.0]:
        half = width_pct / 100 / 2
        pa = current_price * (1 - half)
        pb = current_price * (1 + half)
        ranges.append((pa, pb, f"extreme_{width_pct}pct"))
    return ranges
