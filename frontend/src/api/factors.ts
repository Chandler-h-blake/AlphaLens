import { getJson } from './client'
import type { FactorOverviewResponse, FactorTopPoolResponse } from '../types/factors'

export function getFactorTopPool(
  params: { keyword?: string; industry?: string; limit?: number },
  signal?: AbortSignal,
) {
  const searchParams = new URLSearchParams()
  if (params.keyword) searchParams.set('keyword', params.keyword)
  if (params.industry) searchParams.set('industry', params.industry)
  searchParams.set('limit', String(params.limit ?? 30))

  return getJson<FactorTopPoolResponse>(`/factors/top30?${searchParams}`, signal)
}

export function getFactorOverview(signal?: AbortSignal) {
  return getJson<FactorOverviewResponse>('/factors/overview', signal)
}
