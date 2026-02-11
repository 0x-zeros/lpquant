"use client";

import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";

interface CapitalInputProps {
  value: number;
  onChange: (v: number) => void;
}

export function CapitalInput({ value, onChange }: CapitalInputProps) {
  const t = useTranslations("input");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{t("capital")}</label>
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
