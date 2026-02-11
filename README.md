# LPQuant

Concentrated liquidity LP strategy recommendation engine for Sui DEXs.

## Architecture

Monorepo with two services connected via BFF pattern:

```
Browser → Next.js App Router UI
            ↓ (POST /api/recommend)
         Next.js Route Handlers (BFF)
            ↓ parallel fetch
    ┌───────┼───────────┐
    ↓       ↓           ↓
 Birdeye  Sui RPC   Python FastAPI
 /Binance pool cfg   quant engine
 klines
```

- **Frontend** (`apps/web`): Next.js 16, React 19, shadcn/ui, TailwindCSS v4, lightweight-charts v5, next-intl (en/zh)
- **BFF** (`apps/web/src/app/api/`): Route handlers orchestrating external data (Birdeye/Binance klines + Sui RPC pool data) and forwarding to Python engine
- **Quant Engine** (`services/quant`): FastAPI + numpy/pandas — pure compute, receives klines + pool config, returns scored recommendations with backtest series

## Price Data Sources

Kline (OHLCV) data is fetched via a fallback chain:

1. **Birdeye** (primary, if `BIRDEYE_API_KEY` is configured) — supports all Sui tokens via on-chain address
2. **Binance** (fallback) — maps coin types to Binance trading pairs (e.g. SUI→SUIUSDT)

## Development

```bash
# Frontend
cd apps/web && pnpm dev          # Dev server on :3000

# Python Quant Engine
cd services/quant
uv sync && uv run uvicorn app.main:app --reload --port 8000

# Both services must run simultaneously
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BIRDEYE_API_KEY` | No | Birdeye API key for primary kline source |
| `QUANT_SERVICE_URL` | No | Python engine URL (default: `http://localhost:8000`) |
| `SUI_RPC_URL` | No | Sui fullnode RPC (default: mainnet) |

## Future Work

- **Reconstruct price from Cetus swap events**: Build a full indexer to reconstruct historical OHLCV data directly from on-chain Cetus swap events, eliminating dependency on external price APIs (Birdeye/Binance).
