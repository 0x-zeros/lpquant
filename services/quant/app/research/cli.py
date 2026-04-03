from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from app.research.service import run_study
from app.research.types import StudyRequest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research-first LP interval optimizer using Binance history and walk-forward studies.",
    )
    parser.add_argument("--pair", required=True, help="Trading pair, for example BTC/USDC or SUIUSDC")
    parser.add_argument("--interval", default="4h", help="Binance interval, such as 1h, 4h, 1d")
    parser.add_argument("--days", type=int, default=365, help="How many calendar days of history to load")
    parser.add_argument(
        "--lookback-bars",
        type=int,
        default=90,
        help="How many bars define the current market regime",
    )
    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=30,
        help="How many forward bars each historical study window evaluates",
    )
    parser.add_argument("--capital", type=float, default=10_000.0, help="Capital used in backtests")
    parser.add_argument("--fee-rate", type=float, default=0.003, help="Pool fee rate, e.g. 0.003")
    parser.add_argument(
        "--view",
        choices=["neutral", "bullish", "bearish"],
        default="neutral",
        help="Directional belief used to bias interval centers",
    )
    parser.add_argument(
        "--objective",
        choices=["balanced", "carry", "defensive"],
        default="balanced",
        help="Scoring profile for interval ranking",
    )
    parser.add_argument(
        "--neighbors",
        type=int,
        default=120,
        help="How many similar historical regime windows to include",
    )
    parser.add_argument("--top-k", type=int, default=10, help="How many ranked candidates to print")
    parser.add_argument(
        "--output",
        type=str,
        help="Optional CSV path for the full candidate ranking table",
    )
    return parser


def _format_dataset_summary(result) -> str:
    frame = result.dataset.frame
    start = pd.to_datetime(frame["timestamp"].iloc[0], unit="ms", utc=True)
    end = pd.to_datetime(frame["timestamp"].iloc[-1], unit="ms", utc=True)
    return (
        f"Pair: {result.dataset.pair.symbol}\n"
        f"Bars: {len(frame)} | Interval: {result.dataset.interval} | Source: {result.dataset.source}\n"
        f"Window: {start:%Y-%m-%d %H:%M UTC} -> {end:%Y-%m-%d %H:%M UTC}"
    )


def _format_regime_summary(current_regime: dict[str, float | str]) -> str:
    return (
        f"Current regime: {current_regime['regime_label']}\n"
        f"Trend: {current_regime['trend_pct']}% | Realized vol: {current_regime['realized_vol_pct']}% | "
        f"Downside vol: {current_regime['downside_vol_pct']}%\n"
        f"Distance to SMA: {current_regime['distance_to_sma_pct']}% | "
        f"Drawdown: {current_regime['drawdown_pct']}% | RSI: {current_regime['rsi']}"
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
        print("\nNotes:")
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
    print("Top interval candidates:")
    print(result.rankings[ranking_columns].head(request.top_k).to_string(index=False))

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
    print("Closest historical regime windows:")
    print(result.similar_windows[similar_columns].head(10).to_string(index=False))

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.rankings.to_csv(output_path, index=False)

        windows_path = output_path.with_name(f"{output_path.stem}.windows.csv")
        result.similar_windows.to_csv(windows_path, index=False)
        print()
        print(f"Saved rankings to {output_path}")
        print(f"Saved similar windows to {windows_path}")


if __name__ == "__main__":
    main()
