"use client";

import { Toggle } from "@/components/ui/toggle";

const STRATEGIES = [
  { value: "quantile", label: "Quantile" },
  { value: "volband", label: "Vol Band" },
  { value: "swing", label: "Swing" },
];

interface StrategyTogglesProps {
  selected: string[];
  onToggle: (s: string) => void;
}

export function StrategyToggles({ selected, onToggle }: StrategyTogglesProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Strategies</label>
      <div className="flex gap-2">
        {STRATEGIES.map((s) => (
          <Toggle
            key={s.value}
            pressed={selected.includes(s.value)}
            onPressedChange={() => onToggle(s.value)}
            variant="outline"
            className="flex-1"
          >
            {s.label}
          </Toggle>
        ))}
      </div>
    </div>
  );
}
