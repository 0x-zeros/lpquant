import type { Kline } from "./types";
import { fetchBirdeyeKlines } from "./birdeye";
import { fetchKlines } from "./binance";
import { deriveBinanceSymbol, toBirdeyeAddress } from "./tokens";
import { env } from "./env";

export type KlineSource = "birdeye" | "binance";

export interface KlineResult {
  klines: Kline[];
  source: KlineSource;
}

/**
 * Unified kline fetcher with Birdeye → Binance fallback chain.
 *
 * 1. Birdeye (if BIRDEYE_API_KEY is configured) — uses coin_type_a address for USD price
 * 2. Binance (via deriveBinanceSymbol) — standard CEX klines
 * 3. Throws if both fail
 */
export async function fetchKlinesForPool(
  pool: { coin_type_a: string; coin_type_b: string },
  interval: string,
  startMs: number,
  endMs: number,
): Promise<KlineResult> {
  const errors: string[] = [];

  // 1. Try Birdeye
  if (env.BIRDEYE_API_KEY?.trim()) {
    try {
      const address = toBirdeyeAddress(pool.coin_type_a);
      const klines = await fetchBirdeyeKlines(address, interval, startMs, endMs);
      return { klines, source: "birdeye" };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(`Birdeye: ${msg}`);
      console.warn("[kline-source] Birdeye failed, falling back to Binance:", msg);
    }
  }

  // 2. Try Binance
  const binanceSymbol = deriveBinanceSymbol(pool.coin_type_a, pool.coin_type_b);
  if (binanceSymbol) {
    try {
      const klines = await fetchKlines(binanceSymbol, interval, startMs, endMs);
      return { klines, source: "binance" };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(`Binance(${binanceSymbol}): ${msg}`);
      console.warn("[kline-source] Binance failed:", msg);
    }
  } else {
    errors.push("Binance: cannot derive trading pair symbol");
  }

  throw new Error(
    `All kline sources failed for ${pool.coin_type_a}/${pool.coin_type_b}: ${errors.join("; ")}`,
  );
}
