"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

interface PriceRangeMetaProps {
  currentPrice: number;
  minPrice: number;
  maxPrice: number;
  quoteSymbol?: string;
  quoteIsStable?: boolean;
}

function formatPrice(value: number, quoteSymbol?: string, quoteIsStable?: boolean) {
  if (!Number.isFinite(value)) return "n/a";
  if (quoteIsStable) return `$${value.toFixed(4)}`;
  const suffix = quoteSymbol ? ` ${quoteSymbol}` : "";
  return `${value.toFixed(4)}${suffix}`;
}

function formatDelta(value: number | null) {
  if (value === null || !Number.isFinite(value)) return "n/a";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function deltaColor(delta: number | null) {
  if (delta === null || !Number.isFinite(delta)) return "text-muted-foreground";
  if (delta > 0.01) return "text-emerald-400";
  if (delta < -0.01) return "text-rose-400";
  return "text-muted-foreground";
}

export function PriceRangeMeta({
  currentPrice,
  minPrice,
  maxPrice,
  quoteSymbol,
  quoteIsStable,
}: PriceRangeMetaProps) {
  const tc = useTranslations("cards");
  const safeCurrent = Number.isFinite(currentPrice) && currentPrice > 0 ? currentPrice : null;
  const minDelta = safeCurrent ? ((minPrice / safeCurrent) - 1) * 100 : null;
  const maxDelta = safeCurrent ? ((maxPrice / safeCurrent) - 1) * 100 : null;

  return (
    <div className="grid grid-cols-3 gap-2 rounded-lg border border-white/5 bg-muted/40 p-2">
      <div className="flex flex-col gap-0.5">
        <span className="text-muted-foreground text-xs">{tc("currentPrice")}</span>
        <span className="font-mono text-sm">
          {formatPrice(currentPrice, quoteSymbol, quoteIsStable)}
        </span>
        <span className="text-muted-foreground text-xs">0.0%</span>
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="text-muted-foreground text-xs">{tc("minPrice")}</span>
        <span className="font-mono text-sm">
          {formatPrice(minPrice, quoteSymbol, quoteIsStable)}
        </span>
        <span className={cn("text-xs", deltaColor(minDelta))}>{formatDelta(minDelta)}</span>
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="text-muted-foreground text-xs">{tc("maxPrice")}</span>
        <span className="font-mono text-sm">
          {formatPrice(maxPrice, quoteSymbol, quoteIsStable)}
        </span>
        <span className={cn("text-xs", deltaColor(maxDelta))}>{formatDelta(maxDelta)}</span>
      </div>
    </div>
  );
}
