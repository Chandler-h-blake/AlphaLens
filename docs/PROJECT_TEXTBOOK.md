# AlphaLens 全栈项目完整教材

> 适用读者：能看懂少量 Python/JavaScript，但还不能独立讲清全栈项目的人。  
> 学习目标：读完后能从浏览器、接口、业务逻辑、数据库、外部数据源、AI、部署和测试八个角度完整解释 AlphaLens。

---

## 0. 先说明这本教材覆盖什么

本教材覆盖项目中每个手写模块、核心代码结构、关键算法和主要异常路径。不会逐行解释以下内容：

- `pnpm-lock.yaml`：由包管理器生成的依赖锁文件；理解它保证版本一致即可。
- CSV 中的每一条股票数据：它们是输入样本，不是程序逻辑。
- 图片、SVG 的每个像素或路径：它们是界面资产。
- Python 空的 `__init__.py`：它主要用于标记包目录。

“理解项目”不等于背诵每一行代码。真正需要掌握的是：一条请求经过哪些层、每层为什么存在、数据何时更新、失败时如何处理、哪些结论不能夸大。

---

## 1. 一句话认识项目

AlphaLens 是一个 React + FastAPI + PostgreSQL 的可部署 A 股投研应用。

它包含八个主要页面：

1. 市场概览
2. 因子选股
3. AI 投研报告
4. 资金监控
5. 个股对比
6. AI 每日复盘
7. 行业轮动
8. 设置与数据状态

项目不提供真实交易，也不是交易所级实时行情系统。它提供的是：公开行情快照、最新交易日技术因子、最近披露的财务因子、研究报告和可追踪的数据来源。

---

## 2. 先建立全局画面

用户在浏览器中看到页面，但真正的数据处理发生在后端和数据库中：

```text
用户浏览器
   ↓ HTTP
Nginx :8080
   ├─ /            → React 静态文件
   └─ /api/*       → FastAPI :8000
                         ↓
                Route → Service → Repository
                         ↓             ↓
                   外部数据源      PostgreSQL
```

一次普通页面读取：

```text
React 发 GET 请求
→ Nginx 转发 /api
→ FastAPI 路由接收
→ Service 执行业务规则
→ Repository 查询 PostgreSQL
→ Pydantic 校验响应
→ JSON 返回 React
→ React 更新 state
→ 页面重新渲染
```

一次手动刷新：

```text
用户点击刷新
→ React 发 POST 请求
→ FastAPI 调用公开 Provider
→ 校验和计算新数据
→ 成功后写入 PostgreSQL
→ 返回 fresh 快照

如果失败：
→ 不覆盖数据库
→ 返回最近一次成功快照
→ freshness=stale，并带 warning
```

这就是本项目最核心的工程思想：读取本地持久化结果，刷新才访问外部服务，失败时保护旧结果。

---

## 3. 项目目录怎么读

```text
新任务/
├─ frontend/                 React 前端
│  ├─ src/pages/             页面组件
│  ├─ src/components/        可复用组件
│  ├─ src/api/               HTTP 请求封装
│  ├─ src/types/             TypeScript 数据类型
│  └─ src/styles/            全局 CSS
├─ backend/                  FastAPI 后端
│  ├─ app/api/routes/        API 路由
│  ├─ app/services/          业务逻辑
│  ├─ app/repositories/      数据访问
│  ├─ app/db/                ORM 模型和数据库连接
│  ├─ app/schemas/           Pydantic 请求/响应模型
│  ├─ app/market/            外部行情 Provider
│  ├─ app/llm/               LLM Provider
│  ├─ migrations/            Alembic 数据库迁移
│  └─ tests/                 后端测试
├─ data/seed/                首次启动种子数据
├─ scripts/                  管理员 CLI
├─ infra/                    Dockerfile 和 Nginx
├─ tests/e2e/                端到端冒烟测试
├─ docker-compose.yml        三个容器的编排
└─ .env.example              环境变量模板
```

推荐阅读顺序：

1. `frontend/src/pages/FactorsPage.tsx`
2. `frontend/src/api/factors.ts`
3. `backend/app/api/routes/factors.py`
4. `backend/app/services/factor_service.py`
5. `backend/app/repositories/database_repository.py`
6. `backend/app/db/models.py`

沿这个顺序，你会看到“一次页面请求”从前端一直走到数据库。

---

## 4. 必须掌握的 Web 基础

### 4.1 前端、后端和数据库分别是什么

- 前端负责交互和展示，不应该保存数据库密码或 LLM 密钥。
- 后端负责业务规则、权限边界、数据处理和外部服务调用。
- 数据库负责持久化；服务重启后数据仍然存在。

### 4.2 HTTP 方法

本项目主要使用：

- `GET`：读取，不应改变业务数据。
- `POST`：创建任务或触发刷新，会产生状态变化。

例如：

```text
GET  /api/market/dashboard   读取已保存市场快照
POST /api/market/dashboard   联网刷新市场快照
```

将读取和刷新分开，调用者一看方法就知道是否可能修改数据。

### 4.3 JSON

前后端不是直接共享 Python 对象，而是交换 JSON：

```json
{
  "source": "腾讯财经公开行情",
  "freshness": "fresh",
  "data": {
    "indexes": []
  }
}
```

JSON 只支持字符串、数字、布尔值、空值、数组和对象。日期在网络上传输时通常变成 ISO 字符串。

### 4.4 状态码

- `200`：读取或刷新成功。
- `404`：资源不存在，例如股票没有快照。
- `422`：输入不符合约束，例如代码不是六位数字。
- `429`：刷新过于频繁。
- `502`：上游行情或模型服务失败。
- `503`：数据源或 LLM 未配置。

---

## 5. 前端技术栈

### 5.1 React

React 的核心思想是：界面是状态的函数。

```text
UI = f(state)
```

当 `state` 改变时，React 重新计算需要变化的界面。

项目入口在 `frontend/src/main.tsx`：

```tsx
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

逐层解释：

- `document.getElementById('root')` 找到 HTML 挂载点。
- `createRoot` 创建 React 根节点。
- `StrictMode` 在开发环境帮助发现不安全副作用。
- `BrowserRouter` 根据 URL 决定展示哪个页面。
- `App` 是整个应用的根组件。

### 5.2 TypeScript

TypeScript 在 JavaScript 上增加静态类型。

```ts
export interface FactorTopPoolItem {
  symbol: string
  rank: number
  composite_score: number
}
```

如果代码把 `rank` 当字符串使用，构建阶段就能发现问题。类型不会替代运行时校验：网络可能返回错误 JSON，所以后端仍然需要 Pydantic。

### 5.3 Vite

Vite 负责：

- 本地开发服务器
- TypeScript/React 构建
- 模块打包
- 生成可部署的 `dist/`

```bash
pnpm build
```

实际执行：

```text
tsc -b      类型检查
vite build  打包生产静态文件
```

### 5.4 React Router

`frontend/src/App.tsx` 定义 URL 与页面组件的映射：

```tsx
<Route path="/dashboard" element={<DashboardPage />} />
<Route path="/factors" element={<FactorsPage />} />
<Route path="/research/:symbol" element={<ResearchDetailPage />} />
```

`:symbol` 是动态参数。例如 `/research/002558` 会打开代码为 `002558` 的研报详情。

页面使用 `lazy` 懒加载：

```tsx
const FactorsPage = lazy(() => import('./pages/FactorsPage'))
```

好处是用户第一次访问首页时，不必下载所有页面代码。

### 5.5 React 状态和副作用

因子页的典型状态：

```tsx
const [pool, setPool] = useState<FactorTopPoolResponse | null>(null)
const [isLoading, setIsLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
```

- `pool` 保存接口数据。
- `isLoading` 控制加载提示。
- `error` 控制错误状态。

`useEffect` 用来执行“渲染之外”的动作，例如请求接口：

```tsx
useEffect(() => {
  const controller = new AbortController()
  getFactorTopPool(..., controller.signal).then(setPool)
  return () => controller.abort()
}, [keyword, industry])
```

组件卸载或筛选条件改变时，旧请求会被取消，避免旧响应覆盖新结果。

### 5.6 API Client

`frontend/src/api/client.ts` 统一处理请求：

```ts
async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) throw new ApiError(...)
  return response.json() as Promise<T>
}
```

为什么不在每个页面直接写 `fetch`？

- API 根地址只配置一次。
- 错误格式只解析一次。
- GET/POST 行为保持一致。
- 页面只关心业务，不关心重复网络细节。

### 5.7 Recharts

Recharts 将数组数据映射为图形：

```tsx
<BarChart data={items}>
  <XAxis dataKey="name" />
  <Bar dataKey="composite_score" />
</BarChart>
```

图表不是图片，而是由 React 根据数据生成的 SVG。数据变化后图表自动更新。

### 5.8 React Markdown

LLM 生成的是 Markdown 字符串。`ReactMarkdown` 将它安全转换为 React 元素：

```tsx
<ReactMarkdown>{content}</ReactMarkdown>
```

这比直接注入 HTML 更容易控制，也更适合研报的标题、列表和段落结构。

### 5.9 CSS

`frontend/src/styles/index.css` 统一定义布局、色彩、表格、卡片、移动端断点。关键布局方式：

- Grid：侧边栏、指标卡、报告卡。
- Flexbox：标题栏、按钮、筛选器。
- Media Query：小屏幕下改变列数。
- class 状态：`market-up`、`market-down`、`spin`。

---

## 6. 每个前端文件做什么

### 6.1 入口与布局

- `main.tsx`：挂载 React，启用 Router。
- `App.tsx`：声明路由和页面懒加载。
- `AppLayout.tsx`：侧边栏、顶部栏和 `<Outlet />` 页面出口。
- `index.css`：全局视觉系统与响应式布局。

### 6.2 API 文件

- `api/client.ts`：通用 GET、POST、错误处理。
- `api/dashboard.ts`：市场概览、资金、系统状态、每日复盘接口。
- `api/factors.ts`：TOP30、因子概览、技术因子刷新任务。
- `api/industry.ts`：行业轮动读取。
- `api/market.ts`：单股快照读取与刷新。
- `api/research.ts`：研报列表、详情、生成任务轮询。

### 6.3 类型文件

`types/` 与后端 `schemas/` 基本对应。它们让页面知道响应中有哪些字段，但不会自动验证服务器运行时输出。

### 6.4 组件文件

- `FactorTable.tsx`：候选股表格与数字格式化。
- `FactorScoreChart.tsx`：综合得分图。
- `SnapshotNotice.tsx`：统一显示来源、时间、新鲜度和警告。

### 6.5 页面文件

- `DashboardPage.tsx`：四大指数、行业热度、涨跌分布、成交额排行。
- `FactorsPage.tsx`：因子筛选、排名、在线刷新任务。
- `ResearchPage.tsx`：研报列表与搜索。
- `ResearchDetailPage.tsx`：Markdown 研报、来源、AI 更新按钮。
- `FundsPage.tsx`：行业资金流和不可核验字段说明。
- `ComparePage.tsx`：在浏览器中比较 2–5 只股票，不新增重复后端 API。
- `ReviewPage.tsx`：创建每日复盘任务并轮询。
- `IndustryPage.tsx`：收益排行、轮动状态、刷新。
- `SettingsPage.tsx`：数据库、LLM、Provider 和快照时间。
- `MarketPage.tsx`：单股行情、资金和公告；它是保留的单股研究路由。

---

## 7. 后端技术栈

### 7.1 FastAPI

FastAPI 是 HTTP API 框架。它负责：

- 路由匹配
- 参数校验
- 依赖注入
- 响应序列化
- OpenAPI 文档
- 后台任务

典型路由：

```python
@router.get("/top30", response_model=FactorTopPoolResponse)
def get_top30(service: FactorServiceDependency, limit: int = Query(30, ge=1, le=100)):
    return service.get_top_pool(limit=limit, ...)
```

- 装饰器声明 URL 和 HTTP 方法。
- `Query` 限制参数范围。
- `Depends` 构造 Service。
- `response_model` 保证输出符合约定。

### 7.2 Pydantic

Pydantic 模型是接口契约：

```python
class FactorTopPoolItem(BaseModel):
    symbol: str = Field(description="六位股票代码")
    rank: int = Field(ge=1)
    composite_score: float
```

后端返回错误类型时，Pydantic 会尽早暴露问题，防止未经约束的数据进入前端。

### 7.3 Uvicorn

Uvicorn 是运行 FastAPI 的 ASGI Server：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

FastAPI 是应用代码，Uvicorn 才是真正监听端口、接收网络连接的进程。

### 7.4 HTTPX

HTTPX 用于后端访问：

- 东方财富
- 腾讯财经
- 新浪财经
- 申万研究
- OpenAI-compatible LLM

项目设置超时、检查 HTTP 状态，并将网络异常转换成业务异常。

### 7.5 Pandas

Pandas 用于表格数据处理：

- 读取 CSV
- 数值转换
- 缺失值检查
- 因子标准化
- 排名
- 行业收益计算

它适合当前几十到几百只股票的研究任务。若处理亿级行情，应改用数据库计算、Polars、Spark 或专门的时序系统。

---

## 8. Route → Service → Repository 分层

这是后端最重要的结构。

### 8.1 Route

Route 只处理 HTTP 世界：

- URL
- GET/POST
- 参数
- 状态码
- 调用哪个 Service

Route 不应该写复杂因子公式或 SQL。

### 8.2 Service

Service 处理业务规则：

- 是否允许刷新
- 怎样计算因子
- 什么时候保存
- 失败时是否回退
- 怎样组织 LLM Prompt

### 8.3 Repository

Repository 处理数据访问：

- SQLAlchemy 查询
- 新增、更新、删除
- CSV/Markdown 读取适配

页面不应该知道表结构，Route 也不应该到处复制 SQL。

### 8.4 为什么值得分层

假设以后将 PostgreSQL 换成云数据库，Route 和大部分 Service 不需要变化；只要 Repository 仍返回同样的数据结构即可。

---

## 9. 后端启动过程

`backend/app/main.py` 创建 FastAPI 应用。

启动时的关键过程：

1. 读取环境变量。
2. 注册 CORS。
3. 注册请求 ID、计时、安全响应头和限流中间件。
4. 注册统一异常处理。
5. 注册所有 `/api` 路由。
6. 服务重启时，将遗留的 `pending/running` 任务标为失败，防止前端永远轮询。

`lifespan` 中的任务恢复体现了一个重要原则：进程重启后，数据库状态必须回到可解释状态。

---

## 10. 配置系统

`backend/app/core/config.py` 使用 `pydantic-settings`。

```python
class Settings(BaseSettings):
    database_url: str | None = None
    llm_provider: Literal["disabled", "openai_compatible"] = "disabled"
    market_data_provider: Literal["disabled", "eastmoney_public"] = "eastmoney_public"
```

配置优先来自环境变量和项目根目录 `.env`。真实密钥不提交 Git，仓库只提交 `.env.example`。

`get_settings()` 使用 `@lru_cache`，保证一个进程中不反复解析配置。

`normalize_database_url` 将普通 PostgreSQL URL 转换成 SQLAlchemy 使用的 psycopg 驱动形式。

---

## 11. 统一异常与可观测性

### 11.1 业务异常

`core/exceptions.py` 定义：

- `DataSourceError`
- `ResourceNotFoundError`
- `LLMConfigurationError`
- `LLMProviderError`
- `MarketDataProviderError`

异常处理器将 Python 异常转换成统一 JSON：

```json
{
  "detail": {
    "code": "MARKET_DATA_PROVIDER_ERROR",
    "message": "公开行情暂不可用"
  }
}
```

前端不需要猜测每个接口不同的错误格式。

### 11.2 请求 ID

`RequestContextMiddleware` 为每个响应增加：

- `X-Request-ID`
- `X-Response-Time-Ms`
- 安全响应头

出现问题时可以用请求 ID 串联浏览器和后端日志。

### 11.3 限流

刷新和 AI 生成属于昂贵写操作。中间件按客户端和时间窗口记录请求：

- 普通市场刷新：每分钟限制。
- 研报生成：每小时限制。
- 因子刷新：每小时 2 次。

当前限流状态保存在单个后端进程内，适合个人项目。多实例部署应改为 Redis 等共享限流存储。

---

# 第四篇：数据库——数据为什么能在重启后仍然存在

## 第 12 章 PostgreSQL 与 SQLAlchemy

### 12.1 PostgreSQL 在本项目中的职责

PostgreSQL 是项目唯一的运行时事实来源。页面不会直接读取 CSV，服务启动后也不会把 CSV 当成长期数据库。它保存：

- 股票基础信息；
- 因子得分与因子验证摘要；
- 市场、资金、行业轮动快照；
- 单股行情与公告；
- 已生成的 AI 研报和每日复盘；
- 异步任务的状态；
- 数据来源、行情时间和抓取时间。

这里要区分两个概念：

- `data/seed/` 是“初始教材样例”，用于空数据库第一次初始化；
- PostgreSQL 是“应用真正运行时的数据”，刷新后的新快照写在这里。

因此，应用不是每次打开页面就重新读取 CSV，更不是每次打开页面都必须联网。

### 12.2 ORM 是什么

SQLAlchemy 是 Python ORM。ORM 的作用是把数据库表映射成 Python 类。

例如 `Stock` 类对应 `stocks` 表：

```python
class Stock(Base):
    __tablename__ = "stocks"

    symbol = mapped_column(String(6), primary_key=True)
    name = mapped_column(String(64))
    industry = mapped_column(String(64), nullable=True)
```

你可以把一行股票记录理解为一个 `Stock` 对象。ORM 最终仍会生成 SQL，但业务代码不必到处手写 SQL 字符串。

### 12.3 Session 与事务

数据库 `Session` 可以理解为“一次数据库工作单元”。典型流程是：

```python
with session_factory() as session:
    # 查询或修改对象
    session.commit()
```

关键规则：

- 查询不一定修改数据；
- 修改只存在于当前事务中，`commit()` 后才正式提交；
- 发生异常时应 `rollback()`，避免保存一半；
- `expire_on_commit=False` 让提交后的对象仍能安全读取字段；
- `pool_pre_ping=True` 在复用连接前检查连接，减少容器长时间运行后的失效连接问题。

本项目的刷新流程尽量遵循“先在内存中算完整，再用一次事务发布”。这样不会出现只写了 12 只股票、另外 18 只失败的半成品快照。

### 12.4 表结构逐项说明

#### `stocks`

股票主数据表。`symbol` 是六位股票代码，也是主键。其他股票相关表用外键指向它。

#### `factor_scores`

每只股票、每个数据日期一条因子结果：

- `rank`：当日综合排名；
- `composite_score`：综合得分；
- `factor_values`：JSON，保存原始值、标准分和贡献等细项。

`symbol + data_date` 有唯一约束，防止同一只股票同一天重复写入。

#### `factor_overviews`

保存每个因子的名称、类别、方向、权重、来源、说明和验证指标。它回答“这个因子是什么”，而 `factor_scores` 回答“某只股票这个因子表现如何”。

#### `research_reports`

保存历史 AI 研报。正文使用 Markdown，`sources` 使用 JSON 数组，便于保留来源名称、日期和链接。

#### `industry_rotations`

保存行业近 1 月和近 3 月收益、两个周期的排名以及轮动分类。唯一键为行业代码和数据日期。

#### `research_tasks`

这是通用任务表。`kind` 区分：

- `research_report`：单股 AI 研报；
- `daily_review`：AI 每日复盘；
- `factor_refresh`：技术因子刷新。

状态通常依次为 `pending → running → success`，异常时变为 `failed`。共用一张表可以复用轮询、错误保存和恢复逻辑。

#### `source_documents`

这是为将来的文档检索或 RAG 预留的来源文档表。当前主流程没有依赖它，因此面试时不能声称项目已经实现完整 RAG。

#### `market_snapshots`

每只候选股只保留最新一条行情快照，包括价格、涨跌幅、成交量、成交额、市值、主力净流入、来源、行情时间和抓取时间。

#### `market_announcements`

保存公司公告。`symbol + article_id` 唯一，避免重复刷新产生重复公告。

#### `workspace_snapshots`

保存“整块页面级快照”，目前常见 key 包括市场概览、资金监控和因子刷新元数据。`payload` 是 JSON，因此不同看板可以保存不同结构。

#### `daily_reviews`

保存每日复盘 Markdown、生成时间以及生成时使用的数据摘要。

### 12.5 为什么既有结构化列又有 JSON

经常筛选、排序、关联的字段应使用普通列，例如股票代码、日期、排名。结构变化较快、内部字段较多的快照适合 JSON，例如整个市场概览 payload。

全部做成 JSON 会损失数据库约束和查询能力；全部拆成几十张表又会让个人作品项目过度复杂。本项目选择折中方案。

## 第 13 章 Alembic：数据库版本控制

代码会变，数据库结构也会变。Alembic 用迁移文件记录“数据库从旧版本如何升级到新版本”。

本项目迁移顺序为：

1. `0001_initial_schema.py`：核心股票、因子、行业、报告与任务表；
2. `0002_persist_generated_reports.py`：完善生成报告的持久化；
3. `0003_add_market_data_tables.py`：增加行情和公告表；
4. `0004_add_workspace_snapshots.py`：增加工作区快照与每日复盘。

启动时执行：

```bash
alembic upgrade head
```

`head` 表示升级到最新版本。不要直接在生产数据库里手工改表，否则代码仓库无法记录这次变化。

## 第 14 章 种子数据与幂等导入

### 14.1 为什么需要种子数据

公开数据接口可能限流、改版或暂时不可访问。作品展示不能因为上游接口出故障而只剩空白页。因此项目内置一份明确标注日期和来源的演示快照。

### 14.2 首次启动发生什么

`scripts/start.sh` 启动 Docker Compose。后端容器启动命令先：

1. 等待 PostgreSQL 就绪；
2. 执行 Alembic 迁移；
3. 执行 `scripts/import_seed_data.py`；
4. 启动 Uvicorn API 服务。

### 14.3 幂等是什么意思

幂等表示同一操作执行一次和执行多次，最终结果一致。种子导入会先检查关键数据是否存在，不会每次启动都复制一批相同数据。

这很重要，因为容器重启是正常操作。如果每次重启都插入重复记录，数据库会很快失真。

### 14.4 `--replace` 的边界

管理员需要重置演示数据时可使用替换模式。它针对种子负责的因子、概览、行业等数据进行重导入，而不是粗暴删除所有用户生成的报告。任何实际执行前都应先备份重要数据库卷。

---

# 第五篇：数据工程——数据从哪里来、怎样变成页面

## 第 15 章 三层数据策略

AlphaLens 的数据分三层：

```text
公开行情网站
    ↓ HTTP 获取、解析、校验
后端内存中的标准对象
    ↓ 事务写入
PostgreSQL 最新快照
    ↓ GET API
React 页面
```

页面打开时通常执行 GET，读取数据库中的最近快照。只有用户点击刷新按钮时，才执行 POST，要求后端联网抓取。

所以，“实时”不能理解成交易所逐笔实时推送。当前项目更准确的说法是：

> 用户触发的准实时公开行情刷新，并带有缓存和失败回退。

免费公开接口存在延迟、频率限制和可用性风险，本项目不能替代券商专业行情终端。

## 第 16 章 Provider：隔离外部数据源

Provider 是“外部数据适配器”。业务服务只要求它返回统一格式，不关心上游原始 JSON 的字段编号。

例如单股行情主数据源失败时，可以尝试备用源：

```text
Service 要一份标准 Quote
  ├─ 东方财富请求成功 → 转为 FetchedQuote
  └─ 东方财富失败 → 腾讯公开行情 → 转为同一个 FetchedQuote
```

这种设计的价值是：未来更换数据商时主要修改 Provider，而不是重写页面、路由和数据库。

### 16.1 当前公开数据来源

- 东方财富公开接口：单股行情、历史行情、公告、全市场列表、部分资金数据；
- 腾讯财经公开行情：单股和指数备用行情、候选池历史行情备用源；
- 新浪公开公告能力：公告备用来源；
- 申万公开行业行情：行业轮动数据来源。

这些接口不是本项目控制的正式付费 SLA。字段或访问策略可能变化，所以代码设置了超时、重试、备用源和旧快照回退。

### 16.2 三个时间字段不能混为一谈

- `data_date`：因子或行业结果对应的交易日期；
- `as_of`：行情内容本身截止到什么时间；
- `fetched_at`：后端什么时候抓取到这份数据。

例如周六点击刷新，`fetched_at` 可以是周六，但 `as_of` 通常仍是周五收盘时间。这不是错误，而是市场没有新的交易数据。

## 第 17 章 因子选股的完整计算

### 17.1 因子不是“AI 猜涨跌”

因子是可计算的股票特征。项目使用九个因子，把不同量纲的指标标准化后加权，形成候选池内的相对排名。

它回答的是“在当前规则与候选范围内，谁的综合特征更靠前”，不是保证未来收益。

### 17.2 两类更新频率

九个因子包含两类数据：

- 市场技术因子：20 日动量、换手变化、60 日波动率，可由近期日线刷新；
- 基本面/估值因子：ROE、营收增长、利润增长、毛利率、PE、PB，沿用最近已保存的财务快照。

因此点击“刷新技术因子”不是重新抓取最新财报。教材和界面都应明确这个边界。

### 17.3 三个技术因子公式

20 日动量：

```text
momentum_20 = close_today / close_20_days_ago - 1
```

换手变化：

```text
turnover_change = average(turnover, last 5 days)
                  / average(turnover, last 20 days) - 1
```

当备用行情只提供成交量而没有换手率时，项目在短窗口内使用成交量均值比作为代理。原因是若流通股本近似不变，换手率分母会在比值中抵消。它是合理近似，不是严格等价；送转股、解禁或股本变化时可能偏离。

60 日年化波动率：

```text
daily_return = close_today / close_yesterday - 1
volatility_60 = std(daily_return over 60 days) × sqrt(252)
```

`252` 是一年常用交易日数量近似。

### 17.4 标准化为什么必要

PE 可能是几十，增长率可能是小数，原始数值不能直接相加。项目在当前 30 只候选股范围内计算 Z-score：

```text
z = (x - mean) / standard_deviation
```

它表示某只股票相对候选池平均值高多少个标准差。

### 17.5 方向与权重

有些因子越大越好，例如 ROE；有些越小越好，例如波动率或估值。综合贡献为：

```text
contribution_i = z_i × direction_i × weight_i
composite_score = sum(contribution_i)
```

其中 `direction` 是 `1` 或 `-1`。最后按综合分从高到低排序。

### 17.6 为什么寻找共同交易日

不同股票可能停牌或某个上游请求缺少最新一根 K 线。若直接取各自最后一天，会把不同日期的数据混在同一排名里。

刷新服务会寻找候选股票历史数据的最新共同交易日期，再基于这个日期计算。这样横向比较更一致。

### 17.7 刷新任务完整链路

```text
点击“刷新技术因子”
  → POST /api/factors/refresh
  → 创建 factor_refresh 任务
  → 后台并发获取 30 只候选股日线
  → 主源失败则尝试腾讯备用源
  → 找共同日期并计算 3 个技术因子
  → 合并最近 6 个基本面/估值因子
  → 对 9 因子重新标准化和加权
  → 一次事务写入新日期的 30 条结果
  → 前端轮询任务并重新 GET TOP30
```

并发抓取能缩短等待时间，但并发量应受控，避免对公开接口造成过高压力。

## 第 18 章 市场概览、资金、行业和单股数据

### 18.1 市场概览

理想路径是从全市场列表聚合：

- 主要指数；
- 行业涨跌热力图；
- 上涨、下跌、平盘数量；
- 成交额 TOP20。

若全市场接口不可用，项目会抓取主要指数和当前 30 只研究候选股，生成“候选池范围”的概览。此时响应必须带来源和警告，不能把 30 只股票包装成全 A 股统计。

### 18.2 资金监控

资金页读取已保存的资金快照，点击刷新时再访问公开资金接口。若某项数据无法可靠核验，宁可显示缺失，也不伪造数字。刷新失败时保留旧快照并标记陈旧。

### 18.3 行业轮动

行业刷新获取每个行业的历史收盘序列，并计算：

```text
return_1m = latest_close / close_about_20_trading_days_ago - 1
return_3m = latest_close / close_about_60_trading_days_ago - 1
```

再分别排名，并根据短中期排名组合划分领先、改善、转弱、落后等轮动状态。分类是项目规则，不是行业标准投资评级。

### 18.4 单股行情与公告

AI 研报详情页可读取 `market_snapshots` 和 `market_announcements`。刷新接口先抓取、标准化和保存，再把数据库中的统一响应返回前端。

### 18.5 陈旧快照机制

当上游失败时，系统不会删除旧数据。响应带：

- 当前数据来源；
- 数据截止时间；
- 抓取时间；
- 是否陈旧；
- 为什么回退的警告。

“保留旧数据并明确告知”比“请求失败后整个页面白屏”更适合投研场景。

---

# 第六篇：异步任务与 AI

## 第 19 章 为什么要异步生成

LLM 调用或 30 只股票历史数据抓取可能持续数秒甚至更久。若浏览器一直等待一个长 HTTP 请求，容易超时，也无法清楚展示进度。

项目采用任务模式：

```text
POST 创建任务 → 立即返回 task_id
前端定时 GET 任务状态
成功后 GET result
```

### 19.1 状态机

```text
pending → running → success
                  ↘ failed
```

- `pending`：任务已记录，尚未执行；
- `running`：后台函数正在处理；
- `success`：结果已保存；
- `failed`：错误信息已保存。

### 19.2 为什么状态写数据库

状态若只放在 Python 字典里，进程重启后会丢失。数据库任务表让客户端仍能查询历史结果。

应用启动时会把上次进程中遗留的 `pending/running` 任务标记失败，因为简单的 FastAPI BackgroundTasks 无法跨重启继续执行。

### 19.3 当前实现的能力边界

FastAPI `BackgroundTasks` 适合单机作品项目，但不是可靠任务队列。生产级演进可使用 Celery、RQ 或 Dramatiq，加 Redis/RabbitMQ，并实现重试、超时、任务锁和独立 worker。

## 第 20 章 OpenAI-compatible LLM Provider

### 20.1 为什么称为 compatible

后端按照 OpenAI 风格的 Chat Completions HTTP 协议请求：

```text
POST {LLM_BASE_URL}/chat/completions
Authorization: Bearer {LLM_API_KEY}
```

只要某个服务兼容该协议，通常就能通过环境变量切换，而不用改业务服务。

### 20.2 四个配置项

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_key
LLM_BASE_URL=https://example.com/v1
LLM_MODEL=your-model
```

密钥只放在项目根目录 `.env`，该文件被 Git 忽略。前端永远不读取、保存或展示密钥。

### 20.3 无密钥时为什么禁用按钮

`GET /api/system/status` 只返回 `llm_configured: true/false`，不返回密钥。前端据此禁用生成按钮并提示配置。

系统不会用固定模板伪装成 AI 生成结果。这样演示更诚实，也避免用户误解。

## 第 21 章 AI 研报生成

完整链路：

```text
用户选择股票并点击生成
  → 后端检查 LLM 配置
  → 检查股票是否存在
  → 建立 research_report 任务
  → 收集因子结果、行情、公告等上下文
  → 构造有边界的提示词
  → 调用 LLM
  → 保存 Markdown 和 sources
  → 任务记录 report_id
  → 前端展示 Markdown
```

`ReactMarkdown` 负责把标题、表格、列表等 Markdown 转成 React 元素。需要注意：LLM 输出是辅助研究文本，不等于经过审计的事实；重要结论仍需核验数据来源。

## 第 22 章 AI 每日复盘

每日复盘不会再次随意抓取一套数据，而是读取已经保存的市场、资金和行业快照，形成一致的输入摘要，再调用同一个 LLM Provider。

这样做有两个好处：

1. 用户能看到 AI 基于哪一批时间点的数据生成；
2. 研报和复盘不需要维护两套 LLM 客户端。

`source_summary` 保存生成时使用的数据时间和来源，便于以后追溯。

---

# 第七篇：API 字典与八个页面

## 第 23 章 API 接口全表

### 系统接口

- `GET/HEAD /api/health`：基础健康状态；
- `GET/HEAD /api/health/live`：进程是否存活；
- `GET/HEAD /api/health/ready`：API 和数据库是否就绪；
- `GET /api/system/status`：数据新鲜度、Provider 和 LLM 可用性。

### 因子接口

- `GET /api/factors/top30`：读取某日或最近日期 TOP30；
- `GET /api/factors/overview`：读取因子说明与验证摘要；
- `POST /api/factors/refresh`：创建技术因子刷新任务；
- `GET /api/factors/refresh/tasks/{id}`：查询刷新状态。

### 研报接口

- `GET /api/research/reports`：历史研报列表；
- `GET /api/research/reports/{symbol}`：某只股票最新研报；
- `POST /api/research/reports/{symbol}/generate`：创建研报任务；
- `GET /api/research/tasks/{id}`：查询任务；
- `GET /api/research/tasks/{id}/result`：读取任务结果。

### 市场接口

- `GET /api/market/dashboard`：读取市场概览快照；
- `POST /api/market/dashboard`：联网刷新市场概览；
- `GET /api/market/funds`：读取资金快照；
- `POST /api/market/funds`：联网刷新资金快照；
- `GET /api/market/stocks/{symbol}`：读取单股缓存；
- `POST /api/market/stocks/{symbol}/refresh`：刷新单股和公告。

### 行业与复盘接口

- `GET /api/industry/rotation`：最近行业轮动；
- `GET /api/industry/rotation/dates`：可选日期；
- `POST /api/industry/rotation/refresh`：联网刷新行业；
- `POST /api/reviews/generate`：创建每日复盘任务；
- `GET /api/reviews/tasks/{id}`：查询复盘任务；
- `GET /api/reviews/tasks/{id}/result`：读取复盘结果。

### 公开站点接口

- `GET /robots.txt`：搜索引擎爬取规则；
- `GET /sitemap.xml`：站点页面索引。

## 第 24 章 八个页面逐页理解

### 24.1 市场概览

组件挂载后 GET 最近快照，展示指数、热力图、涨跌分布和成交额榜。点击刷新才 POST。`SnapshotNotice` 统一显示来源、时间和旧数据警告。

### 24.2 因子选股

同时获取 TOP30 和因子概览。筛选、排序在前端完成，不会每点一下表头都请求服务器。点击刷新后轮询任务，成功再重新拉取数据。

### 24.3 AI 投研

先列出历史报告，选中股票后进入详情。无密钥时页面仍可查看历史内容，但生成按钮不可用。

### 24.4 资金监控

读取资金快照，只有刷新动作触发外部请求。旧数据、缺失字段和来源都明确展示。

### 24.5 个股对比

用户从 TOP30 选择 2–5 只股票。综合分和五类因子贡献的比较在浏览器内根据现有 TOP30 数据计算，没有新增重复 API。

### 24.6 AI 每日复盘

读取系统状态决定生成按钮是否可用；提交任务后轮询；成功后渲染 Markdown。没有密钥时不会产生伪报告。

### 24.7 行业轮动

展示 1 月/3 月收益、排名和分类，可切换数据库中已有日期，并可手动刷新。

### 24.8 设置

只展示运行状态、数据新鲜度、Provider 状态和管理员命令说明。网页不提供密钥输入框，因为把服务端密钥送进浏览器会扩大泄漏面。

---

# 第八篇：部署——三个服务如何成为一个网站

## 第 25 章 Docker 与 Docker Compose

### 25.1 镜像、容器、卷

- 镜像：应用的只读打包模板；
- 容器：镜像运行起来的进程；
- 卷：独立于容器生命周期的持久化数据目录。

删除并重建后端容器不会自动删除 PostgreSQL 卷，因此数据仍在。执行删除卷的命令则可能清空数据库，必须谨慎。

### 25.2 三个服务

```text
浏览器 → frontend(Nginx, :8080)
                    ├─ 静态 React 文件
                    └─ /api → backend(Uvicorn, :8000)
                                      ↓
                                db(PostgreSQL, :5432)
```

数据库通常不需要暴露给公网。浏览器只访问 Nginx；Nginx 把 `/api` 反向代理给后端，因此前端代码不需要写死后端容器地址。

### 25.3 多阶段前端构建

前端 Dockerfile 通常先在 Node 镜像中执行依赖安装和 Vite build，再把 `dist` 复制到轻量 Nginx 镜像。

最终运行容器不需要 Node 开发工具，镜像更小，暴露面也更少。

### 25.4 健康检查与启动依赖

PostgreSQL 先通过健康检查；后端完成迁移和种子导入后就绪；前端再向后端代理。健康检查不只是“端口开着”，ready 接口还检查数据库。

### 25.5 常用命令

```bash
cd /Users/heao.mac/Desktop/新任务
cp .env.example .env
sh scripts/start.sh
docker compose ps
docker compose logs -f backend
docker compose down
```

访问地址：`http://localhost:8080`。API 文档：`http://localhost:8080/api/docs`。

`docker compose down` 停容器但默认保留数据卷。不要在不了解后果时附加 `-v`。

---

# 第九篇：测试、排错与代码阅读

## 第 26 章 测试体系

### 26.1 单元测试

单元测试隔离一个小函数或服务，例如因子计算、Provider 字段解析、配置判断。外部 HTTP 通常使用假对象，不让测试结果取决于当天网络。

### 26.2 API/集成测试

使用 FastAPI 测试客户端请求真实路由，验证响应状态、Schema、数据库写入和错误模型。

重点测试包括：

- 健康检查；
- 种子导入幂等；
- 因子、行业、市场、研报 API；
- 刷新成功与失败回退；
- LLM 未配置；
- 任务成功和失败；
- 限流。

### 26.3 前端质量检查

```bash
npm run lint
npm run build
```

TypeScript 编译能提前发现字段类型不一致；ESLint 检查常见代码问题；生产构建验证路由懒加载和资源打包。

### 26.4 端到端冒烟测试

`tests/e2e/smoke.sh` 从外部访问运行中的网站和关键 API，确认 Nginx、后端和数据库链路整体可用。

### 26.5 测试不能证明什么

测试通过不等于投资逻辑有效，也不能保证免费上游永不改版。它只能证明已覆盖场景在当前代码和假设下符合预期。

## 第 27 章 常见故障排查

### 27.1 页面打不开

依次检查：

```bash
docker compose ps
curl -i http://localhost:8080/api/health
docker compose logs --tail=200 frontend
docker compose logs --tail=200 backend
```

若 8080 端口被占用，先找出占用进程，不要随意终止不认识的服务。

### 27.2 后端不就绪

查看数据库日志和 ready 接口。常见原因是数据库密码与已有卷不一致、迁移失败或 PostgreSQL 尚未完成启动。

### 27.3 点击刷新仍是旧日期

先区分三种情况：

1. 非交易日，最新交易日本来就是前一个工作日；
2. 上游失败，系统明确回退到旧快照；
3. 接口返回成功但前端未重新 GET，这才可能是前端状态问题。

看页面的 `as_of`、`fetched_at`、`source` 和 warning，不要只看电脑当前日期。

### 27.4 AI 按钮不可用

检查项目根目录 `.env` 中四项 LLM 配置，再重建或重启后端：

```bash
docker compose up -d --build backend
curl http://localhost:8080/api/system/status
```

状态接口只会告诉你是否配置，不会回显密钥。

### 27.5 如何定位一次请求

浏览器开发者工具查看请求响应头中的 `X-Request-ID`，再在后端日志中查同一个 ID。这比只说“页面报错了”更容易定位。

## 第 28 章 推荐的源码阅读顺序

不要从最大文件第一行盲读到最后。按一条用户链路阅读：

1. `frontend/src/pages/FactorsPage.tsx`：按钮和页面状态；
2. `frontend/src/api/factors.ts`：发出的 HTTP 请求；
3. `backend/app/api/routes/factors.py`：路由入口；
4. `backend/app/services/factor_refresh_service.py`：业务流程；
5. `backend/app/market/eastmoney_provider.py`：外部数据；
6. `backend/app/repositories/database_repository.py`：数据库写入；
7. `backend/app/db/models.py`：表结构；
8. `backend/tests/test_factor_refresh.py`：预期行为。

读完这条链路，再用同一方法读市场概览和 AI 研报。

## 第 29 章 手写源码地图

### 根目录与基础设施

- `README.md`：三分钟项目介绍、启动与面试入口；
- `.env.example`：可提交的配置模板；
- `docker-compose.yml`：三个容器的编排；
- `infra/nginx.conf`：静态站点与 API 反向代理；
- `scripts/start.sh`：一键启动；
- `scripts/import_seed_data.py`：种子导入；
- `scripts/score_factors.py`：离线全量因子计算管道；
- `scripts/refresh_industry.py`：管理员行业刷新入口；
- `scripts/refresh_market_watchlist.py`：候选股行情刷新 CLI。

### 后端核心

- `app/main.py`：应用装配、生命周期、中间件、路由；
- `app/core/config.py`：环境变量配置；
- `app/core/exceptions.py`：统一业务错误；
- `app/core/observability.py`：请求 ID、计时、限流；
- `app/db/models.py`：全部 ORM 表；
- `app/db/session.py`：数据库 engine 与 Session；
- `app/api/router.py`：总路由注册；
- `app/api/routes/*.py`：HTTP 边界；
- `app/schemas/*.py`：请求响应结构；
- `app/services/*.py`：业务规则；
- `app/repositories/*.py`：持久化查询；
- `app/market/*.py`：公开数据 Provider；
- `app/llm/provider.py`：唯一 LLM 客户端；
- `migrations/versions/*.py`：数据库演进历史。

### 前端核心

- `main.tsx`：React 挂载点；
- `App.tsx`：路由与懒加载；
- `components/AppLayout.tsx`：导航和公共布局；
- `components/SnapshotNotice.tsx`：数据新鲜度；
- `components/FactorTable.tsx`：因子表格；
- `components/FactorScoreChart.tsx`：因子图表；
- `api/client.ts`：统一 fetch 与错误处理；
- `api/*.ts`：按业务域封装 API；
- `types/*.ts`：前后端契约的 TypeScript 表达；
- `pages/*.tsx`：八个业务页面和研报详情；
- `styles/index.css`：全局视觉系统与响应式样式。

自动生成的 `node_modules`、`dist`、Python 缓存、锁文件中的每一行不属于业务知识点，不应背诵；理解它们的用途和生成方式即可。

---

# 第十篇：把项目真正讲明白

## 第 30 章 三分钟面试讲解范例

> 我做了一个 React + FastAPI + PostgreSQL 的可部署 A 股投研应用 AlphaLens。前端有市场概览、因子选股、AI 投研、资金监控、个股对比、每日复盘、行业轮动和设置八个页面；后端采用 Route、Service、Repository 分层，PostgreSQL 保存种子快照、刷新数据、报告和任务状态。
>
> 数据侧采用“离线可演示 + 手动准实时刷新”。页面默认读取数据库，用户点击刷新后后端才访问公开行情；主数据源失败时切备用源，再失败就保留旧快照并明确标记来源和时间。因子模块会并发获取 30 只候选股的历史行情，计算 20 日动量、换手变化和 60 日波动率，再与最近基本面因子合并、标准化、加权和排名。
>
> AI 研报和每日复盘共用一个 OpenAI-compatible Provider 和通用任务表。未配置密钥时页面保留但禁用生成，不伪造 AI 内容。整个项目由 Docker Compose 启动 PostgreSQL、FastAPI 和 Nginx 静态前端，并有迁移、种子导入、健康检查、接口测试和冒烟测试。

## 第 31 章 高频追问与诚实回答

### “这是实时行情吗？”

不是交易所逐笔实时行情。它是用户点击触发的准实时公开行情，时间以响应中的 `as_of` 为准，并具有缓存、备用源和旧数据回退。

### “为什么页面不每次都抓最新数据？”

页面加载频繁直接抓上游会变慢、容易被限流，也无法保证多图使用同一时间点。先读数据库能快速稳定展示，刷新动作再显式联网。

### “为什么选 PostgreSQL？”

项目包含结构化关系、唯一约束、日期查询、事务更新和持久化任务；PostgreSQL 比散落 CSV 更适合，同时能体现真实后端工程能力。

### “为什么不用 Redux？”

当前跨页面共享状态很少，服务端状态由各页请求即可，局部 `useState/useEffect` 足够。引入 Redux 会增加样板代码。若未来加入登录、组合管理和复杂缓存，再考虑 Redux Toolkit 或 TanStack Query。

### “因子有效吗？”

项目实现了规范的特征标准化和组合评分，也保存验证摘要，但不能因此声称具有稳定超额收益。更严谨的下一步是做时间序列滚动回测、交易成本、幸存者偏差和未来函数检查。

### “最大的技术取舍是什么？”

为个人作品的可理解性和部署成本，使用进程内 BackgroundTasks 与限流，而没有上 Redis/Celery；为演示稳定性，默认读持久化快照，由用户触发刷新；对免费数据源的降级必须显式标注范围。

## 第 32 章 已知局限与演进路线

已确认的局限：

- 免费公开行情不保证稳定、低延迟或长期字段兼容；
- 市场全量源失败时只能给候选池范围统计；
- 基本面因子不会随“技术因子刷新”同步更新；
- BackgroundTasks 不具备跨进程可靠执行能力；
- 进程内限流不适合多实例；
- 没有用户、权限和审计体系；
- 没有真实交易、订单或组合风控；
- 因子验证不足以构成投资有效性证明；
- LLM 文本可能产生事实性错误，需要人工核验。

合理的演进顺序：

1. 接入有授权和 SLA 的行情/财务数据；
2. 建立定时采集、数据质量检查和血缘记录；
3. 用 Redis + Worker 替换进程内任务；
4. 增加完整历史回测、成本模型和基准比较；
5. 增加登录、组合、权限和操作审计；
6. 为 AI 加入可追溯检索、引用校验和结构化评测；
7. 最后才考虑实时推送与多实例部署。

---

# 第十一篇：学习检验

## 第 33 章 你是否真正理解了项目

如果你能不看答案解释下面问题，就已经掌握了项目主干：

1. 浏览器输入 `localhost:8080` 后，Nginx、React、FastAPI、PostgreSQL 各做什么？
2. GET 市场快照与 POST 刷新有什么根本区别？
3. `as_of` 和 `fetched_at` 为什么可能不同？
4. Provider、Service、Repository 为什么不能混成一个文件？
5. Z-score、因子方向和权重怎样形成综合分？
6. 为什么 30 只股票要使用共同交易日期？
7. 为什么 AI 密钥绝不能放进 Vite 前端环境变量？
8. 为什么生成任务要返回 task id，而不是让请求一直等待？
9. PostgreSQL 事务怎样避免半成品快照？
10. 为什么旧数据回退必须同时显示警告？
11. 种子数据与运行时快照有何区别？
12. 当前实现为什么只能称准实时，而不能称交易级实时？

## 第 34 章 建议的动手练习

按顺序完成以下练习，理解会比背诵更牢：

1. 打开浏览器网络面板，观察市场页首次 GET 和刷新 POST；
2. 用 `curl` 调健康接口和 TOP30 接口；
3. 在代码里从一个按钮追踪到数据库模型；
4. 暂时填入错误的 LLM 地址，观察统一错误与任务失败状态，再恢复配置；
5. 为一个 Schema 增加可选字段，同时修改 TypeScript 类型和测试；
6. 写一个测试模拟主 Provider 失败、备用 Provider 成功；
7. 用一组 5 个数字手算 Z-score 和综合贡献；
8. 查看 PostgreSQL 中刷新前后的 `data_date`，理解快照版本；
9. 重启容器，确认数据库记录仍存在；
10. 根据第 30 章录一段三分钟项目介绍，再回答第 31 章追问。

## 第 35 章 术语速查

- API：程序之间约定好的调用接口；
- HTTP：浏览器和服务器通信协议；
- JSON：常用结构化数据文本格式；
- SPA：由前端路由切换视图的单页应用；
- ORM：把数据库表映射为编程语言对象；
- Schema：输入输出的数据结构约束；
- Migration：可追踪的数据库结构升级；
- Transaction：一组要么全部成功、要么全部失败的数据库操作；
- Snapshot：某个时间点的数据快照；
- Provider：外部服务的适配层；
- Fallback：主路径失败后的备用路径；
- Stale：仍可展示但已经超过新鲜度标准的数据；
- Polling：客户端按间隔查询任务状态；
- Reverse Proxy：接收外部请求并转发给内部服务；
- Container：隔离运行应用的进程环境；
- Volume：容器之外的持久化数据；
- Z-score：数值偏离样本均值多少个标准差；
- LLM：大语言模型；
- Markdown：轻量文本排版语法；
- Idempotent：重复执行不会继续产生额外副作用。

---

# 结语

理解 AlphaLens 的关键，不是背下所有文件名，而是能在脑中复原四条主线：

```text
展示：PostgreSQL → Repository → Service → Route → React
刷新：React POST → Provider → 校验/计算 → 事务保存 → React 重载
AI：保存的数据 → Prompt → LLM → Markdown → 数据库 → 页面
部署：Docker Compose → PostgreSQL + FastAPI + Nginx/React
```

当你能沿任意一个页面，从按钮讲到 API、业务逻辑、数据来源、数据库表、异常回退和测试，你就不只是“运行过这个项目”，而是真正理解了它。
