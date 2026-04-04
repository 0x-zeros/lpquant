# Coverage-Constrained Price Range / 覆盖率约束价格区间方法

## 核心目标

这个方法只做一件事：

> 在满足 `stay-in-range probability` 的前提下，让区间尽量窄。

它不再依赖旧的 `balanced / carry / defensive` 这类 profile，也不再把目标写成多指标打分。

这里虽然沿用了 `coverage-constrained interval` 这个模块命名，但研究对象本质上是
`price range / 价格区间`，不是时间周期。

## 为什么要加这个方法

旧方法更像是一个 research dashboard：

- 会看 fee proxy
- 会看 LP vs HODL
- 会看 drawdown / IL
- 会按不同 objective 打分

但你现在想研究的问题更直接：

- 什么区间比较好？
- 如果区间太窄，虽然 capital efficiency 很高，但一旦 price 出区间，就没有 LP 收益
- 所以真正关键的是：`尽量不出区间` 和 `尽量窄`

这就更适合写成一个 constrained optimization problem。

## 方法定义

给定：

- 一个 trading pair
- 一段历史数据
- 一个 holding period，例如 `30 days`、`60 days`、`365 days`
- 一个 coverage target，例如 `90%`

我们对每个历史起点窗口统计：

- `lower_excursion_pct`：在持有期内，价格相对起点向下最多走了多少
- `upper_excursion_pct`：在持有期内，价格相对起点向上最多走了多少

然后寻找一个价格区间：

- lower bound = `L`
- upper bound = `U`

使得：

- 有至少 `coverage target` 比例的历史窗口，在整个 holding period 内都没有超出 `[L, U]`
- 在所有满足这个约束的区间里，`width = U - L` 最小

## 这个方法和旧方法的关系

旧方法保留，方便继续比较。

新方法更像是：

- 一个更接近主目标的 baseline
- 一个更容易解释的 optimization target
- 一个适合先跑 month / two-month / one-year horizon comparison 的研究工具

如果后面你发现这个方法更稳定、更有洞察力，旧方法再逐步降级或者删除也不迟。

## 需要注意的一点

这里的 `interval` 只是 data sampling interval，例如 `1d`、`4h`。

真正的研究目标不是“4 小时区间”或者“1 小时区间”，而是：

- 给定 `holding period`
- 在这个 period 里，怎样的 `price range / 价格区间` 最合理

也就是说：

- `sampling interval` 是数据分辨率
- `holding period` 才是这次区间研究的核心时间尺度

## CLI 示例

在 `/Users/lilith/dev/web3/lpquant/services/quant` 下运行：

```bash
uv run python -m app.research.coverage_cli \
  --pair BTC/USDC \
  --interval 1d \
  --days 730 \
  --holding-days 30 \
  --coverage-target 90 \
  --output-dir research_runs/btc_30d_interval
```

## 推荐的第一轮实验

先对同一个 pair 比较不同 `holding period`：

- `7 days`
- `30 days`
- `60 days`
- `180 days`
- `365 days`

coverage target 建议至少从 `50%` 开始往上扫，而不是只看 `70%+`。原因是：

- `50%~70%` 区间能告诉你 aggressive 缩窄区间时，宽度到底能收缩多少
- `80%+` 更接近真实可执行的 production 区间
- 这样你才能真正看到 `coverage / width` 的 trade-off 曲线

然后观察：

- `width_pct`
- `lower_bound_pct`
- `upper_bound_pct`
- `out_of_range_pct`
- `downside_touch_pct`
- `upside_touch_pct`

如果 holding period 一拉长，最优区间迅速变宽，那就说明这个 pair 的长期稳定性并不支持特别窄的 LP 区间。

## 当前推荐 heuristic

如果你还没有明确给出“至少要多少覆盖率”这种 production constraint，可以先用一个简单而可解释的 heuristic：

1. 先扫完整 frontier，例如 `50% -> 97.5%`
2. 把 `80%` 设成默认的最低推荐覆盖率门槛
3. 在满足这个门槛的点里，选出最接近 `高 coverage + 低 width` 理想点的那个

这样做的原因是：

- 只看最窄区间，会很容易掉进 `50% coverage` 这种虽然窄但太容易出区间的解
- 只看最高 coverage，又会把区间推得过宽
- 用一个最低 coverage floor，再在里面找 trade-off，比较接近当前阶段的研究目标
