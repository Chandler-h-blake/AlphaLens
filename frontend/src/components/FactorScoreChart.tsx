import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { FactorTopPoolItem } from '../types/factors'

interface FactorScoreChartProps {
  items: FactorTopPoolItem[]
}

export function FactorScoreChart({ items }: FactorScoreChartProps) {
  const chartData = items.slice(0, 8).map((item) => ({
    name: item.name,
    score: Number(item.composite_score.toFixed(3)),
  }))

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={270}>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <XAxis
            axisLine={false}
            dataKey="name"
            tick={{ fill: '#607082', fontSize: 12 }}
            tickLine={false}
          />
          <YAxis
            axisLine={false}
            tick={{ fill: '#607082', fontSize: 12 }}
            tickLine={false}
            width={42}
          />
          <Tooltip
            cursor={{ fill: '#eef5f4' }}
            contentStyle={{ border: '1px solid #d7e2e1', borderRadius: 6, boxShadow: '0 8px 20px rgba(22, 42, 56, 0.1)' }}
            formatter={(value) => [Number(value).toFixed(3), '综合得分']}
          />
          <Bar dataKey="score" radius={[4, 4, 0, 0]} maxBarSize={38}>
            {chartData.map((entry, index) => (
              <Cell key={entry.name} fill={index === 0 ? '#147a6d' : '#77b5ad'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
