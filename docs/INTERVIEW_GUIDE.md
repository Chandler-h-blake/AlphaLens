# AlphaLens 面试讲解提纲

## 一句话介绍

我把一个由 CSV、Streamlit 和分散脚本组成的 A 股投研原型，重构成了 React + FastAPI + PostgreSQL 的可部署应用，并通过快照、降级和异步任务处理公开数据与 LLM 的不稳定性。

## 架构取舍

```text
React 页面 → FastAPI REST API → Service/Repository → PostgreSQL
                                      ├─ 公开市场 Provider
                                      └─ OpenAI-compatible LLM
```

- 用 PostgreSQL 替换运行时 CSV：数据查询、报告和任务状态有统一来源。
- 用种子数据保证离线演示：没有网络或上游失败时仍能完整讲解业务流程。
- 用持久化快照处理公共 API：刷新失败不会让页面报废，前端会显示来源和新鲜度。
- 不使用 LangChain：当前模型调用只需要统一 Provider 和结构化 Prompt，直接 HTTP 客户端更容易维护与测试。

## 可讲的业务闭环

1. 多因子结果筛出 TOP30。
2. 页面支持筛选、因子对比和行业轮动判断。
3. 用户可查看单股市场快照、公告和资金数据。
4. 配置模型后，平台用已有结构化数据异步生成研究报告或每日复盘，并可轮询任务状态。

## 诚实的局限性

- 不包含实盘交易、用户权限和逐笔行情。
- LLM 输出受模型和输入快照约束，页面明确说明不构成投资建议。
- 高并发环境需要把进程内后台任务迁移到 Redis/Celery 等队列。
