from __future__ import annotations

from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def annotate_summary(summary: pd.DataFrame) -> pd.DataFrame:
    annotated = summary.copy()
    if annotated.empty:
        return annotated
    annotated["scenario"] = annotated["view"] + "/" + annotated["objective"]
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
    return table.sort_values(["pair", "interval", "scenario"]).reset_index(drop=True)


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
        raise ValueError("summary is empty; nothing to plot")

    fig, ax = plt.subplots(figsize=figsize)
    pivot.plot(kind="bar", ax=ax)
    ax.set_title(title or f"{metric} by pair and scenario")
    ax.set_xlabel("")
    ax.set_ylabel(metric)
    ax.legend(title="scenario", bbox_to_anchor=(1.02, 1), loc="upper left")
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
        raise ValueError("summary is empty; nothing to plot")

    fig, ax = plt.subplots(figsize=figsize)
    matrix = pivot.to_numpy(dtype=float)
    image = ax.imshow(matrix, aspect="auto", cmap=cmap)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title(title or f"{metric} heatmap")

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            ax.text(col, row, f"{value:.1f}", ha="center", va="center", color="white")

    fig.colorbar(image, ax=ax, shrink=0.85, label=metric)
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
        raise ValueError("rankings is empty; nothing to plot")

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
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(title or f"{y} vs {x}")
    ax.grid(alpha=0.25)

    top_rows = rankings.head(label_top_n)
    for _, row in top_rows.iterrows():
        label = f"w={row['width_pct']:.1f}%, c={row['center_offset_pct']:.1f}%"
        ax.annotate(label, (row[x], row[y]), xytext=(6, 6), textcoords="offset points")

    fig.colorbar(scatter, ax=ax, shrink=0.85, label=color)
    fig.tight_layout()
    return fig, ax
