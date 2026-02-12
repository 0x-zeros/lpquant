"""Tests for sigma-based range candidate generation."""

import math

import pytest

from app.engine.volatility import VolatilityEstimate
from app.engine.candidates import generate_ranges, _estimate_path_prob


class TestEstimatePathProb:
    def test_monotonically_increasing(self):
        """Probability should increase with k."""
        ks = [0.5, 0.75, 1.0, 1.5, 1.75, 2.0, 2.5, 3.0]
        probs = [_estimate_path_prob(k) for k in ks]
        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1], (
                f"P(k={ks[i]})={probs[i]:.4f} >= P(k={ks[i+1]})={probs[i+1]:.4f}"
            )

    def test_range_0_to_1(self):
        """Probability should be in [0, 1]."""
        for k in [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]:
            p = _estimate_path_prob(k)
            assert 0 <= p <= 1, f"P(k={k})={p} out of range"

    def test_near_zero_k(self):
        """Very small k should give near-zero probability."""
        p = _estimate_path_prob(0.01)
        assert p < 0.01

    def test_large_k(self):
        """Large k should approach 1."""
        p = _estimate_path_prob(5.0)
        assert p > 0.99


class TestGenerateRanges:
    @pytest.fixture
    def vol_estimate(self):
        return VolatilityEstimate(
            sigma_annual=0.80,
            sigma_realized=0.75,
            sigma_atr=0.85,
            sigma_ewma=0.80,
            regime="normal",
            regime_multiplier=1.0,
        )

    def test_generates_6_candidates(self, vol_estimate):
        candidates = generate_ranges(3.50, vol_estimate, 7.0)
        assert len(candidates) == 6

    def test_3_balanced_3_narrow(self, vol_estimate):
        candidates = generate_ranges(3.50, vol_estimate, 7.0)
        balanced = [c for c in candidates if c.range_type == "balanced"]
        narrow = [c for c in candidates if c.range_type == "narrow"]
        assert len(balanced) == 3
        assert len(narrow) == 3

    def test_ranges_symmetric_around_price(self, vol_estimate):
        price = 3.50
        candidates = generate_ranges(price, vol_estimate, 7.0)
        for c in candidates:
            # pa < price < pb
            assert c.pa < price
            assert c.pb > price
            # Log-symmetric: ln(pb/price) ≈ ln(price/pa)
            log_upper = math.log(c.pb / price)
            log_lower = math.log(price / c.pa)
            assert abs(log_upper - log_lower) < 1e-10

    def test_wider_k_gives_wider_range(self, vol_estimate):
        candidates = generate_ranges(3.50, vol_estimate, 7.0)
        balanced = sorted(
            [c for c in candidates if c.range_type == "balanced"],
            key=lambda c: c.k,
        )
        for i in range(len(balanced) - 1):
            width_i = balanced[i].pb - balanced[i].pa
            width_next = balanced[i + 1].pb - balanced[i + 1].pa
            assert width_next > width_i

    def test_probability_monotonic_within_type(self, vol_estimate):
        candidates = generate_ranges(3.50, vol_estimate, 7.0)
        for range_type in ("balanced", "narrow"):
            typed = sorted(
                [c for c in candidates if c.range_type == range_type],
                key=lambda c: c.k,
            )
            for i in range(len(typed) - 1):
                assert typed[i].estimated_prob < typed[i + 1].estimated_prob

    def test_longer_horizon_gives_wider_range(self, vol_estimate):
        cands_7d = generate_ranges(3.50, vol_estimate, 7.0)
        cands_14d = generate_ranges(3.50, vol_estimate, 14.0)
        # Same k, longer horizon => wider range
        for c7, c14 in zip(cands_7d, cands_14d):
            width_7 = c7.pb - c7.pa
            width_14 = c14.pb - c14.pa
            assert width_14 > width_7
