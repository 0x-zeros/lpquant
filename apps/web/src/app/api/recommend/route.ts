import { NextResponse } from "next/server";
import { fetchKlines } from "@/lib/binance";
import { getPoolConfig } from "@/lib/cetus";
import { callRecommend } from "@/lib/quant-client";
import { SUPPORTED_PAIRS, DEFAULT_INTERVAL } from "@/lib/constants";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      pair = "SUI-USDC",
      days = 30,
      interval = DEFAULT_INTERVAL,
      profile = "balanced",
      capital = 10000,
      strategies = ["quantile", "volband", "swing"],
    } = body;

    const pairConfig = SUPPORTED_PAIRS[pair];
    if (!pairConfig) {
      return NextResponse.json({ error: "Unsupported pair" }, { status: 400 });
    }

    const endMs = Date.now();
    const startMs = endMs - days * 24 * 60 * 60 * 1000;

    // Parallel fetch: klines + pool config
    const [klines, poolConfig] = await Promise.all([
      fetchKlines(pairConfig.binanceSymbol, interval, startMs, endMs),
      getPoolConfig(pair),
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
