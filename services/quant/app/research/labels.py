from __future__ import annotations

import pandas as pd

VIEW_LABELS = {
    "neutral": "neutral / 中性",
    "bullish": "bullish / 看涨",
    "bearish": "bearish / 看跌",
}

OBJECTIVE_LABELS = {
    "balanced": "balanced / 均衡",
    "carry": "carry / 收益优先",
    "defensive": "defensive / 防御",
}

SOURCE_LABELS = {
    "binance-direct": "Binance direct / Binance 直连",
    "binance-ratio": "Binance ratio / Binance 比价构造",
    "binance-proxy": "Binance proxy / Binance 稳定币代理",
}

COLUMN_LABELS = {
    "case_name": "case name / 案例名",
    "pair": "pair / 交易对",
    "interval": "interval / 周期",
    "view": "view / 方向判断",
    "objective": "objective / 目标函数",
    "scenario": "scenario / 场景",
    "pair_interval": "pair + interval / 交易对/周期",
    "source": "source / 数据源",
    "source_label": "source label / 数据源说明",
    "bars": "bars / K线数量",
    "regime_label": "regime / 市场状态",
    "trend_pct": "trend (%) / 趋势(%)",
    "realized_vol_pct": "realized vol (%) / 已实现波动率(%)",
    "downside_vol_pct": "downside vol (%) / 下行波动率(%)",
    "distance_to_sma_pct": "distance to SMA (%) / 相对均线偏离(%)",
    "drawdown_pct": "drawdown (%) / 回撤(%)",
    "rsi": "RSI",
    "score": "score / 综合得分",
    "width_pct": "width (%) / 区间宽度(%)",
    "center_offset_pct": "center offset (%) / 中心偏移(%)",
    "lower_from_entry_pct": "lower from entry (%) / 下边界相对开仓(%)",
    "upper_from_entry_pct": "upper from entry (%) / 上边界相对开仓(%)",
    "mean_fee_proxy_bps": "mean fee proxy (bps) / 平均手续费代理(bps)",
    "median_fee_proxy_bps": "median fee proxy (bps) / 手续费代理中位数(bps)",
    "mean_in_range_pct": "mean in-range (%) / 平均区间内占比(%)",
    "no_exit_rate": "no-exit rate (%) / 未出圈比例(%)",
    "median_lp_vs_hodl_pct": "median LP vs HODL (%) / LP 相对 HODL 中位数(%)",
    "p10_lp_vs_hodl_pct": "p10 LP vs HODL (%) / LP 相对 HODL P10(%)",
    "mean_max_il_pct": "mean max IL (%) / 平均最大 IL(%)",
    "mean_max_drawdown_pct": "mean max drawdown (%) / 平均最大回撤(%)",
    "downside_breach_rate": "downside breach rate (%) / 向下出圈比例(%)",
    "upside_breach_rate": "upside breach rate (%) / 向上出圈比例(%)",
    "sample_size": "sample size / 样本数",
    "similarity_rank": "similarity rank / 相似度排名",
    "entry_time": "entry time / 历史起点时间",
    "close": "close / 收盘价",
    "distance": "distance / 相似距离",
    "entry_index": "entry index / 历史起点索引",
    "current_price": "current price / 当前价格",
    "vol_rank": "vol rank / 波动率分位",
    "thesis": "thesis / 研究假设",
    "error": "error / 错误信息",
    "holding_days": "holding days / 持有期天数",
    "holding_bars": "holding bars / 持有期样本步数",
    "coverage_target_pct": "coverage target (%) / 目标覆盖率(%)",
    "achieved_coverage_pct": "achieved coverage (%) / 实际覆盖率(%)",
    "out_of_range_pct": "out-of-range (%) / 出区间比例(%)",
    "lower_bound_pct": "lower bound (%) / 下边界(%)",
    "upper_bound_pct": "upper bound (%) / 上边界(%)",
    "downside_touch_pct": "downside touch (%) / 向下触边比例(%)",
    "upside_touch_pct": "upside touch (%) / 向上触边比例(%)",
    "current_lower_price": "current lower price / 当前下边界价格",
    "current_upper_price": "current upper price / 当前上边界价格",
    "entry_timestamp": "entry timestamp / 起点时间戳",
    "exit_timestamp": "exit timestamp / 终点时间戳",
    "entry_price": "entry price / 起点价格",
    "end_price": "end price / 终点价格",
    "min_price": "min price / 最低价",
    "max_price": "max price / 最高价",
    "lower_excursion_pct": "lower excursion (%) / 向下波动幅度(%)",
    "upper_excursion_pct": "upper excursion (%) / 向上波动幅度(%)",
    "end_return_pct": "end return (%) / 期末涨跌幅(%)",
    "path_range_pct": "path range (%) / 路径振幅(%)",
    "p5_end_return_pct": "p5 end return (%) / 持有期收益 P5(%)",
    "p25_end_return_pct": "p25 end return (%) / 持有期收益 P25(%)",
    "p50_end_return_pct": "p50 end return (%) / 持有期收益 P50(%)",
    "p75_end_return_pct": "p75 end return (%) / 持有期收益 P75(%)",
    "p95_end_return_pct": "p95 end return (%) / 持有期收益 P95(%)",
    "mean_end_return_pct": "mean end return (%) / 持有期平均收益(%)",
    "asset": "asset / 币种",
    "quote": "quote / 计价币",
    "window_name": "window / 指标窗口",
    "window_days": "window days / 窗口天数",
    "window_bars": "window bars / 窗口样本步数",
    "description": "description / 说明",
    "return_pct": "return (%) / 收益率(%)",
    "cumulative_return_pct": "cumulative return (%) / 累计收益(%)",
    "atr_pct": "ATR (%) / 平均真实波幅(%)",
    "sma_short": "short SMA / 短期均线",
    "sma_medium": "medium SMA / 中期均线",
    "bollinger_mid": "Bollinger mid / 布林中轨",
    "bollinger_upper": "Bollinger upper / 布林上轨",
    "bollinger_lower": "Bollinger lower / 布林下轨",
    "macd": "MACD",
    "macd_signal": "MACD signal / MACD 信号线",
    "macd_hist": "MACD hist / MACD 柱",
    "volume_zscore": "volume z-score / 成交量 z-score",
    "trend_regime": "trend regime / 趋势状态",
    "vol_regime": "vol regime / 波动状态",
    "momentum_regime": "momentum regime / 动量状态",
    "trend_vs_short_sma_pct": "vs short SMA (%) / 相对短期均线偏离(%)",
    "trend_vs_medium_sma_pct": "vs medium SMA (%) / 相对中期均线偏离(%)",
    "horizon_days": "horizon days / 观察天数",
    "horizon_bars": "horizon bars / 观察步数",
    "annualized_return_pct": "annualized return (%) / 年化收益(%)",
    "annualized_vol_pct": "annualized vol (%) / 年化波动率(%)",
    "sharpe_ratio": "Sharpe ratio / 夏普比率",
    "positive_rate_pct": "positive rate (%) / 上涨占比(%)",
    "skewness": "skewness / 偏度",
    "excess_kurtosis": "excess kurtosis / 超额峰度",
    "var_5_pct": "VaR 5% / 5%分位风险",
    "cvar_5_pct": "CVaR 5% / 条件尾部风险",
    "autocorr_lag1": "autocorr lag1 / 一阶自相关",
    "abs_autocorr_lag1": "abs autocorr lag1 / 绝对收益一阶自相关",
    "lag": "lag / 滞后阶数",
    "return_autocorr": "return autocorr / 收益自相关",
    "abs_return_autocorr": "abs return autocorr / 绝对收益自相关",
    "confidence_band": "confidence band / 置信带",
    "coverage_norm": "coverage norm / 覆盖率归一化",
    "width_norm": "width norm / 宽度归一化",
    "ideal_distance": "ideal distance / 理想点距离",
    "knee_score": "knee score / 拐点分数",
    "efficiency_score": "efficiency score / 覆盖率宽度效率",
    "recommendation_eligible": "eligible / 可进入推荐集",
    "minimum_recommendation_coverage_pct": "minimum recommendation coverage (%) / 最低推荐覆盖率(%)",
    "period_label": "period / 持有期标签",
    "recommendation_reason": "recommendation reason / 推荐原因",
    "is_period_recommendation": "period recommendation / period 最优推荐",
    "is_global_recommendation": "global recommendation / 全局最优推荐",
}


def format_view(view: str) -> str:
    return VIEW_LABELS.get(view, view)


def format_objective(objective: str) -> str:
    return OBJECTIVE_LABELS.get(objective, objective)


def format_scenario(view: str, objective: str) -> str:
    return f"{format_view(view)} | {format_objective(objective)}"


def format_source(source: str) -> str:
    return SOURCE_LABELS.get(source, source)


def format_metric(metric: str) -> str:
    return COLUMN_LABELS.get(metric, metric)


def rename_for_display(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(columns=COLUMN_LABELS)
