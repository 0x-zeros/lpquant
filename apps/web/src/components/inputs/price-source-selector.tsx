"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PriceSourceSelectorProps {
  value: "pool" | "aggregator";
  onChange: (v: "pool" | "aggregator") => void;
}

export function PriceSourceSelector({ value, onChange }: PriceSourceSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Price Source</label>
      <Select value={value} onValueChange={(v) => onChange(v as "pool" | "aggregator")}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="pool">Pool (on-chain)</SelectItem>
          <SelectItem value="aggregator">Aggregator V3</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
