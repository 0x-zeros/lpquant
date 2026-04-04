from __future__ import annotations

import pandas as pd

from app.research.coverage_optimizer import (
    build_coverage_frontier,
    build_window_frame,
    holding_days_to_bars,
    optimize_interval_for_coverage,
    score_frontier_candidates,
    select_recommended_candidate,
    summarize_return_distribution,
)
from app.research.market_data import load_price_history
from app.research.types import (
    CoverageStudyRequest,
    CoverageStudyResult,
    CoverageSweepRequest,
    CoverageSweepResult,
)


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


def run_coverage_sweep(request: CoverageSweepRequest) -> CoverageSweepResult:
    dataset = load_price_history(
        raw_pair=request.pair,
        interval=request.interval,
        days=request.days,
    )
    current_price = float(dataset.frame["close"].iloc[-1])

    frontier_rows: list = []
    period_recommendations: list[dict[str, float | str | bool]] = []
    for holding_days in sorted(set(request.holding_days_list)):
        holding_bars = holding_days_to_bars(request.interval, holding_days)
        window_frame = build_window_frame(dataset.frame, holding_bars=holding_bars)
        frontier = build_coverage_frontier(
            window_frame=window_frame,
            coverage_targets_pct=request.coverage_targets_pct,
            current_price=current_price,
        )
        scored_frontier = score_frontier_candidates(
            frontier,
            minimum_recommendation_coverage_pct=request.minimum_recommendation_coverage_pct,
        )
        scored_frontier["holding_days"] = holding_days
        scored_frontier["holding_bars"] = holding_bars
        scored_frontier["period_label"] = f"{holding_days}d"
        recommended = select_recommended_candidate(scored_frontier)
        recommended["is_period_recommendation"] = True
        period_recommendations.append(recommended)
        frontier_rows.append(scored_frontier)

    frontier_grid = (
        pd.concat(frontier_rows, ignore_index=True)
        .sort_values(["holding_days", "coverage_target_pct"])
        .reset_index(drop=True)
    )
    period_recommendations_frame = (
        pd.DataFrame.from_records(period_recommendations)
        .sort_values("holding_days")
        .reset_index(drop=True)
    )
    global_recommendation = (
        period_recommendations_frame.sort_values(
            [
                "ideal_distance",
                "width_pct",
                "out_of_range_pct",
                "holding_days",
            ],
            ascending=[True, True, True, True],
        )
        .iloc[0]
        .to_dict()
    )
    global_recommendation["is_global_recommendation"] = True

    return CoverageSweepResult(
        request=request,
        dataset=dataset,
        frontier_grid=frontier_grid,
        period_recommendations=period_recommendations_frame,
        global_recommendation=global_recommendation,
    )
