# AlphaPilot 当前状态

最后更新：2026-06-10

## 当前阶段

Phase 5：前端 MVP

## 当前任务

将第一版后端/前端 MVP 脚手架推进为已连接、可持久化的产品 demo。

## 下一步

1. 用 PostgreSQL/SQLAlchemy 或 SQLModel 替换 `AlphaPilotStore` 内存存储。
2. 为 live `TradingAgentsGraph.propagate()` 运行添加真实后台 worker。
3. 选择第一版部署目标，并添加环境/部署文档。
4. 添加 rate limiting 和生产级 token/session 处理。
5. 当 in-app browser 或 Playwright runtime 可用后，补充浏览器截图验证。

## 当前阻塞

暂无记录。

## 重要上下文

- 仓库路径：`/Users/buzhiming/Desktop/AlphaPilot`
- 当前项目名：AlphaPilot
- 基础项目：TauricResearch/TradingAgents
- 本地环境名：`AlphaPilot`
- `.env` 已经包含 DeepSeek API key，但 provider/model overrides 仍需确认。
- 原始引擎入口是 `TradingAgentsGraph.propagate()`。
- 默认配置目前使用 OpenAI，除非通过 `TRADINGAGENTS_*` 环境变量覆盖。
- Codex 后续检查时优先检查 `docs/` 下的英文文档；用户查看时可以对照 `docs/docs_CN/` 下的中文文档。

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
- 全量测试也已通过 `pytest -q`：322 个测试和 75 个 subtests 通过，仅有环境 warning。

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

## 进行中

- [ ] 用持久化存储和生产后台任务替换内存 store/同步任务。

## 待办

- [x] 跑通第一次完整本地股票分析 smoke test。
- [x] 记录核心架构。
- [x] 定义 MVP 后端/前端范围。
- [x] 构建后端 API 和权限系统。
- [x] 构建前端产品 UI。
- [ ] 部署可控的公开 demo。
