import React from 'react'
import { HashRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Overview from './pages/Overview'
import Indicators from './pages/Indicators'
import Alerts from './pages/Alerts'
import MLInsights from './pages/MLInsights'

export default function App() {
  return (
    <HashRouter>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8 max-w-[1600px]">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/indicators" element={<Indicators />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/ml" element={<MLInsights />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}
