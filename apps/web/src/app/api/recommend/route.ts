import { NextResponse } from "next/server";
import { fetchKlines } from "@/lib/binance";
import { getPoolConfig, getPoolSummaryById } from "@/lib/cetus";
import { callRecommend } from "@/lib/quant-client";
import { DEFAULT_INTERVAL } from "@/lib/constants";
import { env } from "@/lib/env";

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
      price_source: priceSourceRaw,
    } = body;

    const priceSource =
      priceSourceRaw === "aggregator"
        ? "aggregator"
        : (env.PRICE_SOURCE_DEFAULT as "pool" | "aggregator");

    if (!poolId) {
      return NextResponse.json({ error: "pool_id is required" }, { status: 400 });
    }

    const endMs = Date.now();
    const startMs = endMs - days * 24 * 60 * 60 * 1000;

    const poolSummary = await getPoolSummaryById(poolId);
    if (!poolSummary) {
      return NextResponse.json({ error: "Pool not found" }, { status: 400 });
    }
    if (!poolSummary.binance_symbol) {
      return NextResponse.json(
        { error: "No Binance symbol mapping for this pool" },
        { status: 400 },
      );
    }

    // Parallel fetch: klines + pool config
    const [klines, poolConfig] = await Promise.all([
      fetchKlines(poolSummary.binance_symbol, interval, startMs, endMs),
      getPoolConfig(poolId, priceSource),
    ]);

    // Convert klines to array format for Python
    const klinesArray = klines.map((k) => [
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

    return NextResponse.json(result);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Recommendation failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
