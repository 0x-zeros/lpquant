import { env } from "./env";

function toBigInt(value: unknown): bigint | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "bigint") return value;
  if (typeof value === "number" && Number.isFinite(value)) {
    return BigInt(Math.floor(value));
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    if (/^\d+$/.test(trimmed)) return BigInt(trimmed);
    const parsed = Number(trimmed);
    if (Number.isFinite(parsed)) return BigInt(Math.floor(parsed));
  }
  if (typeof value === "object" && "toString" in value) {
    return toBigInt(value.toString());
  }
  return null;
}

function extractAmountOut(payload: Record<string, unknown>): bigint | null {
  const keys = [
    "amount_out",
    "amountOut",
    "amount_out_with_fee",
    "amountOutWithFee",
    "output_amount",
    "amount",
  ];
  for (const key of keys) {
    const amt = toBigInt(payload[key]);
    if (amt !== null) return amt;
  }
  return null;
}

export async function getAggregatorPrice(params: {
  from: string;
  to: string;
  decimalsA: number;
  decimalsB: number;
}): Promise<number | null> {
  const amountIn = BigInt(10) ** BigInt(Math.max(params.decimalsA, 0));
  const res = await fetch(env.CETUS_AGGREGATOR_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      from: params.from,
      target: params.to,
      amount: amountIn.toString(),
      byAmountIn: true,
    }),
  });

  if (!res.ok) {
    return null;
  }

  const json = await res.json();
  const routes =
    (json?.data?.routes as Record<string, unknown>[] | undefined) ??
    (json?.data as Record<string, unknown>[] | undefined) ??
    (json?.routes as Record<string, unknown>[] | undefined) ??
    [];

  const best = Array.isArray(routes) ? routes[0] : null;
  if (!best) return null;

  const amountOut = extractAmountOut(best);
  if (!amountOut) return null;

  const denomOut = 10 ** Math.max(params.decimalsB, 0);
  const denomIn = 10 ** Math.max(params.decimalsA, 0);
  const price = (Number(amountOut) / denomOut) / (Number(amountIn) / denomIn);
  if (!Number.isFinite(price) || price <= 0) return null;
  return price;
}
