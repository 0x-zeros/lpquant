"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { POOL_SORT_OPTIONS } from "@/lib/constants";

interface PoolSortSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

export function PoolSortSelector({ value, onChange }: PoolSortSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Sort By</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {POOL_SORT_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
