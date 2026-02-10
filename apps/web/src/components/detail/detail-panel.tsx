"use client";

import { useRecommendContext } from "@/context/recommend-context";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LpVsHodlChart } from "./lp-vs-hodl-chart";
import { IlChart } from "./il-chart";
import { PriceChart } from "./price-chart";
import { ExportButton } from "./export-button";

export function DetailPanel() {
  const { data, selectedKey } = useRecommendContext();

  if (!data || !selectedKey) {
    return (
      <Card className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          Select a recommendation to view details.
        </p>
      </Card>
    );
  }

  const series = data.series[selectedKey];
  if (!series) {
    return (
      <Card className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          No chart data available for this range.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Detail View</CardTitle>
        <ExportButton />
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="value">
          <TabsList className="w-full">
            <TabsTrigger value="value" className="flex-1">
              LP vs HODL
            </TabsTrigger>
            <TabsTrigger value="il" className="flex-1">
              IL
            </TabsTrigger>
            <TabsTrigger value="price" className="flex-1">
              Price
            </TabsTrigger>
          </TabsList>
          <TabsContent value="value" className="mt-3">
            <LpVsHodlChart series={series} />
          </TabsContent>
          <TabsContent value="il" className="mt-3">
            <IlChart series={series} />
          </TabsContent>
          <TabsContent value="price" className="mt-3">
            <PriceChart series={series} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
