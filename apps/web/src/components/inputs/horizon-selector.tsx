"use client";

import { useTranslations } from "next-intl";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InfoTip } from "@/components/ui/info-tip";

const HORIZONS = [
  { value: 1, label: "1D" },
  { value: 3, label: "3D" },
  { value: 7, label: "7D" },
  { value: 14, label: "14D" },
];

interface HorizonSelectorProps {
  value: number;
  onChange: (v: number) => void;
}

export function HorizonSelector({ value, onChange }: HorizonSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("horizon")}
        <InfoTip content={tt("horizon")} />
      </label>
      <Tabs value={String(value)} onValueChange={(v) => onChange(Number(v))}>
        <TabsList className="w-full">
          {HORIZONS.map((h) => (
            <TabsTrigger key={h.value} value={String(h.value)} className="flex-1">
              {h.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
