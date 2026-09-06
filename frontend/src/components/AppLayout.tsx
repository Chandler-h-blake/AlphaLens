import { BarChart3, Database, FileText, LayoutDashboard, Sparkles, TrendingUp, WalletCards, Scale, Settings, ClipboardCheck } from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

const navItems = [
  { label: '市场概览', to: '/dashboard', icon: LayoutDashboard },
  { label: '因子选股', to: '/factors', icon: BarChart3 },
  { label: 'AI 研究报告', to: '/research', icon: FileText },
  { label: '资金监控', to: '/funds', icon: WalletCards },
  { label: '个股对比', to: '/compare', icon: Scale },
  { label: 'AI 每日复盘', to: '/review', icon: ClipboardCheck },
  { label: '行业轮动', to: '/industry', icon: TrendingUp },
  { label: '设置', to: '/settings', icon: Settings },
]

const routeNames: Record<string, string> = {
  '/dashboard': '市场概览',
  '/factors': '因子选股',
  '/research': 'AI 研究报告',
  '/industry': '行业轮动',
  '/market': '在线市场',
  '/funds': '资金监控',
  '/compare': '个股对比',
  '/review': 'AI 每日复盘',
  '/settings': '设置',
}

export function AppLayout() {
  const location = useLocation()
  const currentPage = location.pathname.startsWith('/research/')
    ? '报告详情'
    : routeNames[location.pathname] ?? '研究工作台'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <Sparkles size={18} strokeWidth={2.4} />
          </div>
          <div>
            <p className="brand-name">Alpha Lens</p>
            <p className="brand-subtitle">AI Research Platform</p>
          </div>
        </div>

        <nav className="primary-nav" aria-label="主要导航">
          <p className="nav-label">研究工作台</p>
          {navItems.map(({ label, to, icon: Icon }) => (
            <NavLink key={to} className="nav-item" to={to}>
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-source">
          <Database size={17} />
          <div>
            <span>数据来源</span>
            <strong>研究快照 · PostgreSQL</strong>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-path">
            <LayoutDashboard size={16} />
            <span>研究工作台</span>
            <span className="path-divider">/</span>
            <strong>{currentPage}</strong>
          </div>
          <span className="environment-status"><i /> 个人研究工作台</span>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
