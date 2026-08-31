import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import LandingView from './views/LandingView'

// Route-level code splitting: the initial bundle was a single 585KB chunk
// (Vite's own build warning) because ScorecardsView pulls in recharts
// (a sizeable charting library) directly -- every other page paid for it
// on first load even though only Scorecards uses it. Landing stays a
// static import (it's the most likely first page a visitor hits, so no
// benefit to lazy-loading it) plus each other view gets its own chunk,
// fetched on navigation instead of upfront.
const ScorecardsView = lazy(() => import('./views/ScorecardsView'))
const FitCheckerView = lazy(() => import('./views/FitCheckerView'))
const ChecklistView = lazy(() => import('./views/ChecklistView'))
const SignalsView = lazy(() => import('./views/SignalsView'))
const PricingView = lazy(() => import('./views/PricingView'))
const MethodsView = lazy(() => import('./views/MethodsView'))

function RouteFallback() {
  return <div className="py-16 text-center text-sm text-slate-500 dark:text-slate-400">Loading…</div>
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LandingView />} />
        <Route
          path="/scorecards"
          element={
            <Suspense fallback={<RouteFallback />}>
              <ScorecardsView />
            </Suspense>
          }
        />
        <Route
          path="/fit-checker"
          element={
            <Suspense fallback={<RouteFallback />}>
              <FitCheckerView />
            </Suspense>
          }
        />
        <Route
          path="/checklist"
          element={
            <Suspense fallback={<RouteFallback />}>
              <ChecklistView />
            </Suspense>
          }
        />
        <Route
          path="/signals"
          element={
            <Suspense fallback={<RouteFallback />}>
              <SignalsView />
            </Suspense>
          }
        />
        <Route
          path="/pricing"
          element={
            <Suspense fallback={<RouteFallback />}>
              <PricingView />
            </Suspense>
          }
        />
        <Route
          path="/methods"
          element={
            <Suspense fallback={<RouteFallback />}>
              <MethodsView />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  )
}
