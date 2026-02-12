# LPQuant

[English](README.md) | [中文](README.zh.md)

LPQuant 是面向 Sui DEX 池的集中流动性区间推荐系统。
为 **Sui Vibe Hackathon（Cetus 赛道）** 打造，基于历史价格行为给出清晰可执行的
LP 区间建议，并提供回测指标、图表与 AI 辅助解读。

## 亮点

- **Base/Quote 统一映射**，与 Cetus 展示习惯一致  
  Quote 优先级：稳定币 → SUI → BTC → ETH → SOL。  
  UI 展示与计算全部基于统一的 Base/Quote 视角。
- **最佳区间推荐**：透明评分 + 回测指标
- **双击弹窗详情**：一键查看完整图表与细节
- **AI 分析 Tab**：内置 LLM 提示词与分析流程（不绑定供应商）
- **可导出 JSON**：便于分享与审计

## 界面截图

<!-- 在此处粘贴你的截图（GitHub 可渲染相对路径图片） -->

![截图 1](docs/screenshots/screenshot-1.png)
![截图 2](docs/screenshots/screenshot-2.png)
![截图 3](docs/screenshots/screenshot-3.png)

## 架构

单仓双服务，BFF 模式：

```
Browser → Next.js App Router UI
            ↓ (POST /api/recommend)
         Next.js Route Handlers (BFF)
            ↓ parallel fetch
    ┌───────┼───────────┐
    ↓       ↓           ↓
 Birdeye  Sui RPC   Python FastAPI
 /Binance pool cfg   quant engine
 klines
```

- **Frontend**（`apps/web`）：Next.js 16、React 19、shadcn/ui、TailwindCSS v4、
  lightweight‑charts v5、next‑intl（中英双语）
- **BFF**（`apps/web/src/app/api/`）：统一 kline + 池子配置并转发给量化引擎
- **Quant Engine**（`services/quant`）：FastAPI + numpy/pandas，输出指标评分与图表序列

## 价格模型与数据源

价格全部以 **Base / Quote** 表达，映射规则固定：

- Quote 优先级：**稳定币 → SUI → BTC → ETH → SOL**
- 若两边同类（如都是稳定币或都不在名单），保持 coinA/coinB 映射

K 线（OHLCV）来源：

1. **Birdeye**（主数据源，配置 `BIRDEYE_API_KEY` 后启用）
2. **Binance**（兜底，或使用 USD 交叉比值构造非稳定币报价）

## 开发

```bash
# 前端
cd apps/web && pnpm dev          # :3000

# Python 量化引擎
cd services/quant
uv sync && uv run uvicorn app.main:app --reload --port 8000

# 两个服务需同时运行
```

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `BIRDEYE_API_KEY` | 否 | Birdeye API Key（主 kline 源） |
| `QUANT_SERVICE_URL` | 否 | Python 引擎地址（默认 `http://localhost:8000`） |
| `SUI_RPC_URL` | 否 | Sui 全节点 RPC（默认主网） |

## 黑客松

**Sui Vibe Hackathon — Build on Sui · Build the Vibe**  
Organizer: HOH × Sui  
Sponsors: Cetus, Bucket  

本项目参加 **Cetus 赛道**，目标是打造真正可用、可落地的 Sui CLMM LP 决策工具。

## 后续计划

- **链上价格重建**：基于 Cetus swap 事件重建 OHLCV，降低外部依赖。
