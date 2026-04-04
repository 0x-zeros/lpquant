from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

MarketView = Literal["neutral", "bullish", "bearish"]
ObjectiveName = Literal["balanced", "carry", "defensive"]
SourceMode = Literal["binance-direct", "binance-ratio", "binance-proxy"]


@dataclass(frozen=True)
class PairSpec:
    base: str
    quote: str

    @property
    def symbol(self) -> str:
        return f"{self.base}/{self.quote}"


@dataclass
class PriceDataset:
    pair: PairSpec
    interval: str
    source: SourceMode
    frame: pd.DataFrame
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateSpec:
    width_pct: float
    center_offset_pct: float

    @property
    def lower_offset_pct(self) -> float:
        return self.center_offset_pct - self.width_pct / 2.0

    @property
    def upper_offset_pct(self) -> float:
        return self.center_offset_pct + self.width_pct / 2.0


@dataclass(frozen=True)
class StudyRequest:
    pair: str
    interval: str = "4h"
    days: int = 365
    lookback_bars: int = 90
    horizon_bars: int = 30
    capital: float = 10_000.0
    fee_rate: float = 0.003
    view: MarketView = "neutral"
    objective: ObjectiveName = "balanced"
    neighbors: int = 120
    top_k: int = 10


@dataclass
class StudyResult:
    request: StudyRequest
    dataset: PriceDataset
    feature_frame: pd.DataFrame
    current_regime: dict[str, float | str]
    similar_windows: pd.DataFrame
    rankings: pd.DataFrame


@dataclass(frozen=True)
class CoverageStudyRequest:
    pair: str
    interval: str = "1d"
    days: int = 730
    holding_days: int = 30
    coverage_target_pct: float = 90.0
    frontier_targets_pct: tuple[float, ...] = (50.0, 60.0, 70.0, 80.0, 85.0, 90.0, 95.0, 97.5)


@dataclass
class CoverageStudyResult:
    request: CoverageStudyRequest
    dataset: PriceDataset
    holding_bars: int
    window_frame: pd.DataFrame
    return_stats: dict[str, float]
    best_interval: dict[str, float | str]
    frontier: pd.DataFrame


@dataclass(frozen=True)
class CoverageSweepRequest:
    pair: str
    interval: str = "1d"
    days: int = 730
    holding_days_list: tuple[int, ...] = (7, 30, 60, 180, 365)
    coverage_targets_pct: tuple[float, ...] = (50.0, 60.0, 70.0, 80.0, 85.0, 90.0, 95.0, 97.5)
    minimum_recommendation_coverage_pct: float = 80.0


@dataclass
class CoverageSweepResult:
    request: CoverageSweepRequest
    dataset: PriceDataset
    frontier_grid: pd.DataFrame
    period_recommendations: pd.DataFrame
    global_recommendation: dict[str, float | str | bool]


@dataclass(frozen=True)
class AssetDiagnosticsRequest:
    asset: str
    quote: str = "USDC"
    interval: str = "1d"
    days: int = 730
    horizon_days: tuple[int, ...] = (7, 30, 90, 180)
    autocorr_lags: tuple[int, ...] = (1, 2, 3, 5, 10, 20)


@dataclass
class AssetDiagnosticsResult:
    request: AssetDiagnosticsRequest
    dataset: PriceDataset
    window_config: pd.DataFrame
    feature_frame: pd.DataFrame
    regime_summary: dict[str, float | str]
    snapshot: pd.DataFrame
    return_stats: pd.DataFrame
    horizon_returns: pd.DataFrame
    autocorrelation: pd.DataFrame
