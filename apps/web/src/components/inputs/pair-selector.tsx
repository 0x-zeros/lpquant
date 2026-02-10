"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SUPPORTED_PAIRS } from "@/lib/constants";

interface PairSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

export function PairSelector({ value, onChange }: PairSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Trading Pair</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {Object.entries(SUPPORTED_PAIRS).map(([key, cfg]) => (
            <SelectItem key={key} value={key}>
              {cfg.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
