"use client";

import { useTranslations } from "next-intl";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { InfoTip } from "@/components/ui/info-tip";
import { POOL_SORT_OPTIONS } from "@/lib/constants";

interface PoolSortSelectorProps {
  value: string;
  onChange: (v: string) => void;
}

export function PoolSortSelector({ value, onChange }: PoolSortSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("poolSort")}
        <InfoTip content={tt("poolSort")} />
      </label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {POOL_SORT_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {t(opt.labelKey)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
