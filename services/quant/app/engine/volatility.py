"""Volatility estimation module for LP range recommendations.

Provides multiple volatility estimators and a regime detection mechanism
to produce a blended, forward-looking volatility estimate.
"""

from __future__ import annotations

import math
from typing import NamedTuple

import numpy as np


class VolatilityEstimate(NamedTuple):
    sigma_annual: float
    sigma_realized: float
    sigma_atr: float
    sigma_ewma: float
    regime: str  # "low" | "normal" | "high"
    regime_multiplier: float


def realized_volatility(
    closes: np.ndarray,
    annualize_factor: float = 365 * 24,
) -> float:
    """Close-to-close log-return standard deviation, annualized."""
    if len(closes) < 2:
        return 0.0
    log_returns = np.diff(np.log(closes))
    return float(np.std(log_returns, ddof=1)) * math.sqrt(annualize_factor)


def atr_volatility(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
    annualize_factor: float = 365 * 24,
) -> float:
    """ATR-based volatility, annualized.

    True Range = max(H-L, |H-Cprev|, |L-Cprev|).
    ATR = EMA of True Range over *period*.
    Annualized as (ATR / mean_close) * sqrt(annualize_factor).
    """
    n = len(closes)
    if n < 2:
        return 0.0

    prev_closes = closes[:-1]
    h = highs[1:]
    l = lows[1:]

    tr = np.maximum(
        h - l,
        np.maximum(np.abs(h - prev_closes), np.abs(l - prev_closes)),
    )

    if len(tr) == 0:
        return 0.0

    # EMA smoothing
    alpha = 2.0 / (period + 1)
    atr_val = float(tr[0])
    for i in range(1, len(tr)):
        atr_val = alpha * float(tr[i]) + (1 - alpha) * atr_val

    mean_close = float(np.mean(closes))
    if mean_close <= 0:
        return 0.0

    return (atr_val / mean_close) * math.sqrt(annualize_factor)


def ewma_volatility(
    closes: np.ndarray,
    span: int = 24,
    annualize_factor: float = 365 * 24,
) -> float:
    """EWMA volatility (emphasizes recent data), annualized."""
    if len(closes) < 2:
        return 0.0
    log_returns = np.diff(np.log(closes))
    alpha = 2.0 / (span + 1)

    var = float(log_returns[0] ** 2)
    for i in range(1, len(log_returns)):
        var = alpha * float(log_returns[i] ** 2) + (1 - alpha) * var

    return math.sqrt(var) * math.sqrt(annualize_factor)


def detect_regime(
    closes: np.ndarray,
    short_window: int = 24,
    long_window: int = 168,
) -> tuple[str, float]:
    """Detect volatility regime by comparing short vs long realized vol.

    Returns (regime_label, multiplier).
    """
    if len(closes) < long_window + 1:
        return ("normal", 1.0)

    short_vol = realized_volatility(closes[-short_window:], annualize_factor=1.0)
    long_vol = realized_volatility(closes[-long_window:], annualize_factor=1.0)

    if long_vol <= 0:
        return ("normal", 1.0)

    ratio = short_vol / long_vol

    if ratio < 0.8:
        return ("low", 0.85)
    elif ratio > 1.3:
        return ("high", 1.15)
    else:
        return ("normal", 1.0)


def estimate_volatility(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    annualize_factor: float = 365 * 24,
) -> VolatilityEstimate:
    """Integrated volatility estimator.

    Blends realized (40%), EWMA (35%), and ATR (25%) volatility,
    adjusted by regime multiplier. Floors at 5% annualized.
    """
    sigma_rv = realized_volatility(closes, annualize_factor)
    sigma_atr = atr_volatility(highs, lows, closes, annualize_factor=annualize_factor)
    sigma_ewma = ewma_volatility(closes, annualize_factor=annualize_factor)

    regime, multiplier = detect_regime(closes)

    blended = 0.40 * sigma_rv + 0.35 * sigma_ewma + 0.25 * sigma_atr
    blended *= multiplier

    # Floor at 5% annualized
    blended = max(blended, 0.05)

    return VolatilityEstimate(
        sigma_annual=blended,
        sigma_realized=sigma_rv,
        sigma_atr=sigma_atr,
        sigma_ewma=sigma_ewma,
        regime=regime,
        regime_multiplier=multiplier,
    )
