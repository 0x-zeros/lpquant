export interface Kline {
  openTime: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PoolConfig {
  poolId: string;
  tickSpacing: number;
  currentPrice: number;
  feeRate: number;
  coinTypeA: string;
  coinTypeB: string;
}

export interface RecommendRequest {
  pair: string;
  days: number;
  interval: string;
  profile: "conservative" | "balanced" | "aggressive";
  capital: number;
  strategies: string[];
}

export interface BacktestMetrics {
  in_range_pct: number;
  touch_count: number;
  mean_time_to_exit_hours: number;
  lp_vs_hodl_pct: number;
  max_il_pct: number;
  max_drawdown_pct: number;
  capital_efficiency: number;
}

export interface CandidateResult {
  strategy: string;
  pa: number;
  pb: number;
  tick_lower: number;
  tick_upper: number;
  width_pct: number;
  requested_width_pct?: number | null;
  metrics: BacktestMetrics;
  score: number;
  insight: string;
}

export interface ChartMarker {
  time: number;
  position: "aboveBar" | "belowBar" | "inBar";
  color?: string;
  shape: "circle" | "square" | "arrowUp" | "arrowDown";
  text: string;
}

export interface ChartSeries {
  timestamps: number[];
  lp_values: number[];
  hodl_values: number[];
  il_pct: number[];
  prices: number[];
  markers: ChartMarker[];
}

export interface RecommendResponse {
  top3: CandidateResult[];
  extreme_2pct: CandidateResult;
  extreme_5pct: CandidateResult;
  series: Record<string, ChartSeries>;
  current_price: number;
  pool_fee_rate: number;
}
