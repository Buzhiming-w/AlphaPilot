# AlphaPilot 当前状态

最后更新：2026-06-28

## 当前阶段

Phase 7：Workflow Router Lean MVP

## 当前任务

修复并部署双语报告 pipeline，确保英文是 canonical source report，中文是缓存的完整本地化报告。

## 下一步

1. 验证新生成的 live reports 会产出英文 source report 和缓存的中文完整报告。
2. 继续在已部署环境中测试 Copilot draft 精修流程。
3. 浏览器工具可用后，为重设计后的前端运行浏览器截图验证。
4. 购买域名并将 DNS 指向服务器后，添加域名/HTTPS。

## 当前阻塞

- 最新重设计的浏览器截图验证仍待补充。
- 暂无域名，所以公开 demo 仍通过服务器 IP 使用 HTTP。

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
- 已将 Phase 7 部署到阿里云 demo，服务器提交为 `00a86d8`。
- 公网 smoke checks 已通过：`/` 返回 HTTP 200 且包含 Copilot UI，`/health` 返回 HTTP 200，`/demo/reference` 返回 HTTP 200，未登录访问 `/copilot/route`、`/watchlist` 和 `/compare/test` 均返回 HTTP 401。
- 产品 review 发现 Dashboard 右上角 quick analysis 表单是旧版 MVP 入口残留。应删除该入口，让 Dashboard 的分析启动来自 Copilot confirmation 或 `Analysis` 栏目。
- 产品导航决策：左侧 sidebar 只保留 `Dashboard`、`Analysis` 和 `Compare`；`New Analysis` 和 `Report Detail` 合并进 `Analysis`；`Watchlist` 隐藏为一级入口；`Login` / account 和 admin controls 移到右上角区域。
- 账户区域决策：登录后右上角必须显示用户 `display_name`，必要时 fallback 到 email。
- `Analysis` 和 `Compare` 都必须保留历史记录，Dashboard Copilot confirmation 应直接加载对应分析界面。
- Dashboard decision 展示问题：已保存 NVDA demo 的 `Overweight` rating 不应作为当前 decision 展示。应删除、替换为 `No active analysis`，或重标为 `Demo result`。
- Copilot UX 决策：用两步对话流替换 shortcut/action buttons：一个自然语言 submit action，服务端 LLM 返回结构化 draft 后，再提供一个最终 confirmation action。用户可在确认前通过同一对话继续修正 draft。
- Running report UX 决策：`Analysis` 和 `Compare` 应展示真实 workflow progress 和阶段性结论，并用打字机式效果逐步显示。后端应发出结构化 progress events，最终持久化报告应替换或合并进行中的 streamed text。
- 已在本地实现 Dashboard / Analysis / Compare 清理：删除旧 sidebar items 和右上角 quick analysis，将 login/account/admin controls 移到右上角账户区，隐藏 Watchlist 一级导航，并将 analysis 创建、详情、历史合并进 `Analysis`。
- 已将 Copilot routing 更新为返回 `analysis` 或 `compare` draft，并加入可选的服务端 LLM 解析层；解析后仍使用确定性 ticker validation 兜底校验。
- 已新增 `analysis_progress_events` 持久化、`GET /analysis/{job_id}/progress`、worker progress events，以及前端 polling/typewriter 运行中报告展示。
- 已修复 live worker result 保存问题：写入数据库 JSON 字段前，将 LangChain/TradingAgents raw state 转成 JSON-safe values。
- 已扩展 Copilot 模糊识别能力，使“美国市值最大的医疗股票”这类相对模糊的请求可以返回候选 ticker 列表，交由用户确认。
- 已为 `Analysis` 和 `Compare` 历史项添加删除能力，包括 queued/running/completed analysis jobs；如果已删除的 queued job 后续仍被 worker 从旧队列取到，会被安全跳过。
- 最新一次 router/deletion/frontend 相关目标测试：`26 passed`。
- 最近一次本地全量测试：`359 passed, 9 warnings, 75 subtests passed`。
- 已将最新 Dashboard / Analysis / Compare 重设计部署到阿里云 demo：`http://47.250.149.226/`。
- 已在线上 PostgreSQL 执行 migration `20260615_0003_add_analysis_progress_events`。
- 已重建并重启生产 `api`、`worker` 和 `caddy` 服务。
- 公网 smoke checks 通过：`/`、`/health` 和 `/demo/reference` 均返回 HTTP 200。
- 生产 Copilot smoke 对中文模糊请求返回医疗候选股票 `LLY`、`UNH` 和 `JNJ`。
- 生产删除 smoke 通过：queued `Analysis` job 删除返回 HTTP 204，随后详情查询返回 HTTP 404；`Compare` 删除返回 HTTP 204。
- 修复 compare workflow 删除时的生产 SQLAlchemy warning：删除 workflow 前先用 bulk delete 清理 compare symbols。
- 产品 UX 决策：`Analysis` 和 `Compare` 中的手动表单提交应作为次级路径。Dashboard Copilot confirmation 应先启动或创建 workflow，再进入对应 workspace，不应让用户再点击一次 `Start Workflow`。
- 已实现折叠后的手动入口：`Analysis` 表单现在默认收起在 `Manual analysis` 区域内，`Compare` 表单现在默认收起在 `Manual compare` 区域内。
- 最新一次针对折叠手动入口的前端验证通过：`pytest -q tests/test_alphapilot_frontend_mvp.py` 返回 `3 passed`。
- 折叠手动入口更新后的最新一次本地全量测试：`359 passed, 9 warnings, 75 subtests passed`。
- 已将折叠手动入口的前端/docs 更新部署到 `http://47.250.149.226/`。
- 生产 smoke checks 通过：`/` 包含 `Manual analysis` 和 `Manual compare`，`/styles.css` 包含 `.manual-workflow`，`/health` 返回 `{"status":"ok"}`。
- 产品实现更新：Dashboard Runtime 现在会在选中的 analysis result/job 存在耗时数据时展示对应 runtime；没有耗时数据时才显示 `--`。
- 产品实现更新：`Analysis` 和 `Compare` progress panel 已加入 live status header、elapsed/latest-update 标签、轻量存活指示和阶段式进度条。
- 产品实现更新：最终报告现在通过安全 Markdown 渲染路径展示，会先转义 raw HTML，再生成 headings、lists、tables、blockquotes 和 code blocks。
- 产品实现更新：右上角已加入全局 `EN` / `中文` UI 状态，report 语言切换与 UI 语言独立，并默认展示英文报告。
- 产品实现更新：Dashboard 顶部 eyebrow 已改为 `Agentic stock research terminal`，左侧品牌区不再显示小字 `Research terminal`。
- 产品实现更新：普通用户仍为每日 3 次 live workflow；admin 用户绕过 daily quota，但仍经过现有系统级 rate limiter。
- 产品实现更新：登录用户现在看到 display-name label 和明确的 `Logout`；admin 用户可见 `Manage Users`，点击后打开用户管理界面。
- 产品实现更新：Dashboard 现在包含紧凑的 `How to use AlphaPilot` guide，admin 用户额外看到 `Admin tools` 说明。
- Report 本地化实现更新：当 `ALPHAPILOT_REPORT_TRANSLATION_ENABLED=true` 时，worker 会基于已完成的英文 source report 生成中文缓存报告，在 `report_translations.zh` 中记录翻译状态，失败时按配置次数重试，并在已有中文缓存时避免重复生成。英文仍是 canonical source report。
- Report 本地化修正：source workflow output 必须使用 `TRADINGAGENTS_OUTPUT_LANGUAGE=English` 生成。worker 现在会把组装后的英文完整报告作为 canonical source，将中文完整报告缓存到 `localized_sections.zh.report`，前端只把 `localized_sections.zh.final` 作为旧结果的 fallback。
- Security Master 规划更新：新增 `docs/SECURITY_MASTER_PLAN.md` 及中文镜像，定义数据库驱动的美股/ETF 识别计划、Nasdaq Trader + SEC 同步、`securities` 和 `security_aliases` 表、未解析查询日志，以及 admin 维护中文名/人物线索 aliases 的流程。设计明确要求常见中文名和人物线索维护在数据库 aliases 中，而不是硬编码在 Python 列表中，并规定首次手动同步后，生产环境每周一 00:00 按服务器时间自动同步。
- Security Master 实现更新：已添加 Security Master SQLAlchemy models 和 Alembic migration `20260615_0004_add_security_master_tables`、基于 fixture 的 Nasdaq Trader + SEC 同步、常见美股英文名/中文名/人物线索 seed aliases、`SecurityMasterResolver`、API app resolver wiring、中英文混排 ticker token 抽取、`2015年6月至今` 这类月份日期解析，以及受 `ALPHAPILOT_SECURITY_MASTER_AUTO_SYNC_ENABLED` 控制的 worker-side 每周一 00:00 自动同步调度。
- 产品决策：当前阶段不做 Admin alias 维护 UI/endpoints。对于当前单人运营 demo，中文名、人物线索和其他 aliases 直接维护在 `security_aliases` 数据库表中。
- 下一步 Copilot UX 决策：先增强 draft 精修体验，而不是做 admin alias UI。已识别股票应显示为可删除 chips；有歧义的实体需要用户选择；未识别实体应单独展示；`Compare` 确认前要求最终选择 2 到 5 只股票；`Analysis` 确认允许 1 只或多只股票。
- Copilot draft 精修实现更新：`/copilot/route` 现在会返回候选组和未识别实体；Dashboard draft 将已选股票渲染为可删除 chips，允许用户从有歧义的 ticker 候选中选择，存在未识别实体时阻止确认，`Compare` 确认前校验 2 到 5 只 selected stocks，`Analysis` 确认前校验至少 1 只 selected stock。本地 fallback ticker directory 也已补充常见 MMM/3M 和 ORCL/Oracle aliases。
- 部署更新：Copilot draft 精修改动已部署到 `http://47.250.149.226/`。生产 smoke checks 已验证 `/health`、前端 `/` 和 `/app.js`、`比较3M和orcl两只股票的表现，从2015年6月至今` 的 Copilot route、`Neverland Robotics` 未识别实体处理，以及 Docker Compose 服务健康状态。

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
- [x] Phase 7 Workflow Router 阿里云 demo 部署。
- 2026-06-15 report 翻译和 Security Master 实现已部署到生产环境。
- 已完成验证：`node --check frontend/app.js`；`pytest -q tests/test_alphapilot_frontend_mvp.py tests/test_alphapilot_backend_mvp.py::test_admin_analysis_creation_bypasses_daily_quota`；以及 `pytest -q tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_frontend_mvp.py tests/test_alphapilot_phase6.py tests/test_alphapilot_workflow_router.py tests/test_alphapilot_sqlalchemy_store.py`。
- 已完成本地全量验证：`node --check frontend/app.js && pytest -q` 返回 `360 passed, 9 warnings, 75 subtests passed`。
- 已将本轮产品反馈实现部署到 `http://47.250.149.226/`：将本地 workspace 同步到 `/opt/AlphaPilot`，重建 `api` 和 `worker`，执行 `alembic upgrade head`，并重启 `api`、`worker` 和 `caddy`。
- 生产 smoke checks 通过：`/health` 返回 `{"status":"ok"}`，`/` 包含 `Agentic stock research terminal`、`How to use AlphaPilot`、`Manage Users` 和 `Logout`，`/app.js` 包含 `renderMarkdown`、`renderProgressChrome`、`Admin access` 和 `alphapilot_ui_locale`，且 `api`、`caddy`、`postgres`、`redis`、`worker` 均在运行。
- 浏览器截图验证仍待补充，因为 in-app browser 返回 `Browser is not available: iab`；本地 `127.0.0.1:4173` 和 `127.0.0.1:8100/health` 的 HTTP smoke checks 已通过。
- 当前 report 翻译和 Security Master 目标验证已通过：`pytest -q tests/test_alphapilot_phase6.py tests/test_alphapilot_security_master.py tests/test_alphapilot_sqlalchemy_store.py tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_workflow_router.py` 返回 `42 passed`。
- Report 翻译和 Security Master 改动后的完整本地验证已通过：`node --check frontend/app.js`；`python -m compileall -q alphapilot/backend`；`ALPHAPILOT_DATABASE_URL=sqlite:////tmp/alphapilot_alembic_security_master.db alembic upgrade head`；以及 `pytest -q` 返回 `367 passed, 9 warnings, 75 subtests passed`。
- 已将 report 翻译和 Security Master 改动部署到 `http://47.250.149.226/`：将本地 workspace 同步到 `/opt/AlphaPilot`，确认生产 `.env.production` 已开启 report translation 和 Security Master auto sync，重建 `api` 和 `worker`，执行 Alembic migration `20260615_0004_add_security_master_tables`，并重启 `api`、`worker` 和 `caddy`。
- 生产 smoke checks 通过：`/health` 返回 `{"status":"ok"}`，首页包含 `Agentic stock research terminal`、`How to use AlphaPilot`、`Manage Users` 和 `Logout`，Copilot 已将 `比较3M和orcl两只股票的表现，从2015年6月至今` 解析为 `MMM` 和 `ORCL` 且 `start_date=2015-06-01`，并确认 `api`、`caddy`、`postgres`、`redis` 和 `worker` 均在运行。
- 已将 Copilot draft 精修改动部署到 `http://47.250.149.226/`：将本地 workspace 同步到 `/opt/AlphaPilot`，重建 `api` 和 `worker`，执行 `alembic upgrade head`，并重启 `api`、`worker` 和 `caddy`。
- 生产 smoke checks 通过：`/health` 返回 `{"status":"ok"}`，`/` 包含 `Agentic stock research terminal`、`copilotDraft` 和 `Manual analysis`，`/app.js` 包含 `removeDraftSymbol`、`selectDraftCandidate`、`candidate_groups` 和最终 symbol 数量校验文案，Copilot 已将 `比较3M和orcl两只股票的表现，从2015年6月至今` 解析为 `MMM` 和 `ORCL` 且 `start_date=2015-06-01`，Copilot 对无法识别的 compare 请求返回 `unresolved_entities=["Neverland Robotics"]`，并确认 `api`、`caddy`、`postgres`、`redis` 和 `worker` 均在运行。
- 已将双语报告修正部署到 `http://47.250.149.226/`：生产 `.env.production` 现在设置 `TRADINGAGENTS_OUTPUT_LANGUAGE=English`，已重建并重启 `api` 和 `worker`，`/health` 返回 `{"status":"ok"}`，`/app.js` 会优先读取 `localized_sections.zh.report`，再兼容旧的 `localized_sections.zh.final`，并通过容器内 smoke 确认 worker 会把组装后的英文完整报告翻译并缓存到 `localized_sections.zh.report`。

## 待办

- [x] 跑通第一次完整本地股票分析 smoke test。
- [x] 记录核心架构。
- [x] 定义 MVP 后端/前端范围。
- [x] 构建后端 API 和权限系统。
- [x] 构建前端产品 UI。
- [x] 部署可控的公开 demo。
- [ ] 添加域名/HTTPS 和浏览器截图验证。
