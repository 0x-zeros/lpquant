import json

import pandas as pd

from app.research.artifacts import create_experiment_dir, save_study_artifacts, slugify
from app.research.types import PairSpec, PriceDataset, StudyRequest, StudyResult


def _fake_study_result() -> StudyResult:
    request = StudyRequest(pair="SUI/USDC")
    dataset = PriceDataset(
        pair=PairSpec(base="SUI", quote="USDC"),
        interval="4h",
        source="binance-direct",
        frame=pd.DataFrame(
            {
                "timestamp": [1_000, 2_000, 3_000],
                "open": [1.0, 1.1, 1.2],
                "high": [1.1, 1.2, 1.3],
                "low": [0.9, 1.0, 1.1],
                "close": [1.0, 1.15, 1.22],
                "volume": [100, 120, 140],
            }
        ),
        notes=[],
    )
    feature_frame = pd.DataFrame(
        {
            "timestamp": [1_000, 2_000, 3_000],
            "close": [1.0, 1.15, 1.22],
            "trend_pct": [0.0, 2.0, 4.0],
            "realized_vol_pct": [20.0, 22.0, 25.0],
            "downside_vol_pct": [8.0, 7.0, 6.0],
            "distance_to_sma_pct": [0.0, 1.0, 2.0],
            "drawdown_pct": [0.0, -1.0, -0.5],
            "rsi": [50.0, 58.0, 62.0],
        }
    )
    similar_windows = pd.DataFrame(
        {
            "entry_index": [0, 1],
            "timestamp": [1_000, 2_000],
            "entry_time": ["2024-01-01", "2024-01-02"],
            "close": [1.0, 1.15],
            "trend_pct": [1.0, 3.0],
            "realized_vol_pct": [20.0, 23.0],
            "distance_to_sma_pct": [0.5, 1.1],
            "drawdown_pct": [-0.5, -0.2],
            "rsi": [52.0, 61.0],
            "distance": [0.1, 0.2],
            "similarity_rank": [1, 2],
        }
    )
    rankings = pd.DataFrame(
        {
            "score": [80.0, 72.0],
            "width_pct": [4.0, 6.0],
            "center_offset_pct": [0.0, 1.0],
            "lower_from_entry_pct": [-2.0, -2.0],
            "upper_from_entry_pct": [2.0, 4.0],
            "mean_fee_proxy_bps": [35.0, 31.0],
            "mean_in_range_pct": [70.0, 75.0],
            "no_exit_rate": [42.0, 50.0],
            "median_lp_vs_hodl_pct": [2.5, 2.0],
            "p10_lp_vs_hodl_pct": [-1.0, -0.5],
            "mean_max_il_pct": [5.0, 4.5],
            "mean_max_drawdown_pct": [8.0, 7.0],
            "downside_breach_rate": [20.0, 15.0],
            "upside_breach_rate": [38.0, 35.0],
            "sample_size": [20, 20],
        }
    )
    return StudyResult(
        request=request,
        dataset=dataset,
        feature_frame=feature_frame,
        current_regime={"regime_label": "bullish / high-vol / overbought"},
        similar_windows=similar_windows,
        rankings=rankings,
    )


def test_slugify_and_experiment_dir(tmp_path):
    assert slugify("Baseline Suite 01") == "baseline_suite_01"
    run_dir = create_experiment_dir(tmp_path, "Baseline Suite 01")
    assert run_dir.exists()
    assert "baseline_suite_01" in run_dir.name


def test_save_study_artifacts_writes_metadata_and_csvs(tmp_path):
    study = _fake_study_result()
    paths = save_study_artifacts(study, tmp_path / "study", label="demo_case")

    assert paths["metadata"].exists()
    assert paths["rankings"].exists()
    assert paths["similar_windows"].exists()
    assert paths["feature_tail"].exists()

    metadata = json.loads(paths["metadata"].read_text())
    assert metadata["label"] == "demo_case"
    assert metadata["dataset"]["pair"] == "SUI/USDC"
    assert metadata["top_candidate"]["score"] == 80.0
