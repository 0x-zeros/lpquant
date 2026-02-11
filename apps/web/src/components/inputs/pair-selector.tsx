"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { usePools } from "@/hooks/use-pools";
import type { PoolSummary } from "@/lib/types";

interface PairSelectorProps {
  value: string;
  onChange: (v: string) => void;
  limit: number;
  sortBy: string;
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "n/a";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(2)}K`;
  return value.toFixed(2);
}

function PoolOption({ pool }: { pool: PoolSummary }) {
  return (
    <div className="flex w-full flex-col">
      <div className="flex items-center justify-between">
        <span className="font-medium">{pool.symbol}</span>
        <span className="text-xs text-muted-foreground">
          {(pool.fee_rate * 100).toFixed(2)}%
        </span>
      </div>
      <div className="text-xs text-muted-foreground">
        Vol {formatNumber(pool.volume_24h)} · Fees {formatNumber(pool.fees_24h)} · APR{" "}
        {pool.apr !== null && pool.apr !== undefined ? `${pool.apr.toFixed(2)}%` : "n/a"}
      </div>
    </div>
  );
}

export function PairSelector({ value, onChange, limit, sortBy }: PairSelectorProps) {
  const t = useTranslations("input");
  const { pools, isLoading, error } = usePools(limit, sortBy);

  useEffect(() => {
    if (pools.length === 0) return;
    if (!value || !pools.some((p) => p.pool_id === value)) {
      onChange(pools[0].pool_id);
    }
  }, [value, pools, onChange]);

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">{t("pair")}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select pool" />
        </SelectTrigger>
        <SelectContent>
          {isLoading && (
            <SelectItem value="loading" disabled>
              Loading pools...
            </SelectItem>
          )}
          {error && (
            <SelectItem value="error" disabled>
              Failed to load pools
            </SelectItem>
          )}
          {!isLoading &&
            !error &&
            pools.map((pool) => (
              <SelectItem key={pool.pool_id} value={pool.pool_id}>
                <PoolOption pool={pool} />
              </SelectItem>
            ))}
        </SelectContent>
      </Select>
    </div>
  );
}
