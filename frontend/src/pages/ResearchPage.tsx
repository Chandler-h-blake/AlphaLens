import { ArrowRight, FileText, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError } from '../api/client'
import { getResearchReports } from '../api/research'
import type { ResearchReportListResponse } from '../types/research'

export function ResearchPage() {
  const [reports, setReports] = useState<ResearchReportListResponse | null>(null)
  const [keyword, setKeyword] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getResearchReports(controller.signal)
      .then(setReports)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法读取研究报告。')
      })
    return () => controller.abort()
  }, [])

  const visibleReports = useMemo(() => {
    const normalized = keyword.trim().toLocaleLowerCase()
    if (!normalized) return reports?.items ?? []
    return (reports?.items ?? []).filter((report) =>
      `${report.symbol}${report.name}${report.industry ?? ''}`.toLocaleLowerCase().includes(normalized),
    )
  }, [keyword, reports])

  return (
    <div className="page-content">
      <section className="page-heading research-heading">
        <div>
          <p className="eyebrow">LLM RESEARCH ARCHIVE</p>
          <h1>AI 研究报告</h1>
          <p>查看历史研究归档与平台生成的个股研究更新，正文保留生成时间和来源。</p>
        </div>
        <div className="page-count"><FileText size={18} /><strong>{reports?.total ?? '-'}</strong><span>份报告</span></div>
      </section>

      <section className="report-toolbar">
        <label className="search-field">
          <span className="sr-only">检索报告</span>
          <Search size={16} />
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="检索股票代码、名称或行业" />
        </label>
        <span className="source-caption">{reports?.source ?? '读取报告目录中...'}</span>
      </section>

      {error ? <div className="error-state"><FileText size={20} /><div><strong>报告加载失败</strong><span>{error}</span></div></div> : null}
      {!error && !reports ? <div className="loading-state">正在加载研究报告...</div> : null}
      {reports && !visibleReports.length ? <div className="empty-state">没有匹配的研究报告。</div> : null}

      <section className="report-grid">
        {visibleReports.map((report) => (
          <Link className="report-card" key={report.symbol} to={`/research/${report.symbol}`}>
            <div className="report-card-top"><span className="report-symbol">{report.symbol}</span><span className="industry-tag">{report.industry ?? '未分类'}</span></div>
            <h2>{report.name}</h2>
            <p>{report.title}</p>
            <div className="report-card-footer"><span>{formatDate(report.generated_at)}</span><ArrowRight size={17} /></div>
          </Link>
        ))}
      </section>
    </div>
  )
}

function formatDate(value: string | null) {
  return value ? `生成于 ${value.replace('T', ' ').slice(0, 16)}` : '生成时间未知'
}
