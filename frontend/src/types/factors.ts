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
  items: FactorTopPoolItem[]
  total: number
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
