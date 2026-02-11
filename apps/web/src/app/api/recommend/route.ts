import { NextResponse } from "next/server";
import { getPoolConfig, getPoolSummaryById } from "@/lib/cetus";
import { fetchKlinesForPool } from "@/lib/kline-source";
import { callRecommend } from "@/lib/quant-client";
import { DEFAULT_INTERVAL } from "@/lib/constants";
import { resolveSymbol } from "@/lib/tokens";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      pool_id: poolId,
      days = 30,
      interval = DEFAULT_INTERVAL,
      profile = "balanced",
      capital = 10000,
      strategies = ["quantile", "volband", "swing"],
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
      current_price: poolConfig.currentPrice,
      tick_spacing: poolConfig.tickSpacing,
      fee_rate: poolConfig.feeRate,
      profile,
      capital_usd: capital,
      strategies,
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
      price_asset_symbol: klineResult.pricing.pricingSymbol,
      price_quote_symbol: "USD",
      price_asset_side: klineResult.pricing.pricingSide,
      pool_symbol: poolSummary.symbol,
      coin_symbol_a: coinSymbolA,
      coin_symbol_b: coinSymbolB,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Recommendation failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
