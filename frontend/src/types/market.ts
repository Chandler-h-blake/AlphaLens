export interface MarketAnnouncementItem {
  article_id: string
  title: string
  category: string | null
  published_at: string | null
  url: string | null
  source: string
}

export interface MarketSnapshotResponse {
  symbol: string
  name: string
  latest_price: number
  change_amount: number | null
  change_percent: number | null
  open_price: number | null
  high_price: number | null
  low_price: number | null
  volume: number | null
  amount: number | null
  total_market_cap: number | null
  main_net_inflow: number | null
  source: string
  as_of: string
  fetched_at: string
  freshness: 'fresh' | 'cached' | 'stale'
  warning: string | null
  announcements: MarketAnnouncementItem[]
}
