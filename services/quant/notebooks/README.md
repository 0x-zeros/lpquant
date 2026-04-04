# Research Notebooks / 研究笔记

这些 notebooks 的目标，是让你最快进入正式的 LP interval research workflow。

## Setup

在 `/Users/lilith/dev/web3/lpquant/services/quant` 目录下运行：

```bash
uv sync --extra dev --extra research
uv run jupyter lab
```

然后打开：

- `notebooks/01_lp_baseline_suite.ipynb`
- `notebooks/02_coverage_constrained_interval.ipynb`
- logging convention: `/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md`

## Starter notebook 会做什么

baseline notebook 会：

- 运行 `BTC/USDC`、`SOL/USDC`、`SUI/USDC` 的默认 benchmark suite
- 比较 `neutral/balanced`、`bullish/carry`、`bearish/defensive`
- 画出标准化的 pair / scenario 对比图
- 把 suite 输出保存到带 timestamp 的 `research_runs/` bundle
- 提供一个 single-pair deep-dive 区块，方便你继续改

`coverage constrained` notebook 会：

- 固定一个 pair，比较多个 `holding period`
- 只研究一个目标：在 coverage 约束下找到最窄价格区间
- 更适合 month / two-month / one-year 这种 period-based 区间研究

## 输出内容

默认会导出完整的 research bundle：

- `metadata.json`：run metadata、git info、case definitions
- `summary.csv`：每个 case 的 top interval
- `rankings.csv`：所有 case 的完整 ranking table
- `failures.csv`：未能加载的 pair 或 route
- `cases/<case_name>/...`：每个 case 的 rankings、similar windows、feature tail

如果某个 pair 在 Binance route 上拿不到数据，suite 不会整体中断，而是把失败记录到日志里继续跑后面的 case。
