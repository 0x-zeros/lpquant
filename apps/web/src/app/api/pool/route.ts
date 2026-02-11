import { NextResponse } from "next/server";
import { getPoolConfig } from "@/lib/cetus";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const poolId = searchParams.get("pool_id");

  try {
    if (!poolId) {
      return NextResponse.json({ error: "pool_id is required" }, { status: 400 });
    }
    const config = await getPoolConfig(poolId);
    return NextResponse.json(config);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch pool config";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
