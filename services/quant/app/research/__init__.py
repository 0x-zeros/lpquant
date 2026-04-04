"""集中流动性区间研究工作区。"""

from app.research.asset_diagnostics import plot_asset_diagnostics_dashboard, run_asset_diagnostics
from app.research.benchmarks import (
    BASELINE_CASES,
    BenchmarkCase,
    BenchmarkSuiteResult,
    run_benchmark_suite,
    save_benchmark_suite,
)
from app.research.artifacts import create_experiment_dir, save_study_artifacts
from app.research.coverage_service import run_coverage_study, run_coverage_sweep
from app.research.labels import (
    format_metric,
    format_objective,
    format_scenario,
    format_source,
    format_view,
    rename_for_display,
)
from app.research.reporting import (
    build_pair_comparison_table,
    plot_coverage_frontier,
    plot_coverage_period_heatmap,
    plot_coverage_period_frontiers,
    plot_study_candidate_frontier,
    plot_summary_metric_bars,
    plot_summary_metric_heatmap,
)
from app.research.service import run_study
from app.research.types import (
    AssetDiagnosticsRequest,
    AssetDiagnosticsResult,
    CoverageStudyRequest,
    CoverageStudyResult,
    CoverageSweepRequest,
    CoverageSweepResult,
    StudyRequest,
    StudyResult,
)

__all__ = [
    "BASELINE_CASES",
    "AssetDiagnosticsRequest",
    "AssetDiagnosticsResult",
    "BenchmarkCase",
    "BenchmarkSuiteResult",
    "build_pair_comparison_table",
    "CoverageStudyRequest",
    "CoverageStudyResult",
    "CoverageSweepRequest",
    "CoverageSweepResult",
    "create_experiment_dir",
    "format_metric",
    "format_objective",
    "format_scenario",
    "format_source",
    "format_view",
    "plot_asset_diagnostics_dashboard",
    "plot_coverage_frontier",
    "plot_coverage_period_frontiers",
    "plot_coverage_period_heatmap",
    "plot_study_candidate_frontier",
    "plot_summary_metric_bars",
    "plot_summary_metric_heatmap",
    "rename_for_display",
    "run_asset_diagnostics",
    "run_coverage_study",
    "run_coverage_sweep",
    "save_study_artifacts",
    "StudyRequest",
    "StudyResult",
    "run_benchmark_suite",
    "run_study",
    "save_benchmark_suite",
]
