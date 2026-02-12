"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MetricBadge } from "./metric-badge";
import { PriceRangeMeta } from "./price-range-meta";
import { cn } from "@/lib/utils";
import type { CandidateResult } from "@/lib/types";

interface BalancedCardProps {
  candidate: CandidateResult;
  selected: boolean;
  currentPrice: number;
  onClick: () => void;
  quoteSymbol?: string;
  quoteIsStable?: boolean;
  onDoubleClick?: () => void;
}

function metricVariant(value: number, goodThreshold: number, badThreshold: number, inverted = false) {
  if (inverted) {
    if (value <= goodThreshold) return "good" as const;
    if (value >= badThreshold) return "bad" as const;
  } else {
    if (value >= goodThreshold) return "good" as const;
    if (value <= badThreshold) return "bad" as const;
  }
  return "neutral" as const;
}

export function BalancedCard({
  candidate,
  selected,
  currentPrice,
  onClick,
  quoteSymbol,
  quoteIsStable,
  onDoubleClick,
}: BalancedCardProps) {
  const tc = useTranslations("cards");
  const tm = useTranslations("metrics");
  const tt = useTranslations("tooltips");
  const { pa, pb, metrics, k_sigma, estimated_prob } = candidate;
  const rangeLabel = quoteIsStable
    ? `$${pa.toFixed(4)} — $${pb.toFixed(4)}`
    : `${pa.toFixed(4)} — ${pb.toFixed(4)}${quoteSymbol ? ` ${quoteSymbol}` : ""}`;

  return (
    <Card
      className={cn(
        "cursor-pointer border-emerald-500/30 bg-emerald-950/10 transition-all hover:shadow-lg hover:shadow-emerald-500/5",
        selected && "ring-2 ring-emerald-500 shadow-lg shadow-emerald-500/10",
      )}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <Badge className="h-6 items-center justify-center rounded-full bg-emerald-600 px-2 text-white text-xs">
          {tc("balancedTitle")}
        </Badge>
        <div className="flex-1">
          <div className="font-mono text-sm">{rangeLabel}</div>
          <div className="text-muted-foreground text-xs">
            {k_sigma.toFixed(1)}σ · {tc("width")} {candidate.width_pct.toFixed(1)}%
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-950/20 px-3 py-2">
          <span className="text-muted-foreground text-xs">{tc("stayProbability")}</span>
          <span className="ml-auto font-mono text-lg font-bold text-emerald-400">
            {(estimated_prob * 100).toFixed(0)}%
          </span>
        </div>
        <PriceRangeMeta
          currentPrice={currentPrice}
          minPrice={pa}
          maxPrice={pb}
          quoteSymbol={quoteSymbol}
          quoteIsStable={quoteIsStable}
        />
        <div className="grid grid-cols-3 gap-2">
          <MetricBadge
            label={tm("estProb")}
            value={`${(estimated_prob * 100).toFixed(0)}%`}
            variant={metricVariant(estimated_prob * 100, 70, 40)}
            tooltip={tt("metricEstProb")}
          />
          <MetricBadge
            label={tm("inRange")}
            value={`${metrics.in_range_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.in_range_pct, 80, 50)}
            tooltip={tt("metricInRange")}
          />
          <MetricBadge
            label={tm("capEff")}
            value={`${metrics.capital_efficiency.toFixed(1)}x`}
            tooltip={tt("metricCapEff")}
          />
          <MetricBadge
            label={tm("maxIl")}
            value={`${metrics.max_il_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.max_il_pct, 5, 15, true)}
            tooltip={tt("metricMaxIl")}
          />
          <MetricBadge
            label={tm("lpVsHodl")}
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.lp_vs_hodl_pct, 0, -5)}
            tooltip={tt("metricLpVsHodl")}
          />
          <MetricBadge
            label={tm("touches")}
            value={String(metrics.touch_count)}
            variant={metricVariant(metrics.touch_count, 5, 15, true)}
            tooltip={tt("metricTouches")}
          />
        </div>
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-muted-foreground text-xs leading-relaxed cursor-help border-b border-dashed border-muted-foreground/30">
                {candidate.insight}
              </p>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-sm whitespace-pre-line text-left">
              {candidate.insight}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
