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
  decimalsA: number;
  decimalsB: number;
  priceFromPool: number;
}

export interface RecommendRequest {
  pool_id: string;
  days: number;
  interval: string;
  capital: number;
  horizon_days: number;
}

export interface PoolSummary {
  pool_id: string;
  symbol: string;
  fee_rate: number;
  volume_24h?: number | null;
  fees_24h?: number | null;
  apr?: number | null;
  tvl?: number | null;
  coin_type_a: string;
  coin_type_b: string;
  decimals_a: number;
  decimals_b: number;
  binance_symbol?: string | null;
  logo_url_a?: string | null;
  logo_url_b?: string | null;
}

export interface PoolsResponse {
  pools: PoolSummary[];
  updated_at: number;
  sort_by: string;
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

export interface VolatilityInfo {
  sigma_annual: number;
  sigma_realized: number;
  sigma_atr: number;
  sigma_ewma: number;
  regime: "low" | "normal" | "high";
  regime_multiplier: number;
  sigma_T: number;
}

export interface InsightData {
  range_type: string;
  k_sigma: number;
  estimated_prob: number;
  width_pct: number;
  backtest_in_range_pct: number;
  lp_vs_hodl_pct: number;
  lp_outperforms: boolean;
  max_il_pct: number;
  il_warning: boolean;
  capital_efficiency: number;
}

export interface CandidateResult {
  range_type: "balanced" | "narrow" | "backtest";
  label: string;
  pa: number;
  pb: number;
  tick_lower: number;
  tick_upper: number;
  width_pct: number;
  k_sigma: number;
  estimated_prob: number;
  metrics: BacktestMetrics;
  score: number;
  insight: string;
  insight_data?: InsightData | null;
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
  balanced: CandidateResult;
  narrow: CandidateResult;
  best_backtest: CandidateResult;
  volatility: VolatilityInfo;
  horizon_days: number;
  series: Record<string, ChartSeries>;
  current_price: number;
  pool_fee_rate: number;
  kline_source?: "birdeye" | "binance";
  base_symbol?: string;
  quote_symbol?: string;
  base_side?: "A" | "B";
  quote_side?: "A" | "B";
  quote_is_stable?: boolean;
  pool_symbol?: string;
  coin_symbol_a?: string;
  coin_symbol_b?: string;
}
