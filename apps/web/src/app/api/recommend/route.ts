import { NextResponse } from "next/server";
import { getPoolConfig, getPoolSummaryById } from "@/lib/cetus";
import { fetchKlinesForPool } from "@/lib/kline-source";
import { callRecommend } from "@/lib/quant-client";
import { DEFAULT_INTERVAL } from "@/lib/constants";
import { isStableCoin, resolveSymbol, selectBaseQuote } from "@/lib/tokens";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      pool_id: poolId,
      days = 30,
      interval = DEFAULT_INTERVAL,
      capital = 10000,
      horizon_days = 7,
    } = body;

    if (!poolId) {
      return NextResponse.json({ error: "pool_id is required" }, { status: 400 });
    }

    const endMs = Date.now();
    const startMs = endMs - days * 24 * 60 * 60 * 1000;

    const poolSummary = await getPoolSummaryById(poolId);
    if (!poolSummary) {
      return NextResponse.json({ error: "Pool not found" }, { status: 400 });
    }

    // Parallel fetch: klines (Birdeye → Binance fallback) + pool config
    const [klineResult, poolConfig] = await Promise.all([
      fetchKlinesForPool(poolSummary, interval, startMs, endMs),
      getPoolConfig(poolId),
    ]);

    const selection = selectBaseQuote(
      poolSummary.coin_type_a,
      poolSummary.coin_type_b,
    );
    const invertPrice = selection.baseSide === "B";
    const rawCurrentPrice = poolConfig.currentPrice;
    const currentPrice =
      rawCurrentPrice > 0 && invertPrice ? 1 / rawCurrentPrice : rawCurrentPrice;

    let capitalForEngine = capital;
    const quoteIsStable = isStableCoin(selection.quoteCoinType);
    if (!quoteIsStable && klineResult.quoteUsdEntry && klineResult.quoteUsdEntry > 0) {
      capitalForEngine = capital / klineResult.quoteUsdEntry;
    }

    // Convert klines to array format for Python
    const klinesArray = klineResult.klines.map((k) => [
      k.openTime,
      k.open,
      k.high,
      k.low,
      k.close,
      k.volume,
    ]);

    const result = await callRecommend({
      klines: klinesArray,
      current_price: currentPrice,
      tick_spacing: poolConfig.tickSpacing,
      fee_rate: poolConfig.feeRate,
      capital_usd: capitalForEngine,
      horizon_days,
    });

    const coinSymbolA = poolSummary.coin_type_a
      ? resolveSymbol(poolSummary.coin_type_a)
      : "";
    const coinSymbolB = poolSummary.coin_type_b
      ? resolveSymbol(poolSummary.coin_type_b)
      : "";

    return NextResponse.json({
      ...result,
      kline_source: klineResult.source,
      base_symbol: selection.baseSymbol,
      quote_symbol: selection.quoteSymbol,
      base_side: selection.baseSide,
      quote_side: selection.quoteSide,
      quote_is_stable: quoteIsStable,
      pool_symbol: `${selection.baseSymbol}/${selection.quoteSymbol}`,
      coin_symbol_a: coinSymbolA,
      coin_symbol_b: coinSymbolB,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Recommendation failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
