"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { InfoTip } from "@/components/ui/info-tip";
import type { VolatilityInfo } from "@/lib/types";

interface VolatilitySummaryProps {
  volatility: VolatilityInfo;
  horizonDays: number;
}

function regimeColor(regime: string) {
  switch (regime) {
    case "low":
      return "border-emerald-500/50 text-emerald-400";
    case "high":
      return "border-red-500/50 text-red-400";
    default:
      return "border-blue-500/50 text-blue-400";
  }
}

export function VolatilitySummary({ volatility, horizonDays }: VolatilitySummaryProps) {
  const t = useTranslations("cards");
  const tt = useTranslations("tooltips");

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-white/10 bg-muted/30 px-3 py-2">
      <div className="flex items-center gap-1.5">
        <span className="text-muted-foreground text-xs">{t("volAnnual")}</span>
        <span className="font-mono text-sm font-semibold">
          {(volatility.sigma_annual * 100).toFixed(1)}%
        </span>
        <InfoTip content={tt("volAnnual")} />
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-muted-foreground text-xs">{t("volHorizon")}</span>
        <span className="font-mono text-sm font-semibold">
          {(volatility.sigma_T * 100).toFixed(1)}%
        </span>
        <InfoTip content={tt("volHorizon")} />
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-muted-foreground text-xs">{t("regime")}</span>
        <Badge variant="outline" className={regimeColor(volatility.regime)}>
          {t(`regime_${volatility.regime}`)}
        </Badge>
      </div>
      <div className="flex items-center gap-1.5 ml-auto">
        <span className="text-muted-foreground text-xs">{t("horizonLabel")}</span>
        <span className="font-mono text-sm">{horizonDays}D</span>
      </div>
    </div>
  );
}
