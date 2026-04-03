# LPQuant Research Roadmap / 研究路线

## 项目重新定义

这个仓库现在应该被当成一个正式的 LP research workspace，而不是 hackathon demo。

我们真正要回答的问题，不再是：

“这几个 candidate band 哪个在页面上看起来更合理？”

而是：

> 给定一个 trading pair、当前价格、当前 market regime，以及我的 directional view，什么样的 LP interval 能在控制风险的前提下，把 expected profit 做到最好？

更贴近赚钱目标的 target function 应该逐步靠近：

`expected fee capture - LVR/adverse selection - impermanent loss - gas/rebalance cost - hedge/funding cost`

同时加上明确的约束，例如：

- 最大可接受的 out-of-range probability
- 最大可接受的 drawdown / tail loss
- 最大可接受的 rebalance frequency
- 最低可接受的 capital efficiency

## 为什么现有结构不够

旧的 FastAPI engine 很适合 demo，因为它做的是：

- 生成少量 hand-picked interval candidates
- 对这些 candidates 做一次 backtest
- 用静态 profile weights 打分

但如果这个系统的目标是赚钱，那它至少还缺下面这些层：

- regime conditioning
- 对 interval width 和 center 的 dense search
- 基于很多历史起点的 walk-forward evaluation
- 明确的 reset policy modeling
- fee share / pool microstructure modeling
- gas、hedge、funding、LVR penalty

所以系统定位应该从 `candidate recommender` 升级成 `LP policy lab`。

## 推荐的项目形态

下一阶段，Python 应该是主轴。

推荐工作流顺序：

1. Python library，承载 reusable math 和 experiments
2. CLI / light TUI，用来快速筛选
3. notebook layer，用来做 hypothesis work
4. Web UI 放到后面，等研究流程已经足够有用再说

这也是为什么仓库里现在新增了 `app.research`，把研究层从旧 API route 里拆开。

## 第一阶段 research loop

当前最有价值的一轮研究循环是：

1. 从 Binance 拉 pair history，或者用 Binance ratio 构造价格序列
2. 用 lookback window 计算当前 market regime
3. 找历史上与当前 regime 相似的窗口
4. 扫描多组 interval width 和 center offset
5. 对这些历史相似窗口做 walk-forward backtest
6. 按 `balanced`、`carry`、`defensive` 这类 objective 排序
7. 导出完整 ranking table 到 CSV，继续在 notebook 里深挖

这比旧的“生成三类策略再选一个”更像真正的研究工作。

## 如何理解 LP interval 问题

LP interval problem 和传统 order-book market making 很像，但不是完全等价。

一个非常有用的 mapping 是：

- interval center ~= reservation price
- interval width ~= quoting spread
- reset policy ~= quote update policy
- LP inventory drift ~= inventory risk
- out-of-range event ~= 失去双边报价能力

这不是一个严格 theorem，而是一个很有研究价值的 microstructure 视角。

## Research priorities

### Phase 1：现在先做

- CEX-only price history
- regime features：trend、volatility、downside volatility、drawdown、RSI、distance from moving average
- walk-forward interval sweeps
- objective-based ranking
- notebook-driven analysis

### Phase 2：接下来补

- DEX pool state history
- realized pool volume 与 fee-share estimation
- tick-level / tick-density-aware modeling
- gas 与 rebalance cost accounting
- 同一个 pair 的 multi-chain comparison

### Phase 3：等 simulator 足够可信后再上

- CEX perpetual / spot hedge leg
- funding-rate-aware LP + hedge studies
- LVR proxy 与 adverse selection penalty
- reset policy 与 trigger optimization

## AI 应该怎么用

AI 可以用，但顺序要对。

### 适合尽快上的方向

- time-series forecasting model，作为 interval placement 的一个输入
- regime clustering 与 similarity search
- surrogate model，用来近似昂贵的 backtest
- experiment summarization 与 research note generation

### 先不要急着上的方向

- 在 simulator 还不真实时就直接上 reinforcement learning
- 让 LLM 直接“pick a band”
- 在 market assumptions 很弱的时候堆 fancy agent

风险在于：如果 reward function 还是简化版，RL 会把错误目标学得非常漂亮。

## 文献给我们的启发

有三条线现在就值得参考：

- LP 是一个动态决策问题，窄区间收益高，但 reset 和 reallocation cost 不能忽略。参考：[Strategic Liquidity Provision in Uniswap v3](https://arxiv.org/abs/2106.12033)
- interval choice 可以被看成 online learning，而不是一次性的 static optimization。参考：[Uniswap Liquidity Provision: An Online Learning Approach](https://research.google/pubs/uniswap-liquidity-provision-an-online-learning-approach/)
- LP PnL 不只是 fee vs IL，还要考虑 adverse selection 和 stale-price pickup，也就是 LVR。参考：[Automated Market Making and Loss-Versus-Rebalancing](https://arxiv.org/abs/2208.06046)

如果是 AI / forecasting 这条线，目前更适合把 time-series foundation model 当作输入特征，而不是直接把它当 LP policy：

- [Chronos: Learning the Language of Time Series](https://arxiv.org/abs/2403.07815)
- [A decoder-only foundation model for time-series forecasting](https://proceedings.mlr.press/v235/das24c.html)

## 立即值得做的 baseline experiments

先从下面这组 baseline 开始最稳：

1. `BTC/USDC` on `4h` and `1d`
2. `SOL/USDC` on `4h`
3. `SUI/USDC` on `4h`

每个 pair 先跑三种情景：

- neutral view + balanced objective
- bullish view + carry objective
- bearish view + defensive objective

然后重点比较：

- best width
- best center shift
- no-exit rate
- fee proxy
- p10 LP-vs-HODL
- downside breach rate

如果相邻样本下 ranking 很不稳定，这本身就是一个很重要的 research signal：说明 policy 还需要更强的 regime conditioning，或者更严格的风险约束。

## Example command

在 `services/quant` 目录下运行：

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

## Notebook 入口

如果你要从一次性 CLI run 进入可重复的 research session，建议直接从这里开始：

- Notebook: [/Users/lilith/dev/web3/lpquant/services/quant/notebooks/01_lp_baseline_suite.ipynb](/Users/lilith/dev/web3/lpquant/services/quant/notebooks/01_lp_baseline_suite.ipynb)
- Notebook 说明: [/Users/lilith/dev/web3/lpquant/services/quant/notebooks/README.md](/Users/lilith/dev/web3/lpquant/services/quant/notebooks/README.md)
- Experiment logging 规范: [/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md](/Users/lilith/dev/web3/lpquant/docs/experiment-logging.md)

这个 notebook 会导入 `app.research.benchmarks` 里的默认 baseline suite，运行完整 case matrix，并把结果保存到 `research_runs/`。

## 当前 caveat

目前 research module 里的 fee 仍然是 fee proxy，而不是真正的 realized LP fee share。

所以这套工具已经适合做 screening、ranking 和 hypothesis generation，但它还不是 production-grade 的 live trading policy engine。
