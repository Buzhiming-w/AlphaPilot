# 产品导航重设计

最后更新：2026-06-15

## 目标

将 AlphaPilot 的产品导航简化为真实分析工作流，而不是暴露 MVP 阶段的实现页面。

产品应该像一个研究工作台，核心只有两类分析模式：

- `Analysis`：单股票或多股票研究分析。
- `Compare`：明确的多股票横向对比。

`Dashboard` 作为 Copilot、状态和最近活动的起点。

## 主导航

左侧 sidebar 只保留：

```text
Dashboard
Analysis
Compare
```

左侧不应再包含：

- `Login`
- `New Analysis`
- `Report Detail`
- `Watchlist`
- `Admin Users`
- `Public Demo`

## 右上角账户区

登录和 admin controls 应移出左侧 sidebar。

右上角行为：

- 未登录用户显示 `Login`。
- 已登录用户在右上角账户区域显示当前用户的 display name。
- 如果 `display_name` 不可用，UI 可以 fallback 到用户 email。
- 同一个账户区域显示紧凑的额度/账户状态和账户操作。
- 已登录用户应有明确的 `Logout` action。
- 登录用户的 display name 应作为非主按钮的 account label 或 badge 展示，不应作为黄色主 action button。
- Admin controls 仅 admin 用户可见。
- Admin-only 用户管理入口应命名为 `Manage Users`，而不是 `Admin`，因为当前 admin surface 主要用于管理用户账户。
- 点击 `Manage Users` 后应打开用户管理界面，admin 可以查看用户、启用/禁用账户，并调整普通用户额度设置。
- 普通用户不应看到 `Manage Users` action。
- 普通用户每日限制 3 次 live workflow。
- Admin 用户不受 daily quota 限制，但仍受系统级 rate limiting 和 worker capacity 限制保护。
- Quota UI 不应对 admin 显示 `used / 3`。Admin 登录后应显示 `Admin access` 或 `Unlimited` 这类 admin-specific 状态，同时说明仍存在系统级安全限制。

`Admin Users` 不应作为普通一级导航项。

## 品牌文案

面向用户的产品文案应使用 AlphaPilot 自己的定位，而不是直接引用设计灵感来源。

- 页面顶部当前显示的 `OpenBB-inspired analyst workspace` eyebrow 应改为 `Agentic stock research terminal`。
- 左侧品牌区只显示 `AlphaPilot`，删除旁边的小字 `Research terminal`。
- OpenBB 可以继续作为内部文档中的高密度金融工作台风格参考，但产品 UI 中不应显示 `OpenBB-inspired`，因为 AlphaPilot 当前没有依赖或集成 OpenBB 库。

## Dashboard 行为

Dashboard 是研究指令中心。

它应该包含：

- 简化后的自然语言 Copilot 对话。
- 最近活动或最近分析摘要。
- 产品状态和额度/账户状态。
- 必要时，为未登录访客展示 public demo 内容。
- 一个紧凑的 `How to use AlphaPilot` 使用引导，让首次进入的用户理解产品工作流。

当前单行 disclaimer 应替换为更有用的 Dashboard guide panel。非投资建议提示仍要保留，但应作为 guide 的一部分，而不是用户能看到的唯一说明。

推荐普通用户引导文案：

```text
How to use AlphaPilot

1. Describe your research goal in Copilot
Ask in natural language, for example: "Compare Tesla and AMD from the start of 2024 to now" or "Find large-cap US healthcare stocks and analyze YTD performance."

2. Confirm the interpreted workflow
AlphaPilot resolves tickers, dates, and whether the request belongs in Analysis or Compare. Confirm only when the draft is correct.

3. Follow progress in Analysis or Compare
After confirmation, the workflow starts automatically. Open Analysis for single or multi-stock research, or Compare for explicit cross-stock comparisons.

4. Read the final report
Reports are research assistance only. They are not financial advice and AlphaPilot does not execute trades.
```

推荐 admin-only 追加说明：

```text
Admin tools
Use Manage Users to review registered users, enable or disable accounts, and adjust regular-user quota settings. Admin accounts are not limited by daily workflow quota, but system-level rate limits and worker capacity still apply.
```

显示规则：

- 未登录用户可以看到普通 guide 和登录提示。
- 普通登录用户只看到普通 guide。
- Admin 用户看到普通 guide，并额外看到 `Admin tools` 说明。
- Guide 应保持紧凑，适合放在 Dashboard，不应变成长篇说明文档。

它不应再包含旧版右上角 quick analysis 表单：

```text
ticker
trade_date
Run analysis
```

它也不应把旧 demo rating 显示成当前 decision。

当前需要修复的问题：

- Dashboard metric card 当前显示的 `Decision: Overweight` 来自已保存的 NVDA Phase 1 demo。
- 用户容易把它误解为当前 Copilot 请求的分析结论。
- 如果没有选中的 active analysis，Dashboard 应显示 `No active analysis`、`No current decision`，或明确标注的 `Latest demo result`。
- 如果保留 saved demo 展示，必须标注为 `Demo result`，不能作为当前 workspace decision 展示。
- `Overweight`、`Neutral`、`Underweight` 这类评级应只出现在 `Analysis` 或 `Compare` 的结果状态里，或出现在明确标注的 demo summary 中。
- Dashboard 的 `Runtime` 指标目前在 workflow 完成后仍显示 `--`。
- Runtime 应从当前选中或最近完成的 analysis job 中读取 elapsed/runtime metadata 并回填。
- 如果没有 active、selected 或最近完成的 job runtime metadata，可以继续显示 `--`；否则应显示易读的耗时，例如 `267s` 或 `4m 27s`。
- 该问题应在用户确认完当前产品反馈列表后，和 Dashboard metric binding 的整体修复一起排查。

Copilot 理解用户请求后：

- `single_analysis` 或普通 analysis 请求应跳转到 `Analysis`。
- 非明确对比的多股票分析请求应跳转到 `Analysis`。
- 明确比较请求应跳转到 `Compare`。
- 目标页面应加载已确认的 symbols、时间范围和对应分析界面。

## Copilot 对话模型

Copilot UI 应从“很多按钮的 router 面板”简化为自然语言确认流。

Copilot 不应再显示 workflow shortcut buttons，例如：

- `Watchlist`
- `Single`
- `Route workflow`
- 看起来像多个产品选择的 intent-specific action buttons。

推荐流程：

1. 用户在对话框中输入自然语言诉求。
2. 用户点击一个 `Enter` / submit 按钮，提交自然语言请求。
3. 后端在服务端调用 LLM，将请求解析为结构化 analysis draft。
4. UI 展示清楚的“将要分析的内容”：
   - 目标栏目：`Analysis` 或 `Compare`；
   - 已识别的 ticker symbols 和公司名；
   - 日期或时间范围；
   - 分析模式和重要假设；
   - 任何不明确或缺失的信息。
5. 只有当分析内容正确时，用户点击一个 `Confirm` 按钮。
6. 确认后，AlphaPilot 将 draft 送入已配置好的 workflow，并跳转到 `Analysis` 或 `Compare`。

修正流程：

- 如果分析内容不对，用户不需要点击多个 workflow 按钮。
- 用户可以继续在同一个对话框里用自然语言修正。
- 每次修正都更新现有 draft，而不是从空白 workflow 重新开始。
- 示例：
  - “不是 Facebook，是 Ford”
  - “时间改成 2024 年初到现在”
  - “加上 AMD 一起分析”
  - “这不是 compare，只做普通多股票分析”
- UI 应持续展示最新解析出的 draft，直到用户确认。

后端行为：

- LLM 解析必须发生在服务端；provider API keys 绝不能进入前端。
- LLM 应返回结构化输出，而不是自由文本指令。
- LLM 解析后仍可使用确定性 ticker validation 来校验 symbols，降低 hallucinated tickers 风险。
- 当用户请求比较模糊但包含有用约束时，Copilot 应返回候选股票，而不是立刻要求用户提供 ticker。
- 用户确认 draft 之前，不应启动 workflow。

模糊股票识别：

- Copilot 应能处理类似“美国市值最大的医疗股票今年以来表现”这类没有明确 ticker 或公司名的请求。
- 第一版可以用 curated deterministic directory 覆盖常见高价值场景，再由可选的服务端 LLM 解析兜底。
- UI 应展示候选列表，包括 ticker、公司名、交易所和货币，然后让用户确认或修正 draft。
- 如果候选结果仍有不确定性，draft 必须保持在确认步骤，不得自动启动 workflow。
- 后续版本可以接入外部 market/security master provider，替换或扩展当前 curated directory。

Draft 精修：

- 已识别出的股票应渲染成可删除的 chips，而不只是普通文本。每个 chip 应展示 ticker、公司名和删除操作。
- 如果 Copilot 多识别了股票，用户应能在确认前删除错误 chip。
- 如果某个用户提到的实体对应多个候选，UI 应为该实体展示候选项，并要求用户选择目标 ticker 后才能最终确认。
- 如果用户指出候选不对，同一个 Copilot 输入框应支持类似“不是这个，用 Oracle”或“只保留 ORCL 和 MMM”的修正，并原地更新 draft。
- 如果部分请求实体无法识别，draft 应明确显示哪些实体还需要补充信息，而不是把它们隐藏在泛泛的 clarification message 中。
- `Compare` 确认前必须校验最终 selected symbols 数量为 2 到 5 只。
- `Analysis` 确认可接受 1 只或多只 selected stocks。
- 对多股票 analysis，确认后每个 selected chip 应创建一个 analysis job。
- 对 compare workflow，最终 chip set 应在确认后创建一个 compare workflow。

预期用户体验是：

```text
用户自然语言 -> LLM 解析 draft -> 用户确认或修正 -> Workflow 启动
```

## Analysis 栏目

`Analysis` 替代旧的 `New Analysis` 和 `Report Detail` 一级导航。

它应该支持：

- 单股票分析；
- 多股票分析；
- 从手动输入创建新分析；
- 从 Copilot 确认结果创建新分析；
- analysis 历史记录；
- 删除任意 analysis 历史项，包括 completed、failed、running 或 queued jobs；
- 从历史记录打开 completed 或 running analysis detail。

详情页是 `Analysis` 内部状态，不是 sidebar item。

删除 analysis 项时，应从历史中移除该 job，同时清理已持久化的 result/progress events；如果 worker 后续遇到旧队列里的同一个 job，应安全跳过。

手动 analysis 入口应作为次级入口：

- Dashboard Copilot confirmation 应在跳转到 `Analysis` 前创建并启动 analysis workflow。
- 用户在 Dashboard 确认 draft 后，不应还需要再点击一次 `Start Workflow`。
- 手动 analysis 表单应默认放在折叠的 `Manual analysis` 区域中。
- 该手动区域只用于用户直接从 `Analysis` 页面创建一个独立 workflow。

## 实时分析报告体验

当 `Analysis` 或 `Compare` workflow 正在运行时，报告界面不应该让用户面对一个黑盒等待状态。

预期体验：

- 展示当前 workflow 阶段，例如 ticker 识别、市场数据收集、分析师推理、多空辩论、交易计划、风险审查和最终决策。
- 后端 workflow 运行时，将阶段更新持续推送到报告界面。
- 叙述性文本使用打字机式逐步显示，让用户看到报告正在形成。
- 在 `Progress` 面板顶部加入常驻的运行状态头，避免 workflow 运行时页面看起来像卡住。
- 状态头应展示当前状态、elapsed timer、最近更新时间，以及 queued 或 running 时的轻量 live indicator。
- 加入基于阶段的进度条，而不是伪造精确百分比的进度条。
- 进度条应区分已完成阶段、当前运行阶段和未开始阶段。
- `Analysis` 阶段标签应对应研究 workflow，例如：`Ticker`、`Market data`、`Analyst`、`Debate`、`Risk`、`Final`。
- `Compare` 阶段标签应对应对比 workflow，例如：`Ticker`、`Data`、`Per-stock analysis`、`Cross-stock comparison`、`Final summary`。
- 如果 job 仍处于 queued 或 running，但超过 60 秒这类阈值没有收到新 progress event，UI 应显示温和的存活提示，例如 `Still running. Waiting for next worker update.`，而不是让用户以为页面卡死。
- 每个阶段完成时展示简短的阶段性结论，例如：收集了哪些数据、发现了什么信号、仍有什么不确定性、下一阶段会评估什么。
- 阶段性内容必须明确标注为进行中，不应被误解为最终投资输出。
- workflow 完成后，用持久化的最终报告替换或合并进行中的临时文本。
- 最终报告应渲染为格式化后的 Markdown，而不是以 `<pre>` 风格直接展示原始 Markdown 文本。
- 渲染后的报告应支持 headings、paragraphs、bullet/numbered lists、emphasis、blockquotes、tables、horizontal rules 和 code/preformatted blocks。
- Markdown 表格尤其重要，因为 analyst 输出经常包含指标、比率和横向比较表。
- report renderer 在把内容注入页面前必须做 sanitization；LLM 生成的 Markdown 绝不能被当作可信 raw HTML。
- 阅读视图应使用报告专用的 typography 和 spacing，让输出更像金融研究报告，而不是终端文本。
- 后续可以增加可选 raw/source toggle，方便调试或复制原始 Markdown；但默认用户视图应是渲染后的报告。
- 历史报告打开时展示稳定的最终结果，而不是当时的 transient stream。

实现方向：

- 后端应由 analysis worker 发出结构化 progress events，而不是前端伪造进度。
- events 应包含 stage key、面向用户的 stage label、status、可选 summary text 和 timestamps。
- 前端第一版可以通过 polling endpoint 订阅进度；后续如有需要再升级为 Server-Sent Events 或 WebSocket。
- 前端应从已持久化的 job/progress timestamps 本地计算 elapsed time 和 latest update age，使计时器可以在两次 polling 之间继续跳动。
- 除非后端后续提供可靠的 progress weights，否则前端不应假装知道精确完成百分比。
- 前端可以在本地实现打字机动画，但显示内容必须来自真实 workflow progress 或已保存的阶段摘要。
- 前端应使用安全的 Markdown rendering path 展示最终报告。如果引入第三方 Markdown parser，应同时配套 sanitization，并保持与当前静态前端部署模型兼容。
- 如果 streaming 失败，workflow 仍应正常完成，UI fallback 为清晰的 queued/running/completed 状态。

## Compare 栏目

`Compare` 用于明确的多股票横向对比。

它应该支持：

- 从手动输入创建 compare；
- 从 Copilot 确认结果创建 compare；
- compare workflow 历史记录；
- 删除 compare 历史项；
- 从历史记录打开 completed 或 running compare detail。

`Compare` 应与 `Analysis` 分离，因为用户意图不同：用户是在共同框架下比较哪个资产、公司或组合更好。

手动 compare 入口也应作为次级入口：

- Dashboard Copilot confirmation 应在跳转到 `Compare` 前创建 compare workflow。
- 手动 compare 表单应默认放在折叠的 `Manual compare` 区域中。
- 该手动区域只用于用户直接从 `Compare` 页面创建一个独立 compare setup。

## 语言与报告本地化

AlphaPilot 应支持两套彼此独立的语言控制：

1. 全局 UI 语言。
2. Report 语言。

全局 UI 语言：

- 在右上角账户区域加入 `EN` / `中文` 切换按钮，位置放在用户/account 按钮左侧。
- 全局 UI 语言只控制界面文案：导航、按钮、表单、空状态、状态标签、Copilot 提示、历史记录标签、progress 标签、登录/账户/admin 文案和免责声明。
- 英文 UI 保持接近当前交互方式。
- 中文 UI 应把所有用户可见的交互和展示文案改写为自然中文，而不是机械直译。
- 第一版可先将用户 UI 语言偏好保存在本地，例如 `localStorage`；后续再加入账户级持久化。

Report 语言：

- `Analysis` 和 `Compare` 的 report panel 中应各自加入独立的 report language toggle，例如 `Report: English | 中文`。
- Report 语言切换与全局 UI 语言切换相互独立。
- 无论当前 UI 是英文还是中文，默认 report view 都应先展示原始英文报告，因为美股研究、财报、指标和市场术语用英文最准确。
- 英文 final report 完成后，AlphaPilot 应在后台自动生成中文报告版本。
- 中文报告应基于已经完成的英文报告进行忠实翻译/改写，而不是重新跑一次股票分析。
- 翻译后的中文报告应保持相同的投资结论、结构、关键数字、表格、ticker symbols、引用/来源名称，以及必要的英文金融术语。
- 中文报告应持久化或缓存，避免用户切换语言时反复消耗 LLM quota。
- 中文报告仍在生成时，中文 report toggle 可以暂时 disabled，或显示 `Chinese report generating` 这类状态。
- 如果中文报告生成失败，UI 应继续展示英文报告，并提供清晰的 retry/fallback 状态。

实现说明：

- 当 `ALPHAPILOT_REPORT_TRANSLATION_ENABLED=true` 时，本地后端现在会保持 `TRADINGAGENTS_OUTPUT_LANGUAGE=English`，将英文报告作为 canonical source report，并在 background worker 中基于已完成的英文完整报告生成中文完整报告，缓存到 `localized_sections.zh.report`，在 `report_translations.zh` 中记录状态，按 `ALPHAPILOT_REPORT_TRANSLATION_MAX_ATTEMPTS` 重试失败，并在已有中文完整报告缓存时跳过重复生成。前端仅把 `localized_sections.zh.final` 作为旧结果的兼容 fallback。

推荐语言策略：

- `analysis_language`：English。
- `source_report_language`：English。
- `translated_report_language`：Chinese，在英文报告完成后生成。
- `ui_language`：由全局 UI toggle 控制。
- `report_display_language`：由 report-level toggle 控制，默认 English。

## Watchlist 决策

`Watchlist` 不应作为一级导航项。

目前保留后端/存储能力，但隐藏前端一级入口。当前产品主分析路径不需要独立的股票收藏工作流。

未来选项：

- 持续隐藏；
- 作为 `Saved` 或 `Saved Tickers` 放回 Dashboard 内部；
- 只作为 Analysis 或 Compare 的来源列表。

## 实现备注

- 应先更新前端导航，再继续添加新的分析能力。
- 现有 Watchlist 后端表和 API 可以先保留。
- 测试应验证 sidebar 只包含 `Dashboard`、`Analysis`、`Compare`。
- 测试应验证 `Login`、`Admin` 和账户控制不再作为普通 sidebar views。
- 测试应验证登录用户的 display name 会显示在右上角账户区域。
- 测试应验证已登录用户有明确的 `Logout` action。
- 测试应验证 display name 作为 account label 或 badge 展示，而不是黄色主 action button。
- 测试应验证 admin 用户可以看到 `Manage Users`，普通用户看不到，点击 `Manage Users` 会打开用户管理界面。
- 测试应验证普通用户每日限制 3 次 live workflow。
- 测试应验证 admin 用户绕过 daily quota，但仍受系统级 rate limiting 和 worker capacity 控制。
- 测试应验证 admin 用户的 quota UI 显示 admin-specific 状态，而不是 `used / 3`。
- 测试应验证 Dashboard 不会把 saved demo 的 `Overweight` rating 展示成当前用户 workflow decision。
- 测试应验证 Dashboard 显示实用的 `How to use AlphaPilot` guide，而不是只有单独的 disclaimer。
- 测试应验证普通用户不会在 Dashboard guide 中看到 admin 使用说明。
- 测试应验证 admin 用户会看到 `Admin tools` 追加说明，内容包括 `Manage Users`、启用/禁用账户和额度管理。
- 测试应验证 Dashboard Copilot confirmation 会跳转到正确栏目。
- 测试应验证 Copilot 只暴露一个自然语言 submit action 和一个最终 confirmation action。
- 测试应验证自然语言修正会在 workflow 确认前更新现有 draft。
- 测试应验证模糊请求可以识别候选股票列表，并交由用户确认。
- 测试应验证 Copilot draft 中已识别股票会渲染成可删除 chips。
- 测试应验证用户可以在确认前删除错误识别的 chip。
- 测试应验证存在歧义的实体候选必须由用户选择后才能确认 workflow。
- 测试应验证未识别实体会单独显示，不会从 draft 中静默消失。
- 测试应验证 `Compare` 确认前要求最终选择 2 到 5 只股票。
- 测试应验证 `Analysis` 确认允许 1 只或多只股票。
- 测试应验证 analysis 和 compare 历史项可以删除。
- 测试应验证已删除的 queued job 会被 worker 安全跳过。
- 测试应验证 running report 会展示真实 workflow progress，而不是只有空白等待状态。
- 测试应验证 running `Analysis` 和 `Compare` progress panel 包含 live status header、elapsed time、latest update age 和基于阶段的进度条。
- 测试应验证在后端没有可靠百分比时，进度条使用 workflow stages，而不是误导性的精确百分比。
- 测试应验证 workflow 完成后，最终持久化报告会替换或合并进行中的 streamed text。
- 测试应验证最终报告会将 Markdown 渲染成 headings、lists 和 tables 等结构化 HTML，而不是把原始 Markdown markers 作为主要视图展示。
- 测试应验证 Markdown 渲染会清理不安全的 HTML/script 内容。
- 测试应验证全局 `EN` / `中文` UI toggle 会切换导航、控件、状态标签和空状态，但不会改变当前 report language。
- 测试应验证 `Analysis` 和 `Compare` report 在两种 UI 语言下都默认显示英文。
- 测试应验证英文报告完成后会生成中文报告版本，并可通过 report-level language toggle 选择中文报告，且不会重新跑 analysis。
- 测试应验证中文翻译报告会缓存或持久化，切换语言时不会每次重新生成。
- 测试应验证 Analysis 和 Compare 的手动表单默认折叠，避免 Dashboard 已确认 workflow 被误解为还需要第二次启动。
