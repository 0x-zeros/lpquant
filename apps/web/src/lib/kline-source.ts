import type { Kline } from "./types";
import { fetchBirdeyeKlines } from "./birdeye";
import { fetchKlines } from "./binance";
import {
  deriveBinanceSymbol,
  deriveBinanceSymbolForPair,
  deriveBinanceUsdSymbol,
  isStableCoin,
  selectBaseQuote,
  toBirdeyeAddress,
} from "./tokens";
import { env } from "./env";

export type KlineSource = "birdeye" | "binance";

export interface KlineResult {
  klines: Kline[];
  source: KlineSource;
  base: {
    coinType: string;
    symbol: string;
    side: "A" | "B";
  };
  quote: {
    coinType: string;
    symbol: string;
    side: "A" | "B";
  };
  quoteUsdEntry?: number | null;
}

/**
 * Unified kline fetcher with Binance → Birdeye fallback chain.
 *
 * 1. Binance (via deriveBinanceSymbol) — standard CEX klines, free & fast
 * 2. Birdeye (if BIRDEYE_API_KEY is configured) — fallback for non-Binance pairs
 * 3. Throws if both fail
 */
export async function fetchKlinesForPool(
  pool: { coin_type_a: string; coin_type_b: string },
  interval: string,
  startMs: number,
  endMs: number,
): Promise<KlineResult> {
  const errors: string[] = [];
  const selection = selectBaseQuote(pool.coin_type_a, pool.coin_type_b);
  const base = {
    coinType: selection.baseCoinType,
    symbol: selection.baseSymbol,
    side: selection.baseSide,
  };
  const quote = {
    coinType: selection.quoteCoinType,
    symbol: selection.quoteSymbol,
    side: selection.quoteSide,
  };
  const quoteIsStable = isStableCoin(selection.quoteCoinType);

  const buildRatioKlines = (
    baseKlines: Kline[],
    quoteKlines: Kline[],
  ): { klines: Kline[]; quoteUsdEntry: number | null } => {
    const quoteMap = new Map<number, Kline>();
    for (const q of quoteKlines) {
      quoteMap.set(q.openTime, q);
    }
    const merged: Kline[] = [];
    let quoteUsdEntry: number | null = null;
    for (const b of baseKlines) {
      const q = quoteMap.get(b.openTime);
      if (!q) continue;
      if (q.close <= 0) continue;
      if (quoteUsdEntry === null) {
        quoteUsdEntry = q.close;
      }
      merged.push({
        openTime: b.openTime,
        open: q.open > 0 ? b.open / q.open : b.open / q.close,
        high: q.high > 0 ? b.high / q.high : b.high / q.close,
        low: q.low > 0 ? b.low / q.low : b.low / q.close,
        close: b.close / q.close,
        volume: b.volume,
      });
    }
    return { klines: merged, quoteUsdEntry };
  };

  // 1. Try Binance (free, fast, no API key needed)
  try {
    if (quoteIsStable) {
      const directSymbol = deriveBinanceSymbolForPair(
        selection.baseCoinType,
        selection.quoteCoinType,
      );
      const fallbackSymbol =
        selection.quoteSymbol !== "USDT"
          ? `${selection.baseSymbol}USDT`
          : null;
      const candidates = [directSymbol, fallbackSymbol, deriveBinanceSymbol(pool.coin_type_a, pool.coin_type_b)]
        .filter((s): s is string => Boolean(s));
      let lastErr: Error | null = null;
      for (const symbol of candidates) {
        try {
          const klines = await fetchKlines(symbol, interval, startMs, endMs);
          return { klines, source: "binance", base, quote };
        } catch (err) {
          lastErr = err instanceof Error ? err : new Error(String(err));
        }
      }
      throw lastErr ?? new Error("Binance: cannot fetch klines");
    }

    const baseUsdSymbol = deriveBinanceUsdSymbol(selection.baseCoinType);
    const quoteUsdSymbol = deriveBinanceUsdSymbol(selection.quoteCoinType);
    if (!baseUsdSymbol || !quoteUsdSymbol) {
      throw new Error("Binance: cannot derive USD pairs for ratio");
    }
    const [baseKlines, quoteKlines] = await Promise.all([
      fetchKlines(baseUsdSymbol, interval, startMs, endMs),
      fetchKlines(quoteUsdSymbol, interval, startMs, endMs),
    ]);
    const { klines, quoteUsdEntry } = buildRatioKlines(baseKlines, quoteKlines);
    if (klines.length === 0) {
      throw new Error("Binance ratio returned empty data");
    }
    return { klines, source: "binance", base, quote, quoteUsdEntry };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    errors.push(`Binance: ${msg}`);
    console.warn("[kline-source] Binance failed, falling back to Birdeye:", msg);
  }

  // 2. Try Birdeye (fallback for non-Binance pairs)
  if (env.BIRDEYE_API_KEY?.trim()) {
    try {
      if (quoteIsStable) {
        const address = toBirdeyeAddress(selection.baseCoinType);
        const klines = await fetchBirdeyeKlines(address, interval, startMs, endMs);
        return { klines, source: "birdeye", base, quote };
      }
      const baseAddr = toBirdeyeAddress(selection.baseCoinType);
      const quoteAddr = toBirdeyeAddress(selection.quoteCoinType);
      const [baseKlines, quoteKlines] = await Promise.all([
        fetchBirdeyeKlines(baseAddr, interval, startMs, endMs),
        fetchBirdeyeKlines(quoteAddr, interval, startMs, endMs),
      ]);
      const { klines, quoteUsdEntry } = buildRatioKlines(baseKlines, quoteKlines);
      if (klines.length === 0) {
        throw new Error("Birdeye ratio returned empty data");
      }
      return { klines, source: "birdeye", base, quote, quoteUsdEntry };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(`Birdeye: ${msg}`);
      console.warn("[kline-source] Birdeye failed:", msg);
    }
  }

  throw new Error(
    `All kline sources failed for ${pool.coin_type_a}/${pool.coin_type_b}: ${errors.join("; ")}`,
  );
}
