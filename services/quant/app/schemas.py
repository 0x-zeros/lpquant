from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    klines: list[list[float]]  # [[open_time, open, high, low, close, volume], ...]
    current_price: float
    tick_spacing: int
    fee_rate: float  # e.g. 0.0025
    capital_usd: float
    horizon_days: float = 7.0


class BacktestMetrics(BaseModel):
    in_range_pct: float
    touch_count: int
    mean_time_to_exit_hours: float
    lp_vs_hodl_pct: float
    max_il_pct: float
    max_drawdown_pct: float
    capital_efficiency: float


class VolatilityInfo(BaseModel):
    sigma_annual: float
    sigma_realized: float
    sigma_atr: float
    sigma_ewma: float
    regime: str  # "low" | "normal" | "high"
    regime_multiplier: float
    sigma_T: float


class CandidateResult(BaseModel):
    range_type: str  # "balanced" | "narrow" | "backtest"
    label: str
    pa: float  # lower price
    pb: float  # upper price
    tick_lower: int
    tick_upper: int
    width_pct: float
    k_sigma: float
    estimated_prob: float
    metrics: BacktestMetrics
    score: float
    insight: str
    insight_data: dict | None = None


class ChartMarker(BaseModel):
    time: int  # epoch-ms
    position: str  # "aboveBar" | "belowBar" | "inBar"
    color: str | None = None
    shape: str  # "circle" | "square" | "arrowUp" | "arrowDown"
    text: str


class ChartSeries(BaseModel):
    timestamps: list[int]
    lp_values: list[float]
    hodl_values: list[float]
    il_pct: list[float]
    prices: list[float]
    markers: list[ChartMarker] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    balanced: CandidateResult
    narrow: CandidateResult
    best_backtest: CandidateResult
    volatility: VolatilityInfo
    horizon_days: float
    series: dict[str, ChartSeries]  # keyed by "balanced", "narrow", "best_backtest"
    current_price: float
    pool_fee_rate: float
