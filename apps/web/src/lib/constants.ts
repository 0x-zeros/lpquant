export const SUPPORTED_PAIRS: Record<
  string,
  {
    poolId: string;
    binanceSymbol: string;
    coinTypeA: string;
    coinTypeB: string;
    decimalsA: number;
    decimalsB: number;
    label: string;
  }
> = {
  "SUI-USDC": {
    poolId:
      "0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd6c89f8e2571",
    binanceSymbol: "SUIUSDT",
    coinTypeA:
      "0x0000000000000000000000000000000000000000000000000000000000000002::sui::SUI",
    coinTypeB:
      "0xdba34672e30cb065b1f93e3ab55318768fd6fef66c15942c9f7cb846e2f900e7::usdc::USDC",
    decimalsA: 9,
    decimalsB: 6,
    label: "SUI / USDC",
  },
};

export const DEFAULT_PAIR = "SUI-USDC";
export const DEFAULT_INTERVAL = "1h";
