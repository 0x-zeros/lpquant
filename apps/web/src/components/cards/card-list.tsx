"use client";

import { useRecommendContext } from "@/context/recommend-context";
import { RecommendationCard } from "./recommendation-card";
import { ExtremeCard } from "./extreme-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export function CardList() {
  const { data, loading, error, selectedKey, setSelectedKey } =
    useRecommendContext();

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-destructive font-medium">Error</p>
          <p className="text-muted-foreground mt-1 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-48 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground text-sm">
          Configure parameters and click Analyze to get recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Top Recommendations</h2>
      {data.top3.map((c, i) => (
        <RecommendationCard
          key={`top${i + 1}`}
          candidate={c}
          rank={i + 1}
          selected={selectedKey === `top${i + 1}`}
          onClick={() => setSelectedKey(`top${i + 1}`)}
        />
      ))}

      <Separator />
      <h2 className="text-lg font-semibold">Extreme Ranges</h2>

      <ExtremeCard
        candidate={data.extreme_2pct}
        label="2% Range"
        selected={selectedKey === "extreme_2pct"}
        onClick={() => setSelectedKey("extreme_2pct")}
      />
      <ExtremeCard
        candidate={data.extreme_5pct}
        label="5% Range"
        selected={selectedKey === "extreme_5pct"}
        onClick={() => setSelectedKey("extreme_5pct")}
      />
    </div>
  );
}
