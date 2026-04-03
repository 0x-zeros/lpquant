from __future__ import annotations

import pandas as pd

VIEW_LABELS = {
    "neutral": "中性",
    "bullish": "看涨",
    "bearish": "看跌",
}

OBJECTIVE_LABELS = {
    "balanced": "均衡",
    "carry": "收益优先",
    "defensive": "防御",
}

SOURCE_LABELS = {
    "binance-direct": "Binance 直连",
    "binance-ratio": "Binance 比价构造",
    "binance-proxy": "Binance 稳定币代理",
}

COLUMN_LABELS = {
    "case_name": "案例名",
    "pair": "交易对",
    "interval": "周期",
    "view": "方向判断",
    "objective": "目标函数",
    "scenario": "场景",
    "pair_interval": "交易对/周期",
    "source": "数据源",
    "source_label": "数据源说明",
    "bars": "K线数量",
    "regime_label": "市场状态",
    "trend_pct": "趋势(%)",
    "realized_vol_pct": "已实现波动率(%)",
    "downside_vol_pct": "下行波动率(%)",
    "distance_to_sma_pct": "相对均线偏离(%)",
    "drawdown_pct": "回撤(%)",
    "rsi": "RSI",
    "score": "综合得分",
    "width_pct": "区间宽度(%)",
    "center_offset_pct": "中心偏移(%)",
    "lower_from_entry_pct": "下边界相对开仓(%)",
    "upper_from_entry_pct": "上边界相对开仓(%)",
    "mean_fee_proxy_bps": "平均手续费代理(bps)",
    "median_fee_proxy_bps": "手续费代理中位数(bps)",
    "mean_in_range_pct": "平均区间内占比(%)",
    "no_exit_rate": "未出圈比例(%)",
    "median_lp_vs_hodl_pct": "LP 相对 HODL 中位数(%)",
    "p10_lp_vs_hodl_pct": "LP 相对 HODL P10(%)",
    "mean_max_il_pct": "平均最大 IL(%)",
    "mean_max_drawdown_pct": "平均最大回撤(%)",
    "downside_breach_rate": "向下出圈比例(%)",
    "upside_breach_rate": "向上出圈比例(%)",
    "sample_size": "样本数",
    "similarity_rank": "相似度排名",
    "entry_time": "历史起点时间",
    "close": "收盘价",
    "distance": "相似距离",
    "entry_index": "历史起点索引",
    "current_price": "当前价格",
    "vol_rank": "波动率分位",
    "thesis": "研究假设",
    "error": "错误信息",
}


def format_view(view: str) -> str:
    return VIEW_LABELS.get(view, view)


def format_objective(objective: str) -> str:
    return OBJECTIVE_LABELS.get(objective, objective)


def format_scenario(view: str, objective: str) -> str:
    return f"{format_view(view)}/{format_objective(objective)}"


def format_source(source: str) -> str:
    return SOURCE_LABELS.get(source, source)


def format_metric(metric: str) -> str:
    return COLUMN_LABELS.get(metric, metric)


def rename_for_display(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns=COLUMN_LABELS)
