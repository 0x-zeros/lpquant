"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRecommendContext } from "@/context/recommend-context";
import { VolatilitySummary } from "./volatility-summary";
import { BalancedCard } from "./balanced-card";
import { NarrowCard } from "./narrow-card";
import { BacktestCard } from "./backtest-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { InfoTip } from "@/components/ui/info-tip";
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
            {t("recommendTab")}
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex-1">
            {t("aiTab")}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="recommend" className="mt-4 space-y-4">
          {data.kline_source && (
            <div className="flex items-center gap-1 justify-end">
              <Badge variant="outline" className="text-xs font-normal">
                {klineSourceLabel}
              </Badge>
              <InfoTip content={tt("klineSourceTip")} />
            </div>
          )}

          <VolatilitySummary
            volatility={data.volatility}
            horizonDays={data.horizon_days}
          />

          <BalancedCard
            candidate={data.balanced}
            selected={selectedKey === "balanced"}
            currentPrice={data.current_price}
            quoteSymbol={quoteSymbol}
            quoteIsStable={quoteIsStable}
            onClick={() => setSelectedKey("balanced")}
            onDoubleClick={() => openDetail("balanced")}
          />

          <NarrowCard
            candidate={data.narrow}
            selected={selectedKey === "narrow"}
            currentPrice={data.current_price}
            quoteSymbol={quoteSymbol}
            quoteIsStable={quoteIsStable}
            onClick={() => setSelectedKey("narrow")}
            onDoubleClick={() => openDetail("narrow")}
          />

          <BacktestCard
            candidate={data.best_backtest}
            selected={selectedKey === "best_backtest"}
            currentPrice={data.current_price}
            quoteSymbol={quoteSymbol}
            quoteIsStable={quoteIsStable}
            onClick={() => setSelectedKey("best_backtest")}
            onDoubleClick={() => openDetail("best_backtest")}
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
