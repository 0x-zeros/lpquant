"use client";

import { ChartWrapper } from "@/components/charts/chart-wrapper";
import type { ChartSeries } from "@/lib/types";
import type { UTCTimestamp } from "lightweight-charts";

interface IlChartProps {
  series: ChartSeries;
}

export function IlChart({ series }: IlChartProps) {
  const data = series.timestamps.map((t, i) => ({
    time: (t / 1000) as UTCTimestamp,
    value: series.il_pct[i],
  }));

  return (
    <ChartWrapper
      seriesList={[
        {
          data,
          options: { color: "#ef4444", title: "IL %" },
        },
      ]}
    />
  );
}
