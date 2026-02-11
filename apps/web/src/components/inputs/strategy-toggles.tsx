"use client";

import { useTranslations } from "next-intl";
import { Toggle } from "@/components/ui/toggle";

const STRATEGIES = ["quantile", "volband", "swing"] as const;

interface StrategyTogglesProps {
  selected: string[];
  onToggle: (s: string) => void;
}

export function StrategyToggles({ selected, onToggle }: StrategyTogglesProps) {
  const t = useTranslations("input");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{t("strategies")}</label>
      <div className="flex gap-2">
        {STRATEGIES.map((s) => (
          <Toggle
            key={s}
            pressed={selected.includes(s)}
            onPressedChange={() => onToggle(s)}
            variant="outline"
            className="flex-1"
          >
            {t(s)}
          </Toggle>
        ))}
      </div>
    </div>
  );
}
