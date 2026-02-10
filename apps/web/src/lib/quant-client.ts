import { env } from "./env";
import type { RecommendResponse } from "./types";

interface QuantPayload {
  klines: number[][];
  current_price: number;
  tick_spacing: number;
  fee_rate: number;
  profile: string;
  capital_usd: number;
  strategies: string[];
}

export async function callRecommend(
  payload: QuantPayload,
): Promise<RecommendResponse> {
  const res = await fetch(`${env.QUANT_SERVICE_URL}/api/v1/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Quant engine error (${res.status}): ${text}`);
  }

  return res.json();
}
