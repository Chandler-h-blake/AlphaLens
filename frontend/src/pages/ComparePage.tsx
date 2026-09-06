import { useEffect, useState } from 'react'
import { Bar, BarChart, XAxis, YAxis, Tooltip, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, Legend } from 'recharts'
import { getFactorTopPool } from '../api/factors'
import type { FactorTopPoolItem } from '../types/factors'

const groups: Record<string, string[]> = {成长:['revenue_growth_yoy','net_profit_growth_yoy'],动量:['momentum_20d','turnover_change'],质量:['roe','gross_margin'],价值:['pe_percentile','pb_percentile'],波动:['volatility_60d']}
const colors = ['#147a6d','#447bd1','#aa6a17','#8d52c1','#c54464']
const fields = [['momentum_20d','20日动量'],['roe','ROE'],['gross_margin','毛利率'],['revenue_growth_yoy','营收增长'],['net_profit_growth_yoy','净利润增长'],['pe_percentile','PE分位'],['pb_percentile','PB分位'],['volatility_60d','60日波动']]

export function ComparePage() {
  const [items,setItems] = useState<FactorTopPoolItem[]>([])
  const [selected,setSelected] = useState<string[]>([])
  const [error,setError] = useState('')
  useEffect(() => { getFactorTopPool({limit:30}).then(r => {setItems(r.items);setSelected(r.items.slice(0,2).map(i=>i.symbol))}).catch(()=>setError('股票池加载失败，请刷新页面重试。')) }, [])
  const chosen = items.filter(i => selected.includes(i.symbol))
  const toggle = (symbol:string) => setSelected(current => current.includes(symbol) ? current.filter(s=>s!==symbol) : current.length<5 ? [...current,symbol] : current)
  const radar = Object.entries(groups).map(([category,keys]) => ({category,...Object.fromEntries(chosen.map(stock => [stock.name,keys.reduce((sum,key)=>sum+(stock.factor_values[key+'_weighted_score']??0),0)]))}))
  const hasContributions = chosen.every(stock => Object.values(groups).flat().every(key => stock.factor_values[key+'_weighted_score'] != null))
  return <div className="page-content"><section className="page-heading"><div><h1>个股对比</h1><p>选择2–5只股票，比较历史因子得分；不同指标沿用各自单位。</p></div></section>
    {error && <p role="alert">{error}</p>}
    <section className="content-panel"><h2>选择股票（{selected.length}/5）</h2><div className="choice-grid">{items.map(item=><label key={item.symbol}><input type="checkbox" checked={selected.includes(item.symbol)} disabled={selected.length>=5&&!selected.includes(item.symbol)} onChange={()=>toggle(item.symbol)}/>{item.name} · {item.symbol}</label>)}</div></section>
    {chosen.length>=2 ? <><section className="split-grid"><div className="content-panel"><h2>综合得分</h2><ResponsiveContainer width="100%" height={300}><BarChart data={chosen}><XAxis dataKey="name"/><YAxis/><Tooltip/><Bar dataKey="composite_score" fill="#147a6d"/></BarChart></ResponsiveContainer></div>
      <div className="content-panel"><h2>五维加权贡献</h2>{hasContributions ? <ResponsiveContainer width="100%" height={300}><RadarChart data={radar}><PolarGrid/><PolarAngleAxis dataKey="category"/><Tooltip/><Legend/>{chosen.map((s,i)=><Radar key={s.symbol} name={s.name} dataKey={s.name} stroke={colors[i]} fill={colors[i]} fillOpacity={.1}/>)}</RadarChart></ResponsiveContainer> : <p>当前快照未包含贡献明细，重新导入完整因子表后可展示。</p>}</div></section>
      <section className="content-panel"><div className="table-scroll"><table className="factor-table"><thead><tr><th>指标</th>{chosen.map(i=><th key={i.symbol}>{i.name}</th>)}</tr></thead><tbody><tr><td>得分 / 排名</td>{chosen.map(i=><td key={i.symbol}>{i.composite_score.toFixed(3)} / #{i.rank}</td>)}</tr>{fields.map(([key,label])=><tr key={key}><td>{label}</td>{chosen.map(i=><td key={i.symbol}>{i.factor_values[key]?.toFixed(3)??'-'}</td>)}</tr>)}</tbody></table></div></section></> : <p>请至少选择两只股票。</p>}
  </div>
}
