import { getJson } from './client'
import type { IndustryRotationResponse } from '../types/industry'

export function getIndustryRotation(signal?: AbortSignal) {
  return getJson<IndustryRotationResponse>('/industry/rotation', signal)
}
