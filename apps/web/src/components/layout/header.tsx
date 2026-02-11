"use client";

import { useTranslations } from "next-intl";
import { LocaleSwitcher } from "./locale-switcher";
import { ThemeToggle } from "./theme-toggle";

export function Header() {
  const t = useTranslations("header");

  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-6 py-3">
      <div className="flex items-center gap-3">
        <span className="bg-gradient-to-r from-[#00d2ff] to-[#00f5a0] bg-clip-text text-xl font-bold tracking-tight text-transparent">
          {t("title")}
        </span>
        <span className="text-sm text-muted-foreground">
          {t("subtitle")}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <LocaleSwitcher />
      </div>
    </header>
  );
}
