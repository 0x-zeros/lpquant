"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MetricBadge } from "./metric-badge";
import { cn } from "@/lib/utils";
import type { CandidateResult } from "@/lib/types";

interface ExtremeCardProps {
  candidate: CandidateResult;
  label: string;
  selected: boolean;
  onClick: () => void;
}

export function ExtremeCard({
  candidate,
  label,
  selected,
  onClick,
}: ExtremeCardProps) {
  const { pa, pb, metrics, insight, width_pct } = candidate;

  return (
    <Card
      className={cn(
        "cursor-pointer border-amber-200 bg-amber-50/50 transition-shadow hover:shadow-md dark:border-amber-900 dark:bg-amber-950/20",
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
            ${pa.toFixed(4)} — ${pb.toFixed(4)}
          </div>
          <div className="text-muted-foreground text-xs">
            Width {width_pct.toFixed(1)}%
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <div className="grid grid-cols-3 gap-2">
          <MetricBadge
            label="In Range"
            value={`${metrics.in_range_pct.toFixed(1)}%`}
          />
          <MetricBadge
            label="LP vs HODL"
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
          />
          <MetricBadge
            label="Max IL"
            value={`${metrics.max_il_pct.toFixed(1)}%`}
          />
        </div>
        <p className="text-muted-foreground text-xs leading-relaxed">{insight}</p>
      </CardContent>
    </Card>
  );
}
