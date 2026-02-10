export const SUPPORTED_PAIRS: Record<
  string,
  {
    poolIds: string[];
    binanceSymbol: string;
    coinTypeA: string;
    coinTypeB: string;
    decimalsA: number;
    decimalsB: number;
    label: string;
  }
> = {
  "SUI-USDC": {
    poolIds: [
      "0x51e883ba7c0b566a26cbc8a94cd33eb0abd418a77cc1e60ad22fd9b1f29cd2ab",
      "0xb8d7d9e66a60c239e7a60110efcf8de6c705580ed924d0dde141f4a0e2c90105",
      "0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd6c89f8e2571",
    ],
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
