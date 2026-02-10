import { SUPPORTED_PAIRS } from "./constants";
import { cacheGet, cacheSet } from "./cache";
import type { PoolConfig } from "./types";

const CACHE_TTL = 60 * 1000; // 1 minute
const SUI_RPC = process.env.SUI_RPC_URL || "https://fullnode.mainnet.sui.io:443";

/**
 * Convert sqrtPriceX64 to human-readable price.
 * sqrtPrice = sqrtPriceX64 / 2^64
 * price_raw = sqrtPrice^2
 * price = price_raw * 10^(decimalsA - decimalsB)
 */
function sqrtPriceX64ToPrice(
  sqrtPriceX64: bigint,
  decimalsA: number,
  decimalsB: number,
): number {
  const sqrtPrice = Number(sqrtPriceX64) / 2 ** 64;
  const priceRaw = sqrtPrice * sqrtPrice;
  return priceRaw * 10 ** (decimalsA - decimalsB);
}

interface SuiObjectField {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

async function getPoolObject(poolId: string): Promise<SuiObjectField> {
  const res = await fetch(SUI_RPC, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "sui_getObject",
      params: [
        poolId,
        { showContent: true },
      ],
    }),
  });

  if (!res.ok) {
    throw new Error(`Sui RPC error: ${res.status}`);
  }

  const json = await res.json();
  const content = json?.result?.data?.content;
  if (!content?.fields) {
    throw new Error("Failed to get pool object fields");
  }
  return content.fields;
}

export async function getPoolConfig(pair: string): Promise<PoolConfig> {
  const cacheKey = `pool:${pair}`;
  const cached = cacheGet<PoolConfig>(cacheKey);
  if (cached) return cached;

  const pairConfig = SUPPORTED_PAIRS[pair];
  if (!pairConfig) {
    throw new Error(`Unsupported pair: ${pair}`);
  }

  const fields = await getPoolObject(pairConfig.poolId);

  const sqrtPriceX64 = BigInt(fields.current_sqrt_price);
  const currentPrice = sqrtPriceX64ToPrice(
    sqrtPriceX64,
    pairConfig.decimalsA,
    pairConfig.decimalsB,
  );

  const config: PoolConfig = {
    poolId: pairConfig.poolId,
    tickSpacing: Number(fields.tick_spacing),
    currentPrice,
    feeRate: Number(fields.fee_rate) / 1_000_000,
    coinTypeA: pairConfig.coinTypeA,
    coinTypeB: pairConfig.coinTypeB,
  };

  cacheSet(cacheKey, config, CACHE_TTL);
  return config;
}
