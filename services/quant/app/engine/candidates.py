"""Sigma-based range candidate generation for CLMM positions.

Generates balanced and narrow LP ranges using volatility forecasts
instead of historical pattern matching.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from app.engine.volatility import VolatilityEstimate


class RangeCandidate(NamedTuple):
    pa: float
    pb: float
    label: str
    range_type: str  # "balanced" | "narrow"
    k: float
    sigma_T: float
    estimated_prob: float


def _estimate_path_prob(k: float) -> float:
    """Estimate probability that price stays within [-k*sigma, +k*sigma] over the horizon.

    Uses the approximation: P ≈ erf(k/√2) × (1 - exp(-k²))
    This is more conservative than endpoint probability, accounting for
    path dependency (price can exit and re-enter).
    """
    erf_term = math.erf(k / math.sqrt(2))
    path_penalty = 1.0 - math.exp(-(k ** 2))
    return erf_term * path_penalty


def generate_ranges(
    current_price: float,
    vol_estimate: VolatilityEstimate,
    horizon_days: float,
) -> list[RangeCandidate]:
    """Generate balanced and narrow range candidates based on sigma.

    Balanced: k = [1.5, 1.75, 2.0] — wider ranges, higher stay probability.
    Narrow:   k = [0.5, 0.75, 1.0] — tighter ranges, higher capital efficiency.

    Range formula: pa = price * exp(-k * σ_T), pb = price * exp(+k * σ_T)
    where σ_T = σ_annual * sqrt(T / 365).
    """
    sigma_T = vol_estimate.sigma_annual * math.sqrt(horizon_days / 365.0)

    # Ensure sigma_T has a minimum to avoid degenerate ranges
    sigma_T = max(sigma_T, 0.001)

    candidates: list[RangeCandidate] = []

    balanced_ks = [1.5, 1.75, 2.0]
    narrow_ks = [0.5, 0.75, 1.0]

    for k in balanced_ks:
        pa = current_price * math.exp(-k * sigma_T)
        pb = current_price * math.exp(k * sigma_T)
        prob = _estimate_path_prob(k)
        candidates.append(RangeCandidate(
            pa=pa,
            pb=pb,
            label=f"balanced_{k}σ",
            range_type="balanced",
            k=k,
            sigma_T=sigma_T,
            estimated_prob=prob,
        ))

    for k in narrow_ks:
        pa = current_price * math.exp(-k * sigma_T)
        pb = current_price * math.exp(k * sigma_T)
        prob = _estimate_path_prob(k)
        candidates.append(RangeCandidate(
            pa=pa,
            pb=pb,
            label=f"narrow_{k}σ",
            range_type="narrow",
            k=k,
            sigma_T=sigma_T,
            estimated_prob=prob,
        ))

    return candidates
