# AlphaPilot MVP 范围

最后更新：2026-06-14

## 产品边界

AlphaPilot MVP 是围绕 TradingAgents 引擎构建的可控研究工作台。它支持：

- 公开访客查看已保存的 NVDA demo 结果，不消耗 LLM 额度。
- 注册用户通过后端创建分析任务。
- 管理员启用/禁用账户，并修改每日额度。
- 金融 dashboard 风格前端展示任务状态、分析师输出、辩论模块和最终决策。

AlphaPilot 不执行交易，不提供金融建议，也不会把 LLM API key 暴露给浏览器。

## 角色

- Guest：只能查看 public demo 内容。
- User：可以注册、登录、查看自己的额度、创建分析任务、列出自己的任务并查看自己的报告。
- Admin：拥有普通用户能力，并且可以列出所有用户、禁用账户、调整每日额度。

## 额度与权限

- 默认每日分析额度：每个用户 3 次任务。
- 被禁用用户不能创建分析任务。
- 创建分析任务前，服务端检查额度。
- Public demo 使用已保存输出，最终部署版本中不应要求登录。

## MVP 页面

- Login/Register
- Dashboard
- New Analysis
- Analysis Detail
- Admin Users
- Public Demo

第一版前端实现位于 `frontend/`，是一个静态的 OpenBB-inspired 研究工作台，包含高密度面板、命令栏、指标、报告面板、用户控制和可见免责声明。

## MVP API Endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `POST /analysis`
- `GET /analysis`
- `GET /analysis/{job_id}`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}`
- `GET /demo/reference`

## 数据模型

MVP 后端现在已有 SQLAlchemy 2.0 repository 和 PostgreSQL-ready models。内存 repository 仍作为轻量 fallback。持久化 schema 保留这些概念：

- `users`：邮箱、密码 hash、显示名、角色、是否启用。
- `analysis_jobs`：所属用户、ticker、交易日期、模式、选择的 analysts、状态、结果 id、错误、时间戳。
- `analysis_results`：任务 id、标准化前端结果、原始 engine state。
- `user_quotas`：用户 id、每日额度、今日已用、使用日期。
- `api_usage_logs`：未来用于请求、token 和成本追踪。

本地开发数据库 URL：

```text
postgresql+psycopg://alphapilot:alphapilot@localhost:5432/alphapilot
```

## 结果 Schema

前端友好的结果结构：

```json
{
  "ticker": "NVDA",
  "trade_date": "2024-05-10",
  "decision": "Overweight",
  "sections": {
    "market": "...",
    "investment": "...",
    "trader": "...",
    "final": "..."
  },
  "debates": {
    "investment": {},
    "risk": {}
  }
}
```

Normalizer 同时兼容 live graph state 里的 `trader_investment_plan` 和持久化 log JSON 里的 `trader_investment_decision`。

## OpenBB-inspired UI 方向

OpenBB 将自己定位为面向 analysts、quants 和 AI agents 的金融数据平台。AlphaPilot 应借鉴这种工作台气质：高密度研究面板、数据优先导航、命令/搜索控件、分析师输出面板、状态和额度模块，以及克制的金融产品语言。

## 第一版部署目标

Phase 6 目标是一台 2 vCPU / 2 GB 阿里云轻量应用服务器。第一版在线版本应通过 Docker Compose 在同一台主机上运行 Caddy、FastAPI、静态前端、PostgreSQL、Redis 和一个后台 worker。只有当单机部署稳定后，才考虑把前端托管拆出去。
