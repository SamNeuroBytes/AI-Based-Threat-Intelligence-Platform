import React, { useEffect, useState } from 'react'
import { Search, Filter } from 'lucide-react'
import { getIndicators } from '../api'
import { SeverityBadge, TypeBadge, MLBadge, Panel, Spinner } from '../components/UI'

export default function Indicators() {
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ severity: '', ioc_type: '', source: '', ml_label: '', search: '' })

  const load = () => {
    setLoading(true)
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
    params.limit = 100
    getIndicators(params).then(setIndicators).finally(() => setLoading(false))
  }

  useEffect(() => {
    const timeout = setTimeout(load, 300)
    return () => clearTimeout(timeout)
  }, [filters])

  const update = (key) => (e) => setFilters((f) => ({ ...f, [key]: e.target.value }))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Threat Indicators</h2>
        <p className="text-slate-400 text-sm mt-1">Browse and filter all collected indicators of compromise (IOCs)</p>
      </div>

      <Panel>
        <div className="flex flex-wrap gap-3 items-center mb-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              value={filters.search}
              onChange={update('search')}
              placeholder="Search value (IP, domain, URL, hash)..."
              className="w-full bg-bg-card border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-accent/50"
            />
          </div>
          <FilterSelect value={filters.severity} onChange={update('severity')} options={['', 'critical', 'high', 'medium', 'low']} placeholder="All Severities" />
          <FilterSelect value={filters.ioc_type} onChange={update('ioc_type')} options={['', 'ip', 'domain', 'url', 'hash']} placeholder="All Types" />
          <FilterSelect value={filters.source} onChange={update('source')} options={['', 'URLhaus', 'ThreatFox', 'AbuseIPDB']} placeholder="All Sources" />
          <FilterSelect value={filters.ml_label} onChange={update('ml_label')} options={['', 'anomalous', 'normal']} placeholder="ML Label" />
        </div>

        {loading ? <Spinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-white/5 text-xs uppercase tracking-wide">
                  <th className="py-2.5 pr-4 font-medium">Type</th>
                  <th className="py-2.5 pr-4 font-medium">Value</th>
                  <th className="py-2.5 pr-4 font-medium">Source</th>
                  <th className="py-2.5 pr-4 font-medium">Threat</th>
                  <th className="py-2.5 pr-4 font-medium">Confidence</th>
                  <th className="py-2.5 pr-4 font-medium">Severity</th>
                  <th className="py-2.5 pr-4 font-medium">ML</th>
                  <th className="py-2.5 pr-4 font-medium">Last Seen</th>
                </tr>
              </thead>
              <tbody>
                {indicators.map((ind) => (
                  <tr key={ind.id} className="border-b border-white/5 hover:bg-white/[0.03] transition">
                    <td className="py-2.5 pr-4"><TypeBadge type={ind.ioc_type} /></td>
                    <td className="py-2.5 pr-4 font-mono text-xs text-slate-300 max-w-[260px] truncate" title={ind.value}>{ind.value}</td>
                    <td className="py-2.5 pr-4 text-slate-400">{ind.source}</td>
                    <td className="py-2.5 pr-4 text-slate-400">{ind.threat_type || '—'}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{ind.confidence?.toFixed(0)}%</td>
                    <td className="py-2.5 pr-4"><SeverityBadge severity={ind.severity} /></td>
                    <td className="py-2.5 pr-4"><MLBadge label={ind.ml_label} score={ind.ml_score} /></td>
                    <td className="py-2.5 pr-4 text-slate-500 text-xs">{new Date(ind.last_seen).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {indicators.length === 0 && (
              <div className="text-center py-12 text-slate-500 text-sm">No indicators match the current filters.</div>
            )}
          </div>
        )}
      </Panel>
    </div>
  )
}

function FilterSelect({ value, onChange, options, placeholder }) {
  return (
    <div className="relative">
      <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
      <select
        value={value}
        onChange={onChange}
        className="appearance-none bg-bg-card border border-white/10 rounded-lg pl-8 pr-8 py-2 text-sm text-slate-300 focus:outline-none focus:border-accent/50 cursor-pointer"
      >
        {options.map((o) => (
          <option key={o} value={o}>{o === '' ? placeholder : o}</option>
        ))}
      </select>
    </div>
  )
}
