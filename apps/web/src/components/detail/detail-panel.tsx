"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRecommendContext } from "@/context/recommend-context";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Toggle } from "@/components/ui/toggle";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { LpVsHodlChart } from "./lp-vs-hodl-chart";
import { IlChart } from "./il-chart";
import { PriceChart } from "./price-chart";
import { ExportButton } from "./export-button";
import { LlmPanel } from "./llm-panel";

export function DetailPanel() {
  const t = useTranslations("detail");
  const tt = useTranslations("tooltips");
  const { data, selectedKey } = useRecommendContext();
  const [priceMode, setPriceMode] = useState<"quote" | "base">("quote");

  if (!data || !selectedKey) {
    return (
      <Card className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          {t("selectHint")}
        </p>
      </Card>
    );
  }

  const series = data.series[selectedKey];
  if (!series) {
    return (
      <Card className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          {t("noData")}
        </p>
      </Card>
    );
  }

  const fallbackBaseSymbol =
    data.base_side === "B"
      ? data.coin_symbol_b
      : data.base_side === "A"
        ? data.coin_symbol_a
        : undefined;
  const fallbackQuoteSymbol =
    data.quote_side === "B"
      ? data.coin_symbol_b
      : data.quote_side === "A"
        ? data.coin_symbol_a
        : undefined;
  const baseSymbol = (data.base_symbol ?? fallbackBaseSymbol ?? "").trim();
  const quoteSymbol = (data.quote_symbol ?? fallbackQuoteSymbol ?? "").trim();
  const showPriceToggle = baseSymbol.length > 0 && quoteSymbol.length > 0;
  const priceLabel = showPriceToggle
    ? priceMode === "quote"
      ? `${baseSymbol} / ${quoteSymbol}`
      : `${quoteSymbol} / ${baseSymbol}`
    : t("price");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">{t("title")}</CardTitle>
        <ExportButton />
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="value">
          <TabsList className="w-full">
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <TabsTrigger value="value" className="flex-1">
                    {t("lpVsHodl")}
                  </TabsTrigger>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  {tt("chartLpVsHodl")}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <TabsTrigger value="il" className="flex-1">
                    {t("il")}
                  </TabsTrigger>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  {tt("chartIl")}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <TabsTrigger value="price" className="flex-1">
                    {t("price")}
                  </TabsTrigger>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  {tt("chartPrice")}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <TabsTrigger value="llm" className="flex-1">
              {t("llm")}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="value" className="mt-3">
            <p className="text-muted-foreground text-xs mb-2">{tt("chartLpVsHodl")}</p>
            <LpVsHodlChart series={series} />
          </TabsContent>
          <TabsContent value="il" className="mt-3">
            <p className="text-muted-foreground text-xs mb-2">{tt("chartIl")}</p>
            <IlChart series={series} />
          </TabsContent>
          <TabsContent value="price" className="mt-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <p className="text-muted-foreground text-xs">
                {tt("chartPrice")}
              </p>
              {showPriceToggle && (
                <div className="flex items-center gap-1 rounded-full border border-border/60 bg-muted/20 p-1">
                  <Toggle
                    size="sm"
                    variant="outline"
                    pressed={priceMode === "quote"}
                    onPressedChange={(pressed) => {
                      if (pressed) setPriceMode("quote");
                    }}
                    className="h-7 px-2 text-xs"
                  >
                    {baseSymbol}
                  </Toggle>
                  <Toggle
                    size="sm"
                    variant="outline"
                    pressed={priceMode === "base"}
                    onPressedChange={(pressed) => {
                      if (pressed) setPriceMode("base");
                    }}
                    className="h-7 px-2 text-xs"
                  >
                    {quoteSymbol}
                  </Toggle>
                </div>
              )}
            </div>
            <div className="text-xs font-medium text-muted-foreground mb-2">
              {priceLabel}
            </div>
            <PriceChart
              series={series}
              mode={priceMode}
              label={priceLabel}
            />
          </TabsContent>
          <TabsContent value="llm" className="mt-3">
            <LlmPanel />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
