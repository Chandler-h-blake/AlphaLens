import type { SnapshotResponse } from '../types/dashboard'

export function SnapshotNotice({ snapshot }: { snapshot: SnapshotResponse }) {
  return <div aria-live="polite">
    {snapshot.warning && <p className="market-warning">{snapshot.warning}</p>}
    <p>来源：{snapshot.source} · 数据时间：{snapshot.as_of.replace('T', ' ')} · 保存时间：{snapshot.fetched_at.replace('T', ' ')}</p>
  </div>
}
