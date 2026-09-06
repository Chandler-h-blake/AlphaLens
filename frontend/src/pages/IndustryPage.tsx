import { BarChart3, CalendarDays, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ApiError } from '../api/client'
import { postJson } from '../api/client'
import { getIndustryRotation } from '../api/industry'
import type { IndustryRotationResponse } from '../types/industry'

export function IndustryPage() {
  const [rotation, setRotation] = useState<IndustryRotationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [warning, setWarning] = useState('')
  async function refresh() {
    setBusy(true)
    try { const r = await postJson<IndustryRotationResponse & {warning?: string}>('/industry/rotation/refresh'); setRotation(r); setWarning(r.warning || '') }
    catch { setWarning('刷新失败，保留旧数据。') }
    finally { setBusy(false) }
  }

  useEffect(() => {
    const controller = new AbortController()
    getIndustryRotation(controller.signal)
      .then(setRotation)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法读取行业轮动数据。')
      })
    return () => controller.abort()
  }, [])

  const chartData = rotation?.items.slice(0, 10).map((item) => ({ name: item.industry_name, return_1m: Number((item.return_1m * 100).toFixed(2)) })) ?? []

  return (
    <div className="page-content">
      <section className="page-heading research-heading">
        <div>
          <p className="eyebrow">INDUSTRY MOMENTUM</p>
          <h1>行业轮动</h1>
          <p>基于申万一级行业指数的月度、三月收益与排名，观察行业强弱变化。</p>
        </div>
        <div className="page-count"><CalendarDays size={18} /><strong>{rotation?.data_date ?? '-'}</strong><span>数据日期</span><button disabled={busy} onClick={() => void refresh()}>{busy ? '刷新中…' : '手动刷新'}</button></div>
      </section>

      {warning && <p role="status" className="market-warning">{warning}</p>}
      {error ? <div className="error-state"><TrendingUp size={20} /><div><strong>行业数据加载失败</strong><span>{error}</span></div></div> : null}
      {!error && !rotation ? <div className="loading-state">正在读取行业轮动结果...</div> : null}
      {rotation ? <>
        <section className="industry-stat-grid">
          <article className="metric-card"><span>月度第一行业</span><strong>{rotation.items[0]?.industry_name ?? '-'}</strong><small>{formatPercent(rotation.items[0]?.return_1m)} 月度收益</small></article>
          <article className="metric-card"><span>三月第一行业</span><strong>{[...rotation.items].sort((a, b) => a.rank_3m - b.rank_3m)[0]?.industry_name ?? '-'}</strong><small>{formatPercent([...rotation.items].sort((a, b) => a.rank_3m - b.rank_3m)[0]?.return_3m)} 三月收益</small></article>
          <article className="metric-card"><span>持续强势行业</span><strong>{rotation.items.filter((item) => item.rotation_type === '持续强势').length}</strong><small>共 {rotation.total} 个行业样本</small></article>
        </section>
        <section className="chart-panel">
          <div className="panel-title"><div className="panel-icon panel-icon-blue"><BarChart3 size={18} /></div><div><h2>月度收益排行</h2><span>{rotation.source}</span></div></div>
          <div className="chart-wrap"><ResponsiveContainer width="100%" height={300}><BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 28, left: 14, bottom: 0 }}><XAxis type="number" axisLine={false} tickLine={false} tickFormatter={(value) => `${value}%`} /><YAxis type="category" dataKey="name" axisLine={false} tickLine={false} width={72} tick={{ fontSize: 12, fill: '#607082' }} /><Tooltip formatter={(value) => [`${Number(value).toFixed(2)}%`, '月度收益']} cursor={{ fill: '#eef5f4' }} /><Bar dataKey="return_1m" radius={[0, 4, 4, 0]}>{chartData.map((item, index) => <Cell key={item.name} fill={index < 3 ? '#147a6d' : '#77b5ad'} />)}</Bar></BarChart></ResponsiveContainer></div>
        </section>
        <section className="content-panel industry-table-panel"><div className="panel-toolbar"><div className="panel-title"><div className="panel-icon"><TrendingUp size={18} /></div><div><h2>行业排名明细</h2><span>{rotation.total} 个行业</span></div></div></div><div className="table-scroll"><table className="factor-table"><thead><tr><th>月度排名</th><th>行业</th><th className="numeric">月度收益</th><th className="numeric">三月排名</th><th className="numeric">三月收益</th><th>轮动状态</th></tr></thead><tbody>{rotation.items.map((item) => <tr key={item.industry_code}><td><span className={item.rank_1m <= 3 ? 'rank-badge rank-badge-top' : 'rank-badge'}>{item.rank_1m}</span></td><td><div className="stock-cell"><strong>{item.industry_name}</strong><span>{item.industry_code}</span></div></td><td className="numeric score-cell">{formatPercent(item.return_1m)}</td><td className="numeric">{item.rank_3m}</td><td className="numeric">{formatPercent(item.return_3m)}</td><td><span className="industry-tag">{item.rotation_type}</span></td></tr>)}</tbody></table></div></section>
      </> : null}
    </div>
  )
}

function formatPercent(value: number | undefined) {
  return value === undefined ? '-' : `${(value * 100).toFixed(2)}%`
}
