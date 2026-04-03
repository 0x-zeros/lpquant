# Experiment Logging

## Goal

Every serious research run should leave behind a reproducible artifact bundle, not just a screenshot or one CSV copied out of a notebook.

The standard output location is:

`/Users/lilith/dev/web3/lpquant/services/quant/research_runs/<timestamp>_<label>/`

Example:

`/Users/lilith/dev/web3/lpquant/services/quant/research_runs/20260403T120000Z_baseline_suite/`

## What to save for every run

At minimum, every run should capture:

- the exact study request or benchmark case matrix
- current regime snapshot
- best-ranked interval
- full rankings table
- similar historical windows
- runtime metadata such as git branch and commit

That is why the research helpers now save:

- `metadata.json`
- `summary.csv`
- `rankings.csv`
- `failures.csv`
- `cases/<case_name>/metadata.json`
- `cases/<case_name>/rankings.csv`
- `cases/<case_name>/similar_windows.csv`
- `cases/<case_name>/feature_tail.csv`

## Naming convention

Use timestamped directories with short labels:

- `baseline_suite`
- `sui_4h_bullish`
- `btc_1d_defensive_reset_test`

Good labels are short, specific, and reflect the hypothesis being tested.

## Notebook workflow

Inside notebooks, prefer this pattern:

1. Create a run directory with `create_experiment_dir("research_runs", "baseline_suite")`
2. Save the full benchmark bundle with `save_benchmark_suite(...)`
3. Save any single-pair deep-dive with `save_study_artifacts(...)`
4. Add a short plain-language note describing what changed versus the previous run

## What to compare across runs

The fastest way to tell whether a new idea is actually useful is to compare these fields against the prior run:

- `width_pct`
- `center_offset_pct`
- `mean_fee_proxy_bps`
- `no_exit_rate`
- `p10_lp_vs_hodl_pct`
- `downside_breach_rate`
- `mean_max_drawdown_pct`

If the new run only improves one metric while making the tail metrics much worse, log that explicitly instead of treating the run as a win.

## Important discipline

Do not overwrite old runs.

If a new hypothesis is worth testing, it is worth logging as a new run directory. The time series of your experiments is itself valuable research data.
