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
  const markers = series.markers
    ?.filter((m) => (m.text ?? "").toLowerCase().includes("il"))
    .map((m) => ({
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
          data,
          options: { color: "#ef4444", title: "IL %" },
          markers,
        },
      ]}
    />
  );
}
