# AlphaPilot 部署文档

最后更新：2026-06-14

## 目标

第一版生产部署目标是一台阿里云轻量应用服务器：

- 2 vCPU
- 2 GB RAM
- Ubuntu LTS
- Docker Engine 和 Docker Compose plugin
- 一个公网 IPv4 地址
- 可选：解析到服务器的域名。第一版 demo 支持无域名的 IP-only HTTP。

这是一个可控 demo 部署，不是高流量生产集群。

## 拓扑

```text
Internet
  |
  v
Caddy :80/:443
  |-- 从 /srv/alphapilot/frontend 提供静态前端
  |-- API 反向代理到 FastAPI

FastAPI API
  |-- PostgreSQL
  |-- Redis
  |-- background worker

Worker
  |-- TradingAgentsGraph.propagate()
  |-- PostgreSQL result persistence
  |-- usage 和 failure logging
```

## 服务

- `caddy`：公开 HTTP/HTTPS 入口和静态前端服务器。
- `api`：由 Uvicorn 提供服务的 FastAPI。
- `worker`：后台分析 worker。
- `postgres`：持久化产品数据库。
- `redis`：任务队列和 rate-limit 计数存储。

## 需要用户提供的信息

真实部署到服务器之前，Codex 应暂停并向用户确认这些值：

- 阿里云服务器公网 IP。
- SSH 用户名和认证方式。
- 域名，如果需要真实 hostname 和 HTTPS。
- 生产 `.env` 值，包括 `DEEPSEEK_API_KEY`。
- 强随机 `ALPHAPILOT_ADMIN_PASSWORD`；不能在公网暴露本地默认管理员密码。
- 是否开放 public registration，还是要求 admin-controlled activation。

当前第一版可控 demo 服务器：

- 公网 IP：`47.250.149.226`
- 地域：阿里云马来西亚（吉隆坡）
- 系统：Ubuntu 22.04
- SSH 用户：`root`
- 域名：暂无；使用 IP-only HTTP，并设置 `ALPHAPILOT_PUBLIC_HOST=:80`

## 生产环境变量

生产 secrets 必须保存在服务器上的 `.env.production`，不能提交到 git。

最小变量：

```text
ALPHAPILOT_DATABASE_URL=postgresql+psycopg://alphapilot:<password>@postgres:5432/alphapilot
ALPHAPILOT_REDIS_URL=redis://redis:6379/0
ALPHAPILOT_QUEUE_BACKEND=redis
ALPHAPILOT_RATE_LIMIT_ENABLED=true
ALPHAPILOT_PUBLIC_HOST=:80
ALPHAPILOT_ADMIN_EMAIL=admin@alphapilot.dev
ALPHAPILOT_ADMIN_PASSWORD=<server-only-random-admin-password>
DEEPSEEK_API_KEY=<server-only-secret>
TRADINGAGENTS_LLM_PROVIDER=deepseek
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-v4-flash
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-v4-pro
TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
TRADINGAGENTS_MAX_RISK_ROUNDS=1
```

后续添加域名时，将 `ALPHAPILOT_PUBLIC_HOST` 从 `:80` 改为 hostname，例如 `your-domain.example`。如果 80 和 443 端口开放，并且 DNS 指向服务器，Caddy 可以自动申请 HTTPS 证书。

## 部署步骤

1. 购买阿里云轻量应用服务器。
2. 安装 Docker 和 Docker Compose plugin。
3. 在服务器上 clone AlphaPilot 仓库。
4. 基于 `.env.production.example` 创建 `.env.production`。
5. 填写生产 secrets 和数据库密码。
6. 如果使用域名，将 DNS A record 指向服务器 IP。IP-only HTTP 可以跳过这一步。
7. 运行数据库迁移。
8. 启动 Compose deployment。
9. 验证 `/health`、`/demo/reference`、login、admin controls 和 disabled-user blocking。

仓库和 `.env.production` 已准备好之后，可以执行基础命令：

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm api alembic upgrade head
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

健康检查：

```bash
curl http://127.0.0.1/health
curl http://127.0.0.1/demo/reference
```

当前 IP-only 部署的公网检查地址是 `http://47.250.149.226/health` 和 `http://47.250.149.226/demo/reference`。

## 安全检查

公开 live analysis 前：

- 确认前端文件不包含 LLM API keys。
- 确认 disabled users 不能创建 analysis jobs。
- 确认达到阈值后 rate limiting 返回 HTTP 429。
- 确认 live jobs 会进入队列并由 worker 完成。
- 确认失败的 worker jobs 会标记为 `failed` 并保存错误信息。
- 确认 `.env.production` 没有被 git 跟踪。
- 公开暴露前确认 `ALPHAPILOT_ADMIN_PASSWORD` 已设置为强随机、仅保存在服务器上的值。
