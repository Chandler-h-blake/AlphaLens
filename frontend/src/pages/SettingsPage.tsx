import { useEffect, useState } from 'react'

import { getSystemStatus } from '../api/dashboard'
import type { SystemStatusResponse } from '../types/dashboard'

export function SettingsPage() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)

  useEffect(() => { getSystemStatus().then(setStatus) }, [])

  if (!status) return <div className="page-content"><div className="loading-state">正在读取系统状态…</div></div>

  return <div className="page-content">
    <section className="page-heading"><div><p className="eyebrow">SYSTEM SETTINGS</p><h1>设置与数据状态</h1><p>密钥只通过部署环境变量配置，网页不会读取或展示任何密钥。</p></div></section>
    <section className="metric-grid">
      <article className="metric-card"><span>数据库</span><strong>{status.database_ready ? '已连接' : '未连接'}</strong><small>PostgreSQL 运行时数据源</small></article>
      <article className="metric-card"><span>LLM</span><strong>{status.llm_configured ? '已配置' : '未配置'}</strong><small>{status.llm_configured ? '可生成研报和复盘' : 'AI 生成功能已禁用'}</small></article>
      <article className="metric-card"><span>市场 Provider</span><strong>{status.market_provider}</strong><small>公开接口，非实时行情 SLA</small></article>
    </section>
    <section className="content-panel"><h2>快照新鲜度</h2><div className="distribution">{Object.entries(status.snapshots).map(([name, time]) => <div key={name}><span>{{ dashboard: '市场概览', funds: '资金监控', factor_refresh: '技术因子' }[name] ?? name}</span><strong>{time ? time.slice(0, 16).replace('T', ' ') : '未初始化'}</strong></div>)}</div></section>
    <section className="content-panel"><h2>管理员操作</h2><p>全量因子重算、行业轮动重算和种子导入均通过容器内 CLI 执行，不开放为无认证网页操作。</p><code>docker compose exec backend python /app/scripts/import_seed_data.py --database-url $DATABASE_URL --replace</code></section>
  </div>
}
