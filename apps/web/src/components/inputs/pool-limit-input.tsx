"use client";

import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";
import { InfoTip } from "@/components/ui/info-tip";
import { DEFAULT_POOL_LIMIT, MAX_POOL_LIMIT } from "@/lib/constants";

interface PoolLimitInputProps {
  value: number;
  onChange: (v: number) => void;
}

export function PoolLimitInput({ value, onChange }: PoolLimitInputProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("poolLimit")}
        <InfoTip content={tt("poolLimit")} />
      </label>
      <Input
        type="number"
        min={1}
        max={MAX_POOL_LIMIT}
        step={1}
        value={value || DEFAULT_POOL_LIMIT}
        onChange={(e) => {
          const parsed = Number(e.target.value);
          if (!Number.isFinite(parsed)) return onChange(DEFAULT_POOL_LIMIT);
          const clamped = Math.min(Math.max(parsed, 1), MAX_POOL_LIMIT);
          onChange(clamped);
        }}
      />
    </div>
  );
}
