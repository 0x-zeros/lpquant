"use client";

import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

export function LocaleSwitcher() {
  const pathname = usePathname();

  // Detect current locale from URL
  const isZh = pathname.startsWith("/zh");
  const currentLocale = isZh ? "zh" : "en";

  const toggle = () => {
    const targetLocale = currentLocale === "en" ? "zh" : "en";
    // Strip current locale prefix if present, then add new one
    let basePath = pathname;
    if (basePath.startsWith("/en")) basePath = basePath.slice(3) || "/";
    if (basePath.startsWith("/zh")) basePath = basePath.slice(3) || "/";
    window.location.href = `/${targetLocale}${basePath}`;
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={toggle}
      className="border-[rgba(255,255,255,0.15)] text-[#8892b0] hover:border-[#00d2ff] hover:text-[#00d2ff]"
    >
      {currentLocale === "en" ? "中文" : "EN"}
    </Button>
  );
}
