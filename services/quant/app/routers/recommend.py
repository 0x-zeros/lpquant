"""POST /api/v1/recommend -- Cetus CLMM range recommendation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
import numpy as np

from app.schemas import (
    BacktestMetrics,
    CandidateResult,
    ChartSeries,
    RecommendRequest,
    RecommendResponse,
)
from app.engine.tick_math import (
    align_tick_down,
    align_tick_up,
    price_to_tick,
    tick_to_price,
)
from app.engine.candidates import (
    generate_extreme_ranges,
    generate_quantile_ranges,
    generate_swing_ranges,
    generate_volband_ranges,
)
from app.engine.backtest import run_backtest
from app.engine.scoring import score_candidates

router = APIRouter()

# Map of strategy name -> generator function (excluding extreme, which is always run)
_STRATEGY_GENERATORS = {
    "quantile": generate_quantile_ranges,
    "volband": generate_volband_ranges,
    "swing": generate_swing_ranges,
}


def _build_candidate(
    label: str,
    pa: float,
    pb: float,
    tick_spacing: int,
    current_price: float,
) -> dict:
    """Build a raw candidate dict with aligned ticks and width info."""
    raw_tick_lower = price_to_tick(pa)
    raw_tick_upper = price_to_tick(pb)

    tick_lower = align_tick_down(raw_tick_lower, tick_spacing)
    tick_upper = align_tick_up(raw_tick_upper, tick_spacing)

    # Recalculate aligned prices
    aligned_pa = tick_to_price(tick_lower)
    aligned_pb = tick_to_price(tick_upper)

    # Ensure pa < pb after alignment
    if aligned_pa >= aligned_pb:
        aligned_pb = tick_to_price(tick_upper + tick_spacing)
        tick_upper = tick_upper + tick_spacing

    width_pct = (aligned_pb - aligned_pa) / current_price * 100.0

    return {
        "strategy": label,
        "pa": aligned_pa,
        "pb": aligned_pb,
        "tick_lower": tick_lower,
        "tick_upper": tick_upper,
        "width_pct": round(width_pct, 4),
    }


def _to_candidate_result(cand: dict) -> CandidateResult:
    """Convert an internal candidate dict to a CandidateResult schema."""
    return CandidateResult(
        strategy=cand["strategy"],
        pa=cand["pa"],
        pb=cand["pb"],
        tick_lower=cand["tick_lower"],
        tick_upper=cand["tick_upper"],
        width_pct=cand["width_pct"],
        metrics=cand["metrics"],
        score=cand["score"],
        insight=cand["insight"],
    )


def _to_chart_series(series_dict: dict) -> ChartSeries:
    """Convert the raw series dict from back-test into a ChartSeries schema."""
    return ChartSeries(
        timestamps=series_dict["timestamps"],
        lp_values=series_dict["lp_values"],
        hodl_values=series_dict["hodl_values"],
        il_pct=series_dict["il_pct"],
        prices=series_dict["prices"],
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    """Generate LP range recommendations for a Cetus CLMM pool."""

    # ------------------------------------------------------------------
    # 1. Validate & extract data
    # ------------------------------------------------------------------
    if not req.klines or len(req.klines) < 2:
        raise HTTPException(status_code=400, detail="At least 2 klines are required")

    try:
        timestamps = np.array([k[0] for k in req.klines], dtype=np.float64)
        closes = np.array([k[4] for k in req.klines], dtype=np.float64)
    except (IndexError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid kline format: each kline must have at least 5 elements. {exc}",
        )

    if req.current_price <= 0:
        raise HTTPException(status_code=400, detail="current_price must be positive")

    if req.tick_spacing <= 0:
        raise HTTPException(status_code=400, detail="tick_spacing must be positive")

    current_price = req.current_price
    tick_spacing = req.tick_spacing
    fee_rate = req.fee_rate
    capital = req.capital_usd
    profile = req.profile

    # ------------------------------------------------------------------
    # 2. Generate candidate ranges from requested strategies
    # ------------------------------------------------------------------
    raw_ranges: list[tuple[float, float, str]] = []

    for strat_name in req.strategies:
        gen_fn = _STRATEGY_GENERATORS.get(strat_name)
        if gen_fn is None:
            continue  # silently skip unknown strategies
        if strat_name == "volband":
            raw_ranges.extend(gen_fn(closes))
        else:
            raw_ranges.extend(gen_fn(closes))

    # Always generate extreme ranges (2% and 5%)
    extreme_raw = generate_extreme_ranges(current_price)
    raw_ranges.extend(extreme_raw)

    if not raw_ranges:
        raise HTTPException(
            status_code=400,
            detail="No candidate ranges could be generated from the provided data",
        )

    # ------------------------------------------------------------------
    # 3. Align ticks & build candidate dicts
    # ------------------------------------------------------------------
    all_candidates: list[dict] = []
    for pa, pb, label in raw_ranges:
        if pa <= 0 or pb <= 0 or pa >= pb:
            continue
        cand = _build_candidate(label, pa, pb, tick_spacing, current_price)
        all_candidates.append(cand)

    if not all_candidates:
        raise HTTPException(
            status_code=400,
            detail="All candidate ranges were invalid after tick alignment",
        )

    # ------------------------------------------------------------------
    # 4. Back-test each candidate
    # ------------------------------------------------------------------
    for cand in all_candidates:
        result = run_backtest(
            closes=closes,
            timestamps=timestamps,
            pa=cand["pa"],
            pb=cand["pb"],
            p0=current_price,
            capital=capital,
            fee_rate=fee_rate,
        )
        cand["metrics"] = result["metrics"]
        cand["series"] = result["series"]

    # ------------------------------------------------------------------
    # 5. Score & rank
    # ------------------------------------------------------------------
    # Separate extreme candidates before scoring
    extreme_cands = {c["strategy"]: c for c in all_candidates if c["strategy"].startswith("extreme_")}
    strategy_cands = [c for c in all_candidates if not c["strategy"].startswith("extreme_")]

    # Score strategy candidates (non-extreme)
    if strategy_cands:
        strategy_cands = score_candidates(strategy_cands, profile)

    # Also score extreme candidates so they have scores/insights
    if extreme_cands:
        extreme_list = list(extreme_cands.values())
        extreme_list = score_candidates(extreme_list, profile)
        extreme_cands = {c["strategy"]: c for c in extreme_list}

    # ------------------------------------------------------------------
    # 6. Pick top-3 + extreme 2% and 5%
    # ------------------------------------------------------------------
    # If we don't have enough strategy candidates, pad with extreme ones
    if len(strategy_cands) < 3:
        # Add extreme candidates that aren't already in strategy_cands
        for ec in extreme_cands.values():
            if len(strategy_cands) >= 3:
                break
            strategy_cands.append(ec)
        # Re-sort after adding
        strategy_cands.sort(key=lambda c: c.get("score", 0), reverse=True)

    top3 = strategy_cands[:3]

    # Ensure we always have extreme candidates
    extreme_2pct = extreme_cands.get("extreme_2.0pct")
    extreme_5pct = extreme_cands.get("extreme_5.0pct")

    if extreme_2pct is None or extreme_5pct is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate extreme range candidates",
        )

    # ------------------------------------------------------------------
    # 7. Build series map for selected candidates
    # ------------------------------------------------------------------
    series_map: dict[str, ChartSeries] = {}
    for i, cand in enumerate(top3):
        series_map[f"top{i + 1}"] = _to_chart_series(cand["series"])
    series_map["extreme_2pct"] = _to_chart_series(extreme_2pct["series"])
    series_map["extreme_5pct"] = _to_chart_series(extreme_5pct["series"])

    # ------------------------------------------------------------------
    # 8. Assemble response
    # ------------------------------------------------------------------
    return RecommendResponse(
        top3=[_to_candidate_result(c) for c in top3],
        extreme_2pct=_to_candidate_result(extreme_2pct),
        extreme_5pct=_to_candidate_result(extreme_5pct),
        series=series_map,
        current_price=current_price,
        pool_fee_rate=fee_rate,
    )
