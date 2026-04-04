from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.research.features import bars_per_year, interval_to_hours
from app.research.market_data import load_price_history
from app.research.reporting import _configure_cjk_font
from app.research.types import AssetDiagnosticsRequest, AssetDiagnosticsResult

WINDOW_SPECS: tuple[tuple[str, int, str], ...] = (
    ("short_trend", 20, "短期趋势 SMA / short trend moving average"),
    ("medium_trend", 60, "中期趋势 SMA / medium trend moving average"),
    ("volatility", 30, "滚动波动率 / rolling realized volatility"),
    ("atr", 14, "ATR / average true range"),
    ("rsi", 14, "RSI / relative strength index"),
    ("macd_fast", 12, "MACD fast EMA"),
    ("macd_slow", 26, "MACD slow EMA"),
    ("macd_signal", 9, "MACD signal EMA"),
    ("volume", 20, "成交量 z-score / volume z-score"),
)


def lookback_days_to_bars(interval: str, lookback_days: int, *, minimum: int = 1) -> int:
    if lookback_days <= 0:
        raise ValueError("lookback_days 必须大于 0")

    interval_hours = interval_to_hours(interval)
    lookback_hours = lookback_days * 24.0
    return max(minimum, math.ceil(lookback_hours / interval_hours))


def build_window_config_table(interval: str) -> pd.DataFrame:
    rows = [
        {
            "window_name": window_name,
            "window_days": window_days,
            "window_bars": lookback_days_to_bars(interval, window_days),
            "description": description,
        }
        for window_name, window_days, description in WINDOW_SPECS
    ]
    return pd.DataFrame.from_records(rows)


def _compute_rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.rolling(window).mean()
    avg_loss = losses.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.where(avg_loss > 0, 100.0)
    rsi = rsi.where(avg_gain > 0, 0.0)
    return rsi.where((avg_gain > 0) | (avg_loss > 0), 50.0)


def build_asset_feature_frame(frame: pd.DataFrame, interval: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_frame = frame.copy()
    close = feature_frame["close"].astype(float)
    high = feature_frame["high"].astype(float)
    low = feature_frame["low"].astype(float)
    volume = feature_frame["volume"].astype(float)
    log_return = np.log(close).diff()

    window_config = build_window_config_table(interval)
    windows = dict(zip(window_config["window_name"], window_config["window_bars"], strict=True))
    annualizer = math.sqrt(bars_per_year(interval))

    feature_frame["return_pct"] = close.pct_change() * 100.0
    feature_frame["log_return"] = log_return
    feature_frame["cumulative_return_pct"] = (close / close.iloc[0] - 1.0) * 100.0
    feature_frame["drawdown_pct"] = (close / close.cummax() - 1.0) * 100.0

    feature_frame["sma_short"] = close.rolling(windows["short_trend"]).mean()
    feature_frame["sma_medium"] = close.rolling(windows["medium_trend"]).mean()
    bollinger_std = close.rolling(windows["short_trend"]).std()
    feature_frame["bollinger_mid"] = feature_frame["sma_short"]
    feature_frame["bollinger_upper"] = feature_frame["bollinger_mid"] + 2.0 * bollinger_std
    feature_frame["bollinger_lower"] = feature_frame["bollinger_mid"] - 2.0 * bollinger_std

    feature_frame["realized_vol_pct"] = (
        log_return.rolling(windows["volatility"]).std() * annualizer * 100.0
    )
    feature_frame["downside_vol_pct"] = (
        log_return.where(log_return < 0).rolling(windows["volatility"]).std() * annualizer * 100.0
    )

    prev_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    feature_frame["atr_pct"] = true_range.rolling(windows["atr"]).mean() / close * 100.0

    feature_frame["rsi"] = _compute_rsi(close, windows["rsi"])

    ema_fast = close.ewm(span=windows["macd_fast"], adjust=False).mean()
    ema_slow = close.ewm(span=windows["macd_slow"], adjust=False).mean()
    feature_frame["macd"] = ema_fast - ema_slow
    feature_frame["macd_signal"] = feature_frame["macd"].ewm(
        span=windows["macd_signal"],
        adjust=False,
    ).mean()
    feature_frame["macd_hist"] = feature_frame["macd"] - feature_frame["macd_signal"]

    volume_mean = volume.rolling(windows["volume"]).mean()
    volume_std = volume.rolling(windows["volume"]).std()
    feature_frame["volume_zscore"] = (volume - volume_mean) / volume_std.replace(0.0, np.nan)
    feature_frame["trend_vs_short_sma_pct"] = (close / feature_frame["sma_short"] - 1.0) * 100.0
    feature_frame["trend_vs_medium_sma_pct"] = (close / feature_frame["sma_medium"] - 1.0) * 100.0

    return feature_frame, window_config


def summarize_asset_regime(feature_frame: pd.DataFrame) -> dict[str, float | str]:
    valid = feature_frame.dropna(
        subset=[
            "sma_short",
            "sma_medium",
            "realized_vol_pct",
            "rsi",
            "macd_hist",
            "atr_pct",
            "volume_zscore",
        ]
    )
    if valid.empty:
        raise ValueError("可用特征不足，无法总结单币市场状态")

    latest = valid.iloc[-1]
    vol_rank = float(valid["realized_vol_pct"].rank(pct=True).iloc[-1])
    latest_close = float(latest["close"])
    sma_short = float(latest["sma_short"])
    sma_medium = float(latest["sma_medium"])
    rsi = float(latest["rsi"])
    macd_hist = float(latest["macd_hist"])

    if latest_close > sma_short > sma_medium:
        trend_regime = "bull trend / 多头趋势"
    elif latest_close < sma_short < sma_medium:
        trend_regime = "bear trend / 空头趋势"
    else:
        trend_regime = "range / 震荡整理"

    if vol_rank >= 0.67:
        vol_regime = "high vol / 高波动"
    elif vol_rank <= 0.33:
        vol_regime = "low vol / 低波动"
    else:
        vol_regime = "mid vol / 中等波动"

    if rsi >= 60 and macd_hist >= 0:
        momentum_regime = "positive momentum / 动量偏强"
    elif rsi <= 40 and macd_hist <= 0:
        momentum_regime = "negative momentum / 动量偏弱"
    else:
        momentum_regime = "mixed momentum / 动量中性"

    return {
        "trend_regime": trend_regime,
        "vol_regime": vol_regime,
        "momentum_regime": momentum_regime,
        "current_price": round(latest_close, 6),
        "trend_vs_short_sma_pct": round(float(latest["trend_vs_short_sma_pct"]), 2),
        "trend_vs_medium_sma_pct": round(float(latest["trend_vs_medium_sma_pct"]), 2),
        "realized_vol_pct": round(float(latest["realized_vol_pct"]), 2),
        "downside_vol_pct": round(float(latest["downside_vol_pct"]), 2),
        "atr_pct": round(float(latest["atr_pct"]), 2),
        "rsi": round(rsi, 2),
        "macd_hist": round(macd_hist, 6),
        "volume_zscore": round(float(latest["volume_zscore"]), 2),
        "drawdown_pct": round(float(latest["drawdown_pct"]), 2),
        "vol_rank": round(vol_rank, 3),
        "cumulative_return_pct": round(float(latest["cumulative_return_pct"]), 2),
    }


def build_horizon_return_table(
    feature_frame: pd.DataFrame,
    interval: str,
    horizon_days: tuple[int, ...],
) -> pd.DataFrame:
    close = feature_frame["close"].astype(float).reset_index(drop=True)
    rows: list[dict[str, float | int]] = []
    for days in horizon_days:
        bars = lookback_days_to_bars(interval, days)
        if len(close) <= bars:
            continue
        start_price = float(close.iloc[-bars - 1])
        end_price = float(close.iloc[-1])
        rows.append(
            {
                "horizon_days": days,
                "horizon_bars": bars,
                "return_pct": round((end_price / start_price - 1.0) * 100.0, 2),
            }
        )
    return pd.DataFrame.from_records(rows)


def build_return_statistics_table(feature_frame: pd.DataFrame, interval: str) -> pd.DataFrame:
    returns = feature_frame["return_pct"].dropna()
    log_returns = feature_frame["log_return"].dropna()
    if returns.empty or log_returns.empty:
        raise ValueError("收益率样本不足，无法计算统计指标")

    annualizer = bars_per_year(interval)
    annualized_return_pct = float(log_returns.mean() * annualizer * 100.0)
    annualized_vol_pct = float(log_returns.std() * math.sqrt(annualizer) * 100.0)
    var_5_pct = float(np.percentile(returns, 5))
    tail = returns[returns <= var_5_pct]
    cvar_5_pct = float(tail.mean()) if not tail.empty else var_5_pct

    row = {
        "annualized_return_pct": round(annualized_return_pct, 2),
        "annualized_vol_pct": round(annualized_vol_pct, 2),
        "sharpe_ratio": round(annualized_return_pct / annualized_vol_pct, 3)
        if annualized_vol_pct > 0
        else np.nan,
        "skewness": round(float(returns.skew()), 3),
        "excess_kurtosis": round(float(returns.kurt()), 3),
        "positive_rate_pct": round(float((returns > 0).mean() * 100.0), 2),
        "var_5_pct": round(var_5_pct, 2),
        "cvar_5_pct": round(cvar_5_pct, 2),
        "autocorr_lag1": round(float(returns.autocorr(lag=1)), 3),
        "abs_autocorr_lag1": round(float(returns.abs().autocorr(lag=1)), 3),
        "max_drawdown_pct": round(float(feature_frame["drawdown_pct"].min()), 2),
        "sample_size": int(len(returns)),
    }
    return pd.DataFrame([row])


def build_autocorrelation_table(
    feature_frame: pd.DataFrame,
    lags: tuple[int, ...],
) -> pd.DataFrame:
    returns = feature_frame["return_pct"].dropna()
    if returns.empty:
        raise ValueError("收益率样本不足，无法计算自相关")

    confidence_band = 2.0 / math.sqrt(len(returns))
    rows = []
    for lag in lags:
        if lag >= len(returns):
            continue
        rows.append(
            {
                "lag": lag,
                "return_autocorr": round(float(returns.autocorr(lag=lag)), 3),
                "abs_return_autocorr": round(float(returns.abs().autocorr(lag=lag)), 3),
                "confidence_band": round(confidence_band, 3),
            }
        )
    return pd.DataFrame.from_records(rows)


def run_asset_diagnostics(request: AssetDiagnosticsRequest) -> AssetDiagnosticsResult:
    dataset = load_price_history(
        raw_pair=f"{request.asset}/{request.quote}",
        interval=request.interval,
        days=request.days,
    )
    feature_frame, window_config = build_asset_feature_frame(dataset.frame, request.interval)
    regime_summary = summarize_asset_regime(feature_frame)

    snapshot_row = {
        "asset": request.asset.upper(),
        "quote": request.quote.upper(),
        "pair": dataset.pair.symbol,
        "interval": request.interval,
        "source": dataset.source,
        **regime_summary,
    }
    snapshot = pd.DataFrame([snapshot_row])

    return AssetDiagnosticsResult(
        request=request,
        dataset=dataset,
        window_config=window_config,
        feature_frame=feature_frame,
        regime_summary=regime_summary,
        snapshot=snapshot,
        return_stats=build_return_statistics_table(feature_frame, request.interval),
        horizon_returns=build_horizon_return_table(
            feature_frame,
            request.interval,
            request.horizon_days,
        ),
        autocorrelation=build_autocorrelation_table(feature_frame, request.autocorr_lags),
    )


def plot_asset_diagnostics_dashboard(
    result: AssetDiagnosticsResult,
    *,
    figsize: tuple[float, float] = (16.0, 18.0),
    title: str | None = None,
) -> tuple[plt.Figure, np.ndarray]:
    if result.feature_frame.empty:
        raise ValueError("feature_frame 为空，没有可绘制的数据")

    _configure_cjk_font()
    feature_frame = result.feature_frame.copy()
    timestamps = pd.to_datetime(feature_frame["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
    windows = result.window_config.set_index("window_name")["window_days"].to_dict()
    stats = result.return_stats.iloc[0]
    autocorr = result.autocorrelation

    fig, axes = plt.subplots(4, 2, figsize=figsize)

    price_ax = axes[0, 0]
    price_ax.plot(timestamps, feature_frame["close"], label="close", linewidth=1.4)
    price_ax.plot(
        timestamps,
        feature_frame["sma_short"],
        label=f"SMA {windows['short_trend']}d",
        linewidth=1.1,
    )
    price_ax.plot(
        timestamps,
        feature_frame["sma_medium"],
        label=f"SMA {windows['medium_trend']}d",
        linewidth=1.1,
    )
    price_ax.fill_between(
        timestamps,
        feature_frame["bollinger_lower"],
        feature_frame["bollinger_upper"],
        alpha=0.12,
        label="Bollinger band",
    )
    price_ax.set_title("Price, moving averages, and Bollinger band / 价格、均线与布林带")
    price_ax.grid(alpha=0.2)
    price_ax.legend(loc="upper left")

    drawdown_ax = axes[0, 1]
    drawdown_ax.fill_between(
        timestamps,
        feature_frame["drawdown_pct"],
        0.0,
        color="#d95f02",
        alpha=0.3,
    )
    drawdown_ax.plot(timestamps, feature_frame["drawdown_pct"], color="#d95f02", linewidth=1.1)
    drawdown_ax.set_title("Drawdown / 回撤")
    drawdown_ax.set_ylabel("drawdown (%)")
    drawdown_ax.grid(alpha=0.2)

    vol_ax = axes[1, 0]
    vol_ax.plot(
        timestamps,
        feature_frame["realized_vol_pct"],
        label=f"realized vol ({windows['volatility']}d)",
        linewidth=1.2,
    )
    vol_ax.plot(
        timestamps,
        feature_frame["downside_vol_pct"],
        label=f"downside vol ({windows['volatility']}d)",
        linewidth=1.1,
    )
    vol_ax.plot(
        timestamps,
        feature_frame["atr_pct"],
        label=f"ATR ({windows['atr']}d)",
        linewidth=1.1,
    )
    vol_ax.set_title("Risk measures / 波动与风险度量")
    vol_ax.set_ylabel("(%)")
    vol_ax.grid(alpha=0.2)
    vol_ax.legend(loc="upper left")

    volume_ax = axes[1, 1]
    volume_ax.bar(timestamps, feature_frame["volume"], color="#bdbdbd", width=1.0)
    volume_ax.set_title("Volume and volume z-score / 成交量与成交量 z-score")
    volume_ax.set_ylabel("volume")
    volume_ax.grid(alpha=0.15)
    volume_overlay = volume_ax.twinx()
    volume_overlay.plot(
        timestamps,
        feature_frame["volume_zscore"],
        color="#1b9e77",
        linewidth=1.0,
        label="volume z-score",
    )
    volume_overlay.axhline(2.0, color="#1b9e77", linestyle="--", linewidth=0.9, alpha=0.7)
    volume_overlay.axhline(-2.0, color="#1b9e77", linestyle="--", linewidth=0.9, alpha=0.7)
    volume_overlay.set_ylabel("z-score")

    rsi_ax = axes[2, 0]
    rsi_ax.plot(timestamps, feature_frame["rsi"], color="#7570b3", linewidth=1.2)
    rsi_ax.axhline(70.0, color="#d95f02", linestyle="--", linewidth=0.9)
    rsi_ax.axhline(30.0, color="#1b9e77", linestyle="--", linewidth=0.9)
    rsi_ax.set_ylim(0.0, 100.0)
    rsi_ax.set_title("RSI / 相对强弱指标")
    rsi_ax.grid(alpha=0.2)

    macd_ax = axes[2, 1]
    macd_ax.bar(
        timestamps,
        feature_frame["macd_hist"],
        color=np.where(feature_frame["macd_hist"] >= 0, "#66c2a5", "#fc8d62"),
        alpha=0.6,
        width=1.0,
        label="MACD hist",
    )
    macd_ax.plot(timestamps, feature_frame["macd"], color="#1f78b4", linewidth=1.1, label="MACD")
    macd_ax.plot(
        timestamps,
        feature_frame["macd_signal"],
        color="#e31a1c",
        linewidth=1.0,
        label="signal",
    )
    macd_ax.set_title("MACD / 趋势动量差")
    macd_ax.grid(alpha=0.2)
    macd_ax.legend(loc="upper left")

    hist_ax = axes[3, 0]
    returns = feature_frame["return_pct"].dropna()
    hist_ax.hist(returns, bins=30, color="#80b1d3", alpha=0.8)
    hist_ax.axvline(returns.mean(), color="#1b9e77", linewidth=1.0, label="mean")
    hist_ax.axvline(stats["var_5_pct"], color="#d95f02", linewidth=1.0, label="VaR 5%")
    hist_ax.axvline(stats["cvar_5_pct"], color="#7570b3", linewidth=1.0, label="CVaR 5%")
    hist_ax.set_title("Return distribution / 收益分布")
    hist_ax.set_xlabel("return (%)")
    hist_ax.grid(alpha=0.2)
    hist_ax.legend(loc="upper left")

    acf_ax = axes[3, 1]
    positions = np.arange(len(autocorr))
    acf_ax.bar(positions - 0.18, autocorr["return_autocorr"], width=0.36, label="return acf")
    acf_ax.bar(
        positions + 0.18,
        autocorr["abs_return_autocorr"],
        width=0.36,
        label="|return| acf",
    )
    acf_ax.axhline(float(autocorr["confidence_band"].iloc[0]), color="black", linestyle="--", linewidth=0.9)
    acf_ax.axhline(float(-autocorr["confidence_band"].iloc[0]), color="black", linestyle="--", linewidth=0.9)
    acf_ax.set_xticks(positions)
    acf_ax.set_xticklabels(autocorr["lag"].astype(str))
    acf_ax.set_title("Autocorrelation / 自相关")
    acf_ax.set_xlabel("lag")
    acf_ax.grid(alpha=0.2)
    acf_ax.legend(loc="upper left")

    dashboard_title = title or (
        f"{result.dataset.pair.symbol} quant diagnostics | "
        f"{result.regime_summary['trend_regime']} | "
        f"{result.regime_summary['vol_regime']} | "
        f"{result.regime_summary['momentum_regime']}"
    )
    fig.suptitle(dashboard_title, fontsize=15, y=0.995)
    fig.tight_layout()
    return fig, axes
