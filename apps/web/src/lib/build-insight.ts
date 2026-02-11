import type { InsightData, CandidateResult } from "@/lib/types";

type T = (key: string, values?: Record<string, string | number>) => string;

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

function formatDuration(hours: number): string {
  if (!Number.isFinite(hours) || hours <= 0) return "n/a";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

/**
 * Build a localized insight string from structured insight_data.
 * If insight_data is absent, derives it from candidate metrics
 * so localisation always works regardless of backend version.
 */
export function buildInsight(candidate: CandidateResult, t: T): string {
  const data = candidate.insight_data ?? deriveInsightData(candidate);

  const parts: string[] = [];

  const widthKey =
    data.width_class === "tight"
      ? "insightTight"
      : data.width_class === "moderate"
        ? "insightModerate"
        : "insightWide";

  parts.push(t(widthKey, { width: data.width_pct, inRange: data.in_range_pct }));

  if (data.lp_outperforms) {
    parts.push(t("insightLpOutperforms", { pct: data.lp_vs_hodl_pct }));
  } else if (data.lp_underperforms_significant) {
    parts.push(t("insightLpUnderperforms", { pct: Math.abs(data.lp_vs_hodl_pct) }));
  }

  if (data.il_warning) {
    parts.push(t("insightIlWarning", { pct: data.max_il_pct }));
  }

  return parts.join(" ");
}

/**
 * Build a detailed multi-line analysis of the candidate range.
 *
 * TODO: Replace with LLM-generated analysis — pass candidate data
 * to an LLM endpoint for richer, more natural explanations.
 */
export function buildDetailedInsight(candidate: CandidateResult, t: T): string {
  const { metrics, width_pct } = candidate;
  const lines: string[] = [];

  // 1. Width
  const widthVerdict =
    width_pct < 3
      ? t("detailWidthTight")
      : width_pct < 10
        ? t("detailWidthModerate")
        : t("detailWidthWide");
  lines.push(t("detailWidth", { width: Math.round(width_pct * 10) / 10, widthVerdict }));

  // 2. In-range
  const irp = metrics.in_range_pct;
  const inRangeVerdict =
    irp >= 80
      ? t("detailInRangeHigh")
      : irp >= 50
        ? t("detailInRangeMed")
        : t("detailInRangeLow");
  lines.push(t("detailInRange", { pct: irp.toFixed(1), inRangeVerdict }));

  // 3. Touches
  const tc = metrics.touch_count;
  const touchVerdict =
    tc <= 3
      ? t("detailTouchesLow")
      : tc <= 10
        ? t("detailTouchesMed")
        : t("detailTouchesHigh");
  lines.push(t("detailTouches", { count: tc, touchVerdict }));

  // 4. Mean exit duration
  const dur = formatDuration(metrics.mean_time_to_exit_hours);
  const exitVerdict =
    metrics.mean_time_to_exit_hours < 24
      ? t("detailMeanExitFast")
      : t("detailMeanExitSlow");
  lines.push(t("detailMeanExit", { duration: dur, exitVerdict }));

  // 5. LP vs HODL
  const lp = metrics.lp_vs_hodl_pct;
  const lpStr = `${lp >= 0 ? "+" : ""}${lp.toFixed(1)}`;
  const lpVerdict =
    lp > 1
      ? t("detailLpBetter")
      : lp >= -1
        ? t("detailLpSimilar")
        : t("detailLpWorse");
  lines.push(t("detailLpVsHodl", { pct: lpStr, lpVerdict }));

  // 6. Max IL
  const il = metrics.max_il_pct;
  const ilVerdict =
    il <= 2
      ? t("detailIlLow")
      : il <= 10
        ? t("detailIlMed")
        : t("detailIlHigh");
  lines.push(t("detailIl", { pct: il.toFixed(1), ilVerdict }));

  // 7. Capital efficiency
  const eff = metrics.capital_efficiency;
  const capVerdict =
    eff >= 50
      ? t("detailCapEffHigh")
      : eff >= 10
        ? t("detailCapEffMed")
        : t("detailCapEffLow");
  lines.push(t("detailCapEff", { eff: eff.toFixed(1), capVerdict }));

  return lines.join("\n");
}
