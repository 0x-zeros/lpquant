from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
from typing import TYPE_CHECKING, Any

import pandas as pd

from app.research.types import StudyResult

if TYPE_CHECKING:
    from app.research.benchmarks import BenchmarkCase, BenchmarkSuiteResult

QUANT_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "run"


def create_experiment_dir(root: str | Path, label: str) -> Path:
    base = Path(root).expanduser()
    run_dir = base / f"{utc_timestamp()}_{slugify(label)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _run_git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    output = result.stdout.strip()
    return output or None


def runtime_metadata() -> dict[str, Any]:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "quant_root": str(QUANT_ROOT),
        "git": {
            "branch": _run_git("rev-parse", "--abbrev-ref", "HEAD"),
            "commit": _run_git("rev-parse", "HEAD"),
            "status": _run_git("status", "--short"),
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def study_metadata(
    study: StudyResult,
    *,
    label: str,
    notes: str | None = None,
    tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    frame = study.dataset.frame
    top_candidate = study.rankings.iloc[0].to_dict() if not study.rankings.empty else None
    payload: dict[str, Any] = {
        "label": label,
        "request": asdict(study.request),
        "dataset": {
            "pair": study.dataset.pair.symbol,
            "interval": study.dataset.interval,
            "source": study.dataset.source,
            "rows": len(frame),
            "start_timestamp": int(frame["timestamp"].iloc[0]),
            "end_timestamp": int(frame["timestamp"].iloc[-1]),
            "notes": study.dataset.notes,
        },
        "current_regime": study.current_regime,
        "top_candidate": top_candidate,
        "notes": notes,
        "tags": tags or [],
        "runtime": runtime_metadata(),
    }
    if extra_metadata:
        payload["extra_metadata"] = extra_metadata
    return payload


def save_study_artifacts(
    study: StudyResult,
    output_dir: str | Path,
    *,
    label: str,
    notes: str | None = None,
    tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Path]:
    root = Path(output_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)

    metadata = study_metadata(
        study,
        label=label,
        notes=notes,
        tags=tags,
        extra_metadata=extra_metadata,
    )

    paths = {
        "metadata": root / "metadata.json",
        "rankings": root / "rankings.csv",
        "similar_windows": root / "similar_windows.csv",
        "feature_tail": root / "feature_tail.csv",
    }
    _write_json(paths["metadata"], metadata)
    study.rankings.to_csv(paths["rankings"], index=False)
    study.similar_windows.to_csv(paths["similar_windows"], index=False)

    feature_columns = [
        "timestamp",
        "close",
        "trend_pct",
        "realized_vol_pct",
        "downside_vol_pct",
        "distance_to_sma_pct",
        "drawdown_pct",
        "rsi",
    ]
    tail = study.feature_frame[feature_columns].tail(200)
    tail.to_csv(paths["feature_tail"], index=False)
    return paths


def _suite_case_payload(case: "BenchmarkCase") -> dict[str, Any]:
    return {
        "name": case.name,
        "request": asdict(case.request),
        "thesis": case.thesis,
    }


def save_benchmark_bundle(
    suite: "BenchmarkSuiteResult",
    output_dir: str | Path,
    *,
    label: str,
    notes: str | None = None,
    tags: list[str] | None = None,
    include_case_artifacts: bool = True,
) -> dict[str, Path]:
    root = Path(output_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)

    metadata = {
        "label": label,
        "notes": notes,
        "tags": tags or [],
        "case_count": len(suite.cases),
        "successful_case_count": len(suite.studies),
        "failure_count": len(suite.failures),
        "cases": [_suite_case_payload(case) for case in suite.cases],
        "runtime": runtime_metadata(),
    }

    paths = {
        "metadata": root / "metadata.json",
        "summary": root / "summary.csv",
        "rankings": root / "rankings.csv",
        "failures": root / "failures.csv",
        "cases_dir": root / "cases",
    }
    _write_json(paths["metadata"], metadata)
    suite.summary.to_csv(paths["summary"], index=False)
    suite.rankings.to_csv(paths["rankings"], index=False)
    suite.failures.to_csv(paths["failures"], index=False)

    if include_case_artifacts:
        paths["cases_dir"].mkdir(parents=True, exist_ok=True)
        case_map = {case.name: case for case in suite.cases}
        for case_name, study in suite.studies.items():
            case = case_map[case_name]
            save_study_artifacts(
                study,
                paths["cases_dir"] / case_name,
                label=case_name,
                notes=case.thesis,
                tags=tags,
                extra_metadata={"case": _suite_case_payload(case)},
            )

    return paths
