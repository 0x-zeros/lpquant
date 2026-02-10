"use client";

import dynamic from "next/dynamic";
import type { SeriesConfig } from "./chart-inner";
import { Skeleton } from "@/components/ui/skeleton";

const ChartInner = dynamic(() => import("./chart-inner").then((m) => m.ChartInner), {
  ssr: false,
  loading: () => <Skeleton className="h-[250px] w-full" />,
});

interface ChartWrapperProps {
  seriesList: SeriesConfig[];
  height?: number;
}

export function ChartWrapper({ seriesList, height }: ChartWrapperProps) {
  return <ChartInner seriesList={seriesList} height={height} />;
}
