import { CetusClmmSDK } from "@cetusprotocol/sui-clmm-sdk";
import { TickMath } from "@cetusprotocol/common-sdk";
import BN from "bn.js";
import { cacheGet, cacheSet } from "./cache";
import { env } from "./env";
import type { PoolConfig, PoolSummary } from "./types";
import { getAggregatorPrice } from "./aggregator";
import { resolveSymbol, deriveBinanceSymbol } from "./tokens";

const POOLS_CACHE_TTL = 60 * 1000; // 1 minute
const POOL_CONFIG_TTL = 60 * 1000; // 1 minute
const COIN_META_TTL = 60 * 60 * 1000; // 1 hour
const POOLS_API_FALLBACKS = [
  "https://api-sui.cetus.zone/v2/sui/stats_pools",
  "https://api.cetus.zone/v2/sui/stats_pools",
];

type PoolsInfoEntry = {
  pool?: Record<string, unknown>;
  coin_a?: Record<string, unknown>;
  coin_b?: Record<string, unknown>;
} & Record<string, unknown>;

async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise((r) => setTimeout(r, 1000 * (i + 1)));
    }
  }
  throw new Error("withRetry exhausted");
}

let sdkInstance: CetusClmmSDK | null = null;

function getSDK() {
  if (!sdkInstance) {
    sdkInstance = CetusClmmSDK.createSDK({ env: "mainnet" });
  }
  return sdkInstance;
}

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "bigint") return Number(value);
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  if (typeof value === "object" && "toString" in value) {
    const parsed = Number(value.toString());
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function parseMetric(entry: Record<string, unknown>, keys: string[]): number | null {
  for (const key of keys) {
    const value = entry[key];
    const num = toNumber(value);
    if (num !== null) return num;
  }
  return null;
}

function normalizeFeeRate(value: number | null): number {
  if (value === null) return 0;
  if (value > 1) return value / 1_000_000; // micro-units: 500 → 0.0005
  return value / 100; // percentage: 0.05 → 0.0005
}

function getField(obj: Record<string, unknown> | undefined, keys: string[]): unknown {
  if (!obj) return undefined;
  for (const key of keys) {
    if (obj[key] !== undefined) return obj[key];
  }
  return undefined;
}

async function fetchPoolsInfo(): Promise<PoolsInfoEntry[]> {
  const cacheKey = "cetus:pools_info";
  const cached = cacheGet<PoolsInfoEntry[]>(cacheKey);
  if (cached) return cached;

  const urls = [
    env.CETUS_POOLS_API_URL,
    ...POOLS_API_FALLBACKS.filter((url) => url !== env.CETUS_POOLS_API_URL),
  ].filter((url): url is string => Boolean(url && url.trim()));

  let lastError: string | null = null;
  for (const url of urls) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        lastError = `Cetus pools API error (${res.status}) for ${url}`;
        continue;
      }
      const json = await res.json();

      const apiCode = json?.code;
      const isCodeOk = apiCode === undefined || apiCode === 200 || apiCode === 0 || apiCode === "OK";
      if (!isCodeOk) {
        lastError = `Cetus API returned code ${apiCode} for ${url}`;
        continue;
      }

      const fromLpList = json?.data?.lp_list;
      const fromPools = json?.data?.pools;
      const fromData = json?.data;
      const fromTopPools = json?.pools;

      const raw =
        (fromLpList as PoolsInfoEntry[] | undefined) ??
        (fromPools as PoolsInfoEntry[] | undefined) ??
        (Array.isArray(fromData) ? fromData as PoolsInfoEntry[] : undefined) ??
        (fromTopPools as PoolsInfoEntry[] | undefined) ??
        [];

      const list = raw.filter((entry) => {
        const closed = (entry as Record<string, unknown>).is_closed;
        return closed !== true && closed !== 1;
      });

      cacheSet(cacheKey, list, POOLS_CACHE_TTL);
      return list;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
      console.error("[cetus] fetchPoolsInfo error:", lastError);
    }
  }

  throw new Error(lastError || "Failed to fetch Cetus pools API");
}

function buildPoolSummary(entry: PoolsInfoEntry): PoolSummary | null {
  const pool = (entry.pool ?? entry) as Record<string, unknown>;
  const coinA = (entry.coin_a ?? entry.coinA) as Record<string, unknown> | undefined;
  const coinB = (entry.coin_b ?? entry.coinB) as Record<string, unknown> | undefined;

  const verifiedFlag = getField(pool, [
    "is_verified",
    "isVerified",
    "is_whitelisted",
    "isWhitelist",
    "is_whitelist",
    "is_white_list",
  ]);
  if (verifiedFlag === false || verifiedFlag === 0) return null;

  const poolId =
    (getField(pool, ["address", "pool_id", "poolId", "id"]) as string | undefined) ??
    (getField(entry, ["pool_id", "poolId", "id"]) as string | undefined);
  if (!poolId) return null;

  const coinTypeA =
    (getField(coinA, ["address", "type", "coin_type", "coinType"]) as string | undefined) ??
    "";
  const coinTypeB =
    (getField(coinB, ["address", "type", "coin_type", "coinType"]) as string | undefined) ??
    "";

  const symbolA = resolveSymbol(coinTypeA);
  const symbolB = resolveSymbol(coinTypeB);
  const symbol = symbolA && symbolB ? `${symbolA}/${symbolB}` : poolId.slice(0, 10);

  const feeRaw = parseMetric(pool, ["fee_rate", "fee", "feeRate"]);
  const feeRate = normalizeFeeRate(feeRaw);

  const volume24h =
    parseMetric(pool, ["volume_24h", "volume24h", "vol_24h", "vol24h", "vol_in_usd_24h"]) ??
    parseMetric(entry, ["volume_24h", "volume24h", "vol_24h", "vol24h", "vol_in_usd_24h"]);
  const fees24h =
    parseMetric(pool, ["fees_24h", "fee_24h", "fees24h", "fee24h", "fee_24_h"]) ??
    parseMetric(entry, ["fees_24h", "fee_24h", "fees24h", "fee24h", "fee_24_h"]);
  const aprObj = entry.apr as Record<string, unknown> | undefined;
  const apr =
    parseMetric(pool, ["total_apr", "apr", "apr_24h", "apr24h"]) ??
    parseMetric(entry, ["total_apr", "apr", "apr_24h", "apr24h"]) ??
    (aprObj ? parseMetric(aprObj, ["fee_apr_24h"]) : null);
  const tvl =
    parseMetric(pool, ["tvl", "tvl_usd", "liquidity", "pure_tvl_in_usd"]) ??
    parseMetric(entry, ["tvl", "tvl_usd", "liquidity", "pure_tvl_in_usd"]);

  const decimalsA =
    toNumber(getField(coinA, ["decimals"])) ??
    toNumber(getField(coinA, ["decimal"])) ??
    0;
  const decimalsB =
    toNumber(getField(coinB, ["decimals"])) ??
    toNumber(getField(coinB, ["decimal"])) ??
    0;

  const binanceSymbol = deriveBinanceSymbol(coinTypeA, coinTypeB);

  const logoUrlA = (getField(coinA, ["logo_url", "logo", "icon_url"]) as string | undefined) ?? null;
  const logoUrlB = (getField(coinB, ["logo_url", "logo", "icon_url"]) as string | undefined) ?? null;

  return {
    pool_id: poolId,
    symbol,
    fee_rate: feeRate,
    volume_24h: volume24h,
    fees_24h: fees24h,
    apr,
    tvl,
    coin_type_a: coinTypeA,
    coin_type_b: coinTypeB,
    decimals_a: decimalsA,
    decimals_b: decimalsB,
    binance_symbol: binanceSymbol,
    logo_url_a: logoUrlA,
    logo_url_b: logoUrlB,
  };
}

function toBN(value: unknown): BN {
  if (BN.isBN(value)) return value as BN;
  if (typeof value === "bigint") return new BN(value.toString());
  if (typeof value === "number") return new BN(Math.floor(value));
  if (typeof value === "string") return new BN(value);
  if (typeof value === "object" && value && "toString" in value) {
    return new BN(value.toString());
  }
  throw new Error("Unsupported sqrtPriceX64 value");
}

async function getCoinMetadata(coinType: string): Promise<{ decimals: number } | null> {
  const cacheKey = `cetus:coin_meta:${coinType}`;
  const cached = cacheGet<{ decimals: number }>(cacheKey);
  if (cached) return cached;

  const sdk = getSDK() as unknown as {
    FullClient?: { fetchCoinMetadata?: (t: string) => Promise<{ decimals: number } | null> };
  };
  const meta = await sdk.FullClient?.fetchCoinMetadata?.(coinType);
  if (meta?.decimals !== undefined) {
    const result = { decimals: Number(meta.decimals) };
    cacheSet(cacheKey, result, COIN_META_TTL);
    return result;
  }
  return null;
}

export async function getPoolsSummary(options?: {
  limit?: number;
  sortBy?: string;
}): Promise<PoolSummary[]> {
  const { limit = 20, sortBy = "volume_24h" } = options ?? {};
  let pools: PoolSummary[] = [];

  try {
    const entries = await fetchPoolsInfo();
    pools = entries.map(buildPoolSummary).filter((p): p is PoolSummary => Boolean(p));
  } catch (err) {
    console.error("[cetus] getPoolsSummary: falling back to SDK:", err instanceof Error ? err.message : err);
    pools = await getPoolsSummaryFromSdk();
  }

  const sortable = [...pools];
  sortable.sort((a, b) => {
    const ar = a as unknown as Record<string, unknown>;
    const br = b as unknown as Record<string, unknown>;
    const av = ar[sortBy] ?? (sortBy === "tvl" ? ar.tvl : null);
    const bv = br[sortBy] ?? (sortBy === "tvl" ? br.tvl : null);
    const aNum = toNumber(av) ?? -Infinity;
    const bNum = toNumber(bv) ?? -Infinity;
    return bNum - aNum;
  });

  return sortable.slice(0, limit);
}

async function getPoolsSummaryFromSdk(): Promise<PoolSummary[]> {
  const sdk = getSDK();
  const page = await sdk.Pool.getPoolsWithPage();
  const pools = page?.data;
  if (!Array.isArray(pools)) {
    throw new Error("Cetus SDK returned empty pool list");
  }

  const summaries = await Promise.all(
    pools.map(async (pool) => buildPoolSummaryFromSdk(pool as Record<string, unknown>)),
  );
  return summaries.filter((p): p is PoolSummary => Boolean(p));
}

async function buildPoolSummaryFromSdk(
  pool: Record<string, unknown>,
): Promise<PoolSummary | null> {
  const poolId =
    (getField(pool, ["pool_id", "poolId", "id", "address"]) as string | undefined) ??
    "";
  if (!poolId) return null;

  const coinTypeA =
    (getField(pool, ["coin_type_a", "coinTypeA", "coinA", "coin_a"]) as string | undefined) ??
    "";
  const coinTypeB =
    (getField(pool, ["coin_type_b", "coinTypeB", "coinB", "coin_b"]) as string | undefined) ??
    "";

  const symbolA = resolveSymbol(coinTypeA);
  const symbolB = resolveSymbol(coinTypeB);
  const symbol = symbolA && symbolB ? `${symbolA}/${symbolB}` : poolId.slice(0, 10);

  const feeRaw = parseMetric(pool, ["fee_rate", "fee", "feeRate"]);
  const feeRate = normalizeFeeRate(feeRaw);

  let decimalsA = 0;
  let decimalsB = 0;
  if (coinTypeA) {
    const meta = await getCoinMetadata(coinTypeA);
    decimalsA = meta?.decimals ?? 0;
  }
  if (coinTypeB) {
    const meta = await getCoinMetadata(coinTypeB);
    decimalsB = meta?.decimals ?? 0;
  }

  return {
    pool_id: poolId,
    symbol,
    fee_rate: feeRate,
    volume_24h: null,
    fees_24h: null,
    apr: null,
    tvl: null,
    coin_type_a: coinTypeA,
    coin_type_b: coinTypeB,
    decimals_a: decimalsA,
    decimals_b: decimalsB,
    binance_symbol: deriveBinanceSymbol(coinTypeA, coinTypeB),
    logo_url_a: null,
    logo_url_b: null,
  };
}

export async function getPoolSummaryById(poolId: string): Promise<PoolSummary | null> {
  const entries = await fetchPoolsInfo();
  for (const entry of entries) {
    const summary = buildPoolSummary(entry);
    if (summary?.pool_id === poolId) return summary;
  }
  return null;
}

export async function getPoolConfig(
  poolId: string,
): Promise<PoolConfig> {
  const cacheKey = `pool:${poolId}`;
  const cached = cacheGet<PoolConfig>(cacheKey);
  if (cached) return cached;

  const sdk = getSDK();
  const pool = (await withRetry(() => sdk.Pool.getPool(poolId))) as Record<string, unknown> | null;
  if (!pool) {
    throw new Error(`Pool not found: ${poolId}`);
  }

  const poolSummary = await getPoolSummaryById(poolId);
  const coinTypeA =
    (poolSummary?.coin_type_a ?? (pool.coin_type_a as string | undefined)) ?? "";
  const coinTypeB =
    (poolSummary?.coin_type_b ?? (pool.coin_type_b as string | undefined)) ?? "";

  let decimalsA = poolSummary?.decimals_a ?? 0;
  let decimalsB = poolSummary?.decimals_b ?? 0;

  if (!decimalsA && coinTypeA) {
    const meta = await getCoinMetadata(coinTypeA);
    decimalsA = meta?.decimals ?? 0;
  }
  if (!decimalsB && coinTypeB) {
    const meta = await getCoinMetadata(coinTypeB);
    decimalsB = meta?.decimals ?? 0;
  }

  const sqrtPriceRaw =
    pool.current_sqrt_price ??
    pool.current_sqrt_price_x64 ??
    pool.currentSqrtPrice ??
    pool.currentSqrtPriceX64;
  if (!sqrtPriceRaw) {
    throw new Error(`Pool ${poolId} missing sqrt price`);
  }

  const tickSpacing =
    toNumber(pool.tick_spacing ?? pool.tickSpacing ?? pool.tick_spacing_value) ?? 0;
  if (!tickSpacing) {
    throw new Error(`Pool ${poolId} missing tick spacing`);
  }

  const feeRateRaw = toNumber(pool.fee_rate ?? pool.feeRate ?? pool.fee);
  const feeRate = normalizeFeeRate(feeRateRaw);

  const priceFromPool = Number(
    TickMath.sqrtPriceX64ToPrice(toBN(sqrtPriceRaw), decimalsA, decimalsB),
  );

  let currentPrice = priceFromPool;
  if (coinTypeA && coinTypeB) {
    const aggPrice = await getAggregatorPrice({
      from: coinTypeA,
      to: coinTypeB,
      decimalsA,
      decimalsB,
    });
    if (aggPrice && aggPrice > 0) {
      currentPrice = aggPrice;
    }
  }

  const config: PoolConfig = {
    poolId,
    tickSpacing: Math.round(tickSpacing),
    currentPrice,
    feeRate,
    coinTypeA,
    coinTypeB,
    decimalsA,
    decimalsB,
    priceFromPool,
  };

  cacheSet(cacheKey, config, POOL_CONFIG_TTL);
  return config;
}
