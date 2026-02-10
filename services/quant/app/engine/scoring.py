"""Profile-weighted scoring and insight generation for LP range candidates."""

from __future__ import annotations

from app.schemas import BacktestMetrics


# ---------------------------------------------------------------------------
# Profile weight definitions
# ---------------------------------------------------------------------------
# Each weight dict maps metric names to (weight, inverted) pairs.
# ``inverted=True`` means *lower is better* (e.g. max_il_pct).

PROFILES: dict[str, dict[str, tuple[float, bool]]] = {
    "conservative": {
        "in_range_pct": (0.40, False),
        "max_il_pct": (0.30, True),
        "max_drawdown_pct": (0.20, True),
        "lp_vs_hodl_pct": (0.10, False),
    },
    "balanced": {
        "in_range_pct": (0.25, False),
        "lp_vs_hodl_pct": (0.25, False),
        "max_il_pct": (0.20, True),
        "max_drawdown_pct": (0.15, True),
        "boundary_touches": (0.15, True),
    },
    "aggressive": {
        "lp_vs_hodl_pct": (0.40, False),
        "capital_efficiency": (0.25, False),
        "max_il_pct": (0.15, True),
        "max_drawdown_pct": (0.10, True),
        "boundary_touches": (0.10, True),
    },
}


def _extract_metric(metrics: BacktestMetrics, name: str) -> float:
    """Safely extract a metric value by name."""
    return float(getattr(metrics, name))


def _normalize(values: list[float]) -> list[float]:
    """Min-max normalize a list of values to [0, 100]."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span == 0:
        return [50.0] * len(values)
    return [(v - lo) / span * 100.0 for v in values]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_candidates(
    candidates: list[dict],
    profile: str,
) -> list[dict]:
    """Score and sort *candidates* according to *profile* weights.

    Each element of *candidates* must contain a ``"metrics"`` key holding a
    :class:`BacktestMetrics` instance.  The function adds a ``"score"`` key
    (float in [0, 100]) and an ``"insight"`` key (str) to each candidate
    dict, then returns the list sorted by score descending.
    """
    weights = PROFILES.get(profile, PROFILES["balanced"])

    if not candidates:
        return candidates

    # Gather raw metric vectors for normalization
    metric_names = list(weights.keys())
    raw: dict[str, list[float]] = {m: [] for m in metric_names}
    for cand in candidates:
        metrics: BacktestMetrics = cand["metrics"]
        for m in metric_names:
            raw[m].append(_extract_metric(metrics, m))

    # Normalize each metric
    normed: dict[str, list[float]] = {}
    for m in metric_names:
        normed[m] = _normalize(raw[m])

    # Compute composite score per candidate
    for idx, cand in enumerate(candidates):
        total = 0.0
        for m, (w, inverted) in weights.items():
            value = normed[m][idx]
            if inverted:
                value = 100.0 - value
            total += w * value
        cand["score"] = round(total, 2)

    # Generate insights
    for cand in candidates:
        cand["insight"] = _generate_insight(cand)

    # Sort descending by score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


# ---------------------------------------------------------------------------
# Insight generation
# ---------------------------------------------------------------------------

def _generate_insight(cand: dict) -> str:
    """Return a human-readable one-liner describing the candidate's trade-off."""
    metrics: BacktestMetrics = cand["metrics"]
    width_pct: float = cand.get("width_pct", 0.0)
    in_range = metrics.in_range_pct
    il = metrics.max_il_pct
    eff = metrics.capital_efficiency
    lp_vs_hodl = metrics.lp_vs_hodl_pct

    parts: list[str] = []

    # Width characterisation
    if width_pct < 3:
        parts.append(
            f"Tight range ({width_pct:.1f}% width) with {in_range:.0f}% in-range time "
            f"-- high capital efficiency but watch for IL"
        )
    elif width_pct < 10:
        parts.append(
            f"Moderate range ({width_pct:.1f}% width) capturing {in_range:.0f}% of "
            f"price action"
        )
    else:
        parts.append(
            f"Wide range ({width_pct:.1f}% width) captures {in_range:.0f}% of price "
            f"action -- lower IL risk at cost of efficiency"
        )

    # LP vs HODL hint
    if lp_vs_hodl > 0:
        parts.append(f"LP outperforms HODL by {lp_vs_hodl:.1f}%")
    elif lp_vs_hodl < -5:
        parts.append(f"LP underperforms HODL by {abs(lp_vs_hodl):.1f}%")

    # IL warning
    if il > 10:
        parts.append(f"max IL reached {il:.1f}% -- consider tighter rebalance")

    return ". ".join(parts) + "."
