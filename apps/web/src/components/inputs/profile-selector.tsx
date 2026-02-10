"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const PROFILES = [
  { value: "conservative", label: "Conservative" },
  { value: "balanced", label: "Balanced" },
  { value: "aggressive", label: "Aggressive" },
] as const;

interface ProfileSelectorProps {
  value: string;
  onChange: (v: "conservative" | "balanced" | "aggressive") => void;
}

export function ProfileSelector({ value, onChange }: ProfileSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium">Risk Profile</label>
      <Tabs
        value={value}
        onValueChange={(v) =>
          onChange(v as "conservative" | "balanced" | "aggressive")
        }
      >
        <TabsList className="w-full">
          {PROFILES.map((p) => (
            <TabsTrigger key={p.value} value={p.value} className="flex-1">
              {p.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
    </div>
  );
}
