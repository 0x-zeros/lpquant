"""集中流动性区间研究工作区。"""

from app.research.benchmarks import (
    BASELINE_CASES,
    BenchmarkCase,
    BenchmarkSuiteResult,
    run_benchmark_suite,
    save_benchmark_suite,
)
from app.research.artifacts import create_experiment_dir, save_study_artifacts
from app.research.labels import format_metric, format_objective, format_scenario, format_source, format_view, rename_for_display
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
    "format_metric",
    "format_objective",
    "format_scenario",
    "format_source",
    "format_view",
    "plot_study_candidate_frontier",
    "plot_summary_metric_bars",
    "plot_summary_metric_heatmap",
    "rename_for_display",
    "save_study_artifacts",
    "StudyRequest",
    "StudyResult",
    "run_benchmark_suite",
    "run_study",
    "save_benchmark_suite",
]
