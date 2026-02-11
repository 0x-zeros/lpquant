"use client";

import { useTranslations } from "next-intl";
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

function formatDuration(hours: number) {
  if (!Number.isFinite(hours) || hours <= 0) return "n/a";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 48) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}

export function ExtremeCard({
  candidate,
  label,
  selected,
  onClick,
}: ExtremeCardProps) {
  const tc = useTranslations("cards");
  const tm = useTranslations("metrics");
  const { pa, pb, metrics, insight, width_pct, requested_width_pct } = candidate;
  const requestedWidth = requested_width_pct ?? width_pct;
  const expectedTouch = formatDuration(metrics.mean_time_to_exit_hours);

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
            ${pa.toFixed(4)} — ${pb.toFixed(4)}
          </div>
          <div className="text-muted-foreground text-xs">
            {tc("requested")} {requestedWidth.toFixed(1)}% · {tc("realized")} {width_pct.toFixed(1)}%
          </div>
          <div className="text-muted-foreground text-xs">
            {tc("expectedTouch")} {expectedTouch}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <div className="grid grid-cols-3 gap-2">
          <MetricBadge
            label={tm("inRange")}
            value={`${metrics.in_range_pct.toFixed(1)}%`}
          />
          <MetricBadge
            label={tm("lpVsHodl")}
            value={`${metrics.lp_vs_hodl_pct >= 0 ? "+" : ""}${metrics.lp_vs_hodl_pct.toFixed(1)}%`}
          />
          <MetricBadge
            label={tm("maxIl")}
            value={`${metrics.max_il_pct.toFixed(1)}%`}
          />
        </div>
        <div className="flex flex-wrap gap-1">
          <Badge variant="destructive">{tc("highTouch")}</Badge>
          <Badge variant="destructive">{tc("ultraNarrow")}</Badge>
          <Badge variant="destructive">{tc("activeMgmt")}</Badge>
        </div>
        <p className="text-muted-foreground text-xs leading-relaxed">{insight}</p>
      </CardContent>
    </Card>
  );
}
