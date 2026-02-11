import { NextResponse } from "next/server";
import { fetchKlines } from "@/lib/binance";
import { fetchKlinesForPool } from "@/lib/kline-source";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol");
  const coinTypeA = searchParams.get("coin_type_a");
  const coinTypeB = searchParams.get("coin_type_b");
  const interval = searchParams.get("interval") || "1h";
  const days = parseInt(searchParams.get("days") || "30", 10);

  const endMs = Date.now();
  const startMs = endMs - days * 24 * 60 * 60 * 1000;

  try {
    // If coin types are provided, use unified kline source (Birdeye → Binance fallback)
    if (coinTypeA && coinTypeB) {
      const { klines, source, pricing } = await fetchKlinesForPool(
        { coin_type_a: coinTypeA, coin_type_b: coinTypeB },
        interval,
        startMs,
        endMs,
      );
      return NextResponse.json({ klines, source, pricing });
    }

    // Otherwise, use direct Binance symbol lookup
    const klines = await fetchKlines(symbol || "SUIUSDT", interval, startMs, endMs);
    return NextResponse.json({ klines, source: "binance" });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch klines";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
