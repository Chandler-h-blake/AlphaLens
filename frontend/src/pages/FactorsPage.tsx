import { AlertTriangle, RefreshCw, Search, SlidersHorizontal } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { getFactorOverview, getFactorTopPool } from '../api/factors'
import { ApiError } from '../api/client'
import { FactorScoreChart } from '../components/FactorScoreChart'
import { FactorTable } from '../components/FactorTable'
import type { FactorOverviewResponse, FactorTopPoolResponse } from '../types/factors'

export function FactorsPage() {
  const [keyword, setKeyword] = useState('')
  const [industry, setIndustry] = useState('')
  const [pool, setPool] = useState<FactorTopPoolResponse | null>(null)
  const [overview, setOverview] = useState<FactorOverviewResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setIsLoading(true)
    setError(null)

    Promise.all([
      getFactorTopPool({ keyword: keyword.trim() || undefined, industry: industry || undefined, limit: 30 }, controller.signal),
      getFactorOverview(controller.signal),
    ])
      .then(([nextPool, nextOverview]) => {
        setPool(nextPool)
        setOverview(nextOverview)
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法连接数据服务。')
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false)
      })

    return () => controller.abort()
  }, [keyword, industry, refreshKey])

  const industryOptions = useMemo(() => {
    const values = pool?.items.map((item) => item.industry).filter(Boolean) ?? []
    return [...new Set(values)].sort((left, right) => left.localeCompare(right, 'zh-CN'))
  }, [pool])

  const topScore = pool?.items[0]?.composite_score
  const handleRefresh = useCallback(() => setRefreshKey((value) => value + 1), [])

  return (
    <div className="page-content">
      <section className="page-heading">
        <div>
          <p className="eyebrow">MULTI-FACTOR RESEARCH</p>
          <h1>因子选股</h1>
          <p>基于已验证的多因子快照，筛选综合得分最高的候选股票。</p>
        </div>
        <button className="icon-button" type="button" onClick={handleRefresh} title="重新读取已导入的因子数据" aria-label="重新读取已导入的因子数据">
          <RefreshCw size={18} className={isLoading ? 'spin' : undefined} />
        </button>
      </section>

      <section className="metric-grid" aria-label="因子数据摘要">
        <article className="metric-card">
          <span>当前候选池</span>
          <strong>{isLoading ? '...' : pool?.total ?? 0}</strong>
          <small>符合当前筛选条件的股票</small>
        </article>
        <article className="metric-card">
          <span>最高综合得分</span>
          <strong>{isLoading ? '...' : topScore?.toFixed(3) ?? '-'}</strong>
          <small>{pool?.items[0] ? `${pool.items[0].name} · ${pool.items[0].symbol}` : '暂无数据'}</small>
        </article>
        <article className="metric-card">
          <span>有效因子</span>
          <strong>{isLoading ? '...' : overview?.total ?? 0}</strong>
          <small>来自多截面 IC 与分组回测验证</small>
        </article>
      </section>

      <section className="content-panel">
        <div className="panel-toolbar">
          <div className="panel-title">
            <div className="panel-icon"><SlidersHorizontal size={18} /></div>
            <div>
              <h2>候选股票池</h2>
              <span>{pool?.source ?? '加载数据源中...'}</span>
            </div>
          </div>
          <div className="filters">
            <label className="search-field">
              <span className="sr-only">搜索股票</span>
              <Search size={16} />
              <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索代码或名称" />
            </label>
            <label className="select-field">
              <span className="sr-only">行业筛选</span>
              <select value={industry} onChange={(event) => setIndustry(event.target.value)}>
                <option value="">全部行业</option>
                {industryOptions.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            </label>
          </div>
        </div>

        {error ? (
          <div className="error-state" role="alert">
            <AlertTriangle size={20} />
            <div><strong>数据加载失败</strong><span>{error}</span></div>
            <button type="button" onClick={handleRefresh}>重试</button>
          </div>
        ) : isLoading && !pool ? (
          <div className="loading-state">正在读取因子结果...</div>
        ) : pool?.items.length ? (
          <FactorTable items={pool.items} />
        ) : (
          <div className="empty-state">当前筛选条件没有匹配的股票。</div>
        )}
      </section>

      <section className="chart-panel">
        <div className="panel-title">
          <div className="panel-icon panel-icon-blue"><SlidersHorizontal size={18} /></div>
          <div>
            <h2>综合得分排行</h2>
            <span>当前候选池前 8 名</span>
          </div>
        </div>
        {pool?.items.length ? <FactorScoreChart items={pool.items} /> : <div className="empty-state">暂无可绘制的数据。</div>}
      </section>
    </div>
  )
}
