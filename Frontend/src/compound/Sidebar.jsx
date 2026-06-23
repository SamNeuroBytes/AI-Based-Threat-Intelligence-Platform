import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ShieldAlert, ListFilter, BrainCircuit, Radar } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/indicators', label: 'Indicators', icon: ListFilter },
  { to: '/alerts', label: 'Alerts', icon: ShieldAlert },
  { to: '/ml', label: 'ML Insights', icon: BrainCircuit },
]

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col border-r border-white/5 bg-bg-panel/60 backdrop-blur-xl">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="relative">
          <Radar className="w-8 h-8 text-accent" strokeWidth={2} />
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-severity-critical pulse-dot" />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight text-white">ThreatLens</h1>
          <p className="text-[11px] text-slate-400 leading-tight">AI Threat Intel Platform</p>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-accent/15 text-accent shadow-[inset_0_0_0_1px_rgba(59,130,246,0.25)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`
            }
          >
            <Icon className="w-[18px] h-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 m-3 rounded-xl glass text-xs text-slate-400">
        <p className="font-semibold text-slate-200 mb-1">Live Data Sources</p>
        <ul className="space-y-1">
          <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-severity-low" /> URLhaus</li>
          <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-severity-low" /> ThreatFox</li>
          <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-severity-low" /> AbuseIPDB</li>
        </ul>
      </div>
    </aside>
  )
}
