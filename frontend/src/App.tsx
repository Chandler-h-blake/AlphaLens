import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/AppLayout'

const FactorsPage = lazy(() => import('./pages/FactorsPage').then((module) => ({ default: module.FactorsPage })))
const IndustryPage = lazy(() => import('./pages/IndustryPage').then((module) => ({ default: module.IndustryPage })))
const MarketPage = lazy(() => import('./pages/MarketPage').then((module) => ({ default: module.MarketPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const FundsPage = lazy(() => import('./pages/FundsPage').then((module) => ({ default: module.FundsPage })))
const ComparePage = lazy(() => import('./pages/ComparePage').then((module) => ({ default: module.ComparePage })))
const ReviewPage = lazy(() => import('./pages/ReviewPage').then((module) => ({ default: module.ReviewPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then((module) => ({ default: module.SettingsPage })))
const ResearchDetailPage = lazy(() => import('./pages/ResearchDetailPage').then((module) => ({ default: module.ResearchDetailPage })))
const ResearchPage = lazy(() => import('./pages/ResearchPage').then((module) => ({ default: module.ResearchPage })))

export default function App() {
  return (
    <Suspense fallback={<div className="loading-state">正在加载工作台...</div>}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/factors" element={<FactorsPage />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/research/:symbol" element={<ResearchDetailPage />} />
          <Route path="/industry" element={<IndustryPage />} />
          <Route path="/market" element={<MarketPage />} />
          <Route path="/funds" element={<FundsPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
