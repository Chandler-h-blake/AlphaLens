import { AlertTriangle, ExternalLink, RefreshCw, Radio, TrendingDown, TrendingUp } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { ApiError } from '../api/client'
import { getFactorTopPool } from '../api/factors'
import { getMarketSnapshot, refreshMarketSnapshot } from '../api/market'
import type { FactorTopPoolItem } from '../types/factors'
import type { MarketSnapshotResponse } from '../types/market'

export function MarketPage() {
  const [candidates, setCandidates] = useState<FactorTopPoolItem[]>([])
  const [symbol, setSymbol] = useState('')
  const [snapshot, setSnapshot] = useState<MarketSnapshotResponse | null>(null)
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(true)
  const [isLoadingSnapshot, setIsLoadingSnapshot] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getFactorTopPool({ limit: 30 }, controller.signal)
      .then((pool) => {
        setCandidates(pool.items)
        setSymbol((current) => current || pool.items[0]?.symbol || '')
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法读取研究股票池。')
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingCandidates(false)
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!symbol) return
    const controller = new AbortController()
    setIsLoadingSnapshot(true)
    setError(null)
    getMarketSnapshot(symbol, controller.signal)
      .then(setSnapshot)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        if (requestError instanceof ApiError && requestError.status === 404) {
          setSnapshot(null)
          return
        }
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法读取在线行情快照。')
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingSnapshot(false)
      })
    return () => controller.abort()
  }, [symbol])

  const handleRefresh = useCallback(async () => {
    if (!symbol) return
    setIsRefreshing(true)
    setError(null)
    try {
      setSnapshot(await refreshMarketSnapshot(symbol))
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : '在线数据更新失败。')
    } finally {
      setIsRefreshing(false)
    }
  }, [symbol])

  const isPositive = (snapshot?.change_percent ?? 0) >= 0
  const selected = candidates.find((item) => item.symbol === symbol)

  return (
    <div className="page-content">
      <section className="page-heading">
        <div>
          <p className="eyebrow">LIVE MARKET MONITOR</p>
          <h1>在线市场</h1>
          <p>在线行情快照、资金流与公司公告。</p>
        </div>
        <button className="generate-button" type="button" onClick={handleRefresh} disabled={!symbol || isRefreshing}>
          <RefreshCw size={16} className={isRefreshing ? 'spin' : undefined} /> {isRefreshing ? '刷新中...' : '刷新在线数据'}
        </button>
      </section>

      <section className="market-selector" aria-label="研究股票选择">
        <label className="select-field">
          <span className="sr-only">选择研究股票</span>
          <select value={symbol} onChange={(event) => setSymbol(event.target.value)} disabled={isLoadingCandidates}>
            {candidates.map((item) => <option key={item.symbol} value={item.symbol}>{item.name} · {item.symbol}</option>)}
          </select>
        </label>
        {selected ? <span className="industry-tag">{selected.industry}</span> : null}
        {snapshot ? <span className={`market-freshness market-freshness-${snapshot.freshness}`}><Radio size={13} /> {freshnessLabel(snapshot.freshness)}</span> : null}
      </section>

      {error ? <div className="error-state" role="alert"><AlertTriangle size={20} /><div><strong>在线数据暂不可用</strong><span>{error}</span></div><button type="button" onClick={handleRefresh}>重试</button></div> : null}
      {!error && (isLoadingCandidates || isLoadingSnapshot) ? <div className="loading-state">正在读取市场快照...</div> : null}
      {!error && !isLoadingCandidates && !isLoadingSnapshot && !snapshot ? <div className="empty-state">尚未保存在线快照。</div> : null}

      {snapshot ? <>
        {snapshot.warning ? <div className="market-warning"><AlertTriangle size={17} /><span>{snapshot.warning}</span></div> : null}
        <section className="metric-grid market-metric-grid">
          <article className="metric-card"><span>最新价</span><strong>{snapshot.latest_price.toFixed(2)}</strong><small className={isPositive ? 'market-up' : 'market-down'}>{formatSigned(snapshot.change_amount)} / {formatPercent(snapshot.change_percent)}</small></article>
          <article className="metric-card"><span>主力净流入</span><strong className={isInflow(snapshot.main_net_inflow) ? 'market-up' : 'market-down'}>{formatBillions(snapshot.main_net_inflow)}</strong><small>当日资金流向</small></article>
          <article className="metric-card"><span>成交额</span><strong>{formatBillions(snapshot.amount)}</strong><small>{formatDate(snapshot.fetched_at)} 更新</small></article>
        </section>

        <section className="content-panel">
          <div className="panel-toolbar"><div className="panel-title"><div className="panel-icon panel-icon-blue"><TrendingUp size={18} /></div><div><h2>日内行情</h2><span>{snapshot.source}</span></div></div><span className="source-caption">行情时间 {formatDate(snapshot.as_of)}</span></div>
          <div className="market-detail-grid">
            <MarketField label="今开" value={formatPrice(snapshot.open_price)} />
            <MarketField label="最高" value={formatPrice(snapshot.high_price)} />
            <MarketField label="最低" value={formatPrice(snapshot.low_price)} />
            <MarketField label="成交量" value={formatVolume(snapshot.volume)} />
            <MarketField label="总市值" value={formatBillions(snapshot.total_market_cap)} />
            <MarketField label="股票代码" value={snapshot.symbol} />
          </div>
        </section>

        <section className="content-panel market-announcements">
          <div className="panel-toolbar"><div className="panel-title"><div className="panel-icon"><TrendingDown size={18} /></div><div><h2>公告与资讯</h2><span>近 90 天公开披露与个股资讯</span></div></div><span className="source-caption">{snapshot.announcements.length} 条</span></div>
          {snapshot.announcements.length ? <div className="table-scroll"><table className="factor-table"><thead><tr><th>日期</th><th>标题</th><th>类型</th><th>来源</th><th aria-label="查看详情" /></tr></thead><tbody>{snapshot.announcements.map((item) => <tr key={item.article_id}><td>{item.published_at?.slice(0, 10) ?? '-'}</td><td className="announcement-title">{item.title}</td><td><span className="industry-tag">{item.category ?? '个股资讯'}</span></td><td>{item.source}</td><td>{item.url ? <a className="external-link" href={item.url} target="_blank" rel="noreferrer" title="打开详情"><ExternalLink size={16} /></a> : null}</td></tr>)}</tbody></table></div> : <div className="empty-state">当前时间范围没有可展示的信息。</div>}
        </section>
      </> : null}
    </div>
  )
}

function MarketField({ label, value }: { label: string; value: string }) {
  return <div className="market-detail"><span>{label}</span><strong>{value}</strong></div>
}

function freshnessLabel(value: MarketSnapshotResponse['freshness']) {
  return value === 'fresh' ? '刚刚更新' : value === 'stale' ? '历史快照' : '已保存快照'
}

function formatPrice(value: number | null) { return value === null ? '-' : value.toFixed(2) }
function formatPercent(value: number | null) { return value === null ? '-' : `${value >= 0 ? '+' : ''}${value.toFixed(2)}%` }
function formatSigned(value: number | null) { return value === null ? '-' : `${value >= 0 ? '+' : ''}${value.toFixed(2)}` }
function formatBillions(value: number | null) { return value === null ? '-' : `${(value / 100_000_000).toFixed(2)} 亿` }
function formatVolume(value: number | null) { return value === null ? '-' : `${(value / 10_000).toFixed(2)} 万手` }
function formatDate(value: string) { return value.replace('T', ' ').slice(0, 16) }
function isInflow(value: number | null) { return (value ?? 0) >= 0 }
