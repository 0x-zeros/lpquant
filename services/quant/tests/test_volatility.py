"""Tests for volatility estimation module."""

import math

import numpy as np
import pytest

from app.engine.volatility import (
    realized_volatility,
    atr_volatility,
    ewma_volatility,
    detect_regime,
    estimate_volatility,
)


def _make_random_walk(n: int, start: float = 100.0, seed: int = 42) -> np.ndarray:
    """Generate a simple random walk price series."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0, 0.01, n)
    prices = start * np.exp(np.cumsum(returns))
    return prices


def _make_ohlc(closes: np.ndarray, spread: float = 0.005):
    """Generate synthetic highs/lows from closes."""
    highs = closes * (1 + spread * np.abs(np.random.default_rng(1).normal(size=len(closes))))
    lows = closes * (1 - spread * np.abs(np.random.default_rng(2).normal(size=len(closes))))
    return highs, lows


class TestRealizedVolatility:
    def test_positive_output(self):
        closes = _make_random_walk(200)
        rv = realized_volatility(closes)
        assert rv > 0

    def test_constant_prices_zero_vol(self):
        closes = np.full(100, 50.0)
        rv = realized_volatility(closes)
        assert rv == 0.0

    def test_too_few_data(self):
        assert realized_volatility(np.array([100.0])) == 0.0
        assert realized_volatility(np.array([])) == 0.0

    def test_annualization(self):
        closes = _make_random_walk(500)
        rv_hourly = realized_volatility(closes, annualize_factor=365 * 24)
        rv_daily = realized_volatility(closes, annualize_factor=365)
        # Hourly annualization should be larger than daily
        assert rv_hourly > rv_daily


class TestAtrVolatility:
    def test_positive_output(self):
        closes = _make_random_walk(200)
        highs, lows = _make_ohlc(closes)
        atr = atr_volatility(highs, lows, closes)
        assert atr > 0

    def test_too_few_data(self):
        closes = np.array([100.0])
        highs = np.array([101.0])
        lows = np.array([99.0])
        assert atr_volatility(highs, lows, closes) == 0.0


class TestEwmaVolatility:
    def test_positive_output(self):
        closes = _make_random_walk(200)
        ewma = ewma_volatility(closes)
        assert ewma > 0

    def test_too_few_data(self):
        assert ewma_volatility(np.array([100.0])) == 0.0


class TestDetectRegime:
    def test_normal_regime(self):
        closes = _make_random_walk(300, seed=42)
        regime, mult = detect_regime(closes)
        assert regime in ("low", "normal", "high")
        assert mult in (0.85, 1.0, 1.15)

    def test_short_data_returns_normal(self):
        closes = _make_random_walk(50)
        regime, mult = detect_regime(closes)
        assert regime == "normal"
        assert mult == 1.0


class TestEstimateVolatility:
    def test_returns_volatility_estimate(self):
        closes = _make_random_walk(500)
        highs, lows = _make_ohlc(closes)
        est = estimate_volatility(closes, highs, lows)
        assert est.sigma_annual >= 0.05  # floor check
        assert est.sigma_realized > 0
        assert est.sigma_atr > 0
        assert est.sigma_ewma > 0
        assert est.regime in ("low", "normal", "high")

    def test_floor_at_5_percent(self):
        # Constant prices should hit the 5% floor
        closes = np.full(500, 100.0)
        highs = np.full(500, 100.0)
        lows = np.full(500, 100.0)
        est = estimate_volatility(closes, highs, lows)
        assert est.sigma_annual == 0.05
