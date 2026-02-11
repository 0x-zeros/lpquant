"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type UTCTimestamp,
  LineSeries,
  type LineSeriesOptions,
  type SeriesMarker,
} from "lightweight-charts";

export interface SeriesConfig {
  data: { time: UTCTimestamp; value: number }[];
  options?: Partial<LineSeriesOptions>;
  markers?: SeriesMarker<UTCTimestamp>[];
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
        textColor: "#8892b0",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
      },
    });

    chartRef.current = chart;
    const markerPlugins: { detach: () => void }[] = [];

    for (const s of seriesList) {
      const series = chart.addSeries(LineSeries, {
        lineWidth: 2,
        ...s.options,
      });
      series.setData(s.data);
      if (s.markers && s.markers.length > 0) {
        markerPlugins.push(createSeriesMarkers(series, s.markers));
      }
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
      markerPlugins.forEach((plugin) => plugin.detach());
      chart.remove();
    };
  }, [seriesList, height]);

  return <div ref={containerRef} />;
}
