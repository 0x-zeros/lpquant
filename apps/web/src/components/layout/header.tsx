"use client";

export function Header() {
  return (
    <header className="flex items-center justify-between border-b px-6 py-3">
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold tracking-tight">LPQuant</span>
        <span className="text-muted-foreground text-sm">
          Cetus CLMM Range Recommender
        </span>
      </div>
      <div id="locale-switcher-slot" />
    </header>
  );
}
