from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.research.labels import format_metric, format_source, rename_for_display
from app.research.service import run_study
from app.research.types import StudyRequest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LP interval research optimizer，使用 Binance 历史数据与 walk-forward evaluation。",
    )
    parser.add_argument("--pair", required=True, help="Trading pair / 交易对，例如 BTC/USDC 或 SUIUSDC")
    parser.add_argument("--interval", default="4h", help="Binance interval / K 线周期，例如 1h、4h、1d")
    parser.add_argument("--days", type=int, default=365, help="History days / 历史数据天数")
    parser.add_argument(
        "--lookback-bars",
        type=int,
        default=90,
        help="Lookback bars / 用多少根 K 线定义当前 market regime",
    )
    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=30,
        help="Horizon bars / 每个历史样本向前评估多少根 K 线",
    )
    parser.add_argument("--capital", type=float, default=10_000.0, help="Capital / 回测资金规模")
    parser.add_argument("--fee-rate", type=float, default=0.003, help="Fee rate / 池子手续费率，例如 0.003")
    parser.add_argument(
        "--view",
        choices=["neutral", "bullish", "bearish"],
        default="neutral",
        help="Directional view / 方向判断，用来调整区间中心；可选 neutral、bullish、bearish",
    )
    parser.add_argument(
        "--objective",
        choices=["balanced", "carry", "defensive"],
        default="balanced",
        help="Ranking objective / 区间排序目标；可选 balanced、carry、defensive",
    )
    parser.add_argument(
        "--neighbors",
        type=int,
        default=120,
        help="Neighbors / 纳入多少个相似历史市场窗口",
    )
    parser.add_argument("--top-k", type=int, default=10, help="Top K / 打印前多少个候选区间")
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV / 可选，输出完整候选排名表的 CSV 路径",
    )
    return parser


def _format_dataset_summary(result) -> str:
    frame = result.dataset.frame
    start = pd.to_datetime(frame["timestamp"].iloc[0], unit="ms", utc=True)
    end = pd.to_datetime(frame["timestamp"].iloc[-1], unit="ms", utc=True)
    return (
        f"Pair / 交易对: {result.dataset.pair.symbol}\n"
        f"Bars / K线数量: {len(frame)} | Interval / 周期: {result.dataset.interval} | Source / 数据源: {format_source(result.dataset.source)}\n"
        f"Window / 时间窗口: {start:%Y-%m-%d %H:%M UTC} -> {end:%Y-%m-%d %H:%M UTC}"
    )


def _format_regime_summary(current_regime: dict[str, float | str]) -> str:
    return (
        f"Current regime / 当前市场状态: {current_regime['regime_label']}\n"
        f"Trend / 趋势: {current_regime['trend_pct']}% | Realized vol / 已实现波动率: {current_regime['realized_vol_pct']}% | "
        f"Downside vol / 下行波动率: {current_regime['downside_vol_pct']}%\n"
        f"Distance to SMA / 相对均线偏离: {current_regime['distance_to_sma_pct']}% | "
        f"Drawdown / 回撤: {current_regime['drawdown_pct']}% | RSI: {current_regime['rsi']}"
    )


def main() -> None:
    args = _build_parser().parse_args()
    request = StudyRequest(
        pair=args.pair,
        interval=args.interval,
        days=args.days,
        lookback_bars=args.lookback_bars,
        horizon_bars=args.horizon_bars,
        capital=args.capital,
        fee_rate=args.fee_rate,
        view=args.view,
        objective=args.objective,
        neighbors=args.neighbors,
        top_k=args.top_k,
    )

    result = run_study(request)
    print(_format_dataset_summary(result))
    if result.dataset.notes:
        print("\nNotes / 说明:")
        for note in result.dataset.notes:
            print(f"- {note}")

    print()
    print(_format_regime_summary(result.current_regime))
    print()

    ranking_columns = [
        "score",
        "width_pct",
        "center_offset_pct",
        "lower_from_entry_pct",
        "upper_from_entry_pct",
        "mean_fee_proxy_bps",
        "mean_in_range_pct",
        "no_exit_rate",
        "median_lp_vs_hodl_pct",
        "p10_lp_vs_hodl_pct",
        "mean_max_il_pct",
        "mean_max_drawdown_pct",
        "downside_breach_rate",
        "upside_breach_rate",
        "sample_size",
    ]
    print("Top interval candidates / 候选区间 Top 排名:")
    ranking_table = rename_for_display(result.rankings[ranking_columns].head(request.top_k))
    print(ranking_table.to_string(index=False))

    similar_columns = [
        "similarity_rank",
        "entry_time",
        "close",
        "trend_pct",
        "realized_vol_pct",
        "distance_to_sma_pct",
        "drawdown_pct",
        "rsi",
        "distance",
    ]
    print()
    print("Closest historical regime windows / 最接近的历史市场窗口:")
    similar_table = rename_for_display(result.similar_windows[similar_columns].head(10))
    print(similar_table.to_string(index=False))

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.rankings.to_csv(output_path, index=False)

        windows_path = output_path.with_name(f"{output_path.stem}.windows.csv")
        result.similar_windows.to_csv(windows_path, index=False)
        print()
        print(f"Saved rankings / 候选排名已保存到: {output_path}")
        print(f"Saved similar windows / 相似窗口已保存到: {windows_path}")


if __name__ == "__main__":
    main()
