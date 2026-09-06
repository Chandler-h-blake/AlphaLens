export interface FactorTopPoolItem {
  symbol: string
  name: string
  industry: string
  rank: number
  composite_score: number
  factor_values: Record<string, number | null>
}

export interface FactorTopPoolResponse {
  source: string
  data_date: string | null
  refreshed_at: string | null
  calculation_scope: string
  items: FactorTopPoolItem[]
  total: number
}

export interface FactorRefreshTaskResponse {
  task_id: string
  status: 'pending' | 'running' | 'succeeded' | 'failed'
  created_at: string
  finished_at: string | null
  error_message: string | null
}

export interface FactorOverviewItem {
  factor: string
  name: string
  category: string
  direction: number
  direction_text: string
  weight: number
}

export interface FactorOverviewResponse {
  source: string
  items: FactorOverviewItem[]
  total: number
}
