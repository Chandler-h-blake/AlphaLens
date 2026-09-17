# AlphaLens：A 股 AI 投研平台

[![CI](https://github.com/Chandler-h-blake/AlphaLens/actions/workflows/ci.yml/badge.svg)](https://github.com/Chandler-h-blake/AlphaLens/actions/workflows/ci.yml)

AlphaLens 是一个面向个人研究、实习成果展示和技术面试讲解的全栈 A 股投研项目。项目将多因子选股、市场与资金快照、单股行情、行业轮动、AI 研报和每日复盘整合为一套可运行、可测试、可部署的 React + FastAPI + PostgreSQL 应用。

> 本项目仅用于研究学习和工程演示，不构成投资建议，不提供真实交易，也不应被视为交易所级实时行情系统。

## 项目成果概览

| 成果维度 | 已完成内容 |
| --- | --- |
| 产品交付 | 9 个业务模块、统一工作台、响应式页面、图表与 Markdown 报告展示 |
| 前端工程 | React、TypeScript、Vite、React Router、Recharts、懒加载与统一 API Client |
| 后端工程 | FastAPI、Pydantic、Route → Service → Repository 分层、统一异常与请求 ID |
| 数据工程 | PostgreSQL 持久化、SQLAlchemy ORM、4 版 Alembic 迁移、幂等种子导入 |
| 量化研究 | 9 因子评分、截面 Z-score、方向修正、加权排名、TOP30 候选池与在线技术因子刷新 |
| 外部数据 | 公开行情 Provider、主备数据源、超时处理、快照留存和失败回退 |
| AI 能力 | OpenAI-compatible Provider、研报与复盘异步任务、任务状态持久化 |
| 工程质量 | 34 个后端测试、前端 lint/build、端到端冒烟脚本、GitHub Actions CI |
| 部署交付 | Docker Compose 编排 PostgreSQL、FastAPI、Nginx，包含健康检查和启动依赖 |

仓库内置 300 只股票的因子样本、30 只 TOP 候选股、31 个行业轮动样本和 5 份研究报告，首次启动即可形成完整演示闭环。

## 核心业务模块

| 模块 | 能力 | 关键数据或接口 |
| --- | --- | --- |
| 市场概览 | 指数、行业热力图、涨跌分布、成交额榜 | 市场快照，支持手动刷新与陈旧提示 |
| 在线市场 | 按股票代码查询行情、日内数据、公告与资讯 | 主备公开数据源、单股持久化快照 |
| 因子选股 | TOP30、因子贡献、筛选排序、技术因子在线刷新 | 9 因子模型、异步刷新任务 |
| AI 研究报告 | 历史研报、来源记录、按股票生成新研报 | OpenAI-compatible LLM、任务轮询 |
| 资金监控 | 行业主力资金和可用性信息 | 资金快照、来源和时间字段 |
| 个股对比 | 选择 2–5 只股票对比综合分和五类因子贡献 | 复用 TOP30 数据在前端完成比较 |
| AI 每日复盘 | 基于当前工作台数据生成 Markdown 复盘 | 通用 AI 任务模型与结果持久化 |
| 行业轮动 | 1 月/3 月收益、排名、轮动分类和历史日期 | 行业轮动快照与管理员刷新脚本 |
| 设置与状态 | 数据库、LLM、Provider 和快照新鲜度 | `/api/system/status` |

## 关键设计

### 1. 快照优先与失败回退

页面默认读取已保存快照，只有用户主动刷新时才访问外部数据源。新数据通过校验后才写入 PostgreSQL；抓取失败时保留最后一次成功结果，并向前端返回 `stale` 状态和警告，避免第三方接口波动直接拖垮页面。

```text
页面 GET → 读取 PostgreSQL 最近快照 → 展示来源与时间
页面 POST 刷新 → 主数据源 → 备用数据源 → 校验 → 原子写入
                                      └─ 全部失败 → 返回旧快照 + warning
```

### 2. 可解释的九因子排名

因子覆盖动量、价值、质量、成长和波动五类：

- 技术因子：20 日动量、换手率变化、60 日年化波动率；
- 估值因子：PE 历史分位、PB 历史分位；
- 质量因子：ROE、毛利率；
- 成长因子：营收同比增长、净利润同比增长。

计算过程为“数据清洗 → 截面 Z-score → 因子方向修正 → 权重加总 → 稳定排序”。在线刷新只更新当前 30 只研究候选股的市场敏感因子，财务因子沿用最近披露值；全股票池重算由管理员 CLI 执行。仓库内的 IC 与分层指标是有限历史截面的研究记录，不代表未来收益。

### 3. 可追踪的 AI 异步任务

研报和每日复盘共用 OpenAI-compatible Provider 和任务模型。接口先返回任务 ID，前端轮询 `pending → running → succeeded/failed` 状态；任务与成功结果写入数据库，服务重启后仍可查询。未配置密钥时生成按钮会明确禁用，不使用固定模板伪装 AI 输出。

### 4. 服务分层与数据契约

```text
Browser
  ↓ HTTP :8080
Nginx
  ├─ /          → React 静态资源
  └─ /api/*     → FastAPI
                    ↓
              Route → Service → Repository
                         ↓          ↓
                   外部 Provider  PostgreSQL
```

- Route：接收请求、依赖注入和响应模型约束；
- Service：快照、刷新、评分、任务和降级等业务规则；
- Repository：隔离 CSV/Markdown 种子数据与 PostgreSQL 数据访问；
- Schema/Type：Pydantic 与 TypeScript 分别约束后端响应和前端消费。

## 技术栈

- 前端：React 19、TypeScript、Vite、React Router、Recharts、React Markdown
- 后端：Python、FastAPI、Pydantic、HTTPX、Uvicorn
- 数据库：PostgreSQL 16、SQLAlchemy、Alembic
- 数据处理：Pandas、CSV/JSON/Markdown 种子快照
- AI：OpenAI-compatible Chat Completions Provider
- 基础设施：Docker Compose、Nginx、多阶段镜像、健康检查
- 质量保障：Pytest、Oxlint、TypeScript Build、GitHub Actions、Shell Smoke Test

## 快速启动

### 前置条件

- Docker Desktop，使用 Linux containers；
- Git；
- 可选：OpenAI-compatible 模型服务的 API Key。

### macOS / Linux / WSL / Git Bash

```bash
git clone https://github.com/Chandler-h-blake/AlphaLens.git
cd AlphaLens
cp .env.example .env
sh scripts/start.sh
```

### Windows PowerShell

```powershell
git clone https://github.com/Chandler-h-blake/AlphaLens.git
Set-Location AlphaLens
Copy-Item .env.example .env
docker compose up --build -d --wait
```

启动完成后访问：

- Web 工作台：[http://localhost:8080](http://localhost:8080)
- API 文档：[http://localhost:8080/api/docs](http://localhost:8080/api/docs)
- 就绪检查：[http://localhost:8080/api/health/ready](http://localhost:8080/api/health/ready)

首次启动会自动执行 Alembic 迁移并幂等导入 `data/seed/`。如果某些 Docker Compose Bake 版本在含中文的本地路径下报 `non-printable ASCII`，请将项目移到纯英文路径，或使用 `scripts/start.sh` 中的分步构建方式。

## 可选 AI 配置

默认配置可以查看内置研究报告和其他非 AI 功能，不需要密钥。需要生成新研报或每日复盘时，编辑根目录 `.env`：

```dotenv
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

密钥只由 FastAPI 服务读取，不会进入 Vite 构建产物，也不会通过设置页面返回。

## 验证与测试

### 后端测试

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Windows: .venv\Scripts\python -m pytest -q
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

当前测试覆盖 API 契约、因子计算、数据库导入、AI 任务恢复、限流、行情主备源、快照回退、行业数据、健康检查和 OpenAPI 文档入口，共 34 项。

### 前端检查

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm build
```

### 容器冒烟测试

```bash
sh tests/e2e/smoke.sh
```

冒烟脚本检查健康接口、主要业务 API 和 9 个前端路由。GitHub Actions 会在每次推送和 Pull Request 时自动执行后端测试以及前端 lint/build。

## 常用运维命令

```bash
# 查看三个服务及健康状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 停止服务，保留 PostgreSQL 数据卷
docker compose down

# 停止并删除本项目数据库卷（会清空运行时数据）
docker compose down -v

# 重算全量因子并写入 PostgreSQL
docker compose exec backend python /app/scripts/score_factors.py --help

# 手动刷新行业轮动
docker compose exec backend python /app/scripts/refresh_industry.py \
  --database-url postgresql+psycopg://ai_research:ai_research@db:5432/ai_research
```

## 核心 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/HEAD | `/api/health/ready` | API 与数据库就绪状态 |
| GET | `/api/system/status` | Provider、LLM 与快照状态 |
| GET / POST | `/api/market/dashboard` | 读取 / 刷新市场概览 |
| GET / POST | `/api/market/funds` | 读取 / 刷新资金快照 |
| GET | `/api/market/stocks/{symbol}` | 读取单股缓存行情 |
| POST | `/api/market/stocks/{symbol}/refresh` | 刷新单股行情、公告与资讯 |
| GET | `/api/factors/top30` | 因子 TOP30 候选池 |
| GET | `/api/factors/overview` | 因子定义与验证摘要 |
| POST | `/api/factors/refresh` | 创建候选池技术因子刷新任务 |
| GET / POST | `/api/research/reports...` | 读取历史报告或创建研报任务 |
| GET / POST | `/api/industry/rotation...` | 读取、选择日期或刷新行业轮动 |
| POST | `/api/reviews/generate` | 创建 AI 每日复盘任务 |

完整交互契约可在服务启动后通过 Swagger UI 查看。

## 项目结构

```text
AlphaLens/
├─ frontend/                  React 页面、组件、API Client 和类型
├─ backend/
│  ├─ app/api/routes/         FastAPI 路由
│  ├─ app/services/           业务规则
│  ├─ app/repositories/       数据访问与后端切换
│  ├─ app/market/             公开行情 Provider
│  ├─ app/llm/                LLM Provider
│  ├─ app/db/                 SQLAlchemy 模型与会话
│  ├─ app/schemas/            Pydantic 数据契约
│  ├─ migrations/             Alembic 数据库迁移
│  └─ tests/                  后端测试
├─ data/seed/                 首次启动演示数据
├─ scripts/                   导入、评分和刷新 CLI
├─ infra/                     Dockerfile 与 Nginx 配置
├─ tests/e2e/                 端到端冒烟脚本
├─ docs/                      完整教材与面试提纲
├─ .github/workflows/ci.yml   持续集成
└─ docker-compose.yml         三服务编排
```

## 数据、安全与能力边界

- 行情来自公开数据源的准实时快照，不是逐笔实时数据；供应商可能延迟、限流或调整字段。
- 市场全量源不可用时，概览会降级为“四大指数 + 当前 30 只研究候选股”的真实行情统计，并明确标注范围。
- 基本面因子随财报更新，不应描述为盘中实时数据；在线刷新不会假装更新财务指标。
- `BackgroundTasks` 和进程内限流适合个人演示；多实例生产环境应替换为 Redis/队列/Worker 和共享限流。
- 当前没有登录、权限、审计、组合风控、订单或交易接口。
- LLM 输出可能存在事实错误，必须结合来源记录人工核验。
- `.env`、虚拟环境、构建产物、数据库卷和 macOS `._*` 元数据均被版本控制忽略。

## 实习项目价值

这个项目重点展示的不是“页面数量”，而是完整工程闭环：

1. 将投研需求拆成可交互产品模块；
2. 将外部不稳定数据转化为可追踪、可回退的本地快照；
3. 将量化计算过程做成可解释、可复算的评分链路；
4. 将耗时 LLM 调用改造成可恢复的异步任务；
5. 用数据库迁移、测试、CI、容器和健康检查完成可交付部署；
6. 对实时性、因子有效性、模型输出和生产能力保持明确边界。

## 延伸文档

- [完整项目教材](docs/PROJECT_TEXTBOOK.md)：从 Web 基础、源码、数据、AI、部署到排错的系统说明；
- [面试讲解提纲](docs/INTERVIEW_GUIDE.md)：三分钟介绍、关键设计和常见边界；
- [GitHub Actions](https://github.com/Chandler-h-blake/AlphaLens/actions)：持续集成运行记录。

## 后续演进

1. 接入具备授权和 SLA 的行情与财务数据；
2. 增加定时采集、数据质量检查、血缘和监控告警；
3. 使用 Redis + Worker 替换进程内后台任务；
4. 增加完整历史回测、交易成本、基准比较和组合风控；
5. 增加身份认证、权限、审计与多用户隔离；
6. 为 AI 增加检索引用校验和结构化评测。
