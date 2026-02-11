"use client";

import { useCallback } from "react";
import { useRecommendContext } from "@/context/recommend-context";
import type { FormState } from "./use-form-state";

export function useRecommend() {
  const { setData, setLoading, setError, setSelectedKey, loading } =
    useRecommendContext();

  const analyze = useCallback(
    async (form: FormState) => {
      setLoading(true);
      setError(null);
      setData(null);
      setSelectedKey(null);

      try {
        const res = await fetch("/api/recommend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pool_id: form.poolId,
            days: form.days,
            interval: "1h",
            profile: form.profile,
            capital: form.capital,
            strategies: form.strategies,
          }),
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.error || `Request failed (${res.status})`);
        }

        const data = await res.json();
        setData(data);
        setSelectedKey("top1");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [setData, setLoading, setError, setSelectedKey],
  );

  return { analyze, loading };
}
