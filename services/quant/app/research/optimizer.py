from __future__ import annotations

import numpy as np
import pandas as pd

from app.engine.backtest import run_backtest
from app.research.features import interval_to_hours
from app.research.types import CandidateSpec, ObjectiveName

OBJECTIVE_PROFILES: dict[str, dict[str, tuple[float, bool]]] = {
    "balanced": {
        "mean_fee_proxy_bps": (0.24, False),
        "mean_in_range_pct": (0.20, False),
        "no_exit_rate": (0.12, False),
        "median_lp_vs_hodl_pct": (0.14, False),
        "p10_lp_vs_hodl_pct": (0.10, False),
        "mean_max_il_pct": (0.08, True),
        "mean_max_drawdown_pct": (0.06, True),
        "downside_breach_rate": (0.06, True),
    },
    "carry": {
        "mean_fee_proxy_bps": (0.32, False),
        "mean_in_range_pct": (0.18, False),
        "median_lp_vs_hodl_pct": (0.16, False),
        "no_exit_rate": (0.08, False),
        "mean_capital_efficiency": (0.10, False),
        "mean_max_il_pct": (0.08, True),
        "mean_max_drawdown_pct": (0.04, True),
        "downside_breach_rate": (0.04, True),
    },
    "defensive": {
        "no_exit_rate": (0.24, False),
        "mean_in_range_pct": (0.20, False),
        "p10_lp_vs_hodl_pct": (0.16, False),
        "median_lp_vs_hodl_pct": (0.10, False),
        "mean_max_il_pct": (0.12, True),
        "mean_max_drawdown_pct": (0.10, True),
        "downside_breach_rate": (0.08, True),
    },
}


def build_candidate_grid(view: str) -> list[CandidateSpec]:
    widths = [1.5, 2.5, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0]
    if view == "bullish":
        multipliers = [0.0, 0.25, 0.5, 0.75]
    elif view == "bearish":
        multipliers = [-0.75, -0.5, -0.25, 0.0]
    else:
        multipliers = [-0.25, 0.0, 0.25]

    grid: list[CandidateSpec] = []
    for width in widths:
        for multiplier in multipliers:
            grid.append(
                CandidateSpec(
                    width_pct=width,
                    center_offset_pct=round(width * multiplier, 2),
                )
            )
    return grid


def _normalize(values: pd.Series) -> pd.Series:
    lo = float(values.min())
    hi = float(values.max())
    if hi == lo:
        return pd.Series([50.0] * len(values), index=values.index, dtype=float)
    return (values - lo) / (hi - lo) * 100.0


def _bounds_from_entry(entry_price: float, spec: CandidateSpec) -> tuple[float, float]:
    lower = entry_price * (1.0 + spec.lower_offset_pct / 100.0)
    upper = entry_price * (1.0 + spec.upper_offset_pct / 100.0)
    return max(lower, 1e-12), max(upper, 1e-12)


def _first_exit(prices: np.ndarray, lower: float, upper: float, bar_hours: float) -> tuple[str, float]:
    for idx, price in enumerate(prices[1:], start=1):
        if price < lower:
            return "down", round(idx * bar_hours, 2)
        if price > upper:
            return "up", round(idx * bar_hours, 2)
    return "none", round((len(prices) - 1) * bar_hours, 2)


def _fee_proxy_bps(
    prices: np.ndarray,
    lower: float,
    upper: float,
    fee_rate: float,
    capital_efficiency: float,
) -> float:
    if len(prices) < 2:
        return 0.0
    abs_log_moves = np.abs(np.diff(np.log(prices)))
    in_range = (prices[1:] >= lower) & (prices[1:] <= upper)
    return float(abs_log_moves[in_range].sum() * capital_efficiency * fee_rate * 10_000.0)


def _evaluate_candidate(
    closes: np.ndarray,
    timestamps: np.ndarray,
    entry_indices: list[int],
    horizon_bars: int,
    bar_hours: float,
    capital: float,
    fee_rate: float,
    spec: CandidateSpec,
) -> dict[str, float]:
    window_rows: list[dict[str, float | str]] = []

    for entry_idx in entry_indices:
        forward_end = entry_idx + horizon_bars + 1
        forward_closes = closes[entry_idx:forward_end]
        forward_timestamps = timestamps[entry_idx:forward_end]
        if len(forward_closes) < horizon_bars + 1:
            continue

        entry_price = float(forward_closes[0])
        lower, upper = _bounds_from_entry(entry_price, spec)
        if lower >= upper:
            continue

        result = run_backtest(
            closes=forward_closes,
            timestamps=forward_timestamps,
            pa=lower,
            pb=upper,
            p0=entry_price,
            capital=capital,
            fee_rate=fee_rate,
        )
        metrics = result["metrics"]
        exit_side, first_exit_hours = _first_exit(forward_closes, lower, upper, bar_hours)
        fee_proxy = _fee_proxy_bps(
            forward_closes,
            lower,
            upper,
            fee_rate,
            metrics.capital_efficiency,
        )

        window_rows.append(
            {
                "in_range_pct": float(metrics.in_range_pct),
                "touch_count": float(metrics.touch_count),
                "lp_vs_hodl_pct": float(metrics.lp_vs_hodl_pct),
                "max_il_pct": float(metrics.max_il_pct),
                "max_drawdown_pct": float(metrics.max_drawdown_pct),
                "capital_efficiency": float(metrics.capital_efficiency),
                "exit_side": exit_side,
                "first_exit_hours": first_exit_hours,
                "fee_proxy_bps": fee_proxy,
            }
        )

    if not window_rows:
        raise ValueError("候选区间评估后没有得到有效的前瞻样本窗口")

    window_frame = pd.DataFrame.from_records(window_rows)
    return {
        "width_pct": spec.width_pct,
        "center_offset_pct": spec.center_offset_pct,
        "lower_from_entry_pct": spec.lower_offset_pct,
        "upper_from_entry_pct": spec.upper_offset_pct,
        "sample_size": int(len(window_frame)),
        "mean_in_range_pct": round(float(window_frame["in_range_pct"].mean()), 2),
        "no_exit_rate": round(float((window_frame["exit_side"] == "none").mean() * 100.0), 2),
        "downside_breach_rate": round(
            float((window_frame["exit_side"] == "down").mean() * 100.0), 2
        ),
        "upside_breach_rate": round(
            float((window_frame["exit_side"] == "up").mean() * 100.0), 2
        ),
        "mean_first_exit_hours": round(float(window_frame["first_exit_hours"].mean()), 2),
        "mean_touch_count": round(float(window_frame["touch_count"].mean()), 2),
        "mean_fee_proxy_bps": round(float(window_frame["fee_proxy_bps"].mean()), 2),
        "median_fee_proxy_bps": round(float(window_frame["fee_proxy_bps"].median()), 2),
        "median_lp_vs_hodl_pct": round(float(window_frame["lp_vs_hodl_pct"].median()), 2),
        "p10_lp_vs_hodl_pct": round(float(np.percentile(window_frame["lp_vs_hodl_pct"], 10)), 2),
        "mean_max_il_pct": round(float(window_frame["max_il_pct"].mean()), 2),
        "mean_max_drawdown_pct": round(float(window_frame["max_drawdown_pct"].mean()), 2),
        "mean_capital_efficiency": round(float(window_frame["capital_efficiency"].mean()), 2),
    }


def _score_results(results: pd.DataFrame, objective: ObjectiveName) -> pd.DataFrame:
    profile = OBJECTIVE_PROFILES.get(objective, OBJECTIVE_PROFILES["balanced"])
    scored = results.copy()
    total = pd.Series(0.0, index=scored.index, dtype=float)

    for metric, (weight, inverted) in profile.items():
        normalized = _normalize(scored[metric].astype(float))
        if inverted:
            normalized = 100.0 - normalized
        total += normalized * weight

    scored["score"] = total.round(2)
    return scored.sort_values(["score", "mean_fee_proxy_bps"], ascending=[False, False]).reset_index(
        drop=True
    )


def evaluate_candidates(
    frame: pd.DataFrame,
    similar_windows: pd.DataFrame,
    interval: str,
    horizon_bars: int,
    capital: float,
    fee_rate: float,
    view: str,
    objective: ObjectiveName,
) -> pd.DataFrame:
    closes = frame["close"].to_numpy(dtype=float)
    timestamps = frame["timestamp"].to_numpy(dtype=np.int64)
    entry_indices = [int(value) for value in similar_windows["entry_index"].tolist()]
    bar_hours = interval_to_hours(interval)

    rows = [
        _evaluate_candidate(
            closes=closes,
            timestamps=timestamps,
            entry_indices=entry_indices,
            horizon_bars=horizon_bars,
            bar_hours=bar_hours,
            capital=capital,
            fee_rate=fee_rate,
            spec=spec,
        )
        for spec in build_candidate_grid(view)
    ]
    return _score_results(pd.DataFrame.from_records(rows), objective)
