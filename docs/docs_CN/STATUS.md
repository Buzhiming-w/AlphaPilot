# AlphaPilot 当前状态

最后更新：2026-06-15

## 当前阶段

Phase 7：Workflow Router Lean MVP

## 当前任务

收尾并准备部署本地已验证的 Workflow Router Lean MVP：在登录后的 Dashboard 中加入 Copilot，将自然语言请求转换为已确认的 Watchlist、Multi-Stock Compare 或 Single Stock Analysis workflow。

## 下一步

1. 提交并推送本地已验证的 Phase 7 MVP。
2. 仓库验证完成后，再部署到阿里云 demo。
3. 部署后重新运行公网 smoke checks。
4. Workflow Router MVP 落地后，继续 Phase 6 之后的 hardening。

## 当前阻塞

- 暂无域名，所以第一版部署只能通过服务器 IP 使用 HTTP。
- 浏览器截图验证仍待补充。
- Workflow Router 云部署应等本地测试通过后再进行。

## 重要上下文

- 仓库路径：`/Users/buzhiming/Desktop/AlphaPilot`
- 当前项目名：AlphaPilot
- 基础项目：TauricResearch/TradingAgents
- 本地环境名：`AlphaPilot`
- `.env` 已经包含 DeepSeek API key，但 provider/model overrides 仍需确认。
- 原始引擎入口是 `TradingAgentsGraph.propagate()`。
- 默认配置目前使用 OpenAI，除非通过 `TRADINGAGENTS_*` 环境变量覆盖。
- Codex 后续检查时优先检查 `docs/` 下的英文文档；用户查看时可以对照 `docs/docs_CN/` 下的中文文档。
- Phase 6 部署目标是一台 2 vCPU / 2 GB 阿里云轻量应用服务器。
- 生产拓扑：单台 Docker Compose 主机上运行 Caddy 反向代理、FastAPI、静态前端、PostgreSQL、Redis 和后台 worker。
- 第一版公网部署 URL：`http://47.250.149.226/`
- 服务器地域：阿里云马来西亚（吉隆坡），Ubuntu 22.04。
- 服务器路径：`/opt/AlphaPilot`
- 管理员凭据已从本地默认值轮换为服务器专用随机值。服务器上的 root-only 凭据文件是 `/root/alphapilot_admin_credentials.txt`。
- Workflow Router Lean MVP 设计源文档：`docs/WORKFLOW_ROUTER_MVP.md`。
- Workflow Router 约束：仅登录用户可用、第一版实际支持美股、混合 ticker 识别、执行 workflow 前必须用户确认，并保存时间段但第一版分析仍以 `end_date` 为基准。

## 最近记录

- 创建了项目管理文档，使后续工作可以从仓库状态恢复，而不是依赖聊天记忆。
- 在 `docs/docs_CN/` 下添加了中文镜像文档。Codex 应先检查和更新 `docs/` 下的英文文档，再同步更新中文版本，方便用户查看。
- 已开始执行 Phase 1：环境/配置验证、editable 安装，以及第一次本地分析运行。
- 已完成 Phase 1 smoke run：脚本 `scripts/run_phase1_smoke.py`，ticker `NVDA`，日期 `2024-05-10`，选择 `market` analyst，DeepSeek provider，耗时约 267 秒，最终决策 `Overweight`。
- Demo 输出已保存到 `.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`。
- Full state log 已保存到 `.alphapilot_runtime/results/NVDA/TradingAgentsStrategy_logs/full_states_log_2024-05-10.json`。
- 发现并修复 market tool 注册不一致：`Market Analyst` 提示中要求 `get_verified_market_snapshot`，但 `tools_market` 原先没有注册该工具。
- 添加了显式配置下的 LLM `timeout` / `max_retries` 转发，并用测试覆盖。
- 已在本地安装 `obra/superpowers` skill set，用于后续计划、TDD、调试和 review 工作流。需要重启 Codex 后，新安装的 skills 才会出现在当前可用 skill 列表中。
- 已完成 MVP 所需的 graph flow、agent 职责、dataflows 和报告模块架构文档。
- 新增 `docs/MVP_SCOPE.md`，冻结角色、额度规则、页面、API endpoints、数据库概念和标准化结果结构。
- 新增 `alphapilot.backend` FastAPI MVP，包括 register/login、`/me`、analysis 创建/列表/详情、admin user list 和 admin user patch routes。
- 增加服务端密码 hash、bearer-token auth、默认每日 3 次额度、禁用用户拦截，并从已保存的 NVDA smoke 输出加载 demo result。
- 新增 `frontend/` 静态 OpenBB-inspired dashboard 工作台，包括 dashboard、new analysis、report detail、admin users、public demo、响应式布局和可见的非投资建议免责声明。
- 新增 public `GET /demo/reference`、CORS、前端 login/register 表单、token 持久化，以及接入 API 的 analysis submission 和 demo fallback。
- 已通过 `pytest tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_frontend_mvp.py -q` 验证新增 MVP 行为，8 个测试通过。
- 全量测试也已通过 `pytest -q`：326 个测试和 75 个 subtests 通过，仅有环境 warning。
- 新增 SQLAlchemy 2.0 持久化层 `SqlAlchemyAlphaPilotStore`，支持 PostgreSQL-ready JSONB 字段、token 持久化、quota 持久化、job/result 持久化，并让 API routes 通过 repository 方法访问数据，而不是直接读取内存字典。
- 新增 Alembic 配置和初始 migration，覆盖 `users`、`user_tokens`、`user_quotas`、`analysis_jobs`、`analysis_results`、`api_usage_logs`。
- 在 `docker-compose.yml` 中新增 `postgres` 服务，并在 `.env.example` 中新增 `ALPHAPILOT_DATABASE_URL`。
- 已用 `ALPHAPILOT_DATABASE_URL=sqlite:////tmp/alphapilot_alembic_check.db alembic upgrade head` 验证 migration 可执行。
- 持久化改造后重新运行全量测试：`326 passed, 75 subtests passed`。
- 已选择 Phase 6 部署设计：一台阿里云轻量服务器、Docker Compose、Caddy 反向代理、PostgreSQL、Redis、FastAPI、静态前端和一个后台 worker。
- 新增 Phase 6 后台 worker 路径：live analysis jobs 由 API 入队，并在 HTTP request 外执行。
- 新增 Redis queue implementation、inline test queue、API rate limiting，以及 worker usage/failure logging。
- 新增生产部署脚手架：`docker-compose.prod.yml`、`Caddyfile`、`.env.production.example` 和中英文 `docs/DEPLOYMENT.md`。
- 静态前端默认改为 same-origin API calls，以便在 Caddy 后正常工作；本地直接打开文件时仍可通过 `alphapilot_api_base` 覆盖。
- 已用 `pytest -q` 验证 Phase 6：`332 passed, 75 subtests passed`。
- 已用 SQLite 验证 Alembic migration，并用 `.env.production.example` 验证 Docker Compose production config。
- 补充 Pydantic `EmailStr` 所需但此前漏声明的 `email-validator` 依赖后，已在 `AlphaPilot` conda 环境重新运行测试：`332 passed, 75 subtests passed`。
- 已将 Docker Compose 生产栈部署到 `47.250.149.226`，包括 Caddy、FastAPI、PostgreSQL、Redis 和 worker。
- 已在 2C/2G 服务器上添加 2 GB swap，降低镜像构建时的内存风险。
- 修复 PostgreSQL 下 admin seeding 的外键顺序问题：创建 quota 前先 flush user。
- 将 NVDA demo fixture 打包到 `alphapilot/backend/demo_data/`，生产环境的 `/demo/reference` 不再依赖 gitignored 的 `.alphapilot_runtime` 文件。
- 将 Redis queue timeout 视为空队列，worker 空闲时保持运行，不再反复重启。
- 新增 `ALPHAPILOT_ADMIN_PASSWORD` 支持，并将生产管理员密码轮换为服务器专用随机值。
- 已验证公网部署：`http://47.250.149.226` 的 `/`、`/health`、`/demo/reference` 均返回 HTTP 200。
- 已验证安全项：默认 `admin` 密码返回 HTTP 401，服务器专用随机管理员密码返回 HTTP 200。
- 最近一次在 `AlphaPilot` conda 环境运行全量测试：`336 passed, 75 subtests passed`。
- 已规划 Phase 7 Workflow Router Lean MVP：右侧 Dashboard Copilot、自然语言意图路由、本地优先 ticker directory + AI fallback、Watchlist 基础能力和轻量 Multi-Stock Compare。
- 新增 `docs/WORKFLOW_ROUTER_MVP.md` 及 `docs/docs_CN/` 下的中文镜像。
- 新增 Phase 7 中英文实现计划；实现将从 TDD 开始。
- 新增确定性的本地 ticker directory 和 Workflow Router MVP 边界，并用测试覆盖 exact ticker、公司名、中文名、人物线索、时间段、watchlist、single-analysis 和 multi-compare routing。
- 新增 Watchlist 和 Compare 的持久化/API/前端 MVP 路径，并加入 Dashboard 右侧 Copilot Panel。
- 本地验证通过：`351 passed, 9 warnings, 75 subtests passed`。
- 已用 SQLite 验证 Alembic migration chain 可升级到 `20260615_0002_add_workflow_router_tables.py`。
- 已更新 Caddy 生产代理规则，覆盖 Phase 7 API 前缀：`/copilot/*`、`/watchlist*` 和 `/compare*`。

## 已完成

- [x] 将基础 TradingAgents 项目 clone 到 AlphaPilot 文件夹。
- [x] 创建名为 `AlphaPilot` 的 conda 环境。
- [x] 创建包含 DeepSeek API key 的 `.env`。
- [x] 创建项目计划文档。
- [x] 创建 `docs/docs_CN/` 下的中文镜像文档。
- [x] 使用 `pip install -e .` 将项目安装到 `AlphaPilot` conda 环境。
- [x] 为 `.env` 配置 DeepSeek provider/model overrides。
- [x] 完成第一次 DeepSeek-backed 本地股票分析 smoke test。
- [x] 确认 final decision 和日志已生成。
- [x] 记录足够支撑 MVP schema 设计的核心架构。
- [x] 定义 MVP 后端/前端范围。
- [x] 构建第一版后端 API/auth/quota/admin 脚手架。
- [x] 构建第一版前端产品 UI 脚手架。
- [x] 添加 SQLAlchemy/PostgreSQL 持久化层和 Alembic migration 脚手架。
- [x] 选择第一版部署目标和 Phase 6 生产拓扑。
- [x] 为 live analysis jobs 添加后台 worker queue 路径。
- [x] 添加 rate limiting 和生产部署脚手架。
- [x] 将可控公开 demo 部署到阿里云。
- [x] 验证公网 health/demo endpoints 和生产 worker 稳定性。
- [x] 将生产管理员凭据从本地默认值轮换出去。

## 进行中

- [x] Phase 7 Workflow Router Lean MVP 设计审阅。
- [x] Phase 7 Workflow Router 本地 MVP 实现。

## 待办

- [x] 跑通第一次完整本地股票分析 smoke test。
- [x] 记录核心架构。
- [x] 定义 MVP 后端/前端范围。
- [x] 构建后端 API 和权限系统。
- [x] 构建前端产品 UI。
- [x] 部署可控的公开 demo。
- [ ] 添加域名/HTTPS 和浏览器截图验证。
