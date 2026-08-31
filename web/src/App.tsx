import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import LandingView from './views/LandingView'
import ScorecardsView from './views/ScorecardsView'
import FitCheckerView from './views/FitCheckerView'
import ChecklistView from './views/ChecklistView'
import SignalsView from './views/SignalsView'
import PricingView from './views/PricingView'
import MethodsView from './views/MethodsView'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LandingView />} />
        <Route path="/scorecards" element={<ScorecardsView />} />
        <Route path="/fit-checker" element={<FitCheckerView />} />
        <Route path="/checklist" element={<ChecklistView />} />
        <Route path="/signals" element={<SignalsView />} />
        <Route path="/pricing" element={<PricingView />} />
        <Route path="/methods" element={<MethodsView />} />
      </Route>
    </Routes>
  )
}
