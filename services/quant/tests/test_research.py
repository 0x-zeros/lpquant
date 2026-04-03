import numpy as np
import pandas as pd

from app.research.features import build_feature_frame, select_similar_windows
from app.research.market_data import parse_pair
from app.research.optimizer import build_candidate_grid, evaluate_candidates


def test_parse_pair_supports_delimited_and_suffix_forms():
    assert parse_pair("btc/usdc").symbol == "BTC/USDC"
    assert parse_pair("SUIUSDT").symbol == "SUI/USDT"


def test_build_candidate_grid_respects_directional_bias():
    bullish = build_candidate_grid("bullish")
    bearish = build_candidate_grid("bearish")
    neutral = build_candidate_grid("neutral")

    assert all(spec.center_offset_pct >= 0 for spec in bullish)
    assert all(spec.center_offset_pct <= 0 for spec in bearish)
    assert any(spec.center_offset_pct < 0 for spec in neutral)
    assert any(spec.center_offset_pct > 0 for spec in neutral)


def test_walkforward_evaluation_returns_ranked_candidates():
    timestamps = np.arange(0, 250) * 3_600_000
    closes = 100 + np.sin(np.linspace(0, 10, 250)) * 7 + np.linspace(-3, 6, 250)
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": closes,
            "high": closes * 1.002,
            "low": closes * 0.998,
            "close": closes,
            "volume": np.full_like(closes, 1_000.0),
        }
    )

    feature_frame = build_feature_frame(frame, lookback_bars=20, interval="1h")
    similar_windows = select_similar_windows(feature_frame, horizon_bars=12, neighbors=15)
    rankings = evaluate_candidates(
        frame=frame,
        similar_windows=similar_windows,
        interval="1h",
        horizon_bars=12,
        capital=10_000.0,
        fee_rate=0.003,
        view="neutral",
        objective="balanced",
    )

    assert not rankings.empty
    assert rankings["score"].is_monotonic_decreasing
    assert {"mean_fee_proxy_bps", "mean_in_range_pct", "sample_size"}.issubset(rankings.columns)
