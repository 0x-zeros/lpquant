"use client";

import { useTranslations } from "next-intl";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InfoTip } from "@/components/ui/info-tip";

const WINDOWS = [
  { value: 7, label: "7D" },
  { value: 30, label: "30D" },
  { value: 90, label: "90D" },
  { value: 180, label: "180D" },
  { value: 365, label: "1Y" },
];

interface WindowSelectorProps {
  value: number;
  onChange: (v: number) => void;
}

export function WindowSelector({ value, onChange }: WindowSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("window")}
        <InfoTip content={tt("window")} />
      </label>
      <Tabs value={String(value)} onValueChange={(v) => onChange(Number(v))}>
        <TabsList className="w-full">
          {WINDOWS.map((w) => (
            <TabsTrigger key={w.value} value={String(w.value)} className="flex-1">
              {w.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
