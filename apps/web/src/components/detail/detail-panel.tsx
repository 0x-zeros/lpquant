"use client";

import { useTranslations } from "next-intl";
import { useRecommendContext } from "@/context/recommend-context";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
            <p className="text-muted-foreground text-xs mb-2">{tt("chartPrice")}</p>
            <PriceChart series={series} />
          </TabsContent>
          <TabsContent value="llm" className="mt-3">
            <LlmPanel />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
