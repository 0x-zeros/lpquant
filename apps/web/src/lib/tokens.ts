export interface TokenInfo {
  canonicalSymbol: string;
  isStable: boolean;
}

const STABLE_QUOTES = new Set(["USDC", "USDT", "FDUSD", "BUSD"]);

/** Known Sui coin type → token info mapping */
const TOKEN_REGISTRY: Record<string, TokenInfo> = {
  // Native SUI
  "0x2::sui::SUI": { canonicalSymbol: "SUI", isStable: false },
  // Native Circle USDC
  "0xdba34672e30cb065b1f93e3ab55318768fd6fef66c15942c9f7cb846e2f900e7::usdc::USDC": {
    canonicalSymbol: "USDC",
    isStable: true,
  },
  // Wormhole wUSDC
  "0x5d4b302506645c37ff133b98c4b50a5ae14841659738d6d733d59d0d217a93bf::coin::COIN": {
    canonicalSymbol: "USDC",
    isStable: true,
  },
  // Wormhole USDT
  "0xc060006111016b8a020ad5b33834984a437aaa7d3c74c18e09a95d48aceab08c::coin::COIN": {
    canonicalSymbol: "USDT",
    isStable: true,
  },
  // LayerZero WBTC
  "0x0041f2209cff387c2d4ef9316e38f1275e0db04ef39a3df55576d10ba3a10140::wbtc::WBTC": {
    canonicalSymbol: "BTC",
    isStable: false,
  },
  // Wormhole wETH
  "0xaf8cd5edc19c4512f4259f0bee101a40d41ebed738ade5874359610ef8eeced5::coin::COIN": {
    canonicalSymbol: "ETH",
    isStable: false,
  },
  // Wormhole SOL
  "0xb7844e289a8410e50fb3ca730d5c1f5e0c8c0a0b47e28e90d99e48f4e05e6a6::coin::COIN": {
    canonicalSymbol: "SOL",
    isStable: false,
  },
};

function normalizeSymbol(raw: string | undefined): string {
  if (!raw) return "";
  const symbol = raw.toUpperCase().replace(/\s+/g, "");
  if (symbol === "WETH") return "ETH";
  if (symbol === "WBTC") return "BTC";
  return symbol;
}

function shortType(coinType: string | undefined): string {
  if (!coinType) return "";
  const parts = coinType.split("::");
  return normalizeSymbol(parts[parts.length - 1]);
}

/** Resolve a Sui coin type to canonical token info */
export function resolveToken(coinType: string): TokenInfo {
  const info = TOKEN_REGISTRY[coinType];
  if (info) return info;

  const symbol = shortType(coinType);
  return {
    canonicalSymbol: symbol,
    isStable: STABLE_QUOTES.has(symbol),
  };
}

export function isStableCoin(coinType: string): boolean {
  return resolveToken(coinType).isStable;
}

export type PricingSide = "A" | "B";

export interface BaseQuoteSelection {
  baseCoinType: string;
  quoteCoinType: string;
  baseSymbol: string;
  quoteSymbol: string;
  baseSide: PricingSide;
  quoteSide: PricingSide;
  quoteRank: number;
}

function quoteRank(symbol: string, isStable: boolean): number {
  if (isStable) return 0;
  switch (symbol) {
    case "SUI":
      return 1;
    case "BTC":
      return 2;
    case "ETH":
      return 3;
    case "SOL":
      return 4;
    default:
      return Number.POSITIVE_INFINITY;
  }
}

export function selectBaseQuote(
  coinTypeA: string,
  coinTypeB: string,
): BaseQuoteSelection {
  const tokenA = resolveToken(coinTypeA);
  const tokenB = resolveToken(coinTypeB);
  const rankA = quoteRank(tokenA.canonicalSymbol, tokenA.isStable);
  const rankB = quoteRank(tokenB.canonicalSymbol, tokenB.isStable);

  const baseA: BaseQuoteSelection = {
    baseCoinType: coinTypeA,
    quoteCoinType: coinTypeB,
    baseSymbol: tokenA.canonicalSymbol,
    quoteSymbol: tokenB.canonicalSymbol,
    baseSide: "A",
    quoteSide: "B",
    quoteRank: rankB,
  };
  const baseB: BaseQuoteSelection = {
    baseCoinType: coinTypeB,
    quoteCoinType: coinTypeA,
    baseSymbol: tokenB.canonicalSymbol,
    quoteSymbol: tokenA.canonicalSymbol,
    baseSide: "B",
    quoteSide: "A",
    quoteRank: rankA,
  };

  if (rankA === rankB) {
    return baseA;
  }

  return rankA < rankB ? baseB : baseA;
}

export function isStableSymbol(symbol: string): boolean {
  return STABLE_QUOTES.has(symbol);
}

/** Derive Binance trading pair symbol from two coin types. Returns null if cannot determine. */
export function deriveBinanceSymbol(
  coinTypeA: string,
  coinTypeB: string,
): string | null {
  const symbolA = resolveToken(coinTypeA).canonicalSymbol;
  const symbolB = resolveToken(coinTypeB).canonicalSymbol;
  if (!symbolA || !symbolB) return null;
  if (STABLE_QUOTES.has(symbolB)) return `${symbolA}${symbolB}`;
  if (STABLE_QUOTES.has(symbolA)) return `${symbolB}${symbolA}`;
  return `${symbolA}USDT`;
}

export function deriveBinanceSymbolForPair(
  baseCoinType: string,
  quoteCoinType: string,
): string | null {
  const baseSymbol = resolveToken(baseCoinType).canonicalSymbol;
  const quoteSymbol = resolveToken(quoteCoinType).canonicalSymbol;
  if (!baseSymbol || !quoteSymbol) return null;
  return `${baseSymbol}${quoteSymbol}`;
}

export function deriveBinanceUsdSymbol(coinType: string): string | null {
  const symbol = resolveToken(coinType).canonicalSymbol;
  if (!symbol) return null;
  if (STABLE_QUOTES.has(symbol)) return `${symbol}USDT`;
  return `${symbol}USDT`;
}

/** Return the address Birdeye expects (raw coin type) */
export function toBirdeyeAddress(coinType: string): string {
  return coinType;
}

/** Resolve canonical symbol from coin type (for display) */
export function resolveSymbol(coinType: string): string {
  return resolveToken(coinType).canonicalSymbol;
}
