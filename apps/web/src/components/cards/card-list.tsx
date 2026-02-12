"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRecommendContext } from "@/context/recommend-context";
import { RecommendationCard } from "./recommendation-card";
import { ExtremeCard } from "./extreme-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { InfoTip } from "@/components/ui/info-tip";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LlmPanel } from "@/components/detail/llm-panel";
import { DetailModal } from "@/components/detail/detail-modal";

export function CardList() {
  const t = useTranslations("cards");
  const tt = useTranslations("tooltips");
  const { data, loading, error, selectedKey, setSelectedKey } =
    useRecommendContext();
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailKey, setDetailKey] = useState<string | null>(null);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-destructive font-medium">{t("error")}</p>
          <p className="text-muted-foreground mt-1 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-48 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          {t("emptyState")}
        </p>
      </div>
    );
  }

  const klineSourceLabel =
    data.kline_source === "birdeye"
      ? tt("klineBirdeye")
      : tt("klineBinance");
  const quoteSymbol = data.quote_symbol;
  const quoteIsStable = data.quote_is_stable;

  const openDetail = (key: string) => {
    setSelectedKey(key);
    setDetailKey(key);
    setDetailOpen(true);
  };

  return (
    <div className="space-y-4">
      <Tabs defaultValue="recommend">
        <TabsList className="w-full">
          <TabsTrigger value="recommend" className="flex-1">
            {t("topTitle")}
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex-1">
            {t("aiTab")}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="recommend" className="mt-4 space-y-4">
          <h2 className="text-lg font-semibold text-[#00d2ff] flex items-center gap-1.5">
            {t("topTitle")}
            <InfoTip content={tt("topRecommendations")} />
            {data.kline_source && (
              <span className="ml-auto flex items-center gap-1">
                <Badge variant="outline" className="text-xs font-normal">
                  {klineSourceLabel}
                </Badge>
                <InfoTip content={tt("klineSourceTip")} />
              </span>
            )}
          </h2>
          {data.top3.map((c, i) => {
            const key = `top${i + 1}`;
            return (
              <RecommendationCard
                key={key}
                candidate={c}
                rank={i + 1}
                selected={selectedKey === key}
                currentPrice={data.current_price}
                quoteSymbol={quoteSymbol}
                quoteIsStable={quoteIsStable}
                onClick={() => setSelectedKey(key)}
                onDoubleClick={() => openDetail(key)}
              />
            );
          })}

          <Separator />
          <h2 className="text-lg font-semibold text-amber-400 flex items-center gap-1.5">
            {t("extremeTitle")}
            <InfoTip content={tt("extremeRanges")} />
          </h2>

          <ExtremeCard
            candidate={data.extreme_2pct}
            label={t("range2")}
            selected={selectedKey === "extreme_2pct"}
            currentPrice={data.current_price}
            quoteSymbol={quoteSymbol}
            quoteIsStable={quoteIsStable}
            onClick={() => setSelectedKey("extreme_2pct")}
            onDoubleClick={() => openDetail("extreme_2pct")}
          />
          <ExtremeCard
            candidate={data.extreme_5pct}
            label={t("range5")}
            selected={selectedKey === "extreme_5pct"}
            currentPrice={data.current_price}
            quoteSymbol={quoteSymbol}
            quoteIsStable={quoteIsStable}
            onClick={() => setSelectedKey("extreme_5pct")}
            onDoubleClick={() => openDetail("extreme_5pct")}
          />
        </TabsContent>
        <TabsContent value="ai" className="mt-4">
          <LlmPanel />
        </TabsContent>
      </Tabs>
      <DetailModal
        open={detailOpen}
        selectedKey={detailKey ?? selectedKey}
        onClose={() => {
          setDetailOpen(false);
          setDetailKey(null);
        }}
      />
    </div>
  );
}
