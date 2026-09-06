# AlphaLens AI 投研平台

AlphaLens 是一个用于个人研究、实习展示和面试讲解的 A 股投研全栈项目。它把多因子选股、行业轮动、市场快照、资金监控和 LLM 辅助研究收敛为一套 React + FastAPI + PostgreSQL 应用。

> 仅供研究学习与工程演示，不构成投资建议；不支持真实下单。

## 三分钟讲清项目

1. **数据层**：将历史多因子结果、行业轮动和已生成研报作为种子数据导入 PostgreSQL；市场数据按“保存快照优先、手动刷新、失败回退”的原则处理。
2. **服务层**：FastAPI 通过 Route → Service → Repository 提供因子、研报、行业、市场、资金和 AI 生成任务 API；LLM 密钥只保存在部署环境变量中。
3. **产品层**：React 提供八个页面：市场概览、因子选股、AI 投研、资金监控、个股对比、AI 每日复盘、行业轮动、设置。
4. **可靠性边界**：公开数据源不稳定时展示最后成功快照并提示陈旧；未配置 LLM 时 AI 页面保留但禁止生成，绝不生成模板冒充 AI 内容。

## 一键启动

```bash
cp .env.example .env
sh scripts/start.sh
```

打开 [http://localhost:8080](http://localhost:8080)。首次启动会执行数据库迁移并导入 `data/seed/` 中的演示数据。

启动脚本直接构建镜像，是为了规避部分 Docker Compose Bake 版本在中文目录下的 `non-printable ASCII` 问题。项目移动到纯英文路径后，也可直接运行 `docker compose up --build`。市场与资金种子明确标为合成演示数据，不代表真实交易日。

启用 AI 生成时，在 `.env` 中设置：

```dotenv
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 技术栈

- 前端：React、TypeScript、Vite、React Router、Recharts、React Markdown
- 后端：Python、FastAPI、Pydantic、HTTPX、Uvicorn
- 数据：PostgreSQL、SQLAlchemy、Alembic、Pandas、CSV 种子快照
- AI：统一 OpenAI-compatible LLM Provider
- 工程化：Docker Compose、Nginx、Pytest、前端 lint/build、健康检查

## 项目边界

- 行情是公开数据源的准实时快照，不是逐笔实时行情。
- 因子和行业轮动是可追溯的研究快照；全量重算应通过管理员 CLI 完成。
- FastAPI `BackgroundTasks` 适用于个人演示；高并发生产任务应替换为独立队列。

## 常用命令

```bash
# 查看容器状态
docker compose ps

# 停止服务（保留数据库）
docker compose down

# 重算因子并写入 PostgreSQL
docker compose exec backend python /app/scripts/score_factors.py --help

# 手动刷新行业轮动
docker compose exec backend python /app/scripts/refresh_industry.py --database-url postgresql+psycopg://ai_research:ai_research@db:5432/ai_research
```

核心接口包括 `/api/market/dashboard`、`/api/market/funds`、`/api/factors/top30`、`/api/research/reports`、`/api/industry/rotation`、`/api/reviews/generate` 和 `/api/system/status`；健康检查为 `/api/health/ready`。

更多架构与面试讲解见 [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md)。
