import type { Kline } from "./types";
import { cacheGet, cacheSet } from "./cache";

const BINANCE_API = "https://api.binance.com/api/v3/klines";
const MAX_LIMIT = 1000;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export async function fetchKlines(
  symbol: string,
  interval: string,
  startMs: number,
  endMs: number,
): Promise<Kline[]> {
  const cacheKey = `klines:${symbol}:${interval}:${startMs}:${endMs}`;
  const cached = cacheGet<Kline[]>(cacheKey);
  if (cached) return cached;

  const allKlines: Kline[] = [];
  let currentStart = startMs;

  while (currentStart < endMs) {
    const url = new URL(BINANCE_API);
    url.searchParams.set("symbol", symbol);
    url.searchParams.set("interval", interval);
    url.searchParams.set("startTime", String(currentStart));
    url.searchParams.set("endTime", String(endMs));
    url.searchParams.set("limit", String(MAX_LIMIT));

    const res = await fetch(url.toString());
    if (!res.ok) {
      throw new Error(`Binance API error: ${res.status} ${res.statusText}`);
    }

    const data: unknown[][] = await res.json();
    if (data.length === 0) break;

    for (const k of data) {
      allKlines.push({
        openTime: k[0] as number,
        open: parseFloat(k[1] as string),
        high: parseFloat(k[2] as string),
        low: parseFloat(k[3] as string),
        close: parseFloat(k[4] as string),
        volume: parseFloat(k[5] as string),
      });
    }

    const lastTime = data[data.length - 1][0] as number;
    if (lastTime >= endMs || data.length < MAX_LIMIT) break;
    currentStart = lastTime + 1;
  }

  cacheSet(cacheKey, allKlines, CACHE_TTL);
  return allKlines;
}
