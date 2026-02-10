import { NextResponse } from "next/server";
import { fetchKlines } from "@/lib/binance";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol") || "SUIUSDT";
  const interval = searchParams.get("interval") || "1h";
  const days = parseInt(searchParams.get("days") || "30", 10);

  const endMs = Date.now();
  const startMs = endMs - days * 24 * 60 * 60 * 1000;

  try {
    const klines = await fetchKlines(symbol, interval, startMs, endMs);
    return NextResponse.json(klines);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch klines";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
