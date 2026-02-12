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
import { InfoTip } from "@/components/ui/info-tip";
import { buildInsight, buildDetailedInsight } from "@/lib/build-insight";
import { cn } from "@/lib/utils";
import { PriceRangeMeta } from "./price-range-meta";
import type { CandidateResult } from "@/lib/types";

interface ExtremeCardProps {
  candidate: CandidateResult;
  label: string;
  selected: boolean;
  currentPrice: number;
  onClick: () => void;
  quoteSymbol?: string;
  quoteIsStable?: boolean;
}

function formatDuration(hours: number) {
  if (!Number.isFinite(hours) || hours <= 0) return "n/a";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

function WarningBadge({ label, tooltip }: { label: string; tooltip: string }) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span>
            <Badge variant="destructive" className="cursor-help">{label}</Badge>
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ExtremeCard({
  candidate,
  label,
  selected,
  currentPrice,
  onClick,
  quoteSymbol,
  quoteIsStable,
}: ExtremeCardProps) {
  const tc = useTranslations("cards");
  const tm = useTranslations("metrics");
  const tt = useTranslations("tooltips");
  const { pa, pb, metrics, width_pct, requested_width_pct } = candidate;
  const rangeLabel = quoteIsStable
    ? `$${pa.toFixed(4)} — $${pb.toFixed(4)}`
    : `${pa.toFixed(4)} — ${pb.toFixed(4)}${quoteSymbol ? ` ${quoteSymbol}` : ""}`;
  const requestedWidth = requested_width_pct ?? width_pct;
  const expectedTouch = formatDuration(metrics.mean_time_to_exit_hours);

  const localInsight = buildInsight(candidate, tt);
  const detailedInsight = buildDetailedInsight(candidate, tt);

  return (
    <Card
      className={cn(
        "cursor-pointer border-amber-500/30 bg-amber-950/20 transition-shadow hover:shadow-md hover:shadow-amber-500/10",
        selected && "ring-2 ring-amber-500",
      )}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <Badge variant="outline" className="border-amber-500 text-amber-600">
          {label}
        </Badge>
        <div className="flex-1">
          <div className="font-mono text-sm">
            {rangeLabel}
          </div>
          <div className="text-muted-foreground text-xs">
            {tc("requested")} {requestedWidth.toFixed(1)}%
            <span className="ml-0.5"><InfoTip content={tt("requestedWidth")} side="right" /></span>
            {" "}· {tc("realized")} {width_pct.toFixed(1)}%
            <span className="ml-0.5"><InfoTip content={tt("realizedWidth")} side="right" /></span>
          </div>
          <div className="text-muted-foreground text-xs">
            {tc("expectedTouch")} {expectedTouch}
            <span className="ml-0.5"><InfoTip content={tt("expectedTouch")} side="right" /></span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
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
            tooltip={tt("metricInRange")}
          />
          <MetricBadge
            label={tm("lpVsHodl")}
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
            tooltip={tt("metricLpVsHodl")}
          />
          <MetricBadge
            label={tm("maxIl")}
            value={`${metrics.max_il_pct.toFixed(1)}%`}
            tooltip={tt("metricMaxIl")}
          />
        </div>
        <div className="flex flex-wrap gap-1">
          <WarningBadge label={tc("highTouch")} tooltip={tt("highTouch")} />
          <WarningBadge label={tc("ultraNarrow")} tooltip={tt("ultraNarrow")} />
          <WarningBadge label={tc("activeMgmt")} tooltip={tt("activeMgmt")} />
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
