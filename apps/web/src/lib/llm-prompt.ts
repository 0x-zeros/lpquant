import type { CandidateResult, RecommendRequest, RecommendResponse } from "@/lib/types";

type Locale = "en" | "zh" | string;

type PromptInput = {
  data: RecommendResponse;
  selectedKey: string;
  request: RecommendRequest | null;
  locale?: Locale;
};

function formatCandidate(candidate: CandidateResult) {
  return {
    range_type: candidate.range_type,
    label: candidate.label,
    pa: candidate.pa,
    pb: candidate.pb,
    tick_lower: candidate.tick_lower,
    tick_upper: candidate.tick_upper,
    width_pct: candidate.width_pct,
    k_sigma: candidate.k_sigma,
    estimated_prob: candidate.estimated_prob,
    score: candidate.score,
    metrics: {
      in_range_pct: candidate.metrics.in_range_pct,
      touch_count: candidate.metrics.touch_count,
      mean_time_to_exit_hours: candidate.metrics.mean_time_to_exit_hours,
      lp_vs_hodl_pct: candidate.metrics.lp_vs_hodl_pct,
      max_il_pct: candidate.metrics.max_il_pct,
      max_drawdown_pct: candidate.metrics.max_drawdown_pct,
      capital_efficiency: candidate.metrics.capital_efficiency,
    },
  };
}

function getSelectedCandidate(data: RecommendResponse, selectedKey: string): CandidateResult | null {
  if (selectedKey === "balanced") return data.balanced;
  if (selectedKey === "narrow") return data.narrow;
  if (selectedKey === "best_backtest") return data.best_backtest;
  return null;
}

export function buildLlmPrompt({ data, selectedKey, request, locale }: PromptInput) {
  const isZh = locale === "zh";
  const language = isZh ? "简体中文" : "English";
  const selected = getSelectedCandidate(data, selectedKey);

  const payload = {
    context: {
      pool_id: request?.pool_id ?? "",
      days: request?.days ?? null,
      interval: request?.interval ?? null,
      horizon_days: request?.horizon_days ?? null,
      capital_usd: request?.capital ?? null,
      current_price: data.current_price,
      pool_fee_rate: data.pool_fee_rate,
      kline_source: data.kline_source ?? "unknown",
    },
    volatility: data.volatility,
    candidates: {
      balanced: formatCandidate(data.balanced),
      narrow: formatCandidate(data.narrow),
      best_backtest: formatCandidate(data.best_backtest),
    },
    selected_key: selectedKey,
    selected_candidate: selected ? formatCandidate(selected) : null,
  };

  const header = isZh
    ? [
        `你是 Sui 上 Cetus CLMM 的专业做市/LP 策略顾问。`,
        `系统基于波动率预测生成了 3 个推荐区间：Balanced（长期稳定）、Narrow（短期高效）、Best Backtest（历史最优）。`,
        `请基于以下数据，对所选区间给出简洁清晰的建议。`,
        `请用${language}回答，不要编造缺失数据。`,
        ``,
        `输出格式：`,
        `1. 总结（1-2 句）`,
        `2. 波动率分析（当前 regime + σ 对做市的影响）`,
        `3. 推荐区间（Pa/Pb/width/stay probability）及理由`,
        `4. 风险提示 + 调仓建议`,
        `5. 若有更优候选，说明原因`,
        ``,
        `DATA:`,
      ]
    : [
        `You are an expert CLMM liquidity provider strategist for Cetus on Sui.`,
        `The system generated 3 recommendations based on volatility forecasting: Balanced (long-term stable), Narrow (short-term efficient), Best Backtest (historical best).`,
        `Use the data below to give a concise recommendation for the selected range.`,
        `Answer in ${language}. Do not invent missing values.`,
        ``,
        `Output format:`,
        `1. Summary (1-2 sentences)`,
        `2. Volatility analysis (current regime + sigma implications for LP)`,
        `3. Recommended range (Pa/Pb/width/stay probability) and reasoning`,
        `4. Risk notes + rebalancing suggestion`,
        `5. If another candidate is clearly better, say which and why`,
        ``,
        `DATA:`,
      ];

  return [...header, JSON.stringify(payload, null, 2)].join("\n");
}
