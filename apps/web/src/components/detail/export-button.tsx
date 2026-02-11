"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { useRecommendContext } from "@/context/recommend-context";

export function ExportButton() {
  const t = useTranslations("detail");
  const { data } = useRecommendContext();

  const handleExport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `lpquant-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button variant="outline" size="sm" onClick={handleExport} disabled={!data}>
      {t("export")}
    </Button>
  );
}
