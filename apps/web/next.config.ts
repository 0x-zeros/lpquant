import path from "path";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const shimPath = path.resolve(__dirname, "src/shims/mysten-graphql-latest.ts");

const nextConfig: NextConfig = {
  experimental: {
    turbo: {
      resolveAlias: {
        "@mysten/sui/graphql/schemas/latest": shimPath,
      },
    },
  },
  webpack: (config) => {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      "@mysten/sui/graphql/schemas/latest": shimPath,
    };
    return config;
  },
};

export default withNextIntl(nextConfig);
