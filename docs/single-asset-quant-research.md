# Single-Asset Quant Research / 单币量化研究说明

这份研究模板的目标，是在正式做 LP 区间研究之前，先把某个币本身的价格行为看明白。

如果一个币种本身就具有这些特征：

- 趋势性很强
- 波动率经常突然放大
- 尾部风险很重
- 成交量和价格经常一起爆发

那它通常就不适合被放进一个过窄、长期不动的 LP 区间里。

所以这份 notebook 不是直接给区间，而是先回答更基础的问题：

- 这个币最近是在 trend 还是 range？
- 波动率是高还是低？
- 回撤深不深？
- 收益分布是不是 fat-tailed？
- return autocorrelation 和 absolute-return autocorrelation 有没有特征？

## 这份模板会看哪些指标

### 1. Trend / 趋势

- `SMA short` 与 `SMA medium`
- `trend_vs_short_sma_pct`
- `trend_vs_medium_sma_pct`
- `MACD`

用途：

- 看价格是站在均线之上还是之下
- 看中短期趋势是否同向
- 看动量有没有继续强化或转弱

### 2. Volatility / 波动率

- `realized_vol_pct`
- `downside_vol_pct`
- `ATR %`
- `drawdown_pct`

用途：

- `realized vol` 看整体波动
- `downside vol` 专门看下跌时的波动压力
- `ATR` 看日内或单 bar 的真实波幅
- `drawdown` 看历史上资金曲线最痛的时候有多痛

### 3. Momentum / 动量

- `RSI`
- `MACD hist`

用途：

- RSI 更像一个短期热度和均值回归提示器
- MACD 更像趋势动量差的平滑版本

这两个指标都更偏 practitioner indicator，适合做描述和监控，不建议单独把它们当成最终 alpha 证据。

### 4. Distribution / 分布与尾部风险

- `skewness`
- `excess kurtosis`
- `VaR 5%`
- `CVaR 5%`

用途：

- 看收益分布是否对称
- 看尾部是否比正态分布更厚
- 看坏情况下的典型单期损失有多大

### 5. Serial Dependence / 序列相关性

- `return autocorr`
- `abs return autocorr`

用途：

- `return autocorr` 更接近趋势延续或短期反转
- `abs return autocorr` 更接近 volatility clustering

如果绝对收益的自相关明显更高，通常说明“波动会成团出现”，这对 LP 区间宽度很重要。

## 如何把这些结果映射到 LP 研究

一个简单的经验映射是：

- `trend 强 + drawdown 深 + downside vol 高`
  - 倾向于更宽的区间，或者更高频地重设区间
- `range 明显 + realized vol 低 + ATR 低`
  - 更适合尝试更窄的区间
- `abs return autocorr 高`
  - 说明波动 clustering 明显，区间不能只看平均波动率
- `volume z-score` 经常和 price breakout 一起出现
  - 说明出区间事件可能会集中在少数 burst 时刻

## 推荐阅读

- [Cont (2001), Empirical properties of asset returns: stylized facts and statistical issues](https://ideas.repec.org/a/taf/quantf/v1y2001i2p223-236.html)
- [Engle (2003), Risk and Volatility: Econometric Models and Financial Practice](https://www.nobelprize.org/prizes/economic-sciences/2003/engle/lecture/)
- [Brock, Lakonishok, and LeBaron (1992), Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](https://econpapers.repec.org/RePEc:bla:jfinan:v:47:y:1992:i:5:p:1731-64)
- [Jegadeesh and Titman (1993), Returns to Buying Winners and Selling Losers](https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html)
- [Liu and Tsyvinski (2018), Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877)
- [Liu, Tsyvinski, and Wu (2019), Common Risk Factors in Cryptocurrency](https://www.nber.org/papers/w25882)

## 使用建议

第一轮建议先跑：

- `BTC`
- `ETH`
- `SOL`
- `SUI`

并统一使用：

- `interval = 1d`
- `days = 730`

先从日线看“这个币是什么性格”，再决定后面是否值得往更细的采样频率下钻。
