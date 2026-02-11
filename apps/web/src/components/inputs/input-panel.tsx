"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { PairSelector } from "./pair-selector";
import { WindowSelector } from "./window-selector";
import { ProfileSelector } from "./profile-selector";
import { StrategyToggles } from "./strategy-toggles";
import { CapitalInput } from "./capital-input";
import { useFormState } from "@/hooks/use-form-state";
import { useRecommend } from "@/hooks/use-recommend";

export function InputPanel() {
  const t = useTranslations("input");
  const { form, updateField, toggleStrategy } = useFormState();
  const { analyze, loading } = useRecommend();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">{t("config")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <PairSelector
          value={form.pair}
          onChange={(v) => updateField("pair", v)}
        />
        <WindowSelector
          value={form.days}
          onChange={(v) => updateField("days", v)}
        />
        <Separator />
        <ProfileSelector
          value={form.profile}
          onChange={(v) => updateField("profile", v)}
        />
        <StrategyToggles
          selected={form.strategies}
          onToggle={toggleStrategy}
        />
        <CapitalInput
          value={form.capital}
          onChange={(v) => updateField("capital", v)}
        />
        <Separator />
        <Button
          className="w-full font-semibold"
          size="lg"
          onClick={() => analyze(form)}
          disabled={loading || form.strategies.length === 0}
        >
          {loading ? t("analyzing") : t("analyze")}
        </Button>
      </CardContent>
    </Card>
  );
}
