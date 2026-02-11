"use client";

import { ChartWrapper } from "@/components/charts/chart-wrapper";
import type { ChartSeries } from "@/lib/types";
import type { UTCTimestamp } from "lightweight-charts";

interface PriceChartProps {
  series: ChartSeries;
  mode: "quote" | "base";
  label: string;
}

export function PriceChart({ series, mode, label }: PriceChartProps) {
  const data = series.timestamps
    .map((t, i) => {
      const price = series.prices[i];
      if (!Number.isFinite(price) || price <= 0) return null;
      const value = mode === "quote" ? price : 1 / price;
      if (!Number.isFinite(value)) return null;
      return { time: (t / 1000) as UTCTimestamp, value };
    })
    .filter((item): item is { time: UTCTimestamp; value: number } => Boolean(item));

  return (
    <ChartWrapper
      seriesList={[
        {
          data,
          options: { color: "#3b82f6", title: label },
        },
      ]}
    />
  );
}
