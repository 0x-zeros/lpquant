"use client";

import { ChartWrapper } from "@/components/charts/chart-wrapper";
import type { ChartSeries } from "@/lib/types";
import type { UTCTimestamp } from "lightweight-charts";

interface LpVsHodlChartProps {
  series: ChartSeries;
}

export function LpVsHodlChart({ series }: LpVsHodlChartProps) {
  const lpData = series.timestamps.map((t, i) => ({
    time: (t / 1000) as UTCTimestamp,
    value: series.lp_values[i],
  }));

  const hodlData = series.timestamps.map((t, i) => ({
    time: (t / 1000) as UTCTimestamp,
    value: series.hodl_values[i],
  }));
  const markers = series.markers?.map((m) => ({
    time: (m.time / 1000) as UTCTimestamp,
    position: m.position,
    color: m.color ?? "#9ca3af",
    shape: m.shape,
    text: m.text,
  }));

  return (
    <ChartWrapper
      seriesList={[
        {
          data: lpData,
          options: { color: "#22c55e", title: "LP Value" },
          markers,
        },
        {
          data: hodlData,
          options: { color: "#6366f1", title: "HODL Value" },
        },
      ]}
    />
  );
}
