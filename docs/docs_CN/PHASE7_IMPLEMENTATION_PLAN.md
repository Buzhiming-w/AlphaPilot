# Phase 7 Workflow Router 实现计划

最后更新：2026-06-15

> **给 agentic worker 的要求：** 实现时必须使用 `test-driven-development`。由于项目所有者要求继续沿用当前项目目录，本仓库将在当前 workspace 内 inline 执行计划。

**目标：** 实现 `docs/WORKFLOW_ROUTER_MVP.md` 中定义的 Lean MVP：登录用户在 Dashboard Copilot 中输入自然语言请求后，可以进入 Watchlist、Multi-Stock Compare 或 Single Stock Analysis draft。

**架构：** 先增加可测试的后端边界，再接 UI：ticker directory、workflow router、store persistence、API endpoints。第一版 router 保持确定性和易测性，AI fallback 先保留为可注入接口，不直接接真实 LLM。前端继续使用当前静态 HTML/CSS/JavaScript 和 OpenBB 风格的紧凑金融工作台。

**技术栈：** FastAPI、Pydantic、SQLAlchemy 2.0、Alembic、PostgreSQL/SQLite 测试兼容、vanilla HTML/CSS/JavaScript、pytest。

---

## 执行状态

- Ticker Directory、Workflow Router、Watchlist、Compare 和前端 Copilot MVP 已在本地实现。
- Phase 7 focused verification 已通过：`30 passed`。
- 本地全量验证已通过：`351 passed, 9 warnings, 75 subtests passed`。
- 云部署已完成，阿里云 demo 当前运行提交 `00a86d8`。

## 文件地图

- 新建 `alphapilot/backend/ticker_directory.py`：本地美股记录、别名、人物线索和 fuzzy lookup。
- 新建 `alphapilot/backend/workflow_router.py`：把用户文本解析为结构化 draft workflow。
- 修改 `alphapilot/backend/schemas.py`：Copilot、Watchlist、Compare 请求/响应模型。
- 修改 `alphapilot/backend/store.py`：Watchlist 和 Compare workflow 的内存 dataclass 与方法。
- 修改 `alphapilot/backend/db_models.py`：新增 `watchlist_items`、`compare_workflows`、`compare_workflow_symbols` SQLAlchemy records。
- 修改 `alphapilot/backend/sqlalchemy_store.py`：实现与内存 store 对齐的持久化方法。
- 修改 `alphapilot/backend/app.py`：新增 `/copilot/route`、`/watchlist`、`/compare` 鉴权 API。
- 新建 `alembic/versions/20260615_0002_add_workflow_router_tables.py`：生产迁移。
- 修改 `frontend/index.html`：加入 Watchlist、Compare 和 Dashboard Copilot UI。
- 修改 `frontend/app.js`：调用新 API 并渲染 draft workflow。
- 修改 `frontend/styles.css`：加入右侧 Copilot 与紧凑金融 workflow 样式。
- 新增/扩展测试：
  - `tests/test_alphapilot_ticker_directory.py`
  - `tests/test_alphapilot_workflow_router.py`
  - `tests/test_alphapilot_backend_mvp.py`
  - `tests/test_alphapilot_sqlalchemy_store.py`
  - `tests/test_alphapilot_frontend_mvp.py`
- 更新文档：
  - `docs/STATUS.md`
  - `docs/PROJECT_PLAN.md`
  - `docs/docs_CN/STATUS.md`
  - `docs/docs_CN/PROJECT_PLAN.md`

## Task 1：Ticker Directory

**文件：**
- 新建：`alphapilot/backend/ticker_directory.py`
- 测试：`tests/test_alphapilot_ticker_directory.py`

- [ ] **Step 1：编写失败测试**

覆盖 exact ticker、公司名、别名、中文公司名、人物线索、ambiguous matches 和 no match。

运行：

```bash
pytest tests/test_alphapilot_ticker_directory.py -q
```

预期：失败，因为 `alphapilot.backend.ticker_directory` 尚不存在。

- [ ] **Step 2：实现最小 directory**

创建 `TickerMatch` dataclass 和 `LocalTickerDirectory.search(query, limit=5)` 方法。初始记录包含 NVDA、AMD、AAPL、MSFT、GOOGL、AMZN、META、TSLA、BRK.B。保留 `market`、`exchange`、`currency`、`confidence` 和 `match_reason`。

- [ ] **Step 3：验证通过**

运行：

```bash
pytest tests/test_alphapilot_ticker_directory.py -q
```

预期：ticker directory 测试全部通过。

## Task 2：Workflow Router

**文件：**
- 新建：`alphapilot/backend/workflow_router.py`
- 测试：`tests/test_alphapilot_workflow_router.py`

- [ ] **Step 1：编写失败测试**

覆盖：
- “帮我比较黄仁勋的公司和 AMD，从 2024 年初到现在” route 到 `multi_compare`，解析出 NVDA 和 AMD，并保存 `start_date=2024-01-01`。
- “把苹果加入股票池” route 到 `add_to_watchlist`。
- “研究英伟达 2024-05-10” route 到 `single_analysis`，并得到 `end_date=2024-05-10`。
- 模糊未知文本 route 到 `clarify`。

运行：

```bash
pytest tests/test_alphapilot_workflow_router.py -q
```

预期：失败，因为 `workflow_router` 尚不存在。

- [ ] **Step 2：实现最小 router**

创建 `WorkflowRouter.route(message, today=None)`。MVP 使用确定性 keyword rules 判断 intent，用 `LocalTickerDirectory` 解析 symbols，用简单日期解析支持 ISO 日期、“2024 年初”、“today”、“now”、“现在”。返回可序列化 draft，字段包含 `intent`、`symbols`、`start_date`、`end_date`、`analysis_anchor`、`requires_confirmation` 和 `message`。

- [ ] **Step 3：验证通过**

运行：

```bash
pytest tests/test_alphapilot_workflow_router.py -q
```

预期：workflow router 测试全部通过。

## Task 3：Store 与数据库持久化

**文件：**
- 修改：`alphapilot/backend/store.py`
- 修改：`alphapilot/backend/db_models.py`
- 修改：`alphapilot/backend/sqlalchemy_store.py`
- 新建：`alembic/versions/20260615_0002_add_workflow_router_tables.py`
- 测试：`tests/test_alphapilot_sqlalchemy_store.py`

- [ ] **Step 1：编写失败持久化测试**

新增测试：
- 一个用户 create/list/delete watchlist item；
- 另一个用户不能删除该 item；
- 创建包含两个 symbols 的 compare workflow，并能跨 store instance 持久化。

运行：

```bash
pytest tests/test_alphapilot_sqlalchemy_store.py -q
```

预期：失败，因为 watchlist 和 compare 方法尚不存在。

- [ ] **Step 2：实现内存与 SQLAlchemy stores**

新增 dataclasses：`WatchlistItem`、`CompareWorkflow`、`CompareWorkflowSymbol`。新增 store 方法：
- `create_watchlist_item`
- `list_watchlist_items`
- `delete_watchlist_item`
- `create_compare_workflow`
- `get_compare_workflow`

新增 SQLAlchemy records 和对应 Alembic migration。使用指向 `users.id` 的外键，以及可选的 `analysis_jobs.id` 外键。

- [ ] **Step 3：验证通过**

运行：

```bash
pytest tests/test_alphapilot_sqlalchemy_store.py -q
```

预期：SQLAlchemy store 测试全部通过。

## Task 4：API Routes

**文件：**
- 修改：`alphapilot/backend/schemas.py`
- 修改：`alphapilot/backend/app.py`
- 测试：`tests/test_alphapilot_backend_mvp.py`

- [ ] **Step 1：编写失败 API 测试**

新增测试：
- guest 调 `/copilot/route` 返回 401；
- 登录用户调 `/copilot/route` 得到 multi-compare draft，且不消耗 quota；
- `/watchlist` add/list/delete 对 owner 可用；
- `/compare` 可以用两个 confirmed symbols 创建 workflow；
- inactive user 不能创建 watchlist 或 compare workflow。

运行：

```bash
pytest tests/test_alphapilot_backend_mvp.py -q
```

预期：失败，因为 API routes 尚不存在。

- [ ] **Step 2：实现 API schemas 和 routes**

新增请求/响应模型和 routes：
- `POST /copilot/route`
- `GET /watchlist`
- `POST /watchlist`
- `DELETE /watchlist/{item_id}`
- `POST /compare`
- `GET /compare/{compare_id}`

复用现有 `current_user`、`enforce_rate_limit` 和 disabled-account checks。

- [ ] **Step 3：验证通过**

运行：

```bash
pytest tests/test_alphapilot_backend_mvp.py -q
```

预期：backend MVP 测试全部通过。

## Task 5：Frontend MVP

**文件：**
- 修改：`frontend/index.html`
- 修改：`frontend/app.js`
- 修改：`frontend/styles.css`
- 测试：`tests/test_alphapilot_frontend_mvp.py`

- [ ] **Step 1：编写失败结构测试**

断言前端包含：
- `id="copilotForm"`
- `id="copilotMessage"`
- `id="copilotDraft"`
- `data-view="watchlist"`
- `data-view="compare"`
- JavaScript 调用 `/copilot/route`、`/watchlist` 和 `/compare`。

运行：

```bash
pytest tests/test_alphapilot_frontend_mvp.py -q
```

预期：失败，因为 UI 元素尚不存在。

- [ ] **Step 2：实现 UI**

在 Dashboard 中加入右侧 Copilot Panel。在 sidebar 中加入 Watchlist 和 Compare 视图。渲染 ticker candidates、date range 和确认按钮。游客或未登录状态下，鉴权请求失败时显示 login-required 状态。

- [ ] **Step 3：验证通过**

运行：

```bash
pytest tests/test_alphapilot_frontend_mvp.py -q
```

预期：frontend structure 测试全部通过。

## Task 6：完整验证与文档

**文件：**
- 修改：`docs/STATUS.md`
- 修改：`docs/PROJECT_PLAN.md`
- 修改：`docs/docs_CN/STATUS.md`
- 修改：`docs/docs_CN/PROJECT_PLAN.md`

- [ ] **Step 1：运行 focused tests**

```bash
pytest tests/test_alphapilot_ticker_directory.py tests/test_alphapilot_workflow_router.py tests/test_alphapilot_backend_mvp.py tests/test_alphapilot_sqlalchemy_store.py tests/test_alphapilot_frontend_mvp.py -q
```

预期：focused tests 全部通过。

- [ ] **Step 2：运行本地完整测试**

```bash
pytest -q
```

预期：云部署前，本地测试全部通过。

- [ ] **Step 3：更新文档**

在中英文文档中标记 Phase 7 实现进度，记录已知限制，并注明云部署需要在本地验证通过后进行。

- [ ] **Step 4：提交并推送**

```bash
git status --short
git add alphapilot frontend tests alembic docs
git commit -m "feat: add workflow router lean mvp"
git push origin alphapilot-mvp
```

预期：远端分支包含实现与文档。

## 自检

- Spec 覆盖：计划覆盖 Copilot routing、ticker discovery、time parsing、Watchlist、Compare、permission gates、persistence、frontend entry points、docs 和本地验证。
- 范围控制：计划不包含完整持久化聊天历史、真实 range analytics、付费访问、提醒系统或专用 compare-agent 推理。
- 类型一致性：后端 API 与持久化任务统一使用 `ticker`、`company_name`、`market`、`exchange`、`currency`、`start_date`、`end_date` 和 `analysis_anchor`。
- 占位扫描：Lean MVP 不依赖未定义的后续工作。
