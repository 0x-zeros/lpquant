import numpy as np
import pandas as pd

from app.research.asset_diagnostics import (
    build_asset_feature_frame,
    build_autocorrelation_table,
    build_horizon_return_table,
    build_return_statistics_table,
    build_window_config_table,
    lookback_days_to_bars,
    summarize_asset_regime,
)


def _frame(rows: int = 220) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="D", tz="UTC")
    base = np.linspace(100.0, 140.0, rows)
    wave = 3.0 * np.sin(np.linspace(0, 10, rows))
    close = base + wave
    open_ = close - 0.5
    high = close + 1.2
    low = close - 1.2
    volume = np.linspace(1_000.0, 1_500.0, rows)
    return pd.DataFrame(
        {
            "timestamp": (timestamps.view("int64") // 1_000_000).astype(int),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def test_lookback_days_to_bars_respects_interval():
    assert lookback_days_to_bars("1d", 30) == 30
    assert lookback_days_to_bars("4h", 30) == 180


def test_build_asset_feature_frame_adds_expected_columns():
    feature_frame, window_config = build_asset_feature_frame(_frame(), "1d")

    assert {"sma_short", "realized_vol_pct", "atr_pct", "macd_hist", "volume_zscore"}.issubset(
        feature_frame.columns
    )
    assert list(window_config.columns) == ["window_name", "window_days", "window_bars", "description"]


def test_summary_statistics_tables_are_well_formed():
    feature_frame, _ = build_asset_feature_frame(_frame(), "1d")

    regime = summarize_asset_regime(feature_frame)
    return_stats = build_return_statistics_table(feature_frame, "1d")
    horizons = build_horizon_return_table(feature_frame, "1d", (7, 30, 90))
    autocorr = build_autocorrelation_table(feature_frame, (1, 2, 5))

    assert regime["trend_regime"].startswith("bull trend")
    assert float(return_stats.loc[0, "cvar_5_pct"]) <= float(return_stats.loc[0, "var_5_pct"])
    assert list(horizons["horizon_days"]) == [7, 30, 90]
    assert list(autocorr["lag"]) == [1, 2, 5]
    assert float(autocorr.loc[0, "confidence_band"]) > 0


def test_build_window_config_table_contains_standard_windows():
    config = build_window_config_table("1d")
    assert set(config["window_name"]) >= {
        "short_trend",
        "medium_trend",
        "volatility",
        "atr",
        "rsi",
        "macd_fast",
        "macd_slow",
        "macd_signal",
        "volume",
    }
