# AlphaPilot 技术决策

最后更新：2026-06-10

本文档记录重要技术和产品决策，使项目随着时间推进仍然可理解。

## 决策日志

### 2026-06-10：保留 TradingAgents 作为核心引擎

决策：
- AlphaPilot 初期不会重写 TradingAgents 的多 agent 引擎。
- 第一个产品版本会围绕 `TradingAgentsGraph.propagate()` 增加后端 API、权限、后台任务和前端视图。

原因：
- 原项目已经包含主要 agent workflow。
- 先产品化能更快形成强作品集/面试项目。
- 在理解清楚之前重写引擎会增加风险，但不会立刻带来产品价值。

影响：
- 早期工作应聚焦运行、理解、封装和展示引擎。
- 引擎魔改应逐步进行，并记录原因。

### 2026-06-10：在服务端保护 LLM API Keys

决策：
- DeepSeek 以及未来任何 LLM API keys 都必须只保存在服务端。
- 前端永远不能直接调用 LLM provider。

原因：
- 用户希望网站可以公开访问，但不能暴露或滥用个人 LLM API key。
- 在公开实时分析之前，必须具备后端权限、额度和管理员控制。

影响：
- 实时分析必须经过后端。
- 除非用户已授权，否则 public demo 应使用已保存的样例结果。

### 2026-06-10：用项目文档作为持久记忆

决策：
- 项目计划、当前状态、架构笔记和技术决策都存储在 `docs/`。

原因：
- 聊天上下文可能变长或被压缩。
- 仓库文档提供更稳定的项目记忆。
- 这些文档未来也可以辅助 README、简历和面试准备。

影响：
- 后续工作开始前应先阅读 `docs/STATUS.md` 和 `docs/PROJECT_PLAN.md`。
- 重要变更应更新这些文件。

### 2026-06-10：维护英文源文档和中文镜像

决策：
- `docs/` 目录下的英文文件是 Codex 执行时的 source of truth。
- `docs/docs_CN/` 目录下的中文文件是同步镜像，用于用户查看和中英文对照。

原因：
- Codex 通常能更稳定地理解英文任务描述和技术计划。
- 用户是中文母语者，中文项目管理文档更便于审阅。
- 同时保留两种语言，可以兼顾执行精度和用户可读性。

影响：
- 后续更新文档时，应先更新英文源文件，再更新对应中文镜像。
- 恢复项目工作时，Codex 应检查 `docs/STATUS.md` 和 `docs/PROJECT_PLAN.md`；用户可以查看 `docs/docs_CN/` 下的对应文件。

### 2026-06-10：将本地运行输出保存在 workspace 内且 git ignore 的目录

决策：
- AlphaPilot 本地分析输出、缓存文件、memory logs 和 demo smoke outputs 应写入 `.alphapilot_runtime/`。
- `.alphapilot_runtime/` 已加入 git ignore。

原因：
- 原始 TradingAgents 默认写入用户 home 目录。
- 将 runtime 文件保存在 workspace 内，更方便检查和提取 demo。
- 忽略该目录可以避免大型/生成的分析产物进入版本控制。

影响：
- `.env` 包含 `TRADINGAGENTS_RESULTS_DIR`、`TRADINGAGENTS_CACHE_DIR` 和 `TRADINGAGENTS_MEMORY_LOG_PATH`。
- 未来脚本应把临时/demo 输出放在 `.alphapilot_runtime/` 下。

### 2026-06-10：为开发运行添加显式 LLM Runtime Limits

决策：
- 当 config 中显式存在 `timeout` 和 `max_retries` 时，`TradingAgentsGraph._get_provider_kwargs()` 会将它们转发给 LLM client。
- 默认行为保持不变。

原因：
- Phase 1 调试显示，长 agent run 需要可控的请求行为。
- 未来产品化后台任务也需要有边界的运行行为。

影响：
- Smoke/开发脚本可以设置 `config["timeout"]` 和 `config["max_retries"]`。
- 未来生产后端可以暴露安全的内部 runtime limits，而不需要再次修改 LLM client 代码。

### 2026-06-10：使用 Superpowers Skills 作为辅助工作流

决策：
- 在本地安装 `obra/superpowers` skill set，并在 AlphaPilot 的计划、实现、调试、TDD 和 review 中作为辅助工作流使用。

原因：
- AlphaPilot 正在变成一个多阶段产品项目，更强的过程纪律会很有帮助。
- Superpowers 提供 brainstorming、writing plans、executing plans、systematic debugging、TDD 和 code review 等 skills。

影响：
- 需要重启 Codex，新安装的 skills 才会出现在 active skill list 中。
- 后续实现工作可以在合适时引用 Superpowers 工作流，但 `docs/` 仍然是 AlphaPilot 项目专属的 source of truth。

### 2026-06-10：用 FastAPI 和静态工作台启动产品层 MVP

决策：
- 新增 `alphapilot.backend` FastAPI app，包含认证、额度、管理员控制、分析任务、结果标准化和 engine-service 边界。
- 第一版测试 MVP 使用内存 repository，但保留数据库形状的实体。
- 在选择 Next.js/Vite 之前，先在 `frontend/` 下新增静态 OpenBB-inspired 前端。

原因：
- TradingAgents 引擎本身是 Python，FastAPI 是最短且安全的产品 API 路径。
- 内存存储可以立刻测试 auth/quota/result flow，不被数据库迁移阻塞。
- 静态前端足够验证信息架构、产品文案、报告面板和响应式 dashboard 风格，然后再增加 JavaScript build pipeline。

影响：
- Phase 6 公开部署前必须用持久化数据库替换内存 store。
- Live engine runs 在生产使用前仍需要真实后台 worker。
- 前端可以直接打开 `frontend/index.html`，之后如有需要再迁移到 Next.js/Vite。

### 2026-06-10：发送给前端前先标准化 Engine 输出

决策：
- 新增 `alphapilot/backend/result_normalizer.py`，作为 raw TradingAgents state/logs 和前端报告 sections 之间的稳定边界。
- 同时支持 `trader_investment_plan` 和 `trader_investment_decision`。

原因：
- Live state 和持久化 log JSON 当前使用不同的 trader 字段名。
- 前端不应该知道原始 engine 的命名漂移。

影响：
- API consumers 使用稳定 section 名：`market`、`sentiment`、`news`、`fundamentals`、`investment`、`trader`、`final`。
- 未来 engine 变更应尽量在 normalizer 中吸收。

## 已提出但尚未最终确定

### 后端技术栈

候选：
- FastAPI
- PostgreSQL
- SQLAlchemy 或 SQLModel
- Redis with RQ, Celery, or Arq

原因：
- 引擎本身是 Python。
- 分析任务可能太慢，不适合普通 HTTP 请求/响应流程。
- FastAPI 轻量，适合构建作品集/demo API。

状态：
- FastAPI 已用于 MVP 产品层。持久化数据库和 worker 选择仍未最终确定。

### 前端技术栈

候选：
- React with Next.js or Vite
- TypeScript
- Tailwind CSS
- shadcn/ui 或小型自定义组件系统

原因：
- 适合快速构建精致 dashboard。
- 在认证流程、dashboard 布局和部署方面生态成熟。

状态：
- 第一版 MVP 工作台选择静态 HTML/CSS/JS。API 和存储加固后，仍可迁移到 Next.js 或 Vite。

### 访问控制模型

候选：
- 公开访客可以查看已保存 demo results。
- 注册用户需要激活或受到严格额度限制。
- 管理员可以启用/禁用账户，并设置每日/月度分析限制。

原因：
- 防止 LLM-backed analysis 被随意滥用。
- 同时允许面试官检查产品效果。

状态：
- MVP 已采用 bearer-token auth、默认每日 3 次额度，以及 admin 启用/禁用控制。
