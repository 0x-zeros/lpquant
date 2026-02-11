"use client";

import useSWR from "swr";
import type { PoolsResponse } from "@/lib/types";

const fetcher = (url: string) =>
  fetch(url).then(async (res) => {
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Request failed (${res.status})`);
    }
    return res.json() as Promise<PoolsResponse>;
  });

export function usePools(limit: number, sortBy: string) {
  const { data, error, isLoading } = useSWR(
    `/api/pools?limit=${limit}&sortBy=${encodeURIComponent(sortBy)}`,
    fetcher,
  );
  return { pools: data?.pools ?? [], updatedAt: data?.updated_at, error, isLoading };
}
