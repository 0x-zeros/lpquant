from __future__ import annotations

import math

import numpy as np
import pandas as pd

from app.research.features import interval_to_hours


def holding_days_to_bars(interval: str, holding_days: int) -> int:
    if holding_days <= 0:
        raise ValueError("holding_days 必须大于 0")

    interval_hours = interval_to_hours(interval)
    holding_hours = holding_days * 24.0
    return max(2, math.ceil(holding_hours / interval_hours))


def build_window_frame(
    frame: pd.DataFrame,
    holding_bars: int,
) -> pd.DataFrame:
    closes = frame["close"].to_numpy(dtype=float)
    timestamps = frame["timestamp"].to_numpy(dtype=np.int64)

    if len(closes) <= holding_bars:
        raise ValueError("历史数据不足，无法构造所需 holding period 的样本窗口")

    rows: list[dict[str, float | int]] = []
    for entry_index in range(len(closes) - holding_bars):
        window = closes[entry_index : entry_index + holding_bars + 1]
        entry_price = float(window[0])
        min_price = float(window.min())
        max_price = float(window.max())
        end_price = float(window[-1])

        rows.append(
            {
                "entry_index": entry_index,
                "entry_timestamp": int(timestamps[entry_index]),
                "exit_timestamp": int(timestamps[entry_index + holding_bars]),
                "entry_price": entry_price,
                "end_price": end_price,
                "min_price": min_price,
                "max_price": max_price,
                "lower_excursion_pct": (min_price / entry_price - 1.0) * 100.0,
                "upper_excursion_pct": (max_price / entry_price - 1.0) * 100.0,
                "end_return_pct": (end_price / entry_price - 1.0) * 100.0,
                "path_range_pct": (max_price / min_price - 1.0) * 100.0 if min_price > 0 else 0.0,
            }
        )

    return pd.DataFrame.from_records(rows)


def summarize_return_distribution(window_frame: pd.DataFrame) -> dict[str, float]:
    returns = window_frame["end_return_pct"].to_numpy(dtype=float)
    return {
        "p5_end_return_pct": round(float(np.percentile(returns, 5)), 2),
        "p25_end_return_pct": round(float(np.percentile(returns, 25)), 2),
        "p50_end_return_pct": round(float(np.percentile(returns, 50)), 2),
        "p75_end_return_pct": round(float(np.percentile(returns, 75)), 2),
        "p95_end_return_pct": round(float(np.percentile(returns, 95)), 2),
        "mean_end_return_pct": round(float(np.mean(returns)), 2),
    }


def _evaluate_interval(
    window_frame: pd.DataFrame,
    lower_bound_pct: float,
    upper_bound_pct: float,
    coverage_target_pct: float,
    current_price: float,
) -> dict[str, float]:
    lower_moves = window_frame["lower_excursion_pct"].to_numpy(dtype=float)
    upper_moves = window_frame["upper_excursion_pct"].to_numpy(dtype=float)
    end_returns = window_frame["end_return_pct"].to_numpy(dtype=float)

    in_range_mask = (lower_moves >= lower_bound_pct) & (upper_moves <= upper_bound_pct)
    achieved_coverage_pct = float(in_range_mask.mean() * 100.0)
    out_of_range_pct = 100.0 - achieved_coverage_pct
    width_pct = upper_bound_pct - lower_bound_pct
    center_offset_pct = (upper_bound_pct + lower_bound_pct) / 2.0

    return {
        "coverage_target_pct": round(float(coverage_target_pct), 2),
        "achieved_coverage_pct": round(achieved_coverage_pct, 2),
        "out_of_range_pct": round(out_of_range_pct, 2),
        "lower_bound_pct": round(float(lower_bound_pct), 2),
        "upper_bound_pct": round(float(upper_bound_pct), 2),
        "width_pct": round(float(width_pct), 2),
        "center_offset_pct": round(float(center_offset_pct), 2),
        "downside_touch_pct": round(float((lower_moves < lower_bound_pct).mean() * 100.0), 2),
        "upside_touch_pct": round(float((upper_moves > upper_bound_pct).mean() * 100.0), 2),
        "median_end_return_pct": round(float(np.percentile(end_returns, 50)), 2),
        "p10_end_return_pct": round(float(np.percentile(end_returns, 10)), 2),
        "p90_end_return_pct": round(float(np.percentile(end_returns, 90)), 2),
        "sample_size": int(len(window_frame)),
        "current_price": round(float(current_price), 6),
        "current_lower_price": round(float(current_price * (1.0 + lower_bound_pct / 100.0)), 6),
        "current_upper_price": round(float(current_price * (1.0 + upper_bound_pct / 100.0)), 6),
    }


def optimize_interval_for_coverage(
    window_frame: pd.DataFrame,
    coverage_target_pct: float,
    current_price: float,
) -> dict[str, float]:
    if not 0 < coverage_target_pct <= 100:
        raise ValueError("coverage_target_pct 必须在 0 到 100 之间")

    lower_moves = window_frame["lower_excursion_pct"].to_numpy(dtype=float)
    upper_moves = window_frame["upper_excursion_pct"].to_numpy(dtype=float)
    target_count = max(1, math.ceil(len(window_frame) * coverage_target_pct / 100.0))

    best_row: dict[str, float] | None = None
    unique_lowers = np.unique(np.round(lower_moves, 8))
    for lower_bound_pct in unique_lowers:
        eligible_upper_moves = upper_moves[lower_moves >= lower_bound_pct]
        if len(eligible_upper_moves) < target_count:
            continue

        kth_index = target_count - 1
        upper_bound_pct = float(np.partition(eligible_upper_moves, kth_index)[kth_index])
        candidate = _evaluate_interval(
            window_frame=window_frame,
            lower_bound_pct=float(lower_bound_pct),
            upper_bound_pct=upper_bound_pct,
            coverage_target_pct=coverage_target_pct,
            current_price=current_price,
        )

        if best_row is None:
            best_row = candidate
            continue

        better_width = candidate["width_pct"] < best_row["width_pct"] - 1e-9
        same_width = abs(candidate["width_pct"] - best_row["width_pct"]) <= 1e-9
        better_coverage = candidate["achieved_coverage_pct"] > best_row["achieved_coverage_pct"] + 1e-9
        better_center = abs(candidate["center_offset_pct"]) < abs(best_row["center_offset_pct"]) - 1e-9

        if better_width or (same_width and better_coverage) or (same_width and not better_coverage and better_center):
            best_row = candidate

    if best_row is None:
        raise ValueError("没有找到满足 coverage target 的区间候选")

    return best_row


def build_coverage_frontier(
    window_frame: pd.DataFrame,
    coverage_targets_pct: tuple[float, ...],
    current_price: float,
) -> pd.DataFrame:
    frontier_rows = [
        optimize_interval_for_coverage(
            window_frame=window_frame,
            coverage_target_pct=target,
            current_price=current_price,
        )
        for target in sorted({round(float(target), 4) for target in coverage_targets_pct})
    ]
    return pd.DataFrame.from_records(frontier_rows).sort_values("coverage_target_pct").reset_index(
        drop=True
    )
