"use client";

import { ChartWrapper } from "@/components/charts/chart-wrapper";
import type { ChartSeries } from "@/lib/types";
import type { UTCTimestamp } from "lightweight-charts";

interface PriceChartProps {
  series: ChartSeries;
}

export function PriceChart({ series }: PriceChartProps) {
  const data = series.timestamps.map((t, i) => ({
    time: (t / 1000) as UTCTimestamp,
    value: series.prices[i],
  }));

  return (
    <ChartWrapper
      seriesList={[
        {
          data,
          options: { color: "#3b82f6", title: "Price" },
        },
      ]}
    />
  );
}
