from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.research.coverage_service import run_coverage_study
from app.research.labels import rename_for_display
from app.research.types import CoverageStudyRequest


def _parse_targets(raw: str) -> tuple[float, ...]:
    values = [part.strip() for part in raw.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("frontier targets 不能为空")
    try:
        return tuple(float(value) for value in values)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"frontier targets 解析失败: {exc}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Coverage-constrained price-range optimizer / "
            "在 stay-in-range 概率约束下寻找最窄价格区间的研究工具。"
        ),
    )
    parser.add_argument("--pair", required=True, help="Trading pair / 交易对，例如 BTC/USDC")
    parser.add_argument(
        "--interval",
        default="1d",
        help="Sampling interval / 采样周期，默认 1d；这里只是数据采样频率，不是区间目标本身。",
    )
    parser.add_argument("--days", type=int, default=730, help="History days / 历史数据天数")
    parser.add_argument(
        "--holding-days",
        type=int,
        default=30,
        help="Holding period days / 持有期天数，例如 30、60、365",
    )
    parser.add_argument(
        "--coverage-target",
        type=float,
        default=90.0,
        help="Coverage target (%%) / stay-in-range 目标概率，例如 90",
    )
    parser.add_argument(
        "--frontier-targets",
        type=_parse_targets,
        default=(70.0, 80.0, 85.0, 90.0, 95.0, 97.5),
        help="Coverage frontier / 想比较的 coverage target 列表，逗号分隔",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory / 可选，保存 best range、frontier、window frame 的目录",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    request = CoverageStudyRequest(
        pair=args.pair,
        interval=args.interval,
        days=args.days,
        holding_days=args.holding_days,
        coverage_target_pct=args.coverage_target,
        frontier_targets_pct=args.frontier_targets,
    )

    result = run_coverage_study(request)
    frame = result.dataset.frame
    start = pd.to_datetime(frame["timestamp"].iloc[0], unit="ms", utc=True)
    end = pd.to_datetime(frame["timestamp"].iloc[-1], unit="ms", utc=True)

    print(f"Pair / 交易对: {result.dataset.pair.symbol}")
    print(
        "Sampling interval / 采样周期: "
        f"{result.dataset.interval} | History days / 历史天数: {request.days}"
    )
    print(
        "Holding period / 持有期: "
        f"{request.holding_days} 天 | Holding bars / 对应样本步数: {result.holding_bars}"
    )
    print(f"Window / 时间窗口: {start:%Y-%m-%d} -> {end:%Y-%m-%d}")
    print()

    print("Holding-period return distribution / 持有期收益分布:")
    return_stats = pd.DataFrame([result.return_stats])
    print(rename_for_display(return_stats).to_string(index=False))
    print()

    print("Best price range under coverage constraint / coverage 约束下的最优价格区间:")
    best_interval = pd.DataFrame([result.best_interval])
    print(rename_for_display(best_interval).to_string(index=False))
    print()

    print("Coverage frontier / coverage 前沿:")
    frontier_columns = [
        "coverage_target_pct",
        "achieved_coverage_pct",
        "lower_bound_pct",
        "upper_bound_pct",
        "width_pct",
        "center_offset_pct",
        "out_of_range_pct",
        "downside_touch_pct",
        "upside_touch_pct",
        "current_lower_price",
        "current_upper_price",
    ]
    print(rename_for_display(result.frontier[frontier_columns]).to_string(index=False))

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([result.best_interval]).to_csv(output_dir / "best_interval.csv", index=False)
        result.frontier.to_csv(output_dir / "coverage_frontier.csv", index=False)
        result.window_frame.to_csv(output_dir / "holding_windows.csv", index=False)
        print()
        print(f"Saved outputs / 输出已保存到: {output_dir}")


if __name__ == "__main__":
    main()
