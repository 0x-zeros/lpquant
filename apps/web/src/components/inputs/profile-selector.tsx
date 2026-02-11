"use client";

import { useTranslations } from "next-intl";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const PROFILES = ["conservative", "balanced", "aggressive"] as const;

interface ProfileSelectorProps {
  value: string;
  onChange: (v: "conservative" | "balanced" | "aggressive") => void;
}

export function ProfileSelector({ value, onChange }: ProfileSelectorProps) {
  const t = useTranslations("input");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{t("profile")}</label>
      <Tabs
        value={value}
        onValueChange={(v) =>
          onChange(v as "conservative" | "balanced" | "aggressive")
        }
      >
        <TabsList className="w-full">
          {PROFILES.map((p) => (
            <TabsTrigger key={p} value={p} className="flex-1">
              {t(p)}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
