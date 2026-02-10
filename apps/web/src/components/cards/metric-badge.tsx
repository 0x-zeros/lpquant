"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface MetricBadgeProps {
  label: string;
  value: string;
  variant?: "good" | "neutral" | "bad";
}

export function MetricBadge({ label, value, variant = "neutral" }: MetricBadgeProps) {
  return (
    <div className="flex flex-col items-center gap-0.5 text-center">
      <span className="text-muted-foreground text-xs">{label}</span>
      <Badge
        variant="outline"
        className={cn(
          "text-xs font-mono",
          variant === "good" && "border-green-500 text-green-600",
          variant === "bad" && "border-red-500 text-red-600",
        )}
      >
        {value}
      </Badge>
    </div>
  );
}
