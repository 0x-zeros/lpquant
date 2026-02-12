"use client";

import { useState } from "react";
import { DEFAULT_POOL_LIMIT } from "@/lib/constants";

export interface FormState {
  poolId: string;
  days: number;
  horizonDays: number;
  capital: number;
  poolLimit: number;
  poolSortBy: string;
}

export function useFormState() {
  const [form, setForm] = useState<FormState>({
    poolId: "",
    days: 30,
    horizonDays: 7,
    capital: 10000,
    poolLimit: DEFAULT_POOL_LIMIT,
    poolSortBy: "volume_24h",
  });

  const updateField = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return { form, updateField };
}
