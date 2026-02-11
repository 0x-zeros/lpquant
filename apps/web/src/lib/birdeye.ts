import type { Kline } from "./types";
import { cacheGet, cacheSet } from "./cache";
import { env } from "./env";

const BIRDEYE_API = "https://public-api.birdeye.so/defi/v3/ohlcv";
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/** Map lowercase interval to Birdeye type parameter */
function toBirdeyeType(interval: string): string {
  // Birdeye expects: 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M
  const map: Record<string, string> = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "8h": "8H",
    "12h": "12H",
    "1d": "1D",
    "3d": "3D",
    "1w": "1W",
    "1M": "1M",
  };
  return map[interval] ?? interval.toUpperCase();
}

export async function fetchBirdeyeKlines(
  tokenAddress: string,
  interval: string,
  startMs: number,
  endMs: number,
): Promise<Kline[]> {
  const apiKey = env.BIRDEYE_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("BIRDEYE_API_KEY is not configured");
  }

  const cacheKey = `birdeye:klines:${tokenAddress}:${interval}:${startMs}:${endMs}`;
  const cached = cacheGet<Kline[]>(cacheKey);
  if (cached) return cached;

  const url = new URL(BIRDEYE_API);
  url.searchParams.set("address", tokenAddress);
  url.searchParams.set("type", toBirdeyeType(interval));
  url.searchParams.set("time_from", String(Math.floor(startMs / 1000)));
  url.searchParams.set("time_to", String(Math.floor(endMs / 1000)));

  const res = await fetch(url.toString(), {
    headers: {
      "x-chain": "sui",
      "X-API-KEY": apiKey,
    },
  });

  if (!res.ok) {
    throw new Error(`Birdeye API error: ${res.status} ${res.statusText}`);
  }

  const json = await res.json();
  const items = json?.data?.items;
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error("Birdeye API returned no data");
  }

  const klines: Kline[] = items.map(
    (item: {
      unixTime: number;
      o: number;
      h: number;
      l: number;
      c: number;
      v: number;
    }) => ({
      openTime: item.unixTime * 1000,
      open: item.o,
      high: item.h,
      low: item.l,
      close: item.c,
      volume: item.v ?? 0,
    }),
  );

  cacheSet(cacheKey, klines, CACHE_TTL);
  return klines;
}
