# LPQuant Research Roadmap

## New project definition

This repository should now be treated as a serious LP research workspace, not a hackathon demo.

The real question is no longer "which of these few candidate bands looks nice on a page?"

The real question is:

> Given a trading pair, the current price, the current market regime, and my directional view, what LP interval maximizes expected profit after accounting for range exits, inventory drift, and reallocation friction?

That means the target function should move toward:

`expected fee capture - LVR/adverse selection - impermanent loss - gas/rebalance cost - hedge/funding cost`

under explicit constraints such as:

- maximum acceptable out-of-range probability
- maximum acceptable drawdown or tail loss
- maximum acceptable rebalance frequency
- minimum acceptable capital efficiency

## Why the current architecture is no longer enough

The existing FastAPI engine is good for a demo because it:

- generates a few hand-picked interval candidates
- backtests them once
- scores them with static profile weights

But for a research system that is meant to make money, it is missing several important layers:

- no regime conditioning
- no dense search over interval width and center
- no walk-forward evaluation anchored at many historical entry points
- no explicit modeling of reset policy
- no fee-share or pool microstructure model
- no gas, hedge, funding, or LVR penalty model

So the system should evolve from a `candidate recommender` into an `LP policy lab`.

## The right project shape

For the next phase, Python should be the center of gravity.

Recommended workflow order:

1. Python library for reusable math and experiments
2. CLI / light TUI for quick screening
3. Notebook layer for hypothesis work
4. Web UI only after the research workflow is already useful

That is why this repo now includes `app.research`, a research-first module separate from the old API route.

## First research loop

The first useful loop is:

1. Pull pair history from Binance or construct it from Binance ratios
2. Compute the current market regime from a lookback window
3. Find historical windows that look similar to the current regime
4. Sweep many interval widths and center offsets
5. Run walk-forward backtests from those similar historical windows
6. Rank intervals by a research objective such as `balanced`, `carry`, or `defensive`
7. Export the full ranking table to CSV and keep iterating in notebooks

This is intentionally more useful than the old "generate three strategies and choose one" approach.

## How to think about the LP problem

The LP interval problem is very close to order-book market making, but not identical.

A useful mapping is:

- interval center ~= reservation price
- interval width ~= quoting spread
- reset policy ~= quote update policy
- LP inventory drift ~= market maker inventory risk
- out-of-range event ~= losing both-sided quoting ability

This is an inference from market microstructure rather than a direct theorem, but it is a very productive mental model for research.

## Research priorities

### Phase 1: do this now

- CEX-only price history
- regime features: trend, volatility, downside volatility, drawdown, RSI, distance from moving average
- walk-forward interval sweeps
- objective-function ranking
- notebook-driven analysis

### Phase 2: add next

- DEX pool state history
- realized pool volume and fee-share estimation
- tick-level or tick-density-aware modeling
- gas and rebalance-cost accounting
- multi-chain comparison for the same pair

### Phase 3: add once the simulator is trustworthy

- hedge leg on CEX perpetuals or spot
- funding-rate-aware LP + hedge studies
- LVR proxy and adverse-selection penalties
- position reset policies and trigger optimization

## Where AI should and should not be used

AI can help, but it should enter in the right order.

### Good near-term uses

- time-series forecasting models as one input into interval placement
- regime clustering and similarity search
- surrogate models that approximate expensive backtests
- experiment summarization and research note generation

### Uses to delay

- full reinforcement learning before the simulator is realistic
- LLM-based "pick a band" decision systems
- fancy agents on top of weak market assumptions

The risk with jumping straight to RL is that it will overfit a simplified reward function and teach you the wrong policy.

## What the literature suggests

Three ideas from recent LP literature matter immediately:

- Strategic liquidity provision is fundamentally dynamic: narrow bands pay more if price stays inside, but resets and reallocation costs matter. Source: [Strategic Liquidity Provision in Uniswap v3](https://arxiv.org/abs/2106.12033)
- LP interval choice can be treated as an online learning problem instead of a one-shot static optimizer. Source: [Uniswap Liquidity Provision: An Online Learning Approach](https://research.google/pubs/uniswap-liquidity-provision-an-online-learning-approach/)
- LP PnL is not just fees versus impermanent loss; adverse selection and stale-price pickup matter. Source: [Automated Market Making and Loss-Versus-Rebalancing](https://arxiv.org/abs/2208.06046)

For AI specifically, modern time-series foundation models are promising as forecasting inputs, not as full LP policies by themselves:

- [Chronos: Learning the Language of Time Series](https://arxiv.org/abs/2403.07815)
- [A decoder-only foundation model for time-series forecasting](https://proceedings.mlr.press/v235/das24c.html)

## Immediate next experiments

For now, the most valuable experiments are probably:

1. `BTC/USDC` on `4h` and `1d`
2. `SOL/USDC` on `4h`
3. `SUI/USDC` on `4h`

For each pair, run:

- neutral view + balanced objective
- bullish view + carry objective
- bearish view + defensive objective

Then compare:

- best width
- best center shift
- no-exit rate
- fee proxy
- p10 LP-vs-HODL
- downside breach rate

If the rankings are unstable across neighboring samples, that is already a strong research result: it means the policy needs better regime conditioning or stricter risk constraints.

## Example command

From `services/quant`:

```bash
uv run python -m app.research.cli \
  --pair SUI/USDC \
  --interval 4h \
  --days 365 \
  --lookback-bars 90 \
  --horizon-bars 30 \
  --view neutral \
  --objective balanced \
  --fee-rate 0.0025 \
  --output research_runs/sui_usdc_4h.csv
```

## Notebook entry point

If you want to move from one-off CLI runs into repeatable research sessions, start here:

- Notebook: [/Users/lilith/dev/web3/lpquant/services/quant/notebooks/01_lp_baseline_suite.ipynb](/Users/lilith/dev/web3/lpquant/services/quant/notebooks/01_lp_baseline_suite.ipynb)
- Notebook notes: [/Users/lilith/dev/web3/lpquant/services/quant/notebooks/README.md](/Users/lilith/dev/web3/lpquant/services/quant/notebooks/README.md)
- Experiment logging: [/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md](/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md)

The notebook imports the default `BTC/USDC`, `SOL/USDC`, and `SUI/USDC` baseline suite from `app.research.benchmarks`, runs the full matrix, and saves clean CSV outputs under `research_runs/`.

## Important caveat

The current research module still uses a fee proxy, not true realized LP fee share.

So the new tool is already useful for screening and hypothesis generation, but it is **not** yet a production-grade live trading policy engine.
