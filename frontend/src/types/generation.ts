import type { ResearchReportDetail } from './research'

export type GenerationStatus = 'pending' | 'running' | 'succeeded' | 'failed'

export interface GenerationTaskResponse {
  task_id: string
  symbol: string
  status: GenerationStatus
  created_at: string
  finished_at: string | null
  error_message: string | null
}

export interface GenerationResultResponse extends GenerationTaskResponse {
  result: ResearchReportDetail | null
}
