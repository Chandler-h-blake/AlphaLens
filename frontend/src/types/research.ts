export interface SourceReference {
  name: string
  type: string
  as_of: string | null
}

export interface ResearchReportListItem {
  symbol: string
  name: string
  title: string
  industry: string | null
  generated_at: string | null
}

export interface ResearchReportListResponse {
  source: string
  items: ResearchReportListItem[]
  total: number
}

export interface ResearchReportDetail extends ResearchReportListItem {
  content_markdown: string
  sources: SourceReference[]
  disclaimer: string
}
