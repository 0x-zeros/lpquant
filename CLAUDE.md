# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Frontend (Next.js) - from root or apps/web
pnpm dev                    # Dev server on :3000
pnpm build                  # Production build
cd apps/web && pnpm lint    # ESLint

# Python Quant Engine - from services/quant
uv sync                     # Install/sync dependencies
uv run uvicorn app.main:app --reload --port 8000   # Dev server on :8000
uv run pytest               # Run tests

# Both services must run simultaneously for full functionality
```

## Architecture

Monorepo with two services connected via BFF pattern:

```
Browser → Next.js App Router UI
            ↓ (POST /api/recommend)
         Next.js Route Handlers (BFF)
            ↓ parallel fetch
    ┌───────┼───────────┐
    ↓       ↓           ↓
 Binance  Sui RPC   Python FastAPI
 klines   pool cfg   quant engine
```

**Frontend (`apps/web`)**: Next.js 16, React 19, shadcn/ui, TailwindCSS v4, lightweight-charts v5, next-intl (en/zh).

**BFF (`apps/web/src/app/api/`)**: Route handlers that orchestrate external data fetching (Binance klines + Sui RPC pool data) and forward to Python engine. In-memory TTL caching (5min klines, 1min pool).

**Quant Engine (`services/quant`)**: FastAPI + numpy/pandas. Pure compute — receives klines + pool config from BFF, returns scored recommendations with backtest series.

## Key Data Flow

`POST /api/recommend` → parallel fetch [Binance klines + Sui pool via JSON-RPC] → `POST :8000/api/v1/recommend` (Python: generate candidate ranges → align ticks → backtest each → score/rank → return top-3 + extremes with chart series)

## Important Technical Decisions

- **No Cetus SDK**: v5.4.0 is incompatible with latest @mysten/sui. Pool data fetched via direct Sui JSON-RPC (`sui_getObject` with `showContent: true`). Price derived from `sqrtPriceX64`: `(sqrtPriceX64 / 2^64)^2 * 10^(decimalsA - decimalsB)`.
- **Binance SUIUSDT** as price proxy for SUI/USDC (no SUI/USDC pair on Binance; USDT≈USDC).
- **Zod v4** imported as `zod/v4`.
- **lightweight-charts**: Must use `UTCTimestamp` type casts; `dynamic import` with `ssr: false` required.
- **Backtest is fee-free**: No on-chain fee accrual simulation (requires tick liquidity distribution data — out of scope for MVP).

## Pool Constants

SUI/USDC pool: `0xcf994611fd4c48e277ce3ffd4d4364c914af2c3cbb05f7bf6facd6c89f8e2571`, SUI decimals 9, USDC decimals 6, tick spacing 60.

## Python Engine Modules

- `engine/tick_math.py` — price↔tick conversion, tick alignment to spacing
- `engine/candidates.py` — range generation: quantile, volband, swing, extreme
- `engine/backtest.py` — concentrated liquidity LP vs HODL simulation (Uniswap v3 math)
- `engine/scoring.py` — profile-weighted scoring (conservative/balanced/aggressive) + insight generation
- `schemas.py` — Pydantic v2 request/response models (must stay in sync with `lib/types.ts`)
