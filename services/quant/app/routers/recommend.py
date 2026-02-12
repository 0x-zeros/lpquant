"""POST /api/v1/recommend -- Volatility-based LP range recommendation endpoint."""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException
import numpy as np

from app.schemas import (
    BacktestMetrics,
    CandidateResult,
    ChartSeries,
    RecommendRequest,
    RecommendResponse,
    VolatilityInfo,
)
from app.engine.tick_math import (
    align_tick_down,
    align_tick_up,
    price_to_tick,
    tick_to_price,
)
from app.engine.volatility import estimate_volatility
from app.engine.candidates import generate_ranges
from app.engine.backtest import run_backtest
from app.engine.scoring import score_and_select

router = APIRouter()


def _build_candidate(
    candidate,
    tick_spacing: int,
    current_price: float,
) -> dict:
    """Build a raw candidate dict with aligned ticks and width info."""
    raw_tick_lower = price_to_tick(candidate.pa)
    raw_tick_upper = price_to_tick(candidate.pb)

    tick_lower = align_tick_down(raw_tick_lower, tick_spacing)
    tick_upper = align_tick_up(raw_tick_upper, tick_spacing)

    aligned_pa = tick_to_price(tick_lower)
    aligned_pb = tick_to_price(tick_upper)

    if aligned_pa >= aligned_pb:
        aligned_pb = tick_to_price(tick_upper + tick_spacing)
        tick_upper = tick_upper + tick_spacing

    width_pct = (aligned_pb - aligned_pa) / current_price * 100.0

    return {
        "range_type": candidate.range_type,
        "label": candidate.label,
        "pa": aligned_pa,
        "pb": aligned_pb,
        "tick_lower": tick_lower,
        "tick_upper": tick_upper,
        "width_pct": round(width_pct, 4),
        "k_sigma": candidate.k,
        "estimated_prob": candidate.estimated_prob,
    }


def _to_candidate_result(cand: dict) -> CandidateResult:
    """Convert an internal candidate dict to a CandidateResult schema."""
    return CandidateResult(
        range_type=cand["range_type"],
        label=cand["label"],
        pa=cand["pa"],
        pb=cand["pb"],
        tick_lower=cand["tick_lower"],
        tick_upper=cand["tick_upper"],
        width_pct=cand["width_pct"],
        k_sigma=cand["k_sigma"],
        estimated_prob=cand["estimated_prob"],
        metrics=cand["metrics"],
        score=cand["score"],
        insight=cand["insight"],
        insight_data=cand.get("insight_data"),
    )


def _to_chart_series(series_dict: dict) -> ChartSeries:
    """Convert the raw series dict from back-test into a ChartSeries schema."""
    return ChartSeries(
        timestamps=series_dict["timestamps"],
        lp_values=series_dict["lp_values"],
        hodl_values=series_dict["hodl_values"],
        il_pct=series_dict["il_pct"],
        prices=series_dict["prices"],
        markers=series_dict.get("markers", []),
    )


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    """Generate LP range recommendations using volatility forecasting."""

    # ------------------------------------------------------------------
    # 1. Validate & extract OHLC data
    # ------------------------------------------------------------------
    if not req.klines or len(req.klines) < 2:
        raise HTTPException(status_code=400, detail="At least 2 klines are required")

    try:
        timestamps = np.array([k[0] for k in req.klines], dtype=np.float64)
        opens = np.array([k[1] for k in req.klines], dtype=np.float64)
        highs = np.array([k[2] for k in req.klines], dtype=np.float64)
        lows = np.array([k[3] for k in req.klines], dtype=np.float64)
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

    sort_idx = np.argsort(timestamps)
    timestamps = timestamps[sort_idx]
    opens = opens[sort_idx]
    highs = highs[sort_idx]
    lows = lows[sort_idx]
    closes = closes[sort_idx]

    current_price = req.current_price
    tick_spacing = req.tick_spacing
    fee_rate = req.fee_rate
    capital = req.capital_usd
    horizon_days = req.horizon_days
    p0_price = float(closes[0])

    # ------------------------------------------------------------------
    # 2. Estimate volatility
    # ------------------------------------------------------------------
    vol_estimate = estimate_volatility(closes, highs, lows)
    sigma_T = vol_estimate.sigma_annual * math.sqrt(horizon_days / 365.0)
    sigma_T = max(sigma_T, 0.001)

    # ------------------------------------------------------------------
    # 3. Generate candidate ranges (3 balanced + 3 narrow = 6)
    # ------------------------------------------------------------------
    raw_candidates = generate_ranges(current_price, vol_estimate, horizon_days)

    if not raw_candidates:
        raise HTTPException(
            status_code=400,
            detail="No candidate ranges could be generated",
        )

    # ------------------------------------------------------------------
    # 4. Tick alignment
    # ------------------------------------------------------------------
    all_candidates: list[dict] = []
    for rc in raw_candidates:
        if rc.pa <= 0 or rc.pb <= 0 or rc.pa >= rc.pb:
            continue
        cand = _build_candidate(rc, tick_spacing, current_price)
        all_candidates.append(cand)

    if not all_candidates:
        raise HTTPException(
            status_code=400,
            detail="All candidate ranges were invalid after tick alignment",
        )

    # ------------------------------------------------------------------
    # 5. Back-test each candidate
    # ------------------------------------------------------------------
    for cand in all_candidates:
        result = run_backtest(
            closes=closes,
            timestamps=timestamps,
            pa=cand["pa"],
            pb=cand["pb"],
            p0=p0_price,
            capital=capital,
            fee_rate=fee_rate,
        )
        cand["metrics"] = result["metrics"]
        cand["series"] = result["series"]

    # ------------------------------------------------------------------
    # 6. Score & select best balanced + best narrow + best backtest
    # ------------------------------------------------------------------
    best_balanced, best_narrow, best_backtest = score_and_select(all_candidates)

    if best_balanced is None or best_narrow is None or best_backtest is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to select recommendations",
        )

    # If best_backtest is the same as balanced or narrow, mark it differently
    if best_backtest.get("range_type") != "backtest":
        best_backtest = {**best_backtest, "range_type": "backtest", "label": "best_backtest"}

    # ------------------------------------------------------------------
    # 7. Build series map
    # ------------------------------------------------------------------
    series_map: dict[str, ChartSeries] = {
        "balanced": _to_chart_series(best_balanced["series"]),
        "narrow": _to_chart_series(best_narrow["series"]),
        "best_backtest": _to_chart_series(best_backtest["series"]),
    }

    # ------------------------------------------------------------------
    # 8. Assemble response
    # ------------------------------------------------------------------
    vol_info = VolatilityInfo(
        sigma_annual=round(vol_estimate.sigma_annual, 4),
        sigma_realized=round(vol_estimate.sigma_realized, 4),
        sigma_atr=round(vol_estimate.sigma_atr, 4),
        sigma_ewma=round(vol_estimate.sigma_ewma, 4),
        regime=vol_estimate.regime,
        regime_multiplier=vol_estimate.regime_multiplier,
        sigma_T=round(sigma_T, 4),
    )

    return RecommendResponse(
        balanced=_to_candidate_result(best_balanced),
        narrow=_to_candidate_result(best_narrow),
        best_backtest=_to_candidate_result(best_backtest),
        volatility=vol_info,
        horizon_days=horizon_days,
        series=series_map,
        current_price=current_price,
        pool_fee_rate=fee_rate,
    )
