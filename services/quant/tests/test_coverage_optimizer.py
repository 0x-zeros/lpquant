import pandas as pd

from app.research.coverage_optimizer import (
    build_coverage_frontier,
    build_window_frame,
    holding_days_to_bars,
    optimize_interval_for_coverage,
    score_frontier_candidates,
    select_recommended_candidate,
)


def test_holding_days_to_bars_uses_sampling_interval():
    assert holding_days_to_bars("1d", 30) == 30
    assert holding_days_to_bars("4h", 30) == 180


def test_optimize_interval_finds_narrowest_bounds_for_target():
    window_frame = pd.DataFrame(
        {
            "lower_excursion_pct": [-5.0, -2.0, -1.0, 0.0],
            "upper_excursion_pct": [1.0, 2.0, 4.0, 10.0],
            "end_return_pct": [0.5, 1.0, 1.5, 2.0],
        }
    )

    best = optimize_interval_for_coverage(
        window_frame=window_frame,
        coverage_target_pct=75.0,
        current_price=100.0,
    )

    assert best["lower_bound_pct"] == -5.0
    assert best["upper_bound_pct"] == 4.0
    assert best["width_pct"] == 9.0
    assert best["achieved_coverage_pct"] == 75.0


def test_build_window_frame_and_frontier_work_together():
    frame = pd.DataFrame(
        {
            "timestamp": [1, 2, 3, 4, 5, 6],
            "close": [100.0, 102.0, 101.0, 103.0, 104.0, 105.0],
        }
    )
    window_frame = build_window_frame(frame, holding_bars=2)
    assert {"lower_excursion_pct", "upper_excursion_pct", "end_return_pct"}.issubset(
        window_frame.columns
    )

    frontier = build_coverage_frontier(
        window_frame=window_frame,
        coverage_targets_pct=(50.0, 75.0, 100.0),
        current_price=105.0,
    )
    assert list(frontier["coverage_target_pct"]) == [50.0, 75.0, 100.0]
    assert frontier["width_pct"].is_monotonic_increasing


def test_score_frontier_candidates_and_select_recommendation():
    frontier = pd.DataFrame(
        {
            "coverage_target_pct": [50.0, 70.0, 80.0, 90.0, 95.0],
            "achieved_coverage_pct": [50.0, 70.0, 80.0, 90.0, 95.0],
            "out_of_range_pct": [50.0, 30.0, 20.0, 10.0, 5.0],
            "width_pct": [4.0, 5.0, 6.0, 10.0, 16.0],
            "center_offset_pct": [0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )

    scored = score_frontier_candidates(
        frontier,
        minimum_recommendation_coverage_pct=80.0,
    )
    recommendation = select_recommended_candidate(scored)

    assert "ideal_distance" in scored.columns
    assert "knee_score" in scored.columns
    assert list(scored["recommendation_eligible"]) == [False, False, True, True, True]
    assert recommendation["coverage_target_pct"] == 80.0
    assert recommendation["recommendation_eligible"] is True
