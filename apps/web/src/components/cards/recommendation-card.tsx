"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MetricBadge } from "./metric-badge";
import { cn } from "@/lib/utils";
import type { CandidateResult } from "@/lib/types";

interface RecommendationCardProps {
  candidate: CandidateResult;
  rank: number;
  selected: boolean;
  onClick: () => void;
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

export function RecommendationCard({
  candidate,
  rank,
  selected,
  onClick,
}: RecommendationCardProps) {
  const { pa, pb, tick_lower, tick_upper, metrics, score, insight, strategy } =
    candidate;

  return (
    <Card
      className={cn(
        "cursor-pointer transition-shadow hover:shadow-md",
        selected && "ring-2 ring-primary",
      )}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center gap-2 pb-2">
        <Badge className="h-6 w-6 items-center justify-center rounded-full p-0">
          {rank}
        </Badge>
        <div className="flex-1">
          <div className="font-mono text-sm">
            ${pa.toFixed(4)} — ${pb.toFixed(4)}
          </div>
          <div className="text-muted-foreground text-xs">
            Ticks {tick_lower} → {tick_upper} | {strategy} | Score{" "}
            <span className="font-semibold">{score.toFixed(1)}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <div className="grid grid-cols-3 gap-2">
          <MetricBadge
            label="In Range"
            value={`${metrics.in_range_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.in_range_pct, 80, 50)}
          />
          <MetricBadge
            label="LP vs HODL"
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.lp_vs_hodl_pct, 0, -5)}
          />
          <MetricBadge
            label="Max IL"
            value={`${metrics.max_il_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.max_il_pct, 5, 15, true)}
          />
          <MetricBadge
            label="Max DD"
            value={`${metrics.max_drawdown_pct.toFixed(1)}%`}
            variant={metricVariant(metrics.max_drawdown_pct, 10, 25, true)}
          />
          <MetricBadge
            label="Cap Eff"
            value={`${metrics.capital_efficiency.toFixed(1)}x`}
          />
          <MetricBadge
            label="Touches"
            value={String(metrics.boundary_touches)}
            variant={metricVariant(metrics.boundary_touches, 5, 15, true)}
          />
        </div>
        <p className="text-muted-foreground text-xs leading-relaxed">{insight}</p>
      </CardContent>
    </Card>
  );
}
