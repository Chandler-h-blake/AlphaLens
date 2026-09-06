import { useEffect, useState } from 'react'
import { getFunds, refreshFunds } from '../api/dashboard'
import { SnapshotNotice } from '../components/SnapshotNotice'
import type { SnapshotResponse } from '../types/dashboard'

const money = (value: number | null) => value === null ? '暂无数据' : `${(value / 1e8).toFixed(2)} 亿`

export function FundsPage() {
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function load(refresh = false) {
    setBusy(true); setError('')
    try { setSnapshot(await (refresh ? refreshFunds() : getFunds())) }
    catch { setError('资金数据暂不可用，请重试。') }
    finally { setBusy(false) }
  }
  useEffect(() => { void load() }, [])
  return <div className="page-content">
    <section className="page-heading"><div><h1>资金监控</h1><p>行业主力资金与北向数据可用性。</p></div><button className="generate-button" disabled={busy} onClick={() => void load(true)}>{busy ? '刷新中…' : '手动刷新'}</button></section>
    {error && <p role="alert">{error}<button onClick={() => void load()}>重试</button></p>}
    {snapshot ? <><SnapshotNotice snapshot={snapshot} /><section className="metric-grid"><article className="metric-card"><span>{snapshot.data.northbound.label}</span><strong>{money(snapshot.data.northbound.net_inflow)}</strong><small>{snapshot.data.northbound.note}</small></article></section>
      <section className="content-panel"><h2>行业主力净流入</h2><table className="factor-table"><thead><tr><th>行业</th><th>净流入</th></tr></thead><tbody>{snapshot.data.main_flow.map((item: { name: string; net_inflow: number | null }) => <tr key={item.name}><td>{item.name}</td><td>{money(item.net_inflow)}</td></tr>)}</tbody></table></section></> : busy && <p>正在加载…</p>}
  </div>
}
