export const DEFAULT_INTERVAL = "1h";
export const DEFAULT_POOL_LIMIT = 5;
export const MAX_POOL_LIMIT = 50;
export const POOL_SORT_OPTIONS = [
  { value: "volume_24h", labelKey: "sortVolume" as const },
  { value: "fees_24h", labelKey: "sortFees" as const },
  { value: "apr", labelKey: "sortApr" as const },
  { value: "tvl", labelKey: "sortTvl" as const },
];
