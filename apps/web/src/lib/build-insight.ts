import type { InsightData, CandidateResult } from "@/lib/types";

/**
 * Derive InsightData from candidate metrics when the backend
 * hasn't returned the structured field yet.
 */
function deriveInsightData(candidate: CandidateResult): InsightData {
  const { width_pct, metrics } = candidate;
  const widthClass =
    width_pct < 3 ? "tight" : width_pct < 10 ? "moderate" : "wide";

  return {
    width_class: widthClass,
    width_pct: Math.round(width_pct * 10) / 10,
    in_range_pct: Math.round(metrics.in_range_pct),
    lp_vs_hodl_pct: Math.round(metrics.lp_vs_hodl_pct * 10) / 10,
    lp_outperforms: metrics.lp_vs_hodl_pct > 0,
    lp_underperforms_significant: metrics.lp_vs_hodl_pct < -5,
    max_il_pct: Math.round(metrics.max_il_pct * 10) / 10,
    il_warning: metrics.max_il_pct > 10,
  };
}

/**
 * Build a localized insight string from structured insight_data.
 * If insight_data is absent, derives it from candidate metrics
 * so localisation always works regardless of backend version.
 */
export function buildInsight(
  candidate: CandidateResult,
  t: (key: string, values?: Record<string, string | number>) => string,
): string {
  const data = candidate.insight_data ?? deriveInsightData(candidate);

  const parts: string[] = [];

  // Width characterization
  const widthKey =
    data.width_class === "tight"
      ? "insightTight"
      : data.width_class === "moderate"
        ? "insightModerate"
        : "insightWide";

  parts.push(t(widthKey, { width: data.width_pct, inRange: data.in_range_pct }));

  // LP vs HODL
  if (data.lp_outperforms) {
    parts.push(t("insightLpOutperforms", { pct: data.lp_vs_hodl_pct }));
  } else if (data.lp_underperforms_significant) {
    parts.push(t("insightLpUnderperforms", { pct: Math.abs(data.lp_vs_hodl_pct) }));
  }

  // IL warning
  if (data.il_warning) {
    parts.push(t("insightIlWarning", { pct: data.max_il_pct }));
  }

  return parts.join(" ");
}
