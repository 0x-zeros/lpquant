import { z } from "zod/v4";

const envSchema = z.object({
  QUANT_SERVICE_URL: z.string().default("http://localhost:8000"),
});

export const env = envSchema.parse({
  QUANT_SERVICE_URL: process.env.QUANT_SERVICE_URL,
});
