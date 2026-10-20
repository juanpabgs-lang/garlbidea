import { Navigate, Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { AskPage } from './pages/Ask'
import { BriefPage } from './pages/Brief'
import { FreightPage } from './pages/Freight'
import { MarketsPage } from './pages/Markets'
import { PolicyPage } from './pages/Policy'
import { PricesPage } from './pages/Prices'
import { SourcesPage } from './pages/Sources'

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<BriefPage />} />
        <Route path="/ask" element={<AskPage />} />
        <Route path="/markets" element={<MarketsPage />} />
        <Route path="/markets/:code" element={<MarketsPage />} />
        <Route path="/prices" element={<PricesPage />} />
        <Route path="/freight" element={<FreightPage />} />
        <Route path="/policy" element={<PolicyPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Shell>
  )
}
