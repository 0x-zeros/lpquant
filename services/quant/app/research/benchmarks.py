from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from app.research.artifacts import save_benchmark_bundle
from app.research.labels import format_scenario, format_source
from app.research.service import run_study
from app.research.types import StudyRequest, StudyResult


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    request: StudyRequest
    thesis: str


@dataclass
class BenchmarkSuiteResult:
    cases: list[BenchmarkCase]
    studies: dict[str, StudyResult]
    summary: pd.DataFrame
    rankings: pd.DataFrame
    failures: pd.DataFrame


SCENARIOS: list[tuple[str, str, str, str]] = [
    (
        "neutral_balanced",
        "neutral",
        "balanced",
        "基准情景：不带方向偏见，使用均衡型收益/风险目标。",
    ),
    (
        "bullish_carry",
        "bullish",
        "carry",
        "看涨情景：如果当前状态支持，优先考虑更窄、收益更高的区间。",
    ),
    (
        "bearish_defensive",
        "bearish",
        "defensive",
        "防御情景：重点检验下跌保护，对出圈和回撤的容忍度更低。",
    ),
]

PAIR_INTERVALS: list[tuple[str, list[str]]] = [
    ("BTC/USDC", ["4h", "1d"]),
    ("SOL/USDC", ["4h"]),
    ("SUI/USDC", ["4h"]),
]


def default_baseline_cases() -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for pair, intervals in PAIR_INTERVALS:
        pair_slug = pair.lower().replace("/", "_")
        for interval in intervals:
            for suffix, view, objective, thesis in SCENARIOS:
                cases.append(
                    BenchmarkCase(
                        name=f"{pair_slug}_{interval}_{suffix}",
                        request=StudyRequest(
                            pair=pair,
                            interval=interval,
                            view=view,  # type: ignore[arg-type]
                            objective=objective,  # type: ignore[arg-type]
                        ),
                        thesis=thesis,
                    )
                )
    return cases


BASELINE_CASES = default_baseline_cases()


def _study_summary_row(case: BenchmarkCase, study: StudyResult) -> dict[str, object]:
    best = study.rankings.iloc[0]
    regime = study.current_regime
    return {
        "case_name": case.name,
        "pair": case.request.pair,
        "interval": case.request.interval,
        "view": case.request.view,
        "objective": case.request.objective,
        "scenario": format_scenario(case.request.view, case.request.objective),
        "pair_interval": f"{case.request.pair} {case.request.interval}",
        "source": study.dataset.source,
        "source_label": format_source(study.dataset.source),
        "bars": len(study.dataset.frame),
        "regime_label": regime["regime_label"],
        "trend_pct": regime["trend_pct"],
        "realized_vol_pct": regime["realized_vol_pct"],
        "drawdown_pct": regime["drawdown_pct"],
        "rsi": regime["rsi"],
        "score": float(best["score"]),
        "width_pct": float(best["width_pct"]),
        "center_offset_pct": float(best["center_offset_pct"]),
        "lower_from_entry_pct": float(best["lower_from_entry_pct"]),
        "upper_from_entry_pct": float(best["upper_from_entry_pct"]),
        "mean_fee_proxy_bps": float(best["mean_fee_proxy_bps"]),
        "mean_in_range_pct": float(best["mean_in_range_pct"]),
        "no_exit_rate": float(best["no_exit_rate"]),
        "median_lp_vs_hodl_pct": float(best["median_lp_vs_hodl_pct"]),
        "p10_lp_vs_hodl_pct": float(best["p10_lp_vs_hodl_pct"]),
        "mean_max_il_pct": float(best["mean_max_il_pct"]),
        "mean_max_drawdown_pct": float(best["mean_max_drawdown_pct"]),
        "downside_breach_rate": float(best["downside_breach_rate"]),
        "upside_breach_rate": float(best["upside_breach_rate"]),
        "sample_size": int(best["sample_size"]),
        "thesis": case.thesis,
    }


def _rankings_with_context(case: BenchmarkCase, study: StudyResult) -> pd.DataFrame:
    rankings = study.rankings.copy()
    rankings.insert(0, "case_name", case.name)
    rankings.insert(1, "pair", case.request.pair)
    rankings.insert(2, "interval", case.request.interval)
    rankings.insert(3, "view", case.request.view)
    rankings.insert(4, "objective", case.request.objective)
    rankings.insert(5, "scenario", format_scenario(case.request.view, case.request.objective))
    rankings.insert(6, "pair_interval", f"{case.request.pair} {case.request.interval}")
    rankings.insert(7, "source", study.dataset.source)
    rankings.insert(8, "source_label", format_source(study.dataset.source))
    rankings.insert(9, "regime_label", study.current_regime["regime_label"])
    return rankings


def run_benchmark_suite(
    cases: list[BenchmarkCase] | None = None,
    *,
    skip_errors: bool = True,
    study_runner: Callable[[StudyRequest], StudyResult] = run_study,
) -> BenchmarkSuiteResult:
    selected_cases = cases or BASELINE_CASES
    studies: dict[str, StudyResult] = {}
    summary_rows: list[dict[str, object]] = []
    ranking_frames: list[pd.DataFrame] = []
    failure_rows: list[dict[str, str]] = []

    for case in selected_cases:
        try:
            study = study_runner(case.request)
        except Exception as exc:
            failure_rows.append(
                {
                    "case_name": case.name,
                    "pair": case.request.pair,
                    "interval": case.request.interval,
                    "view": case.request.view,
                    "objective": case.request.objective,
                    "error": str(exc),
                }
            )
            if not skip_errors:
                raise
            continue

        studies[case.name] = study
        summary_rows.append(_study_summary_row(case, study))
        ranking_frames.append(_rankings_with_context(case, study))

    summary = pd.DataFrame.from_records(summary_rows)
    if not summary.empty:
        summary = summary.sort_values(["pair", "interval", "view"]).reset_index(drop=True)

    rankings = pd.concat(ranking_frames, ignore_index=True) if ranking_frames else pd.DataFrame()
    failures = pd.DataFrame.from_records(failure_rows)

    return BenchmarkSuiteResult(
        cases=selected_cases,
        studies=studies,
        summary=summary,
        rankings=rankings,
        failures=failures,
    )


def save_benchmark_suite(
    suite: BenchmarkSuiteResult,
    output_dir: str | Path,
    *,
    label: str = "benchmark_suite",
    notes: str | None = None,
    tags: list[str] | None = None,
    include_case_artifacts: bool = True,
) -> dict[str, Path]:
    return save_benchmark_bundle(
        suite,
        output_dir,
        label=label,
        notes=notes,
        tags=tags,
        include_case_artifacts=include_case_artifacts,
    )
