# Experiment Logging / 实验日志规范

## 目标

每一次正式的 research run，都应该留下一个可复现的 artifact bundle，而不只是 notebook 截图或者随手导出的一个 CSV。

标准输出目录建议放在：

`/Users/lilith/dev/web3/lpquant/services/quant/research_runs/<timestamp>_<label>/`

例如：

`/Users/lilith/dev/web3/lpquant/services/quant/research_runs/20260403T120000Z_baseline_suite/`

## 每次 run 至少要保存什么

最少应保存：

- 精确的 study request 或 benchmark case matrix
- 当前 regime snapshot
- best-ranked interval
- 完整 rankings table
- similar historical windows
- runtime metadata，例如 git branch / commit

因此现在研究工具会默认保存：

- `metadata.json`
- `summary.csv`
- `rankings.csv`
- `failures.csv`
- `cases/<case_name>/metadata.json`
- `cases/<case_name>/rankings.csv`
- `cases/<case_name>/similar_windows.csv`
- `cases/<case_name>/feature_tail.csv`

## 命名规范

目录名使用 timestamp + 短 label：

- `baseline_suite`
- `sui_4h_bullish`
- `btc_1d_defensive_reset_test`

一个好的 label 应该是：

- 短
- 明确
- 能反映这次 hypothesis 在测什么

## Notebook 工作流

在 notebook 里，推荐固定使用下面的顺序：

1. 用 `create_experiment_dir("research_runs", "baseline_suite")` 创建新的 run directory
2. 用 `save_benchmark_suite(...)` 保存完整 benchmark bundle
3. 用 `save_study_artifacts(...)` 保存 single-pair deep dive
4. 补一段简短的 plain-language note，说明这次和上一次相比改了什么

## Run 之间重点比较什么

判断一个新想法是不是真的有用，最快的方法通常是和上一轮对比这些字段：

- `width_pct`
- `center_offset_pct`
- `mean_fee_proxy_bps`
- `no_exit_rate`
- `p10_lp_vs_hodl_pct`
- `downside_breach_rate`
- `mean_max_drawdown_pct`

如果新 run 只是把某一个指标拉高了，但 tail metrics 明显变差，就应该明确记在日志里，而不是把它当成 win。

## 一条很重要的纪律

不要覆盖旧 run。

如果一个 hypothesis 值得测，它就值得拥有一个新的 run directory。  
你的 experiment history 本身就是有价值的 research data。
