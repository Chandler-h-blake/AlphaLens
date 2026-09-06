import { getJson, postJson } from './client'
import type { ReviewResultResponse, ReviewTaskResponse, SnapshotResponse, SystemStatusResponse } from '../types/dashboard'

export const getDashboard = (signal?: AbortSignal) => getJson<SnapshotResponse>('/market/dashboard', signal)
export const refreshDashboard = () => postJson<SnapshotResponse>('/market/dashboard')
export const getFunds = (signal?: AbortSignal) => getJson<SnapshotResponse>('/market/funds', signal)
export const refreshFunds = () => postJson<SnapshotResponse>('/market/funds')
export const getSystemStatus = (signal?: AbortSignal) => getJson<SystemStatusResponse>('/system/status', signal)
export const generateReview = () => postJson<ReviewTaskResponse>('/reviews/generate')
export const getReviewTask = (id: string) => getJson<ReviewTaskResponse>(`/reviews/tasks/${id}`)
export const getReviewResult = (id: string) => getJson<ReviewResultResponse>(`/reviews/tasks/${id}/result`)
