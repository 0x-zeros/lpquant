"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import type { RecommendResponse } from "@/lib/types";

interface RecommendContextValue {
  data: RecommendResponse | null;
  setData: (d: RecommendResponse | null) => void;
  selectedKey: string | null;
  setSelectedKey: (k: string | null) => void;
  loading: boolean;
  setLoading: (l: boolean) => void;
  error: string | null;
  setError: (e: string | null) => void;
}

const RecommendContext = createContext<RecommendContextValue | null>(null);

export function RecommendProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <RecommendContext.Provider
      value={{
        data,
        setData,
        selectedKey,
        setSelectedKey,
        loading,
        setLoading,
        error,
        setError,
      }}
    >
      {children}
    </RecommendContext.Provider>
  );
}

export function useRecommendContext() {
  const ctx = useContext(RecommendContext);
  if (!ctx) throw new Error("useRecommendContext must be inside RecommendProvider");
  return ctx;
}
