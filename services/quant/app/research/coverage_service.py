from __future__ import annotations

from app.research.coverage_optimizer import (
    build_coverage_frontier,
    build_window_frame,
    holding_days_to_bars,
    optimize_interval_for_coverage,
    summarize_return_distribution,
)
from app.research.market_data import load_price_history
from app.research.types import CoverageStudyRequest, CoverageStudyResult


def run_coverage_study(request: CoverageStudyRequest) -> CoverageStudyResult:
    dataset = load_price_history(
        raw_pair=request.pair,
        interval=request.interval,
        days=request.days,
    )
    holding_bars = holding_days_to_bars(request.interval, request.holding_days)
    window_frame = build_window_frame(dataset.frame, holding_bars=holding_bars)
    current_price = float(dataset.frame["close"].iloc[-1])

    frontier_targets = tuple(
        sorted({*request.frontier_targets_pct, float(request.coverage_target_pct)})
    )
    frontier = build_coverage_frontier(
        window_frame=window_frame,
        coverage_targets_pct=frontier_targets,
        current_price=current_price,
    )
    best_interval = optimize_interval_for_coverage(
        window_frame=window_frame,
        coverage_target_pct=request.coverage_target_pct,
        current_price=current_price,
    )
    return_stats = summarize_return_distribution(window_frame)

    return CoverageStudyResult(
        request=request,
        dataset=dataset,
        holding_bars=holding_bars,
        window_frame=window_frame,
        return_stats=return_stats,
        best_interval=best_interval,
        frontier=frontier,
    )
