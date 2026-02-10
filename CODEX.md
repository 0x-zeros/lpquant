# CODEX.md

This file provides guidance to Codex (OpenAI) when working with code in this repository.

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
```

## Architecture

Monorepo with a Next.js UI + BFF and a Python quant engine:

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

## Key Data Flow

`POST /api/recommend` → parallel fetch [Binance klines + Sui pool via JSON-RPC] → `POST :8000/api/v1/recommend`

Python: generate candidate ranges → align ticks → backtest each → score/rank → return top-3 + extremes with chart series.

## Important Technical Decisions

- No Cetus SDK: pool data fetched via Sui JSON-RPC (`sui_getObject` with `showContent: true`).
- Binance SUIUSDT used as price proxy for SUI/USDC (USDT≈USDC).
- Backtest is fee-free (no on-chain fee accrual simulation in MVP).
- Keep `services/quant/app/schemas.py` in sync with `apps/web/src/lib/types.ts`.
