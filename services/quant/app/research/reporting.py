from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd

from app.research.labels import format_metric, format_scenario, rename_for_display

CJK_FONT_CANDIDATES = [
    # macOS
    "Hiragino Sans GB",
    "PingFang SC",
    "Songti SC",
    "STHeiti",
    "Arial Unicode MS",
    # Windows
    "Microsoft YaHei",
    "Microsoft JhengHei",
    "DengXian",
    "SimHei",
    "SimSun",
    # Linux / cross-platform CJK packs
    "Noto Sans CJK SC",
    "Noto Sans CJK TC",
    "Noto Sans CJK JP",
    "WenQuanYi Zen Hei",
    "Source Han Sans SC",
    "Source Han Sans CN",
]


@lru_cache(maxsize=1)
def _configure_cjk_font() -> str:
    """配置 matplotlib 的 CJK font fallback，避免中文 glyph 丢失。"""
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    selected_font = next(
        (font_name for font_name in CJK_FONT_CANDIDATES if font_name in installed_fonts),
        "DejaVu Sans",
    )

    existing_fonts = list(plt.rcParams.get("font.sans-serif", []))
    merged_fonts: list[str] = []
    for font_name in [selected_font, *CJK_FONT_CANDIDATES, *existing_fonts, "DejaVu Sans"]:
        if font_name not in merged_fonts:
            merged_fonts.append(font_name)

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = merged_fonts
    plt.rcParams["axes.unicode_minus"] = False
    return selected_font


def annotate_summary(summary: pd.DataFrame) -> pd.DataFrame:
    annotated = summary.copy()
    if annotated.empty:
        return annotated
    annotated["scenario"] = annotated.apply(
        lambda row: format_scenario(row["view"], row["objective"]),
        axis=1,
    )
    annotated["pair_interval"] = annotated["pair"] + " " + annotated["interval"]
    return annotated


def build_pair_comparison_table(
    summary: pd.DataFrame,
    *,
    pair: str | None = None,
    metrics: Iterable[str] | None = None,
) -> pd.DataFrame:
    annotated = annotate_summary(summary)
    if pair:
        annotated = annotated[annotated["pair"] == pair].copy()

    default_metrics = [
        "score",
        "width_pct",
        "center_offset_pct",
        "mean_fee_proxy_bps",
        "mean_in_range_pct",
        "no_exit_rate",
        "median_lp_vs_hodl_pct",
        "p10_lp_vs_hodl_pct",
        "downside_breach_rate",
        "mean_max_drawdown_pct",
    ]
    selected_metrics = list(metrics) if metrics else default_metrics
    base_columns = ["pair", "interval", "scenario", "regime_label"]
    table = annotated[base_columns + selected_metrics].copy()
    table = table.sort_values(["pair", "interval", "scenario"]).reset_index(drop=True)
    return rename_for_display(table)


def _metric_pivot(summary: pd.DataFrame, metric: str) -> pd.DataFrame:
    annotated = annotate_summary(summary)
    if annotated.empty:
        return pd.DataFrame()
    pivot = annotated.pivot(index="pair_interval", columns="scenario", values=metric)
    return pivot.sort_index()


def plot_summary_metric_bars(
    summary: pd.DataFrame,
    metric: str,
    *,
    figsize: tuple[float, float] = (10.0, 4.5),
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    pivot = _metric_pivot(summary, metric)
    if pivot.empty:
        raise ValueError("summary 为空，没有可绘制的数据")

    _configure_cjk_font()
    fig, ax = plt.subplots(figsize=figsize)
    pivot.plot(kind="bar", ax=ax)
    metric_label = format_metric(metric)
    ax.set_title(title or f"{metric_label}在不同交易对与场景下的对比")
    ax.set_xlabel("")
    ax.set_ylabel(metric_label)
    ax.legend(title="场景", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig, ax


def plot_summary_metric_heatmap(
    summary: pd.DataFrame,
    metric: str,
    *,
    figsize: tuple[float, float] = (8.0, 4.0),
    title: str | None = None,
    cmap: str = "viridis",
) -> tuple[plt.Figure, plt.Axes]:
    pivot = _metric_pivot(summary, metric)
    if pivot.empty:
        raise ValueError("summary 为空，没有可绘制的数据")

    _configure_cjk_font()
    fig, ax = plt.subplots(figsize=figsize)
    matrix = pivot.to_numpy(dtype=float)
    image = ax.imshow(matrix, aspect="auto", cmap=cmap)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    metric_label = format_metric(metric)
    ax.set_title(title or f"{metric_label}热力图")

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            ax.text(col, row, f"{value:.1f}", ha="center", va="center", color="white")

    fig.colorbar(image, ax=ax, shrink=0.85, label=metric_label)
    fig.tight_layout()
    return fig, ax


def plot_study_candidate_frontier(
    rankings: pd.DataFrame,
    *,
    x: str = "mean_in_range_pct",
    y: str = "mean_fee_proxy_bps",
    color: str = "score",
    label_top_n: int = 5,
    figsize: tuple[float, float] = (8.0, 5.0),
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    if rankings.empty:
        raise ValueError("rankings 为空，没有可绘制的数据")

    _configure_cjk_font()
    fig, ax = plt.subplots(figsize=figsize)
    scatter = ax.scatter(
        rankings[x],
        rankings[y],
        c=rankings[color],
        s=60 + rankings["width_pct"].fillna(0) * 4,
        cmap="plasma",
        alpha=0.85,
        edgecolors="black",
        linewidths=0.4,
    )
    ax.set_xlabel(format_metric(x))
    ax.set_ylabel(format_metric(y))
    ax.set_title(title or f"{format_metric(y)} 与 {format_metric(x)} 的关系")
    ax.grid(alpha=0.25)

    top_rows = rankings.head(label_top_n)
    for _, row in top_rows.iterrows():
        label = f"宽={row['width_pct']:.1f}%，偏移={row['center_offset_pct']:.1f}%"
        ax.annotate(label, (row[x], row[y]), xytext=(6, 6), textcoords="offset points")

    fig.colorbar(scatter, ax=ax, shrink=0.85, label=format_metric(color))
    fig.tight_layout()
    return fig, ax


def plot_coverage_frontier(
    frontier: pd.DataFrame,
    *,
    figsize: tuple[float, float] = (8.0, 4.8),
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    if frontier.empty:
        raise ValueError("frontier 为空，没有可绘制的数据")

    _configure_cjk_font()
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(
        frontier["coverage_target_pct"],
        frontier["width_pct"],
        marker="o",
        linewidth=2,
    )
    ax.set_xlabel(format_metric("coverage_target_pct"))
    ax.set_ylabel(format_metric("width_pct"))
    ax.set_title(title or "Coverage frontier / 覆盖率前沿")
    ax.grid(alpha=0.25)

    for _, row in frontier.iterrows():
        ax.annotate(
            f"{row['width_pct']:.1f}%",
            (row["coverage_target_pct"], row["width_pct"]),
            xytext=(6, 6),
            textcoords="offset points",
        )

    fig.tight_layout()
    return fig, ax


def plot_coverage_period_frontiers(
    frontier_grid: pd.DataFrame,
    *,
    figsize: tuple[float, float] = (9.0, 5.2),
    title: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    if frontier_grid.empty:
        raise ValueError("frontier_grid 为空，没有可绘制的数据")

    _configure_cjk_font()
    fig, ax = plt.subplots(figsize=figsize)
    ordered = frontier_grid.sort_values(["holding_days", "coverage_target_pct"])
    for holding_days, frame in ordered.groupby("holding_days", sort=True):
        ax.plot(
            frame["coverage_target_pct"],
            frame["width_pct"],
            marker="o",
            linewidth=1.8,
            label=f"{holding_days}d",
        )
        recommendations = frame[frame["recommendation_eligible"]].copy()
        if not recommendations.empty:
            recommendation = recommendations.sort_values(
                ["ideal_distance", "width_pct", "out_of_range_pct", "coverage_target_pct"],
                ascending=[True, True, True, False],
            ).iloc[0]
            ax.scatter(
                [recommendation["coverage_target_pct"]],
                [recommendation["width_pct"]],
                s=90,
                edgecolors="black",
                linewidths=0.8,
            )

    ax.set_xlabel(format_metric("coverage_target_pct"))
    ax.set_ylabel(format_metric("width_pct"))
    ax.set_title(title or "Coverage x range width frontiers / 覆盖率与区间宽度前沿")
    ax.grid(alpha=0.25)
    ax.legend(title="holding period")
    fig.tight_layout()
    return fig, ax


def plot_coverage_period_heatmap(
    frontier_grid: pd.DataFrame,
    metric: str = "width_pct",
    *,
    figsize: tuple[float, float] = (9.0, 4.8),
    title: str | None = None,
    cmap: str = "viridis",
) -> tuple[plt.Figure, plt.Axes]:
    if frontier_grid.empty:
        raise ValueError("frontier_grid 为空，没有可绘制的数据")

    _configure_cjk_font()
    pivot = (
        frontier_grid.assign(period_label=frontier_grid["holding_days"].astype(str) + "d")
        .pivot(index="period_label", columns="coverage_target_pct", values=metric)
        .sort_index(key=lambda idx: idx.str.replace("d", "", regex=False).astype(int))
    )

    fig, ax = plt.subplots(figsize=figsize)
    matrix = pivot.to_numpy(dtype=float)
    image = ax.imshow(matrix, aspect="auto", cmap=cmap)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([f"{value:.0f}%" for value in pivot.columns], rotation=0)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    metric_label = format_metric(metric)
    ax.set_title(title or f"{metric_label} 在 period x coverage 上的交叉研究")

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            ax.text(col, row, f"{value:.1f}", ha="center", va="center", color="white")

    ax.set_xlabel(format_metric("coverage_target_pct"))
    ax.set_ylabel("holding period / 持有期")
    fig.colorbar(image, ax=ax, shrink=0.85, label=metric_label)
    fig.tight_layout()
    return fig, ax
