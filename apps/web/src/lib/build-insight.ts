import type { InsightData, CandidateResult } from "@/lib/types";

type T = (key: string, values?: Record<string, string | number>) => string;

function deriveInsightData(candidate: CandidateResult): InsightData {
  const { width_pct, metrics, k_sigma, estimated_prob, range_type } = candidate;

  return {
    range_type,
    k_sigma,
    estimated_prob,
    width_pct: Math.round(width_pct * 10) / 10,
    backtest_in_range_pct: Math.round(metrics.in_range_pct),
    lp_vs_hodl_pct: Math.round(metrics.lp_vs_hodl_pct * 10) / 10,
    lp_outperforms: metrics.lp_vs_hodl_pct > 0,
    max_il_pct: Math.round(metrics.max_il_pct * 10) / 10,
    il_warning: metrics.max_il_pct > 10,
    capital_efficiency: Math.round(metrics.capital_efficiency * 10) / 10,
  };
}

export function buildInsight(candidate: CandidateResult, t: T): string {
  const data = candidate.insight_data ?? deriveInsightData(candidate);

  const parts: string[] = [];

  const prob = Math.round(data.estimated_prob * 100);

  if (data.range_type === "balanced") {
    parts.push(
      t("insightBalanced", {
        k: data.k_sigma.toFixed(1),
        width: data.width_pct,
        prob,
      }),
    );
  } else if (data.range_type === "narrow") {
    parts.push(
      t("insightNarrow", {
        k: data.k_sigma.toFixed(2),
        width: data.width_pct,
        prob,
      }),
    );
  } else {
    parts.push(
      t("insightBacktest", {
        width: data.width_pct,
        inRange: data.backtest_in_range_pct,
      }),
    );
  }

  if (data.lp_outperforms) {
    parts.push(t("insightLpOutperforms", { pct: data.lp_vs_hodl_pct }));
  }

  if (data.il_warning) {
    parts.push(t("insightIlWarning", { pct: data.max_il_pct }));
  }

  return parts.join(" ");
}

export function buildDetailedInsight(candidate: CandidateResult, t: T): string {
  const data = candidate.insight_data ?? deriveInsightData(candidate);
  const { metrics } = candidate;
  const lines: string[] = [];

  // 1. Volatility-based range info
  if (data.range_type !== "backtest") {
    lines.push(
      t("detailSigma", {
        k: data.k_sigma.toFixed(2),
        prob: Math.round(data.estimated_prob * 100),
      }),
    );
  }

  // 2. Width
  lines.push(t("detailWidth", { width: data.width_pct }));

  // 3. Backtest in-range
  const irp = metrics.in_range_pct;
  const inRangeVerdict =
    irp >= 80
      ? t("detailInRangeHigh")
      : irp >= 50
        ? t("detailInRangeMed")
        : t("detailInRangeLow");
  lines.push(t("detailInRange", { pct: irp.toFixed(1), inRangeVerdict }));

  // 4. LP vs HODL
  const lp = metrics.lp_vs_hodl_pct;
  const lpStr = `${lp >= 0 ? "+" : ""}${lp.toFixed(1)}`;
  const lpVerdict =
    lp > 1
      ? t("detailLpBetter")
      : lp >= -1
        ? t("detailLpSimilar")
        : t("detailLpWorse");
  lines.push(t("detailLpVsHodl", { pct: lpStr, lpVerdict }));

  // 5. Max IL
  const il = metrics.max_il_pct;
  const ilVerdict =
    il <= 2
      ? t("detailIlLow")
      : il <= 10
        ? t("detailIlMed")
        : t("detailIlHigh");
  lines.push(t("detailIl", { pct: il.toFixed(1), ilVerdict }));

  // 6. Capital efficiency
  const eff = metrics.capital_efficiency;
  lines.push(t("detailCapEff", { eff: eff.toFixed(1) }));

  return lines.join("\n");
}
