import { z } from "zod/v4";

const envSchema = z.object({
  QUANT_SERVICE_URL: z.string().default("http://localhost:8000"),
  SUI_RPC_URL: z.string().default("https://fullnode.mainnet.sui.io:443"),
  CETUS_POOLS_API_URL: z
    .string()
    .default("https://api-sui.cetus.zone/v2/sui/stats_pools"),
  CETUS_AGGREGATOR_URL: z
    .string()
    .default("https://api-sui.cetus.zone/router_v3/find_routes"),
  CETUS_KLINE_API_URL: z.string().default(""),
  BIRDEYE_API_KEY: z.string().default(""),
  PRICE_SOURCE_DEFAULT: z
    .enum(["pool", "aggregator"])
    .default("pool"),
});

export const env = envSchema.parse({
  QUANT_SERVICE_URL: process.env.QUANT_SERVICE_URL,
  SUI_RPC_URL: process.env.SUI_RPC_URL,
  CETUS_POOLS_API_URL: process.env.CETUS_POOLS_API_URL,
  CETUS_AGGREGATOR_URL: process.env.CETUS_AGGREGATOR_URL,
  CETUS_KLINE_API_URL: process.env.CETUS_KLINE_API_URL,
  BIRDEYE_API_KEY: process.env.BIRDEYE_API_KEY,
  PRICE_SOURCE_DEFAULT: process.env.PRICE_SOURCE_DEFAULT,
});
