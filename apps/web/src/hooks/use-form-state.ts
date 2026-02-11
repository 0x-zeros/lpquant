"use client";

import { useState } from "react";
import { DEFAULT_POOL_LIMIT } from "@/lib/constants";

export interface FormState {
  poolId: string;
  days: number;
  profile: "conservative" | "balanced" | "aggressive";
  strategies: string[];
  capital: number;
  poolLimit: number;
  poolSortBy: string;
}

export function useFormState() {
  const [form, setForm] = useState<FormState>({
    poolId: "",
    days: 30,
    profile: "balanced",
    strategies: ["quantile", "volband", "swing"],
    capital: 10000,
    poolLimit: DEFAULT_POOL_LIMIT,
    poolSortBy: "volume_24h",
  });

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const toggleStrategy = (s: string) => {
    setForm((prev) => {
      const has = prev.strategies.includes(s);
      return {
        ...prev,
        strategies: has
          ? prev.strategies.filter((x) => x !== s)
          : [...prev.strategies, s],
      };
    });
  };

  return { form, updateField, toggleStrategy };
}
