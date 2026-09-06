import { getJson, postJson } from './client'
import type { GenerationResultResponse, GenerationTaskResponse } from '../types/generation'
import type { ResearchReportDetail, ResearchReportListResponse } from '../types/research'

export function getResearchReports(signal?: AbortSignal) {
  return getJson<ResearchReportListResponse>('/research/reports', signal)
}

export function getResearchReport(symbol: string, signal?: AbortSignal) {
  return getJson<ResearchReportDetail>(`/research/reports/${symbol}`, signal)
}

export function generateResearchReport(symbol: string) {
  return postJson<GenerationTaskResponse>(`/research/reports/${symbol}/generate`)
}

export function getGenerationResult(taskId: string) {
  return getJson<GenerationResultResponse>(`/research/tasks/${taskId}/result`)
}
