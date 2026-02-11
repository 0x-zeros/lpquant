import type { Kline } from "./types";
import { cacheGet, cacheSet } from "./cache";
import { env } from "./env";

const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function toMillis(value: number): number {
  return value < 1e12 ? value * 1000 : value;
}

function extractList(payload: any): unknown[] {
  if (!payload) return [];
  const candidates = [
    payload.data?.list,
    payload.data?.kline,
    payload.data?.klines,
    payload.data?.items,
    payload.data?.rows,
    payload.data,
    payload.list,
    payload.kline,
    payload.klines,
    payload.items,
    payload.rows,
  ];
  for (const cand of candidates) {
    if (Array.isArray(cand)) return cand;
  }
  return [];
}

function normalizeKline(entry: unknown): Kline | null {
  if (Array.isArray(entry)) {
    const time = toNumber(entry[0]);
    const open = toNumber(entry[1]);
    const high = toNumber(entry[2]);
    const low = toNumber(entry[3]);
    const close = toNumber(entry[4]);
    const volume = toNumber(entry[5]) ?? 0;
    if (time === null || open === null || high === null || low === null || close === null) {
      return null;
    }
    return {
      openTime: toMillis(time),
      open,
      high,
      low,
      close,
      volume,
    };
  }

  if (entry && typeof entry === "object") {
    const obj = entry as Record<string, unknown>;
    const time =
      toNumber(obj.open_time) ??
      toNumber(obj.openTime) ??
      toNumber(obj.timestamp) ??
      toNumber(obj.time);
    const open = toNumber(obj.open);
    const high = toNumber(obj.high);
    const low = toNumber(obj.low);
    const close = toNumber(obj.close);
    const volume = toNumber(obj.volume) ?? toNumber(obj.vol) ?? 0;
    if (time === null || open === null || high === null || low === null || close === null) {
      return null;
    }
    return {
      openTime: toMillis(time),
      open,
      high,
      low,
      close,
      volume,
    };
  }

  return null;
}

function resolveKlineUrl(params: {
  poolId: string;
  interval: string;
  startMs: number;
  endMs: number;
}): string {
  const base = env.CETUS_KLINE_API_URL?.trim();
  if (!base) {
    throw new Error("CETUS_KLINE_API_URL is not configured");
  }

  if (
    base.includes("{poolId}") ||
    base.includes("{interval}") ||
    base.includes("{start}") ||
    base.includes("{end}")
  ) {
    return base
      .replaceAll("{poolId}", encodeURIComponent(params.poolId))
      .replaceAll("{interval}", encodeURIComponent(params.interval))
      .replaceAll("{start}", encodeURIComponent(String(params.startMs)))
      .replaceAll("{end}", encodeURIComponent(String(params.endMs)));
  }

  const url = new URL(base);
  url.searchParams.set("pool_id", params.poolId);
  url.searchParams.set("interval", params.interval);
  url.searchParams.set("start", String(params.startMs));
  url.searchParams.set("end", String(params.endMs));
  return url.toString();
}

export async function fetchCetusKlines(
  poolId: string,
  interval: string,
  startMs: number,
  endMs: number,
): Promise<Kline[]> {
  const cacheKey = `cetus:klines:${poolId}:${interval}:${startMs}:${endMs}`;
  const cached = cacheGet<Kline[]>(cacheKey);
  if (cached) return cached;

  const url = resolveKlineUrl({ poolId, interval, startMs, endMs });
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Cetus kline API error: ${res.status} ${res.statusText}`);
  }

  const json = await res.json();
  const list = extractList(json);
  const klines = list
    .map((entry) => normalizeKline(entry))
    .filter((entry): entry is Kline => Boolean(entry));

  if (klines.length === 0) {
    throw new Error("Cetus kline API returned no data");
  }

  cacheSet(cacheKey, klines, CACHE_TTL);
  return klines;
}
