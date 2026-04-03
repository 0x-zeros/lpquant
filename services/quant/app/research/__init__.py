"""Research workspace for concentrated-liquidity interval studies."""

from app.research.benchmarks import (
    BASELINE_CASES,
    BenchmarkCase,
    BenchmarkSuiteResult,
    run_benchmark_suite,
    save_benchmark_suite,
)
from app.research.artifacts import create_experiment_dir, save_study_artifacts
from app.research.reporting import (
    build_pair_comparison_table,
    plot_study_candidate_frontier,
    plot_summary_metric_bars,
    plot_summary_metric_heatmap,
)
from app.research.service import run_study
from app.research.types import StudyRequest, StudyResult

__all__ = [
    "BASELINE_CASES",
    "BenchmarkCase",
    "BenchmarkSuiteResult",
    "build_pair_comparison_table",
    "create_experiment_dir",
    "plot_study_candidate_frontier",
    "plot_summary_metric_bars",
    "plot_summary_metric_heatmap",
    "save_study_artifacts",
    "StudyRequest",
    "StudyResult",
    "run_benchmark_suite",
    "run_study",
    "save_benchmark_suite",
]
