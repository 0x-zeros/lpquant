import { NextResponse } from "next/server";
import { getPoolConfig } from "@/lib/cetus";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const pair = searchParams.get("pair") || "SUI-USDC";

  try {
    const config = await getPoolConfig(pair);
    return NextResponse.json(config);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch pool config";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
