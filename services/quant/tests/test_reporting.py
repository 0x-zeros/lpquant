import pandas as pd

from app.research.reporting import annotate_summary, build_pair_comparison_table


def _summary_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "pair": ["BTC/USDC", "BTC/USDC", "SUI/USDC"],
            "interval": ["4h", "1d", "4h"],
            "view": ["neutral", "bullish", "bearish"],
            "objective": ["balanced", "carry", "defensive"],
            "regime_label": ["sideways", "bullish", "bearish"],
            "score": [70.0, 74.0, 62.0],
            "width_pct": [4.0, 6.0, 8.0],
            "center_offset_pct": [0.0, 1.5, -2.0],
            "mean_fee_proxy_bps": [24.0, 31.0, 22.0],
            "mean_in_range_pct": [65.0, 70.0, 72.0],
            "no_exit_rate": [40.0, 55.0, 58.0],
            "median_lp_vs_hodl_pct": [2.0, 3.0, 1.0],
            "p10_lp_vs_hodl_pct": [-1.0, 0.5, -2.0],
            "downside_breach_rate": [20.0, 18.0, 14.0],
            "mean_max_drawdown_pct": [9.0, 8.0, 7.0],
        }
    )


def test_annotate_summary_adds_scenario_and_pair_interval():
    annotated = annotate_summary(_summary_frame())
    assert "scenario" in annotated.columns
    assert "pair_interval" in annotated.columns
    assert annotated.loc[0, "scenario"] == "neutral / 中性 | balanced / 均衡"
    assert annotated.loc[0, "pair_interval"] == "BTC/USDC 4h"


def test_build_pair_comparison_table_filters_and_sorts():
    table = build_pair_comparison_table(_summary_frame(), pair="BTC/USDC")
    assert list(table["pair / 交易对"].unique()) == ["BTC/USDC"]
    assert list(table["scenario / 场景"]) == [
        "bullish / 看涨 | carry / 收益优先",
        "neutral / 中性 | balanced / 均衡",
    ]
