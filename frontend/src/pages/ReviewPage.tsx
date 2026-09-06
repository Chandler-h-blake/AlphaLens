import { AlertTriangle, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'

import { generateReview, getReviewResult, getReviewTask, getSystemStatus } from '../api/dashboard'
import type { SystemStatusResponse } from '../types/dashboard'

export function ReviewPage() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)
  const [content, setContent] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getSystemStatus().then(setStatus).catch(() => setMessage('无法读取系统配置。'))
  }, [])

  async function generate() {
    setBusy(true)
    setMessage(null)
    try {
      const task = await generateReview()
      for (let attempt = 0; attempt < 30; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        const next = await getReviewTask(task.task_id)
        if (next.status === 'succeeded') {
          const result = await getReviewResult(task.task_id)
          setContent(result.content_markdown)
          return
        }
        if (next.status === 'failed') {
          setMessage(next.error_message || '生成失败。')
          return
        }
      }
      setMessage('生成超时，请稍后查看任务状态。')
    } catch {
      setMessage('生成失败，请检查 LLM 配置。')
    } finally {
      setBusy(false)
    }
  }

  const enabled = status?.llm_configured === true
  return (
    <div className="page-content">
      <section className="page-heading">
        <div>
          <p className="eyebrow">AI DAILY REVIEW</p>
          <h1>AI 每日复盘</h1>
          <p>仅基于平台已保存的市场和资金快照生成，不编造新闻或交易建议。</p>
        </div>
        <button className="generate-button" disabled={!enabled || busy} onClick={generate}>
          <RefreshCw size={16} className={busy ? 'spin' : ''} />
          {busy ? '生成中…' : '生成复盘'}
        </button>
      </section>

      {!enabled ? (
        <div className="market-warning">
          <AlertTriangle size={17} />需配置密钥后才能生成。请在 `.env` 设置 LLM_API_KEY 后重启容器；平台不会使用模板伪造 AI 输出。
        </div>
      ) : null}
      {message ? <div className="error-state">{message}</div> : null}
      {content ? (
        <section className="markdown-content"><ReactMarkdown>{content}</ReactMarkdown></section>
      ) : (
        <div className="empty-state">生成后将在此展示本次复盘。</div>
      )}
    </div>
  )
}
