"use client";

import { useLocale } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { Button } from "@/components/ui/button";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const toggle = () => {
    const next = locale === "en" ? "zh" : "en";
    router.replace(pathname, { locale: next });
  };

  return (
    <Button variant="ghost" size="sm" onClick={toggle}>
      {locale === "en" ? "中文" : "English"}
    </Button>
  );
}
