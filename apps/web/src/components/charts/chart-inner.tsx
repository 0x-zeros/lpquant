"use client";

import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type UTCTimestamp, LineSeries, type LineSeriesOptions } from "lightweight-charts";

export interface SeriesConfig {
  data: { time: UTCTimestamp; value: number }[];
  options?: Partial<LineSeriesOptions>;
}

interface ChartInnerProps {
  seriesList: SeriesConfig[];
  height?: number;
}

export function ChartInner({ seriesList, height = 250 }: ChartInnerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { color: "transparent" },
        textColor: "#999",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(150,150,150,0.1)" },
        horzLines: { color: "rgba(150,150,150,0.1)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    for (const s of seriesList) {
      const series = chart.addSeries(LineSeries, {
        lineWidth: 2,
        ...s.options,
      });
      series.setData(s.data);
    }

    chart.timeScale().fitContent();

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [seriesList, height]);

  return <div ref={containerRef} />;
}
