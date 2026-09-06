export interface SnapshotResponse {
  data: Record<string, any>
  source: string
  as_of: string
  fetched_at: string
  freshness: 'fresh' | 'cached' | 'stale'
  warning: string | null
}

export interface SystemStatusResponse {
  app_name: string
  database_ready: boolean
  llm_configured: boolean
  market_provider: string
  snapshots: Record<string, string | null>
}

export interface ReviewTaskResponse { task_id: string; status: string; created_at: string; finished_at: string | null; error_message: string | null }
export interface ReviewResultResponse extends ReviewTaskResponse { content_markdown: string | null }
