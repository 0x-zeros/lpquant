from pydantic import BaseModel


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
    lp_vs_hodl_pct: float
    max_il_pct: float
    max_drawdown_pct: float
    capital_efficiency: float
    boundary_touches: int


class CandidateResult(BaseModel):
    strategy: str
    pa: float  # lower price
    pb: float  # upper price
    tick_lower: int
    tick_upper: int
    width_pct: float
    metrics: BacktestMetrics
    score: float
    insight: str


class ChartSeries(BaseModel):
    timestamps: list[int]
    lp_values: list[float]
    hodl_values: list[float]
    il_pct: list[float]
    prices: list[float]


class RecommendResponse(BaseModel):
    top3: list[CandidateResult]
    extreme_2pct: CandidateResult
    extreme_5pct: CandidateResult
    series: dict[str, ChartSeries]  # keyed by "top1", "top2", "top3", "extreme_2pct", "extreme_5pct"
    current_price: float
    pool_fee_rate: float
