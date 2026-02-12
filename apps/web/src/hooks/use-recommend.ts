"use client";

import { useCallback } from "react";
import { useRecommendContext } from "@/context/recommend-context";
import type { FormState } from "./use-form-state";

export function useRecommend() {
  const { setData, setLoading, setError, setSelectedKey, setRequest, loading } =
    useRecommendContext();

  const analyze = useCallback(
    async (form: FormState) => {
      setLoading(true);
      setError(null);
      setData(null);
      setSelectedKey(null);
      setRequest({
        pool_id: form.poolId,
        days: form.days,
        interval: "1h",
        capital: form.capital,
        horizon_days: form.horizonDays,
      });

      try {
        const res = await fetch("/api/recommend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            pool_id: form.poolId,
            days: form.days,
            interval: "1h",
            capital: form.capital,
            horizon_days: form.horizonDays,
          }),
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.error || `Request failed (${res.status})`);
        }

        const data = await res.json();
        setData(data);
        setSelectedKey("balanced");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [setData, setLoading, setError, setSelectedKey, setRequest],
  );

  return { analyze, loading };
}
