"use client";

import type { ReactNode } from "react";

interface DashboardProps {
  inputPanel: ReactNode;
  cardList: ReactNode;
  detailPanel: ReactNode;
}

export function Dashboard({ inputPanel, cardList, detailPanel }: DashboardProps) {
  return (
    <div className="grid h-[calc(100vh-57px)] grid-cols-1 gap-4 overflow-hidden p-4 lg:grid-cols-[320px_1fr_400px]">
      <aside className="overflow-y-auto">{inputPanel}</aside>
      <main className="overflow-y-auto">{cardList}</main>
      <aside className="overflow-y-auto">{detailPanel}</aside>
    </div>
  );
}
