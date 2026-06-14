# AlphaPilot Workflow Router Lean MVP

最后更新：2026-06-15

## 目标

Workflow Router Lean MVP 会把 AlphaPilot 从“单股报告工具”升级为“自然语言驱动的研究工作台”。

第一版应允许已登录用户在 Dashboard 中输入自然语言请求，由 AlphaPilot 识别用户想做的 workflow，解析可能的美股 ticker，解析日期或时间段，要求用户确认，然后路由到 Watchlist、Multi-Stock Compare 或 Single Stock Analysis。

该功能仍然只用于研究辅助。不能提供金融建议，不能执行真实交易，也不能把 LLM API key 暴露给前端。

## 产品决策

- 使用 Dashboard 右侧 Copilot Panel 作为 Workflow Router 的主要 UI。
- 第一版 Copilot 只对登录用户开放。访客继续只能查看 public demo。
- 第一版实际支持美股，但保留 `market`、`exchange`、`currency` 字段，方便未来扩展港股和 A 股。
- 使用混合 ticker 识别策略：
  - 先查本地美股公司目录；
  - 本地置信度低时使用 AI 解析兜底；
  - 外部市场搜索 provider 作为未来可插拔接口。
- 支持自然语言时间段，但第一版调用 TradingAgents 时仍使用 `end_date` / `as-of date` 作为分析基准。
- AI 解析出来的请求必须经过用户明确确认，才能创建 watchlist item、compare workflow 或 analysis job。

## 第一版支持的意图

- `add_to_watchlist`：将确认后的 ticker 加入用户 Watchlist。
- `single_analysis`：创建或预填单股分析 workflow。
- `multi_compare`：对 2 到 5 个确认后的 ticker 做对比。
- `clarify`：信息不足时继续追问。
- `unsupported`：请求超出当前产品能力时明确说明。

示例：

```text
帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在
```

预期解析结果：

```json
{
  "intent": "multi_compare",
  "symbols": [
    {
      "ticker": "NVDA",
      "company_name": "NVIDIA Corporation",
      "market": "US",
      "exchange": "NASDAQ",
      "currency": "USD",
      "confidence": "high",
      "match_reason": "Matched Jensen Huang / 黄仁勋 to NVIDIA"
    },
    {
      "ticker": "AMD",
      "company_name": "Advanced Micro Devices, Inc.",
      "market": "US",
      "exchange": "NASDAQ",
      "currency": "USD",
      "confidence": "high",
      "match_reason": "Exact ticker match"
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "latest",
  "analysis_anchor": "latest",
  "requires_confirmation": true
}
```

## 用户体验

Dashboard 保持当前 data-first 工作台布局。登录用户会看到右侧 Copilot Panel。

Panel 包含：

- 自然语言输入框；
- 示例 prompt；
- 对话片段；
- 解析后的 workflow 卡片；
- 候选 ticker 确认卡片；
- 日期或时间段确认；
- `Confirm Compare`、`Add To Watchlist`、`Start Analysis`、`Edit` 等动作按钮。

Copilot 不应立刻运行昂贵分析。它先返回结构化 draft workflow，并要求用户确认或编辑。

## Watchlist Lean MVP

第一版 Watchlist 应保持小而可用：

- 查看当前用户的 watchlist items；
- 添加确认后的 ticker；
- 删除 watchlist items；
- 保存可选用户备注；
- 保存创建来源，例如 `manual` 或 `copilot`。

建议字段：

- `id`
- `user_id`
- `ticker`
- `company_name`
- `market`
- `exchange`
- `currency`
- `note`
- `source`
- `last_analysis_job_id`
- `created_at`
- `updated_at`

第一版不需要分组、提醒、自动刷新或仓位管理。

## Multi-Stock Compare Lean MVP

第一版 Compare 支持 2 到 5 个 ticker。

Compare workflow 保存：

- 已确认 ticker；
- `start_date`；
- `end_date`；
- `analysis_anchor`；
- 创建来源；
- 状态；
- 创建出的关联 analysis jobs。

第一版 Compare 页面可以并列展示多个单股分析输出，不需要立刻构建专用 compare agent。页面应包括：

- ticker cards；
- 每个 ticker 的 job status；
- 每个完成分析的 final decision；
- 选定的报告 sections；
- 用户原始时间段；
- 如果可用，展示一个简单 aggregate summary。

真正的区间收益、回撤、波动、事件时间线和专用 compare agent 延后实现。

## 后端设计

新增后端边界应保持小而可测试：

- `ticker_directory`：本地公司/ticker/别名/人物索引和模糊查找。
- `workflow_router`：意图、ticker 和时间解析边界。
- `watchlist` 持久化方法和 API routes。
- `compare` 持久化方法和 API routes。
- `copilot` route endpoint，返回 draft workflow。

可能新增 API endpoints：

```text
POST /copilot/route
GET /watchlist
POST /watchlist
DELETE /watchlist/{item_id}
POST /compare
GET /compare/{compare_id}
```

第一版 router response 应足够 deterministic，方便测试。AI fallback 应隔离在接口后面，测试时可以注入 fake resolver。

## 数据与持久化

SQLAlchemy/PostgreSQL 模型应新增：

- `watchlist_items`
- `compare_workflows`
- `compare_workflow_symbols`

即使第一版只支持美股，schema 也应保留多市场字段。

已有 `analysis_jobs` 和 `analysis_results` 继续作为单股分析输出来源。Compare workflows 可以引用 analysis jobs，而不是复制完整报告。

## 权限与安全

- 访客不能调用 `/copilot/route`、`/watchlist` 或 `/compare`。
- 登录但 inactive 的用户不能创建新的 analysis 或 compare workflows。
- 当确认后的 workflow 创建 analysis jobs 时，沿用现有每日额度规则。
- AI 解析本身不消耗 analysis quota，但需要 rate limit。
- 前端永远不能接收 provider API keys。
- UI 必须保持可见的非投资建议免责声明。

## 测试策略

本地测试应覆盖：

- 公司名、ticker、别名、中文名和已知人物的 ticker directory matching；
- 无匹配和歧义匹配行为；
- workflow intent routing；
- 日期和时间段解析；
- 访客访问 Copilot、Watchlist、Compare 时被拒绝；
- watchlist 添加/列表/删除；
- 2 到 5 个 ticker 的 compare workflow 创建；
- compare 创建拒绝未确认或不支持的 ticker；
- 只有创建 analysis jobs 时才消耗 quota；
- 右侧 Copilot Panel 和确认状态的前端结构。

云服务器测试应继续作为本地测试通过后的部署 smoke test。

## 本 MVP 不包含

- 美股以外市场的真实支持。
- 真正的区间分析和回测。
- 专用 compare 多 agent 推理。
- 完整持久化聊天历史。
- Watchlist 分组、提醒、定时刷新。
- 组合仓位管理或真实交易。
- 付费、账单或账户套餐。

## 完成标准

- 登录用户可以输入自然语言请求，并收到结构化 draft workflow。
- Router 至少能识别常见美股 ticker、公司名、别名、中文名和人物线索。
- 用户可以确认候选项，并创建 Watchlist、Compare 或 Single Analysis workflows。
- Watchlist items 可以持久化，刷新后仍可见。
- Compare workflows 可以持久化确认后的 tickers 和时间段。
- Dashboard 包含右侧 Copilot Panel，且不破坏现有 workflow。
- 测试覆盖 router、watchlist、compare、permission 和 frontend structure 路径。
