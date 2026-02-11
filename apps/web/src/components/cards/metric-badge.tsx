"use client";

import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface MetricBadgeProps {
  label: string;
  value: string;
  variant?: "good" | "neutral" | "bad";
  tooltip?: string;
}

export function MetricBadge({ label, value, variant = "neutral", tooltip }: MetricBadgeProps) {
  const content = (
    <div className={cn("flex flex-col items-center gap-0.5 text-center", tooltip && "cursor-help")}>
      <span className="text-muted-foreground text-xs">{label}</span>
      <Badge
        variant="outline"
        className={cn(
          "text-xs font-mono",
          variant === "good" && "border-emerald-500/50 text-emerald-400",
          variant === "bad" && "border-red-500/50 text-red-400",
        )}
      >
        {value}
      </Badge>
    </div>
  );

  if (!tooltip) return content;

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          {content}
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          {tooltip}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
