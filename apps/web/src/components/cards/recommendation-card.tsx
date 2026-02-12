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
import { InfoTip } from "@/components/ui/info-tip";
import { buildInsight, buildDetailedInsight } from "@/lib/build-insight";
import { cn } from "@/lib/utils";
import type { CandidateResult } from "@/lib/types";

interface RecommendationCardProps {
  candidate: CandidateResult;
  rank: number;
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

function formatDuration(hours: number) {
  if (!Number.isFinite(hours) || hours <= 0) return "n/a";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

export function RecommendationCard({
  candidate,
  rank,
  selected,
  currentPrice,
  onClick,
  quoteSymbol,
  quoteIsStable,
  onDoubleClick,
}: RecommendationCardProps) {
  const tc = useTranslations("cards");
  const tm = useTranslations("metrics");
  const tt = useTranslations("tooltips");
  const { pa, pb, tick_lower, tick_upper, metrics, score, strategy } = candidate;
  const rangeLabel = quoteIsStable
    ? `$${pa.toFixed(4)} — $${pb.toFixed(4)}`
    : `${pa.toFixed(4)} — ${pb.toFixed(4)}${quoteSymbol ? ` ${quoteSymbol}` : ""}`;

  const localInsight = buildInsight(candidate, tt);
  const detailedInsight = buildDetailedInsight(candidate, tt);

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-lg hover:shadow-[#00d2ff]/5",
        selected && "ring-2 ring-[#00d2ff] shadow-lg shadow-[#00d2ff]/10",
      )}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <Badge className="h-6 w-6 items-center justify-center rounded-full bg-[#00d2ff] p-0 text-[#0d0e21]">
          {rank}
        </Badge>
        <div className="flex-1">
          <div className="font-mono text-sm">
            {rangeLabel}
          </div>
          <div className="text-muted-foreground text-xs">
            {tc("ticks")} {tick_lower} → {tick_upper} |{" "}
            <TooltipProvider delayDuration={200}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-help">{strategy}</span>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  {tt("strategy")}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            {" "}| {tc("score")}{" "}
            <span className="font-semibold">{score.toFixed(1)}</span>
            <span className="ml-0.5"><InfoTip content={tt("score")} side="right" /></span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <PriceRangeMeta
          currentPrice={currentPrice}
          minPrice={pa}
          maxPrice={pb}
          quoteSymbol={quoteSymbol}
          quoteIsStable={quoteIsStable}
        />
        <div className="grid grid-cols-3 gap-2">
          <MetricBadge
            label={tm("inRange")}
            value={`${metrics.in_range_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.in_range_pct, 80, 50)}
            tooltip={tt("metricInRange")}
          />
          <MetricBadge
            label={tm("touches")}
            value={String(metrics.touch_count)}
            variant={metricVariant(metrics.touch_count, 5, 15, true)}
            tooltip={tt("metricTouches")}
          />
          <MetricBadge
            label={tm("meanExit")}
            value={formatDuration(metrics.mean_time_to_exit_hours)}
            tooltip={tt("metricMeanExit")}
          />
          <MetricBadge
            label={tm("lpVsHodl")}
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.lp_vs_hodl_pct, 0, -5)}
            tooltip={tt("metricLpVsHodl")}
          />
          <MetricBadge
            label={tm("maxIl")}
            value={`${metrics.max_il_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.max_il_pct, 5, 15, true)}
            tooltip={tt("metricMaxIl")}
          />
          <MetricBadge
            label={tm("maxDd")}
            value={`${metrics.max_drawdown_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.max_drawdown_pct, 10, 25, true)}
            tooltip={tt("metricMaxDd")}
          />
        </div>
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>
              <p className="text-muted-foreground text-xs leading-relaxed cursor-help border-b border-dashed border-muted-foreground/30">
                {localInsight}
              </p>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-sm whitespace-pre-line text-left">
              {detailedInsight}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
