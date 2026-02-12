"use client";

import { useEffect, type ReactNode } from "react";
import { useTranslations } from "next-intl";
import { X } from "lucide-react";
import { useRecommendContext } from "@/context/recommend-context";
import { BalancedCard } from "@/components/cards/balanced-card";
import { NarrowCard } from "@/components/cards/narrow-card";
import { BacktestCard } from "@/components/cards/backtest-card";
import { DetailPanel } from "./detail-panel";

interface DetailModalProps {
  open: boolean;
  selectedKey: string | null;
  onClose: () => void;
}

export function DetailModal({ open, selectedKey, onClose }: DetailModalProps) {
  const t = useTranslations("detail");
  const { data } = useRecommendContext();

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open || !data || !selectedKey) return null;

  const quoteSymbol = data.quote_symbol;
  const quoteIsStable = data.quote_is_stable;

  let card: ReactNode = null;
  if (selectedKey === "balanced") {
    card = (
      <BalancedCard
        candidate={data.balanced}
        selected
        currentPrice={data.current_price}
        quoteSymbol={quoteSymbol}
        quoteIsStable={quoteIsStable}
        onClick={() => {}}
      />
    );
  } else if (selectedKey === "narrow") {
    card = (
      <NarrowCard
        candidate={data.narrow}
        selected
        currentPrice={data.current_price}
        quoteSymbol={quoteSymbol}
        quoteIsStable={quoteIsStable}
        onClick={() => {}}
      />
    );
  } else if (selectedKey === "best_backtest") {
    card = (
      <BacktestCard
        candidate={data.best_backtest}
        selected
        currentPrice={data.current_price}
        quoteSymbol={quoteSymbol}
        quoteIsStable={quoteIsStable}
        onClick={() => {}}
      />
    );
  }

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        aria-label="Close"
      />
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="relative z-10 w-full max-w-6xl overflow-hidden rounded-2xl border border-white/10 bg-[#0b0f1e] shadow-2xl">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div className="text-sm text-muted-foreground">{data.pool_symbol}</div>
            <div className="text-base font-semibold">{t("title")}</div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-2 text-muted-foreground hover:text-foreground"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="max-h-[80vh] overflow-y-auto p-4">
            <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
              <div className="space-y-4">{card}</div>
              <DetailPanel />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
