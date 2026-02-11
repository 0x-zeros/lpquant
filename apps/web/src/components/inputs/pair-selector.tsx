"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { Copy, Check } from "lucide-react";
import { InfoTip } from "@/components/ui/info-tip";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
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

function formatFeeRate(decimal: number): string {
  const pct = decimal * 100;
  return `${parseFloat(pct.toFixed(4))}%`;
}

function formatApr(apr: number | null | undefined): string {
  if (apr === null || apr === undefined || !Number.isFinite(apr)) return "n/a";
  return `${(apr * 100).toFixed(2)}%`;
}

function truncateAddress(addr: string): string {
  if (addr.length <= 14) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

function TokenIcon({
  src,
  symbol,
  className,
}: {
  src?: string | null;
  symbol: string;
  className?: string;
}) {
  const [error, setError] = useState(false);
  const onError = useCallback(() => setError(true), []);

  if (!src || error) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded-full bg-current/15 text-[10px] font-bold ${className ?? ""}`}
      >
        {symbol.slice(0, 2)}
      </span>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={symbol}
      className={`rounded-full ${className ?? ""}`}
      onError={onError}
    />
  );
}

function TokenPairIcon({ pool }: { pool: PoolSummary }) {
  const symbolA = pool.symbol.split("/")[0] ?? "";
  const symbolB = pool.symbol.split("/")[1] ?? "";

  return (
    <span className="relative mr-1.5 inline-flex h-6 w-9 shrink-0 items-center">
      <TokenIcon
        src={pool.logo_url_a}
        symbol={symbolA}
        className="absolute left-0 z-10 h-5 w-5 ring-1 ring-background"
      />
      <TokenIcon
        src={pool.logo_url_b}
        symbol={symbolB}
        className="absolute left-3 h-5 w-5 ring-1 ring-background"
      />
    </span>
  );
}

function PoolOption({ pool }: { pool: PoolSummary }) {
  return (
    <div className="flex w-full flex-col">
      <div className="flex items-center justify-between">
        <span className="flex items-center font-medium">
          <TokenPairIcon pool={pool} />
          {pool.symbol}
        </span>
        <span className="text-xs opacity-60">
          {formatFeeRate(pool.fee_rate)}
        </span>
      </div>
      <div className="text-xs opacity-60">
        Vol {formatNumber(pool.volume_24h)} · Fees {formatNumber(pool.fees_24h)} · APR{" "}
        {formatApr(pool.apr)}
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    },
    [text],
  );

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-1 inline-flex shrink-0 items-center opacity-50 hover:opacity-100"
    >
      {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

function AddressLink({
  address,
  href,
}: {
  address: string;
  href: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="opacity-60 hover:opacity-100 hover:underline"
    >
      {truncateAddress(address)}
    </a>
  );
}

function PoolTooltipContent({ pool }: { pool: PoolSummary }) {
  const symbolA = pool.symbol.split("/")[0] ?? "";
  const symbolB = pool.symbol.split("/")[1] ?? "";
  return (
    <div className="space-y-1.5 text-xs">
      <div className="flex items-center">
        <span className="opacity-60">Pool</span>
        <span className="flex-1" />
        <AddressLink
          address={pool.pool_id}
          href={`https://suivision.xyz/object/${pool.pool_id}`}
        />
        <CopyButton text={pool.pool_id} />
      </div>
      {pool.coin_type_a && (
        <div className="flex items-center gap-1.5">
          <TokenIcon src={pool.logo_url_a} symbol={symbolA} className="h-4 w-4" />
          <span>{symbolA}</span>
          <span className="flex-1" />
          <AddressLink
            address={pool.coin_type_a}
            href={`https://suivision.xyz/coin/${pool.coin_type_a}`}
          />
          <CopyButton text={pool.coin_type_a} />
        </div>
      )}
      {pool.coin_type_b && (
        <div className="flex items-center gap-1.5">
          <TokenIcon src={pool.logo_url_b} symbol={symbolB} className="h-4 w-4" />
          <span>{symbolB}</span>
          <span className="flex-1" />
          <AddressLink
            address={pool.coin_type_b}
            href={`https://suivision.xyz/coin/${pool.coin_type_b}`}
          />
          <CopyButton text={pool.coin_type_b} />
        </div>
      )}
      {pool.tvl != null && (
        <div className="flex items-center">
          <span className="opacity-60">TVL</span>
          <span className="flex-1" />
          <span>${formatNumber(pool.tvl)}</span>
        </div>
      )}
    </div>
  );
}

export function PairSelector({ value, onChange, limit, sortBy }: PairSelectorProps) {
  const t = useTranslations("input");
  const tt = useTranslations("tooltips");
  const { pools, isLoading, error } = usePools(limit, sortBy);

  useEffect(() => {
    if (pools.length === 0) return;
    if (!value || !pools.some((p) => p.pool_id === value)) {
      onChange(pools[0].pool_id);
    }
  }, [value, pools, onChange]);

  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium flex items-center gap-1">
        {t("pair")}
        <InfoTip content={tt("pair")} />
      </label>
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
            pools.map((pool, index) => (
              <SelectItem
                key={pool.pool_id}
                value={pool.pool_id}
                className={index > 0 ? "border-t border-border" : ""}
              >
                <TooltipProvider delayDuration={300}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div>
                        <PoolOption pool={pool} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <PoolTooltipContent pool={pool} />
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </SelectItem>
            ))}
        </SelectContent>
      </Select>
    </div>
  );
}
