# AlphaPilot 架构笔记

最后更新：2026-06-10

本文档用于记录我们在阅读 TradingAgents 代码库并将其改造成 AlphaPilot 时学到的内容。

## 当前理解

AlphaPilot 会保留 TradingAgents Python 引擎作为决策分析核心，并在它外面增加产品层：

- 后端 API：认证、权限、额度、任务编排。
- 后台 worker：运行耗时的 LLM 分析任务。
- 数据库：保存用户、任务、结果、额度和使用日志。
- 前端：提交股票分析并查看报告。
- 管理员控制：防止服务端 LLM API key 被滥用。

## Phase 4/5 MVP 实现快照

当前产品层文件：

- `alphapilot/backend/app.py`：FastAPI app factory 和路由定义。
- `alphapilot/backend/store.py`：内存 repository，包含数据库形状的用户、额度、任务和结果实体。
- `alphapilot/backend/engine_service.py`：API 路由和 `TradingAgentsGraph` 之间的服务边界。
- `alphapilot/backend/result_normalizer.py`：将原始 engine state 或已保存 log JSON 转成前端报告 sections。
- `alphapilot/backend/security.py`：本地密码 hash 和 bearer token 生成。
- `frontend/index.html`、`frontend/styles.css`、`frontend/app.js`：静态 OpenBB-inspired MVP 工作台。

重要取舍：

- 后端当前使用内存 store，以便快速测试 auth、quota、admin controls、result normalization 和前端集成。
- Store 方法按未来数据库操作形状设计，所以 Phase 6 可以用 PostgreSQL/SQLAlchemy 替换存储，而不改变路由语义。

## 第一次已验证本地运行

命令：

- `conda run --no-capture-output -n AlphaPilot python scripts/run_phase1_smoke.py`

运行详情：

- Ticker：`NVDA`
- 交易日期：`2024-05-10`
- 选择的 analysts：`market`
- LLM provider：`deepseek`
- Quick model：`deepseek-v4-flash`
- Deep model：`deepseek-v4-pro`
- 耗时：约 267 秒
- 最终处理后的决策：`Overweight`

输出文件：

- Demo summary：`.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`
- Full state log：`.alphapilot_runtime/results/NVDA/TradingAgentsStrategy_logs/full_states_log_2024-05-10.json`
- Memory log：`.alphapilot_runtime/memory/trading_memory.md`

Smoke 输出中观察到的可用模块：

- `market_report`
- `investment_plan`
- `trader_investment_plan`
- `final_trade_decision`

重要发现：

- `Market Analyst` 会提示模型调用 `get_verified_market_snapshot`，但 graph 的 `tools_market` 节点原本只注册了 `get_stock_data` 和 `get_indicators`。
- 这导致第一次诊断运行中出现 invalid tool call。
- 已通过在 `TradingAgentsGraph._create_tool_nodes()` 中注册 `get_verified_market_snapshot` 修复。

## 核心引擎

主要类：

- `tradingagents/graph/trading_graph.py`
- `TradingAgentsGraph`

主要方法：

- `TradingAgentsGraph.propagate(company_name, trade_date, asset_type="stock")`

预期高层输入：

- 股票代码，例如 `NVDA` 或 `AAPL`。
- 交易日期，例如 `2026-06-10`。
- 资产类型，通常是 `stock`。

已验证的高层输出：

- 完整 graph state。
- 处理后的交易决策信号。

详细行为：

- `TradingAgentsGraph.propagate(company_name, trade_date, asset_type="stock")` 是同步运行，可能耗时数分钟。
- 它返回 `(final_state, processed_signal)`。
- 它会把 full-state JSON 日志写到 `results_dir/<safe_ticker>/TradingAgentsStrategy_logs/full_states_log_<trade_date>.json`。
- 它会把最终决策写入 memory log，供后续 reflection 使用。
- 如果 `checkpoint_enabled` 为 true，它会用每个 ticker/date 的 checkpoint thread 重新编译 graph，并在成功完成后清理 checkpoint。

Smoke run 已验证 full state log 包含：

- `company_of_interest`
- `trade_date`
- `market_report`
- `sentiment_report`
- `news_report`
- `fundamentals_report`
- `investment_debate_state`
- `trader_investment_decision`
- `risk_debate_state`
- `investment_plan`
- `final_trade_decision`

已知命名不一致：

- Live graph state 使用 `trader_investment_plan`。
- 持久化 full-state log JSON 使用 `trader_investment_decision`。
- AlphaPilot 后端 normalizer 同时兼容两者，并对前端暴露稳定的 `trader` section。

## Agent Flow

Graph 在 `tradingagents/graph/setup.py` 中组装。

1. 按配置选择的 analyst 列表依次运行：`market`、`social`、`news`、`fundamentals`。
2. 每个 analyst 可以调用对应 tool node，直到 conditional logic 发现不再需要 tool call。
3. 进入下一个 analyst 前会清理 analyst messages，以控制状态大小。
4. Bull 和 bear researchers 进行投资观点辩论。
5. Research manager 写出 `investment_plan`。
6. Trader 将计划转成 `trader_investment_plan`。
7. Aggressive、conservative、neutral risk debators 讨论 trader plan。
8. Portfolio manager 写出 `final_trade_decision`。

## Agent 职责

- Market analyst：技术指标、OHLCV 数据、verified market snapshot、价格/指标解释。
- Sentiment analyst：已收集的 ticker news/social-style sentiment 输入。
- News analyst：通过 `get_news`、`get_global_news` 和 insider transaction 工具分析 ticker 和宏观新闻。
- Fundamentals analyst：公司 profile、fundamentals、balance sheet、cash flow、income statement 工具。
- Bull researcher：最强看多/支持投资论点。
- Bear researcher：最强风险/下行论点。
- Research manager：辩论后的最终投资计划。
- Trader：基于研究生成可执行的投资决策计划。
- Risk debators：aggressive、conservative、neutral 三种风险视角。
- Portfolio manager：最终风险调整后决策。

## Dataflows

当前 dataflow modules 包括：

- `y_finance.py`、`stockstats_utils.py`、`market_data_validator.py`：市场和指标数据。
- `yfinance_news.py`、`reddit.py`、`stocktwits.py`：新闻/sentiment-style 输入。
- `alpha_vantage_*`：可选 Alpha Vantage 市场、新闻、基本面和指标。
- `symbol_utils.py`、`config.py`：ticker 处理和 vendor 选择。

风险区域：

- 网络/数据 provider 不稳定。
- 最近日期可能市场数据不完整。
- LLM tool-call 与已注册工具不匹配。
- 如果直接在 HTTP 请求里调用，长同步运行会拖慢服务。

## 当前需要学习的代码区域

- `tradingagents/default_config.py`
  - 默认模型/provider 配置。
  - results/cache 路径。
  - debate rounds 和 analyst 设置。
  - 数据 vendor 配置。

- `tradingagents/graph/trading_graph.py`
  - 引擎编排。
  - LLM client 设置。
  - Tool node 设置。
  - State logging。
  - Checkpoint/resume 行为。

- `tradingagents/graph/propagation.py`
  - 初始 graph state 结构。
  - Graph invocation 参数。

- `tradingagents/agents/analysts/`
  - Market analyst。
  - Sentiment/social analyst。
  - News analyst。
  - Fundamentals analyst。

- `tradingagents/agents/researchers/`
  - Bull researcher。
  - Bear researcher。
  - Research manager。

- `tradingagents/agents/trader/`
  - Trader agent 和 investment plan 生成。

- `tradingagents/agents/risk_mgmt/`
  - Aggressive、neutral、conservative risk discussion。

- `tradingagents/agents/managers/portfolio_manager.py`
  - 最终 portfolio decision。

- `tradingagents/dataflows/`
  - 市场数据。
  - 新闻数据。
  - 基本面数据。
  - Ticker 处理。

## 前端需要展示的报告模块

根据 `TradingAgentsGraph._log_state()` 和 NVDA smoke output 已确认包括：

- `market_report`
- `sentiment_report`
- `news_report`
- `fundamentals_report`
- `investment_debate_state`
- `trader_investment_decision`
- `risk_debate_state`
- `investment_plan`
- `final_trade_decision`

AlphaPilot API 会将它们标准化为：

- `market`
- `sentiment`
- `news`
- `fundamentals`
- `investment`
- `trader`
- `final`

## 产品架构草图

```text
User Browser
    |
    v
Frontend App
    |
    v
Backend API
    |
    +--> Auth and permissions
    +--> Quota checks
    +--> Analysis job records
    |
    v
Background Worker
    |
    v
TradingAgentsGraph.propagate()
    |
    +--> LLM provider: DeepSeek
    +--> Market/news/fundamental data providers
    |
    v
Database stores final result
```

## 开放问题

- AlphaPilot 的 quick thinking 和 deep thinking 应使用哪些具体 DeepSeek 模型？
- 一次默认分析大概耗时多久？
- 单次分析平均 token/API 成本是多少？
- Public MVP 应启用哪些 analyst modules？
- 普通用户是否可以选择日期和深度，还是由 admin 控制？
- 注册应该开放、邀请码制，还是管理员审核？

## 风险

- 如果公开创建分析任务且没有额度控制，LLM 成本可能被滥用。
- 如果直接在 HTTP 请求里运行分析，任务可能过慢。
- 外部数据 provider 可能不稳定。
- LLM 输出具有非确定性。
- 如果产品措辞不谨慎，可能产生金融建议责任风险。
- 如果太晚加入 worker/database/cache，部署复杂度会增加。

## 第一次运行后需要补充

- 真实示例命令：`conda run --no-capture-output -n AlphaPilot python scripts/run_phase1_smoke.py`
- 真实运行耗时：`market`-only smoke path 约 267 秒。
- 真实输出路径：`.alphapilot_runtime/demo_outputs/phase1_smoke_NVDA_2024-05-10.json`
- 真实最终决策结构：processed signal 字符串，加 Markdown 风格的完整 `final_trade_decision`。
- 失败依赖或缺失 key：补齐 `.env` DeepSeek 设置后暂无。
- 推荐最小配置：DeepSeek provider/model 环境变量、workspace runtime 路径、开发/smoke 运行时显式设置 LLM timeout/max_retries。
