"use client";

import { useState } from "react";

export interface FormState {
  pair: string;
  days: number;
  profile: "conservative" | "balanced" | "aggressive";
  strategies: string[];
  capital: number;
}

export function useFormState() {
  const [form, setForm] = useState<FormState>({
    pair: "SUI-USDC",
    days: 30,
    profile: "balanced",
    strategies: ["quantile", "volband", "swing"],
    capital: 10000,
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
