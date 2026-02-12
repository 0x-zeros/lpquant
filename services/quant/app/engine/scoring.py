"""Fixed probability-based scoring and selection for LP range candidates."""

from __future__ import annotations

from app.schemas import BacktestMetrics


def _efficiency_score(metrics: BacktestMetrics) -> float:
    """Capital efficiency score normalized to [0, 1]."""
    eff = metrics.capital_efficiency
    # cap_eff is sqrt(pb/pa), typical range 1-100+
    # Normalize: log scale, cap at ~50x
    if eff <= 1:
        return 0.0
    import math
    return min(math.log(eff) / math.log(50), 1.0)


def score_and_select(
    candidates: list[dict],
) -> tuple[dict | None, dict | None, dict | None]:
    """Score candidates and select best balanced, best narrow, and best backtest.

    Scoring formula for balanced/narrow:
        0.50 × estimated_prob + 0.30 × backtest_in_range + 0.20 × efficiency_score

    Best backtest: highest lp_vs_hodl_pct across all candidates.

    Returns (best_balanced, best_narrow, best_backtest).
    """
    if not candidates:
        return (None, None, None)

    # Score all candidates
    for cand in candidates:
        metrics: BacktestMetrics = cand["metrics"]
        est_prob = cand.get("estimated_prob", 0.0)
        in_range_norm = metrics.in_range_pct / 100.0
        eff = _efficiency_score(metrics)

        score = 0.50 * est_prob + 0.30 * in_range_norm + 0.20 * eff
        cand["score"] = round(score * 100, 2)  # scale to 0-100

    # Generate insights
    for cand in candidates:
        cand["insight"] = _generate_insight(cand)
        cand["insight_data"] = _generate_insight_data(cand)

    # Select best balanced
    balanced = [c for c in candidates if c.get("range_type") == "balanced"]
    best_balanced = max(balanced, key=lambda c: c["score"]) if balanced else None

    # Select best narrow
    narrow = [c for c in candidates if c.get("range_type") == "narrow"]
    best_narrow = max(narrow, key=lambda c: c["score"]) if narrow else None

    # Select best backtest (highest lp_vs_hodl_pct across all)
    best_backtest = max(
        candidates,
        key=lambda c: c["metrics"].lp_vs_hodl_pct,
    )

    return (best_balanced, best_narrow, best_backtest)


def _generate_insight(cand: dict) -> str:
    """Return a human-readable one-liner for the candidate."""
    metrics: BacktestMetrics = cand["metrics"]
    width_pct: float = cand.get("width_pct", 0.0)
    est_prob: float = cand.get("estimated_prob", 0.0)
    range_type: str = cand.get("range_type", "")
    k: float = cand.get("k_sigma", 0.0)

    parts: list[str] = []

    if range_type == "balanced":
        parts.append(
            f"{k:.1f}σ range ({width_pct:.1f}% width) with "
            f"{est_prob * 100:.0f}% estimated stay probability"
        )
    elif range_type == "narrow":
        parts.append(
            f"Tight {k:.1f}σ range ({width_pct:.1f}% width) — "
            f"{est_prob * 100:.0f}% stay probability, high efficiency"
        )
    else:
        parts.append(
            f"Range ({width_pct:.1f}% width) with {metrics.in_range_pct:.0f}% "
            f"historical in-range time"
        )

    lp_vs_hodl = metrics.lp_vs_hodl_pct
    if lp_vs_hodl > 0:
        parts.append(f"LP outperforms HODL by {lp_vs_hodl:.1f}%")
    elif lp_vs_hodl < -5:
        parts.append(f"LP underperforms HODL by {abs(lp_vs_hodl):.1f}%")

    if metrics.max_il_pct > 10:
        parts.append(f"max IL reached {metrics.max_il_pct:.1f}%")

    return ". ".join(parts) + "."


def _generate_insight_data(cand: dict) -> dict:
    """Return structured insight data for client-side rendering."""
    metrics: BacktestMetrics = cand["metrics"]
    width_pct: float = cand.get("width_pct", 0.0)
    est_prob: float = cand.get("estimated_prob", 0.0)
    k: float = cand.get("k_sigma", 0.0)
    range_type: str = cand.get("range_type", "")

    return {
        "range_type": range_type,
        "k_sigma": round(k, 2),
        "estimated_prob": round(est_prob, 4),
        "width_pct": round(width_pct, 1),
        "backtest_in_range_pct": round(metrics.in_range_pct, 1),
        "lp_vs_hodl_pct": round(metrics.lp_vs_hodl_pct, 1),
        "lp_outperforms": metrics.lp_vs_hodl_pct > 0,
        "max_il_pct": round(metrics.max_il_pct, 1),
        "il_warning": metrics.max_il_pct > 10,
        "capital_efficiency": round(metrics.capital_efficiency, 1),
    }
