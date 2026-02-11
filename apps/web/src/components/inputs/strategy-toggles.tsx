"use client";

import { useTranslations } from "next-intl";
import { Toggle } from "@/components/ui/toggle";
import { InfoTip } from "@/components/ui/info-tip";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const STRATEGIES = ["quantile", "volband", "swing"] as const;
const STRATEGY_TIP_KEYS = {
  quantile: "strategyQuantile",
  volband: "strategyVolband",
  swing: "strategySwing",
} as const;

interface StrategyTogglesProps {
  selected: string[];
  onToggle: (s: string) => void;
}

export function StrategyToggles({ selected, onToggle }: StrategyTogglesProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("strategies")}
        <InfoTip content={tt("strategies")} />
      </label>
      <div className="flex gap-2">
        {STRATEGIES.map((s) => (
          <TooltipProvider key={s} delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Toggle
                  pressed={selected.includes(s)}
                  onPressedChange={() => onToggle(s)}
                  variant="outline"
                  className="flex-1"
                >
                  {t(s)}
                </Toggle>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-xs">
                {tt(STRATEGY_TIP_KEYS[s])}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        ))}
      </div>
    </div>
  );
}
