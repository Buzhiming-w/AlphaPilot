# AlphaPilot 项目计划

最后更新：2026-06-15

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
- [x] 更新额度策略：普通用户每日 3 次 live workflow；admin 用户不受 daily quota 限制，但仍受系统级 rate limiting 和 worker capacity 约束。
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
- [x] 定义第一版部署目标。
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

状态：Phase 6 脚手架已完成

推荐技术栈：
- FastAPI
- SQLAlchemy 或 SQLModel
- PostgreSQL
- Redis + RQ/Celery/Arq 作为后台任务系统
- Pydantic schemas

任务：
- [x] 创建后端 app 结构。
- [x] 添加从环境变量读取配置的机制。
- [x] 创建数据库形状模型：
  - users
  - analysis_jobs
  - analysis_results
  - user_quotas
  - api_usage_logs
- [x] 实现认证。
- [x] 实现管理员用户控制。
- [x] 实现使用额度检查。
- [x] 实现后台分析任务创建。
- [x] 将 `TradingAgentsGraph.propagate()` 封装为 engine service。
- [x] 在 SQLAlchemy-backed store 中保存原始 final state 和适合前端展示的标准化结果。
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

状态：基线部署已完成

设计：
- 目标平台：一台 2 vCPU / 2 GB 阿里云轻量应用服务器。
- 部署模型：单机 Docker Compose。
- 反向代理：Caddy，因为它能让小型服务器上的 HTTPS 和静态文件服务更简单。
- 主机上的服务：
  - Caddy 反向代理和静态前端。
  - Uvicorn 提供的 FastAPI API。
  - PostgreSQL 保存产品数据。
  - Redis 用于后台任务队列和 rate limiting 计数。
  - 一个后台 worker 处理 live `TradingAgentsGraph.propagate()` 任务。
- 安全默认值：
  - 公开访客可以无登录查看 `GET /demo/reference`。
  - 注册用户只有在 active 且额度未耗尽时才能创建任务。
  - Live analysis 进入队列，在 HTTP 请求外执行。
  - API keys 只存在于服务端环境变量，永远不暴露给前端文件。
  - Public demo、auth 和 analysis creation endpoints 都需要 rate limiting。
  - 部署文档必须明确说明服务器 IP、域名、SSH 和密钥值由操作者在 git 外填写。

任务：
- [x] 选择部署平台。
- [x] 配置生产环境变量模板。
- [x] 设置数据库迁移。
- [x] 配置 Redis/background worker。
- [x] 添加 rate limiting。
- [ ] 如有需要，添加 admin-only 激活或邀请码流程。
- [x] 添加任务失败和 LLM 使用量日志。
- [x] 添加部署 README。
- [x] 验证前端永远拿不到 API keys。
- [x] 验证被禁用用户不能创建任务。

完成标准：
- 网站可在线访问。
- 访客可以查看 public demo 内容。
- 只有被允许的用户可以消耗 LLM-backed analysis。
- 生产 secrets 未被提交到仓库。
- 在操作者提供服务器 IP、SSH access、DNS/domain 和 secret values 之后，可以在 2 vCPU / 2 GB 阿里云轻量服务器上复现部署。
- 公网 `/`、`/health` 和 `/demo/reference` 返回 HTTP 200。

依赖：
- Phase 4 和 Phase 5。

## Phase 7：Workflow Router Lean MVP

目标：将 Dashboard 升级为自然语言研究工作台，让登录用户通过 Copilot 进入 `Analysis` 或 `Compare` workflow。

状态：已部署到阿里云 demo

设计：
- 在 Dashboard 加入仅登录用户可用的 Copilot 对话。
- 将自然语言请求解析为结构化 draft workflow。
- 部署后清理目标支持的意图：
  - `analysis`，用于单股票或多股票研究分析；
  - `compare`，用于明确的多股票横向比较；
  - `clarify`；
  - `unsupported`。
- 现有 Watchlist 后端和存储可以先保留，但 Watchlist 不再作为 Copilot shortcut 或一级导航目的地。
- 使用混合 ticker 识别策略：
  - 先查本地美股目录；
  - 本地置信度低时使用 AI fallback；
  - 未来外部搜索 provider 放在接口后面。
- 第一版实际支持美股，同时保留 `market`、`exchange`、`currency` 字段，方便未来扩展市场。
- 解析自然语言日期和时间段；保存 `start_date` 和 `end_date`，但第一版 TradingAgents 分析仍以 `end_date` 为基准。
- 创建 compare workflows 或 analysis jobs 前必须经过用户确认。

任务：
- [x] 选择 Lean MVP 范围，而不是一次性做完整 workflow platform。
- [x] 选择 Copilot 仅登录用户可用。
- [x] 选择美股优先实现，同时保留多市场字段。
- [x] 选择混合 ticker resolution。
- [x] 选择保存时间段，但以 `end_date` 作为分析基准。
- [x] 编写 `docs/WORKFLOW_ROUTER_MVP.md` 和中文镜像。
- [x] 编写详细实现计划。
- [x] 添加 ticker directory 和 resolver 测试。
- [x] 添加 workflow router 测试和实现。
- [x] 添加 Watchlist 持久化、API、测试和前端视图。
- [x] 添加 Compare 持久化、API、测试和前端视图。
- [x] 添加 Dashboard 右侧 Copilot Panel。
- [x] 验证访客无法访问 Copilot、Watchlist 和 Compare。
- [x] 云部署前先完成本地测试验证。
- [x] 本地验证通过后，将 Phase 7 部署到阿里云 demo。

部署后清理：
- [x] 删除 Dashboard 右上角旧版 quick analysis 表单（`ticker`、`trade_date`、`Run analysis`），因为分析入口后续应通过 `Analysis` 或 Copilot confirmation 进入。
- [x] Dashboard topbar 保持为工作区状态和导航区域，不再直接承担 analysis execution。
- [x] 将左侧导航重设计为只包含 `Dashboard`、`Analysis` 和 `Compare`。
- [x] 将 `Login` / account controls 移到右上角账户区域。
- [x] 登录后在右上角账户区域显示用户 display name，必要时 fallback 到 email。
- [x] Admin controls 仅 admin 用户可见，并移出普通一级导航。
- [x] 将 `New Analysis` 和 `Report Detail` 合并进 `Analysis` 栏目。
- [x] 隐藏 `Watchlist` 一级导航，同时保留后端能力。
- [x] `Analysis` 和 `Compare` 均保留历史分析记录。
- [x] Dashboard Copilot 确认 workflow 后，直接跳转到 `Analysis` 或 `Compare` 并加载对应分析界面。
- [x] 删除或重标 Dashboard 中旧 demo 的 `Decision: Overweight` 指标，避免用户误解为当前 workflow decision。
- [x] `Overweight` / `Neutral` / `Underweight` 只应出现在 `Analysis`、`Compare` 或明确标注的 demo result summary 中。
- [x] 将当前按钮较多的 Copilot Router 替换为简化的自然语言对话流。
- [x] 删除 Copilot shortcut buttons，例如 `Watchlist`、`Single` 和 `Route workflow`。
- [x] 只保留一个自然语言 submit action 和一个最终 `Confirm` action。
- [x] 用户可以在确认前继续通过对话修正已解析出的 analysis draft。
- [x] 服务端调用 LLM 解析用户意图为结构化 draft，并在 workflow 启动前校验识别出的 tickers。
- [x] 对有约束但较模糊的 Copilot 请求返回候选 ticker 列表，例如美国大市值医疗股票研究。
- [x] 增强 Copilot draft 精修能力：可删除股票 chips、按实体选择候选、展示未识别实体，并在确认前校验最终 symbol 数量。
- [x] 用户可以删除 `Analysis` 历史项，不论 job 处于 queued、running、completed 还是 failed。
- [x] 用户可以删除 `Compare` 历史项。
- [x] 如果已删除的 queued job 后续仍被旧队列取到，worker 会安全跳过。
- [x] 增加真实 workflow progress events，让运行中的 `Analysis` 和 `Compare` 报告可以展示分阶段更新。
- [x] 为真实 streamed 或 polled progress text 增加打字机式报告展示效果。
- [x] workflow 完成后持久化最终报告，并与进行中的 streamed text 替换或合并。

完成标准：
- 登录用户可以输入自然语言请求，并收到结构化 draft workflow。
- Router 能识别常见美股 ticker、公司名、别名、中文名和人物线索。
- 用户可以在最终确认前删除错误 symbol、从歧义候选中选择目标，并看到未识别实体。
- 用户可以确认 draft，并创建 `Analysis` 或 `Compare` workflow。
- 现有 Watchlist API/存储保持受保护且可持久化，但不作为主用户路径。
- Compare workflows 能持久化确认后的 tickers 和时间段。
- Dashboard 包含简化后的 Copilot 对话，且不破坏现有分析 workflow。
- 运行中的报告能展示真实阶段进度和阶段性结论，而不是黑盒等待状态。
- 测试覆盖 router、compare、permission、account/nav visibility、progress reporting 和 frontend structure 路径。

依赖：
- Phase 4 后端 API/auth/quota。
- Phase 5 dashboard frontend。
- Phase 6 PostgreSQL/Redis 部署基础。

可并行：
- 文档打磨。
- 本地实现稳定后，继续域名/HTTPS 部署加固。
- 部署后的 Phase 7 UI 清理。

导航重设计源文档：
- `docs/PRODUCT_NAVIGATION_REDESIGN.md`

## Phase 7.5：Security Master 与实体识别

目标：用数据库驱动的 Security Master 替换当前狭窄的硬编码 ticker directory，让 Copilot 可以识别美股、常见 ETF、中文名、别名和人物线索。

状态：本地实现进行中

设计源文档：
- `docs/SECURITY_MASTER_PLAN.md`

设计：
- 保留当前 Copilot LLM 层，让它继续作为语义抽取辅助。
- 使用 PostgreSQL-backed Security Master 作为最终 ticker confirmation 权威来源。
- 从 Nasdaq Trader symbol directory 文件载入基础美股证券数据，并使用 SEC `company_tickers_exchange.json` 补充 CIK 和公司名。
- 将常见中文名、中文简称、旧名、品牌名、CEO/创始人/人物线索存入 `security_aliases`，不再硬编码在 Python 列表中。
- 保留 unresolved Copilot query logging 作为后续排查依据，但当前阶段不做 admin alias 维护 UI/endpoints。
- 保留 workflow 启动前必须用户确认的约束。

任务：
- [x] 编写详细 Security Master 设计和维护计划。
- [x] 添加 `securities`、`security_aliases`、`security_master_sync_runs` 和 `security_resolution_failures` 数据表。
- [x] 添加 Nasdaq Trader 和 SEC 文件同步命令。
- [x] 在服务器时间每周一 00:00 自动执行生产 Security Master 同步。
- [x] 为常见美股大盘股和 ETF seed 高价值 aliases，包括中文名和人物线索。
- [x] 添加 `SecurityMasterResolver`，并替换 Copilot routing 中硬编码的 `LocalTickerDirectory`。
- [x] 决定当前阶段不做 admin 维护 endpoints/UI；直接在 `security_aliases` 表中维护 aliases。
- [x] 添加测试，证明 `Compare 3M and ORCL from June 2015 to now` 能解析为 `MMM` 和 `ORCL`。

完成标准：
- `MMM`、`ORCL`、常见大盘股和常见 ETF 能从数据库驱动的 Security Master 中解析。
- 中文名和人物线索以数据库 aliases 的形式表达。
- Copilot 对歧义匹配返回候选列表，并且在用户确认前不启动 workflow。
- Security Master 同步过程幂等且可审计。
- 首次手动同步后，生产 Security Master 在服务器时间每周一 00:00 自动同步。
- 现有 Workflow Router 行为继续由测试覆盖。

依赖：
- Phase 6 PostgreSQL 持久化。
- Phase 7 Copilot routing 和 confirmation workflow。

## Phase 8：作品集打磨

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

- [x] Watchlist 已提升到 Phase 7。
- [ ] 完整持久化聊天历史。
- [ ] 专用 compare 多 agent 推理。
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
