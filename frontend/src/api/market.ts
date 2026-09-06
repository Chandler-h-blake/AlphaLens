import { getJson, postJson } from './client'
import type { MarketSnapshotResponse } from '../types/market'

export function getMarketSnapshot(symbol: string, signal?: AbortSignal) {
  return getJson<MarketSnapshotResponse>(`/market/stocks/${symbol}`, signal)
}

export function refreshMarketSnapshot(symbol: string, signal?: AbortSignal) {
  return postJson<MarketSnapshotResponse>(`/market/stocks/${symbol}/refresh`, signal)
}
