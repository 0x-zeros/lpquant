import type { InsightData } from "@/lib/types";

/**
 * Build a localized insight string from structured insight_data.
 * Falls back to the raw English `insight` when insight_data is absent.
 */
export function buildInsight(
  data: InsightData | null | undefined,
  fallback: string,
  t: (key: string, values?: Record<string, string | number>) => string,
): string {
  if (!data) return fallback;

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
