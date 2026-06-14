# AlphaPilot 项目计划

最后更新：2026-06-10

## 目标

AlphaPilot 是一个基于 TauricResearch/TradingAgents 产品化改造的美股分析助手。第一个偏生产化的版本应该支持用户注册、提交美股分析任务、查看结构化报告，并允许管理员控制账户权限和使用额度，从而保护服务端的 LLM API key。

AlphaPilot 只用于投资研究辅助、面试展示和作品集展示。它不能把自己包装成金融建议工具，也不执行真实交易。

## 执行规则

- 开始新阶段或重要任务前，先更新 `docs/STATUS.md`。
- 完成任务后，在本文件中勾选对应 checklist。
- 重要技术选择记录到 `docs/DECISIONS.md`。
- Codex 执行时以 `docs/` 下的英文文件作为主要依据。
- `docs/docs_CN/` 下的中文镜像文件需要同步更新，方便用户查看和中英文对照。
- 在新增产品层之前，先保证原始 TradingAgents 引擎可用。
- 不要把 LLM API key 暴露给前端。

## Phase 1：跑通原始引擎

目标：在围绕项目做任何产品化封装之前，先证明克隆下来的项目可以在本地通过 DeepSeek 正常运行。

状态：已完成

任务：
- [x] 激活 `AlphaPilot` conda 环境。
- [x] 使用 `pip install -e .` 以 editable 模式安装项目。
- [x] 为 DeepSeek 配置 `.env`：
  - `DEEPSEEK_API_KEY`
  - `TRADINGAGENTS_LLM_PROVIDER=deepseek`
  - `TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-flash`
  - `TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro`
  - `TRADINGAGENTS_OUTPUT_LANGUAGE=Chinese`
  - `TRADINGAGENTS_MAX_DEBATE_ROUNDS=1`
  - `TRADINGAGENTS_MAX_RISK_ROUNDS=1`
- [x] 对 `NVDA` 或 `AAPL` 跑一次最小股票分析。
- [x] 确认可以生成完整的 `final_trade_decision`。
- [x] 确认日志和结果可以正常写入。
- [x] 保存一份成功输出，作为后续 public demo 的参考结果。

完成标准：
- 使用 DeepSeek 完成一次完整本地分析。
- 可以查看最终决策和中间报告。
- 主要失败点已经记录在 `docs/STATUS.md`。

依赖：
- 无。

必须先于以下任务完成：
- 后端 API 封装。
- 前端接入实时分析。
- 公开部署。

## Phase 2：理解核心架构

目标：充分理解现有引擎，确保后续封装和魔改是安全的。

状态：MVP 所需部分已完成

任务：
- [x] 阅读 `tradingagents/graph/trading_graph.py`。
- [x] 阅读 `tradingagents/default_config.py`。
- [x] 阅读 `tradingagents/graph/propagation.py`。
- [x] 阅读 `tradingagents/agents/analysts/`。
- [x] 阅读 `tradingagents/agents/researchers/`。
- [x] 阅读 `tradingagents/agents/trader/`。
- [x] 阅读 `tradingagents/agents/risk_mgmt/`。
- [x] 阅读 `tradingagents/agents/managers/portfolio_manager.py`。
- [x] 阅读 `tradingagents/dataflows/`。
- [x] 记录 `TradingAgentsGraph.propagate()` 的输入/输出结构。
- [x] 记录前端可以展示的最终报告模块。
- [x] 识别耗时、昂贵、容易失败的步骤。

完成标准：
- `docs/ARCHITECTURE_NOTES.md` 解释清楚 agent 流程、输入、输出、存储和数据来源。
- 后端结果 schema 可以基于真实 engine 输出设计，而不是凭空猜。

依赖：
- Phase 1 可以先做，也可以和阅读工作并行；但后端实现应等 Phase 1 跑通后再开始。

可并行：
- 前端视觉调研。
- 简历/项目描述草稿。

## Phase 3：定义 MVP 产品范围

目标：冻结一个窄而清晰的第一版，做到有用、可展示、足够安全。

状态：MVP 已完成

任务：
- [x] 定义用户角色：游客、普通用户、管理员。
- [x] 定义分析权限和额度。
- [x] 定义 public demo 用户能看到什么，并且不消耗 LLM 额度。
- [x] 定义 MVP 页面：
  - 登录/注册
  - Dashboard
  - New Analysis
  - Analysis Detail
  - Admin Users
  - Public Demo
- [x] 定义 MVP API endpoints。
- [x] 定义数据库表。
- [ ] 定义第一版部署目标。
- [x] 增加明确可见的“非投资建议”免责声明要求。

完成标准：
- MVP 可以在不膨胀范围的情况下完成。
- 所有功能都能保护服务端 LLM key，避免被随意滥用。

依赖：
- Phase 1 应完成。
- Phase 2 应基本完成。

可并行：
- 静态前端 mockup。
- API/schema 决策清楚后，可以开始后端脚手架。

## Phase 4：后端 MVP

目标：通过可控的后端 API 暴露 TradingAgents 能力。

状态：MVP 脚手架已实现

推荐技术栈：
- FastAPI
- SQLAlchemy 或 SQLModel
- PostgreSQL
- Redis + RQ/Celery/Arq 作为后台任务系统
- Pydantic schemas

任务：
- [x] 创建后端 app 结构。
- [ ] 添加从环境变量读取配置的机制。
- [x] 创建数据库形状模型：
  - users
  - analysis_jobs
  - analysis_results
  - user_quotas
  - api_usage_logs
- [x] 实现认证。
- [x] 实现管理员用户控制。
- [x] 实现使用额度检查。
- [ ] 实现后台分析任务创建。
- [x] 将 `TradingAgentsGraph.propagate()` 封装为 engine service。
- [x] 在 MVP store 中保存原始 final state 和适合前端展示的标准化结果。
- [x] 添加 API endpoints：
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /me`
  - `POST /analysis`
  - `GET /analysis`
  - `GET /analysis/{job_id}`
  - `GET /admin/users`
  - `PATCH /admin/users/{user_id}`
- [x] 为认证、额度、任务创建添加基础测试。

完成标准：
- 登录用户可以创建分析任务。
- 任务在后台运行。
- 可以通过 API 获取最终报告。
- 管理员可以禁用或限制用户。

依赖：
- Phase 1 必须完成。
- Phase 3 的 API 和 schema 决策应完成。

可并行：
- 前端使用 mock API response 开发。
- 部署方案调研。

## Phase 5：前端 MVP

目标：创建一个适合面试和公开 demo 的精致网页体验。

状态：静态 MVP 脚手架已实现

推荐技术栈：
- Next.js 或 Vite React
- TypeScript
- Tailwind CSS
- shadcn/ui 或小型本地组件系统

任务：
- [x] 创建前端 app 结构。
- [x] 构建认证页面。
- [x] 构建 dashboard。
- [x] 构建新建分析表单。
- [x] 构建分析状态视图。
- [x] 构建分析详情报告视图。
- [x] 构建管理员用户管理视图。
- [x] 使用已保存的参考输出添加 public demo 页面。
- [x] 在产品内添加“非投资建议”免责声明。
- [x] 前端接入后端 API。
- [x] 使用自动化文件检查验证响应式布局基础。

完成标准：
- 用户可以注册、登录、提交分析并阅读结果。
- 管理员可以管理账户。
- Public demo 不消耗 LLM 额度。
- UI 达到作品集展示质量。

依赖：
- Phase 3 后可以用 mocks 开始。
- 接入真实分析需要 Phase 4。

可并行：
- 后端实现。
- 简历和 README 撰写。

## Phase 6：部署与安全

目标：以低成本、可控、防滥用的方式把应用上线。

状态：未开始

任务：
- [ ] 选择部署平台。
- [ ] 配置生产环境变量。
- [ ] 设置数据库迁移。
- [ ] 配置 Redis/background worker。
- [ ] 添加 rate limiting。
- [ ] 如有需要，添加 admin-only 激活或邀请码流程。
- [ ] 添加任务失败和 LLM 使用量日志。
- [ ] 添加部署 README。
- [ ] 验证前端永远拿不到 API keys。
- [ ] 验证被禁用用户不能创建任务。

完成标准：
- 网站可在线访问。
- 访客可以查看 public demo 内容。
- 只有被允许的用户可以消耗 LLM-backed analysis。
- 生产 secrets 未被提交到仓库。

依赖：
- Phase 4 和 Phase 5。

## Phase 7：作品集打磨

目标：把 AlphaPilot 打造成一个有说服力的简历和面试项目。

状态：未开始

任务：
- [ ] 编写项目 README。
- [ ] 添加架构图。
- [ ] 添加截图。
- [ ] 添加 demo account 或 demo-only mode。
- [ ] 添加成本控制说明。
- [ ] 添加安全/防滥用说明。
- [ ] 添加限制和免责声明。
- [ ] 编写简历 bullet points。
- [ ] 准备面试讲解：
  - 问题背景
  - 架构
  - agent 工作流
  - 产品取舍
  - 安全决策
  - 部署决策

完成标准：
- 评审者可以快速理解项目。
- 项目清楚展示全栈工程、AI 集成、产品思维和部署意识。

依赖：
- MVP 形态清楚后即可开始。
- 最终打磨依赖已部署应用。

## 可选增强

这些应该等 MVP 正常工作后再做：

- [ ] Watchlist。
- [ ] Saved portfolios。
- [ ] 跨日期分析对比。
- [ ] 成本和 token 使用量 dashboard。
- [ ] 策略模式：保守、平衡、激进、长期、短线。
- [ ] 财报日历集成。
- [ ] 宏观事件时间线。
- [ ] 回测摘要。
- [ ] Prompt/admin 配置面板。
- [ ] 分析完成后邮件通知。
- [ ] 付费或邀请码访问控制。

## 并行关系图

严格串行：
- Phase 1 必须先于 live backend wrapper。
- 理解 engine 输出必须先于最终 result schema。
- Auth/quota 必须先于公开 live analysis。
- Backend API 必须先于前端真实接入。
- 安全检查必须先于部署。

可以并行：
- Phase 2 代码阅读和前端视觉探索。
- Phase 3 产品范围定义和静态前端 mock。
- Phase 4 后端和 Phase 5 前端可以基于 mocked API 并行。
- Phase 6 部署准备和 Phase 7 文档撰写。
