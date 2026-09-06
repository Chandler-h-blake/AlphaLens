import type { FactorTopPoolItem } from '../types/factors'

const factorColumns = [
  { key: 'momentum_20d', label: '20 日动量', formatter: (value: number | undefined) => formatPercent(value) },
  { key: 'roe', label: 'ROE', formatter: (value: number | undefined) => formatNumber(value, 2) },
  { key: 'revenue_growth_yoy', label: '营收增长', formatter: (value: number | undefined) => formatPercent(value) },
  { key: 'net_profit_growth_yoy', label: '净利增长', formatter: (value: number | undefined) => formatPercent(value) },
]

interface FactorTableProps {
  items: FactorTopPoolItem[]
}

export function FactorTable({ items }: FactorTableProps) {
  return (
    <div className="table-scroll">
      <table className="factor-table">
        <thead>
          <tr>
            <th className="rank-column">排名</th>
            <th>股票</th>
            <th>行业</th>
            <th className="numeric">综合得分</th>
            {factorColumns.map((column) => <th className="numeric" key={column.key}>{column.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.symbol}>
              <td><span className={item.rank <= 3 ? 'rank-badge rank-badge-top' : 'rank-badge'}>{item.rank}</span></td>
              <td>
                <div className="stock-cell">
                  <strong>{item.name}</strong>
                  <span>{item.symbol}</span>
                </div>
              </td>
              <td><span className="industry-tag">{item.industry}</span></td>
              <td className="numeric score-cell">{formatNumber(item.composite_score, 3)}</td>
              {factorColumns.map((column) => (
                <td className="numeric" key={column.key}>
                  {column.formatter(item.factor_values[column.key] ?? undefined)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatNumber(value: number | undefined, digits: number) {
  return value === undefined || value === null || Number.isNaN(value) ? '-' : value.toFixed(digits)
}

function formatPercent(value: number | undefined) {
  return value === undefined || value === null || Number.isNaN(value) ? '-' : `${(value * 100).toFixed(2)}%`
}
