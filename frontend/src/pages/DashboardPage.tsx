import { RefreshCw } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { getDashboard, refreshDashboard } from '../api/dashboard'
import type { SnapshotResponse } from '../types/dashboard'

export function DashboardPage() {
  const [snapshot, setSnapshot] = useState<SnapshotResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async (refresh = false) => {
    try {
      setError(null)
      setSnapshot(refresh ? await refreshDashboard() : await getDashboard())
    } catch {
      setError('市场快照暂不可用。')
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])
  const data = snapshot?.data

  return (
    <div className="page-content">
      <section className="page-heading">
        <div>
          <p className="eyebrow">MARKET OVERVIEW</p>
          <h1>市场概览</h1>
          <p>指数、行业、涨跌分布和成交额活跃股票的统一快照。</p>
        </div>
        <button
          className="generate-button"
          onClick={() => { setBusy(true); void load(true) }}
          disabled={busy}
        >
          <RefreshCw size={16} className={busy ? 'spin' : ''} /> 手动刷新
        </button>
      </section>

      {error ? <div className="error-state">{error}</div> : null}
      {snapshot?.warning ? <div className="market-warning">{snapshot.warning}</div> : null}
      {data ? (
        <>
          <section className="metric-grid">
            {data.indexes.map((item: any) => (
              <article className="metric-card" key={item.name}>
                <span>{item.name}</span>
                <strong>{item.value.toLocaleString()}</strong>
                <small className={item.change_percent >= 0 ? 'market-up' : 'market-down'}>
                  {item.change_percent >= 0 ? '+' : ''}{item.change_percent.toFixed(2)}%
                </small>
              </article>
            ))}
          </section>

          <section className="split-grid">
            <article className="content-panel">
              <h2>行业热力图</h2>
              <div className="heatmap">
                {data.industries.map((item: any) => (
                  <span className={item.change_percent >= 0 ? 'heat-up' : 'heat-down'} key={item.name}>
                    {item.name}<b>{item.change_percent >= 0 ? '+' : ''}{item.change_percent.toFixed(2)}%</b>
                  </span>
                ))}
              </div>
            </article>
            <article className="content-panel">
              <h2>市场涨跌分布</h2>
              <div className="distribution">
                {[
                  ['上涨', data.distribution.up],
                  ['下跌', data.distribution.down],
                  ['平盘', data.distribution.flat],
                  ['涨停', data.distribution.limit_up],
                  ['跌停', data.distribution.limit_down],
                ].map(([label, value]) => (
                  <div key={String(label)}><span>{label}</span><strong>{Number(value).toLocaleString()}</strong></div>
                ))}
              </div>
            </article>
          </section>

          <section className="content-panel">
            <h2>成交额 TOP20</h2>
            <TurnoverTable items={data.top_turnover} />
          </section>
          <p className="source-caption">
            来源：{snapshot.source} · 数据时间 {snapshot.as_of.slice(0, 16).replace('T', ' ')}
          </p>
        </>
      ) : <div className="loading-state">正在加载市场快照…</div>}
    </div>
  )
}

function TurnoverTable({ items }: { items: any[] }) {
  return (
    <div className="table-scroll">
      <table className="factor-table">
        <thead><tr><th>代码</th><th>名称</th><th>涨跌幅</th><th>成交额</th></tr></thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.symbol}>
              <td>{item.symbol}</td><td>{item.name}</td>
              <td className={item.change_percent >= 0 ? 'market-up' : 'market-down'}>
                {item.change_percent >= 0 ? '+' : ''}{item.change_percent.toFixed(2)}%
              </td>
              <td>{(item.amount / 1e8).toFixed(1)} 亿</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
