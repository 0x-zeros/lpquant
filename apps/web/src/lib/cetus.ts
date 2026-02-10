import { SUPPORTED_PAIRS } from "./constants";
import { cacheGet, cacheSet } from "./cache";
import type { PoolConfig } from "./types";

const CACHE_TTL = 60 * 1000; // 1 minute
const SUI_RPC = process.env.SUI_RPC_URL || "https://fullnode.mainnet.sui.io:443";

const Q64 = 2n ** 64n;
const PRICE_PRECISION = 12;

function bigintDivToNumber(numerator: bigint, denominator: bigint, precision = PRICE_PRECISION) {
  if (denominator === 0n) return 0;
  const integer = numerator / denominator;
  let remainder = numerator % denominator;
  let fraction = "";
  for (let i = 0; i < precision; i += 1) {
    remainder *= 10n;
    const digit = remainder / denominator;
    fraction += digit.toString();
    remainder %= denominator;
  }
  return Number(`${integer.toString()}.${fraction}`);
}

/**
 * Convert sqrtPriceX64 to human-readable price using bigint math to avoid
 * precision loss when sqrtPriceX64 exceeds Number.MAX_SAFE_INTEGER.
 *
 * price = (sqrtPriceX64^2 / 2^128) * 10^(decimalsA - decimalsB)
 */
function sqrtPriceX64ToPrice(
  sqrtPriceX64: bigint,
  decimalsA: number,
  decimalsB: number,
): number {
  const numeratorBase = sqrtPriceX64 * sqrtPriceX64;
  let numerator = numeratorBase;
  let denominator = Q64 * Q64;
  const decimalDelta = decimalsA - decimalsB;
  if (decimalDelta >= 0) {
    numerator *= 10n ** BigInt(decimalDelta);
  } else {
    denominator *= 10n ** BigInt(-decimalDelta);
  }
  return bigintDivToNumber(numerator, denominator);
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
