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
    strategy: candidate.strategy,
    pa: candidate.pa,
    pb: candidate.pb,
    tick_lower: candidate.tick_lower,
    tick_upper: candidate.tick_upper,
    width_pct: candidate.width_pct,
    requested_width_pct: candidate.requested_width_pct ?? null,
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
  if (selectedKey === "top1") return data.top3[0] ?? null;
  if (selectedKey === "top2") return data.top3[1] ?? null;
  if (selectedKey === "top3") return data.top3[2] ?? null;
  if (selectedKey === "extreme_2pct") return data.extreme_2pct;
  if (selectedKey === "extreme_5pct") return data.extreme_5pct;
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
      profile: request?.profile ?? "",
      capital_usd: request?.capital ?? null,
      strategies: request?.strategies ?? [],
      current_price: data.current_price,
      pool_fee_rate: data.pool_fee_rate,
      kline_source: data.kline_source ?? "unknown",
    },
    candidates: {
      top1: data.top3[0] ? formatCandidate(data.top3[0]) : null,
      top2: data.top3[1] ? formatCandidate(data.top3[1]) : null,
      top3: data.top3[2] ? formatCandidate(data.top3[2]) : null,
      extreme_2pct: formatCandidate(data.extreme_2pct),
      extreme_5pct: formatCandidate(data.extreme_5pct),
    },
    selected_key: selectedKey,
    selected_candidate: selected ? formatCandidate(selected) : null,
  };

  const header = isZh
    ? [
        `你是 Sui 上 Cetus CLMM 的专业做市/LP 策略顾问。`,
        `请基于以下数据，对所选区间给出简洁清晰的建议。`,
        `请用${language}回答，不要编造缺失数据。`,
        ``,
        `输出格式：`,
        `1. 总结（1-2 句）`,
        `2. 推荐区间（Pa/Pb/width）及理由`,
        `3. 风险提示 + 调仓建议`,
        `4. 若有明显更优候选，请说明是哪一个及原因`,
        ``,
        `DATA:`,
      ]
    : [
        `You are an expert CLMM liquidity provider strategist for Cetus on Sui.`,
        `Use the data below to give a concise recommendation for the selected range.`,
        `Answer in ${language}. Do not invent missing values.`,
        ``,
        `Output format:`,
        `1. Summary (1-2 sentences)`,
        `2. Recommended range (Pa/Pb/width) and reasoning`,
        `3. Risk notes + rebalancing suggestion`,
        `4. If another candidate is clearly better, say which and why`,
        ``,
        `DATA:`,
      ];

  return [...header, JSON.stringify(payload, null, 2)].join("\n");
}
