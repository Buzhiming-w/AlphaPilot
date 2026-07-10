# Security Master 与实体识别计划

最后更新：2026-06-15

实现状态：

- 本地实现已包含数据库模型、Alembic migration、基于 fixture 的 Nasdaq Trader + SEC 同步、初始 alias seed、`SecurityMasterResolver`、Copilot router wiring，以及 worker-side 每周一 00:00 自动同步调度。
- 产品决策：当前阶段不做 Admin alias 维护 UI/endpoints。对于当前单人运营 demo，中文名、人物线索和其他 aliases 直接维护在 `security_aliases` 数据库表中。

## 目标

AlphaPilot 的 Copilot 需要用更广、更可靠的方式，从自然语言请求中识别股票、ETF 和常见市场代理工具。

当前 `LocalTickerDirectory` 是一个很小的确定性 MVP 目录，但它无法覆盖真实用户输入。例如：

```text
比较3M和orcl两只股票的表现，从2015年6月至今
```

理想解析结果应为：

- `MMM` / 3M Company；
- `ORCL` / Oracle Corporation；
- intent：`compare`；
- start date：`2015-06-01`；
- end date：当前日期。

解决方案不应只依赖 LLM。AlphaPilot 应使用本地 Security Master 作为权威确认层，LLM 只作为语言理解辅助。

## 产品原则

采用混合实体识别模型：

```text
用户自然语言
-> Copilot 提取意图、实体和日期
-> Security Master 解析并校验证券
-> 用户确认候选
-> AlphaPilot 启动 Analysis 或 Compare workflow
```

LLM 可以推断用户提到了 “Oracle” 或 “3M”，但最终 ticker 必须由 Security Master 确认。

## 为什么不只用 LLM

LLM-only ticker resolver 对金融研究产品风险较高：

- 可能 hallucinate ticker。
- 可能混淆改名公司、不同 share class、ADR、ETF 和相似名称发行人。
- 每次查询都会消耗 token。
- 不易审计。
- 可能返回看似合理但过期或无效的 symbol。

AlphaPilot 应让 LLM 负责语义抽取，而不是让 LLM 充当最终证券数据库。

## 为什么不手工维护

手写 `ticker_directory.py` 也不可持续：

- 美股和 ETF 有数千个活跃标的。
- 公司会改名、合并、拆分、退市。
- 用户会用 ticker、公司名、品牌、中文名、旧名、CEO/创始人/人物线索、行业描述来搜索。
- 每次识别失败都变成代码改动，维护成本会越来越高。

第一版可扩展方案应把官方或半官方市场数据载入 PostgreSQL，并把别名维护在数据库表中。

## 推荐数据源

### 1. Nasdaq Trader Symbol Directory

用途：

- 当前 Nasdaq 和其他美国交易所上市证券。
- 字段包括 symbol、security name、exchange、ETF flag、test issue flag 等。

初始文件：

- `https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt`
- `https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt`

用法：

- 作为主要 active US listing 来源。
- 排除 test issues。
- 根据 ETF flag 区分 ETF 与非 ETF。
- 保留原始 source row，方便审计和调试。

### 2. SEC EDGAR Company Tickers

用途：

- 提供 CIK、ticker、SEC company name 和 exchange 关联。
- 后续连接财报、10-K/10-Q workflow 时很有用。

初始文件：

- `https://www.sec.gov/files/company_tickers_exchange.json`

用法：

- 给 Security Master 补充 `cik`。
- 如果 SEC conformed company name 与交易所名称不同，将其作为 alias 加入。
- 不把 SEC 数据本身当作完整 active listing 来源。

### 3. 后续可选来源：Financial Modeling Prep

用途：

- Company symbol list、ETF list、index list、profile、sector/industry、ETF 详情等。

用法：

- 在 Nasdaq + SEC 路径稳定后作为增强源。
- 需要 API key，并需要检查额度和许可限制。
- 第一版 Security Master MVP 不应强依赖 FMP。

### 4. yfinance 使用边界

用途：

- 对已知 symbol 拉行情、历史价格或 profile 做验证。

用法：

- 可以作为 resolution 后的校验或数据拉取工具。
- 不建议作为全量 symbol list 的权威来源。

## 数据库模型

### `securities`

保存 canonical tradable / researchable instruments。

建议字段：

```text
id
symbol
normalized_symbol
name
normalized_name
exchange
market
currency
asset_type
is_etf
cik
status
source
first_seen_at
last_seen_at
delisted_at
raw_payload
created_at
updated_at
```

字段说明：

- `symbol`：展示用 canonical symbol，例如 `ORCL`、`MMM`、`SPY`、`BRK.B`。
- `normalized_symbol`：用于搜索的小写/标点归一化 symbol。
- `asset_type`：例如 `stock`、`etf`、`adr`、`preferred`、`warrant`、`unit`、`fund`、`index_proxy`、`unknown`。
- `status`：`active`、`inactive`、`delisted` 或 `unknown`。
- `raw_payload`：来源原始行的 JSONB 快照。

索引：

- `(market, symbol)` 唯一索引。
- `normalized_symbol` 索引。
- `normalized_name` 索引。
- 启用 `pg_trgm` 后，对 `normalized_name` 和 alias values 加 trigram 模糊搜索索引。

### `security_aliases`

保存 alternate names 和用户可搜索线索。

建议字段：

```text
id
security_id
alias
normalized_alias
alias_type
confidence
source
created_at
updated_at
```

Alias 类型：

- `company_short_name`
- `company_legal_name`
- `sec_name`
- `old_name`
- `brand`
- `english_common_name`
- `chinese_name`
- `chinese_abbreviation`
- `person`
- `manual`
- `llm_suggested`

重要要求：

- 常见中文名和人物线索必须维护在数据库里，不能继续硬编码在 Python 中。
- 示例：
  - `甲骨文` -> `ORCL`
  - `3M` -> `MMM`
  - `英伟达` -> `NVDA`
  - `黄仁勋` -> `NVDA`
  - `巴菲特的公司` / `伯克希尔` -> `BRK.B`

人物线索：

- CEO、创始人、人物相关线索使用 `alias_type='person'` 存入 `security_aliases`。
- 第一版先人工维护，后续根据失败查询日志逐步补充。
- 不要每次请求都依赖实时 web search。

### `security_master_sync_runs`

保存同步审计历史。

建议字段：

```text
id
source
started_at
finished_at
status
inserted_count
updated_count
deactivated_count
error
raw_metadata
```

### `security_resolution_failures`

保存 Copilot 未识别或低置信度查询，方便后续维护 alias。

建议字段：

```text
id
user_id
query
entities
reason
created_at
resolved_at
resolved_by_user_id
notes
```

用法：

- Copilot 无法解析请求时，记录失败 query。
- Admin 可以查看高频失败并补充 alias，而不需要改代码。

## 同步流程

新增脚本或 CLI：

```bash
python -m alphapilot.backend.security_master.sync
```

第一版步骤：

1. 下载 `nasdaqlisted.txt`。
2. 下载 `otherlisted.txt`。
3. 下载 SEC `company_tickers_exchange.json`。
4. 用结构化 parser 解析来源记录。
5. 归一化 symbol、name、exchange 和 asset type。
6. upsert 到 `securities`。
7. 将来源派生出的 alias upsert 到 `security_aliases`。
8. 本次来源中缺失、但此前为 active 的记录标记为 `inactive`，不要直接删除。
9. 写入 `security_master_sync_runs`。

本地开发：

- 手动运行。
- 为测试准备小型 fixture。

生产：

- 第一次部署后手动运行。
- 后续在服务器时间每周一 00:00 自动同步一次。
- 使用 cron 或现有 Docker worker/scheduler，并将每次定时同步记录到 `security_master_sync_runs`。

失败行为：

- 如果某个来源失败但另一个来源成功，应记录 partial status，不要清空已有数据。
- 失败同步期间绝不删除 canonical securities。

## Resolver 行为

新增 resolver 边界，例如：

```text
SecurityMasterResolver.resolve(query, limit=5)
```

解析优先级：

1. Exact symbol match。
2. Exact alias match。
3. Exact normalized company name match。
4. Name / alias 的 prefix 或 contains 搜索。
5. Trigram / fuzzy search。
6. 可选 LLM-extracted entity search。

返回结构应包含：

```text
ticker
company_name
market
exchange
currency
asset_type
confidence
match_reason
source
```

置信度规则：

- `high`：exact symbol、exact alias、exact name。
- `medium`：prefix/contains/fuzzy match，且 top candidate 明显。
- `low`：模糊或多候选。

Workflow 行为：

- 高置信度单一匹配可以直接进入确认 draft。
- 多候选或中低置信度匹配应展示候选列表，由用户确认。
- 没有用户确认前，不启动 workflow。

## Copilot 集成

保留当前 Copilot LLM 的角色，但替换校验来源。

当前：

```text
LLM optional hint + hardcoded LocalTickerDirectory
```

目标：

```text
LLM optional hint + PostgreSQL-backed SecurityMasterResolver
```

LLM 应抽取结构化 hints：

```json
{
  "intent": "analysis|compare|clarify|unsupported",
  "entities": ["3M", "orcl"],
  "start_date": "2015-06-01",
  "end_date": null
}
```

然后 resolver 校验：

```text
3M -> MMM / 3M Company
orcl -> ORCL / Oracle Corporation
```

LLM 不允许绕过 Security Master 直接决定最终 ticker。

## Admin 维护

当前阶段不增加 admin-only alias 维护 UI/endpoints。

对于单人运营 demo，直接在 PostgreSQL 中维护 aliases：

- 在 `security_aliases` 中 insert 或 update 行。
- 使用 `alias_type='chinese_name'`、`alias_type='chinese_abbreviation'`、`alias_type='person'`、`alias_type='old_name'` 或 `alias_type='brand'`。
- 运营人员手动添加的 aliases 使用 `source='manual'`。
- 保留 workflow 启动前的用户确认，避免错误 alias 静默启动分析。

这样 “常见中文名 / 人物线索” 仍然是数据维护，而不是 Python 代码维护，同时暂不把产品界面复杂化。

第一批有用的 admin 操作：

- 添加 `chinese_name`。
- 添加 `chinese_abbreviation`。
- 添加 `person`。
- 添加 `old_name`。
- 添加 `brand`。

## 初始 Alias Seed

第一批数据库 seed 应包含最常见美股大盘股和 ETF 的高价值 alias。

示例：

```text
MMM: 3M, 3M Company, 明尼苏达矿务, 3M公司
ORCL: Oracle, Oracle Corporation, 甲骨文
NVDA: NVIDIA, 英伟达, 辉达, 黄仁勋, Jensen Huang
AMD: Advanced Micro Devices, 超威半导体, 苏姿丰, Lisa Su
AAPL: Apple, 苹果, 苹果公司, Tim Cook, 库克
MSFT: Microsoft, 微软, Satya Nadella, 纳德拉
GOOGL/GOOG: Google, Alphabet, 谷歌, 字母表
META: Meta, Facebook, 脸书, Zuckerberg, 扎克伯格
TSLA: Tesla, 特斯拉, Elon Musk, 马斯克
BRK.B: Berkshire Hathaway, 伯克希尔, Warren Buffett, 巴菲特
SPY: S&P 500 ETF, 标普500 ETF
QQQ: Nasdaq 100 ETF, 纳指100 ETF
VOO: Vanguard S&P 500 ETF
VTI: Vanguard Total Stock Market ETF
IWM: Russell 2000 ETF
TLT: long Treasury ETF, 长债 ETF
GLD: gold ETF, 黄金 ETF
```

Seed 应作为数据保存，而不是作为硬编码业务逻辑。

## 实施阶段

### Phase SM-1：Schema 与同步 MVP

- 添加 Alembic migration：`securities`、`security_aliases`、`security_master_sync_runs`、`security_resolution_failures`。
- 添加 SQLAlchemy models 和 store methods。
- 添加 Nasdaq Trader 和 SEC 文件同步命令。
- 用本地 fixtures 编写测试。

完成标准：

- 本地数据库可以从 fixture 文件导入。
- `MMM` 和 `ORCL` 存在。
- 同步过程可重复执行且幂等。

### Phase SM-2：替换 Resolver

- 新增 `SecurityMasterResolver`。
- 将 `WorkflowRouter` 中的 `LocalTickerDirectory` 替换为 resolver。
- 测试中保留小型 in-memory fixture resolver。
- 保持当前 Copilot API response shape 不变。

完成标准：

- “比较3M和orcl两只股票的表现，从2015年6月至今” 能解析为 `MMM` 和 `ORCL`。
- 现有 NVDA、AMD、AAPL、医疗候选、人物线索测试继续通过，但数据来自数据库 alias。

### Phase SM-3：Alias 维护

- 当前阶段不做 alias review / creation 的 admin endpoints 或 UI。
- 单人运营 demo 期间，直接维护 `security_aliases` 表。
- 将常见中文名和人物线索维护在 `security_aliases`。

完成标准：

- 运营人员可以直接在数据库中添加 `甲骨文 -> ORCL`，无需改代码。
- 运营人员可以直接在数据库中添加 `黄仁勋 -> NVDA`，无需改代码。

### Phase SM-4：生产同步与监控

- 手动执行第一次生产同步。
- 增加最新同步时间和 counts 状态。
- 增加安全 retry 和失败日志。
- 在服务器时间每周一 00:00 自动执行生产同步。

完成标准：

- 生产 Copilot 可以从 Security Master 识别常见美股和 ETF 请求。
- 失败查询日志可以形成实用的 alias backlog。

## 风险与控制

风险：来源文件格式变化。

- 控制：parser fixture 测试和 sync-run failure log。

风险：错误 alias 映射到错误 ticker。

- 控制：alias source/confidence 字段；用户确认仍是强制步骤。

风险：退市或过期 symbol 出现。

- 控制：status 字段和 active/inactive 过滤；不要静默删除历史记录。

风险：ETF 和 share class 歧义。

- 控制：置信度不足时返回候选列表。

风险：数据供应商许可。

- 控制：第一版使用 public Nasdaq Trader 和 SEC 文件；可选付费/增强源隔离处理。

## 第一版代码实现停止标准

第一轮代码实现应在以下条件满足时停止：

- PostgreSQL 可以保存从 Nasdaq Trader + SEC 文件或本地 fixtures 导入的 Security Master。
- `MMM`、`ORCL`、常见大盘股和常见 ETF 可以被解析。
- 中文名和人物线索用 `security_aliases` 表表达。
- Copilot 使用 Security Master resolver，而不是硬编码小目录。
- 测试证明“比较3M和orcl两只股票的表现，从2015年6月至今”可以正确路由。
- 中英文 docs 均已更新。
