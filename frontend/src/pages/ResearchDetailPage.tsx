import { ArrowLeft, BookOpenText, CalendarDays, Database, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { getSystemStatus } from '../api/dashboard'
import { generateResearchReport, getGenerationResult, getResearchReport } from '../api/research'
import type { ResearchReportDetail } from '../types/research'

export function ResearchDetailPage() {
  const { symbol = '' } = useParams()
  const [report, setReport] = useState<ResearchReportDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [llmConfigured, setLlmConfigured] = useState(false)
  useEffect(() => { getSystemStatus().then(s => setLlmConfigured(s.llm_configured)).catch(() => setLlmConfigured(false)) }, [])
  const [generationMessage, setGenerationMessage] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getResearchReport(symbol, controller.signal)
      .then(setReport)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof ApiError ? requestError.message : '暂时无法读取研究报告。')
      })
    return () => controller.abort()
  }, [symbol])

  if (error) return <div className="page-content"><div className="error-state"><BookOpenText size={20} /><div><strong>报告加载失败</strong><span>{error}</span></div></div></div>
  if (!report) return <div className="page-content"><div className="loading-state">正在读取报告正文...</div></div>

  const isGeneratedReport = report.sources.some((source) => source.type === 'llm_generated')

  async function handleGenerate() {
    setIsGenerating(true)
    setGenerationMessage('正在创建生成任务...')
    try {
      const task = await generateResearchReport(symbol)
      for (let attempt = 0; attempt < 45; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 1000))
        const result = await getGenerationResult(task.task_id)
        if (result.status === 'succeeded' && result.result) {
          setReport(result.result)
          setGenerationMessage('已加载最新生成结果。')
          return
        }
        if (result.status === 'failed') throw new Error(result.error_message ?? '生成任务失败。')
        setGenerationMessage('模型正在整理研究内容...')
      }
      setGenerationMessage('任务仍在运行，可稍后刷新本页查看结果。')
    } catch (requestError) {
      setGenerationMessage(requestError instanceof ApiError || requestError instanceof Error ? requestError.message : '暂时无法创建生成任务。')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="page-content report-detail-page">
      <Link className="back-link" to="/research"><ArrowLeft size={16} /> 返回报告列表</Link>
      <section className="report-detail-header">
        <div>
          <p className="eyebrow">{report.symbol} · {report.industry ?? '未分类'}</p>
          <h1>{report.title}</h1>
          <div className="report-meta"><span><CalendarDays size={15} /> {formatDate(report.generated_at)}</span><span><Database size={15} /> {isGeneratedReport ? 'AI 生成更新' : '历史研究归档'}</span></div>
        </div>
        <div className="generation-control"><button className="generate-button" type="button" onClick={handleGenerate} disabled={isGenerating || !llmConfigured}><Sparkles size={16} /> {isGenerating ? '生成中...' : '生成更新'}</button>{!llmConfigured ? <span>需配置密钥后才能生成</span> : null}{generationMessage ? <span>{generationMessage}</span> : null}</div>
      </section>
      <section className="report-reading-layout">
        <article className="markdown-content"><ReactMarkdown>{report.content_markdown}</ReactMarkdown></article>
        <aside className="source-panel">
          <h2>来源记录</h2>
          {report.sources.map((source) => <div className="source-item" key={source.name}><strong>{source.name}</strong><span>{source.type}</span></div>)}
          <p>{report.disclaimer}</p>
        </aside>
      </section>
    </div>
  )
}

function formatDate(value: string | null) {
  return value ? value.replace('T', ' ').slice(0, 16) : '生成时间未知'
}
