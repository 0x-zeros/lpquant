# Research Notebooks

These notebooks are meant to be the fastest way to start formal LP interval research.

## Setup

From `/Users/lilith/dev/web3/lpquant/services/quant`:

```bash
uv sync --extra dev --extra research
uv run jupyter lab
```

Then open:

- `notebooks/01_lp_baseline_suite.ipynb`
- logging convention: `/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md`

## What the starter notebook does

The baseline notebook:

- runs the default benchmark suite for `BTC/USDC`, `SOL/USDC`, and `SUI/USDC`
- compares `neutral/balanced`, `bullish/carry`, and `bearish/defensive`
- plots standard visual comparisons across pairs and scenarios
- saves the suite outputs under timestamped `research_runs/` bundles
- gives you one single-pair deep-dive cell block you can keep modifying

## Outputs

By default the notebook can export a full research bundle:

- `metadata.json`: run metadata, git info, and case definitions
- `summary.csv`: the top interval per case
- `rankings.csv`: the full ranking table for every case
- `failures.csv`: any pairs or routes that could not be loaded
- `cases/<case_name>/...`: per-case rankings, similar windows, and feature tails

If a Binance route is missing for a given pair, the suite keeps going and logs the failure instead of stopping the whole benchmark.
