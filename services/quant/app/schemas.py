from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    klines: list[list[float]]  # [[open_time, open, high, low, close, volume], ...]
    current_price: float
    tick_spacing: int
    fee_rate: float  # e.g. 0.0025
    profile: str  # "conservative" | "balanced" | "aggressive"
    capital_usd: float
    strategies: list[str]  # subset of ["quantile", "volband", "swing"]


class BacktestMetrics(BaseModel):
    in_range_pct: float
    touch_count: int
    mean_time_to_exit_hours: float
    lp_vs_hodl_pct: float
    max_il_pct: float
    max_drawdown_pct: float
    capital_efficiency: float


class CandidateResult(BaseModel):
    strategy: str
    pa: float  # lower price
    pb: float  # upper price
    tick_lower: int
    tick_upper: int
    width_pct: float
    requested_width_pct: float | None = None
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
    top3: list[CandidateResult]
    extreme_2pct: CandidateResult
    extreme_5pct: CandidateResult
    series: dict[str, ChartSeries]  # keyed by "top1", "top2", "top3", "extreme_2pct", "extreme_5pct"
    current_price: float
    pool_fee_rate: float
