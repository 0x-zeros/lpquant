"use client";

import { RecommendProvider } from "@/context/recommend-context";
import { Header } from "@/components/layout/header";
import { Dashboard } from "@/components/layout/dashboard";
import { InputPanel } from "@/components/inputs/input-panel";
import { CardList } from "@/components/cards/card-list";

export default function Home() {
  return (
    <RecommendProvider>
      <Header />
      <Dashboard
        inputPanel={<InputPanel />}
        cardList={<CardList />}
      />
    </RecommendProvider>
  );
}
