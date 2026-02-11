"use client";

import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";
import { InfoTip } from "@/components/ui/info-tip";

interface CapitalInputProps {
  value: number;
  onChange: (v: number) => void;
}

export function CapitalInput({ value, onChange }: CapitalInputProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("capital")}
        <InfoTip content={tt("capital")} />
      </label>
      <Input
        type="number"
        min={100}
        step={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value) || 0)}
      />
    </div>
  );
}
