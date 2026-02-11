import { NextResponse } from "next/server";
import { getPoolsSummary } from "@/lib/cetus";
import { DEFAULT_POOL_LIMIT, MAX_POOL_LIMIT } from "@/lib/constants";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limitRaw = searchParams.get("limit");
  const sortBy = searchParams.get("sortBy") || "volume_24h";

  const limit = Math.min(
    Math.max(parseInt(limitRaw || String(DEFAULT_POOL_LIMIT), 10) || DEFAULT_POOL_LIMIT, 1),
    MAX_POOL_LIMIT,
  );

  try {
    const pools = await getPoolsSummary({ limit, sortBy });
    return NextResponse.json({
      pools,
      updated_at: Date.now(),
      sort_by: sortBy,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to fetch pools";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
