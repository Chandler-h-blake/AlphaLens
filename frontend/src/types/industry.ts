export interface IndustryRotationItem {
  industry_code: string
  industry_name: string
  last_date: string
  latest_close: number | null
  return_1m: number
  return_3m: number
  rank_1m: number
  rank_3m: number
  rotation_type: string
  generated_at: string
}

export interface IndustryRotationResponse {
  source: string
  data_date: string
  items: IndustryRotationItem[]
  total: number
}
