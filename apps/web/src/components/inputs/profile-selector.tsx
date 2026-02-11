"use client";

import { useTranslations } from "next-intl";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InfoTip } from "@/components/ui/info-tip";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const PROFILES = ["conservative", "balanced", "aggressive"] as const;
const PROFILE_TIP_KEYS = {
  conservative: "profileConservative",
  balanced: "profileBalanced",
  aggressive: "profileAggressive",
} as const;

interface ProfileSelectorProps {
  value: string;
  onChange: (v: "conservative" | "balanced" | "aggressive") => void;
}

export function ProfileSelector({ value, onChange }: ProfileSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("profile")}
        <InfoTip content={tt("profile")} />
      </label>
      <Tabs
        value={value}
        onValueChange={(v) =>
          onChange(v as "conservative" | "balanced" | "aggressive")
        }
      >
        <TabsList className="w-full">
          {PROFILES.map((p) => (
            <TooltipProvider key={p} delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <TabsTrigger value={p} className="flex-1">
                    {t(p)}
                  </TabsTrigger>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  {tt(PROFILE_TIP_KEYS[p])}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
