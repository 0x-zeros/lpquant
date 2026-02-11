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

interface PriceSourceSelectorProps {
  value: "pool" | "aggregator";
  onChange: (v: "pool" | "aggregator") => void;
}

export function PriceSourceSelector({ value, onChange }: PriceSourceSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("priceSource")}
        <InfoTip content={tt("priceSource")} />
      </label>
      <Select value={value} onValueChange={(v) => onChange(v as "pool" | "aggregator")}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="pool">{t("pricePool")}</SelectItem>
          <SelectItem value="aggregator">{t("priceAggregator")}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
