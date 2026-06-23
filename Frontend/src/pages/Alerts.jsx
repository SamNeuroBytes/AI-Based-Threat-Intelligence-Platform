import React, { useEffect, useState } from 'react'
import { CheckCircle2, Sparkles, Clock } from 'lucide-react'
import { getAlerts, acknowledgeAlert } from '../api'
import { SeverityBadge, Panel, Spinner } from '../components/UI'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('unacknowledged')

  const load = () => {
    setLoading(true)
    const params = {}
    if (filter === 'unacknowledged') params.acknowledged = 0
    if (filter === 'acknowledged') params.acknowledged = 1
    getAlerts(params).then(setAlerts).finally(() => setLoading(false))
  }

  useEffect(load, [filter])

  const handleAck = async (id) => {
    await acknowledgeAlert(id)
    setAlerts((a) => a.filter((al) => al.id !== id || filter !== 'unacknowledged'))
    load()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-white">AI-Generated Alerts</h2>
          <p className="text-slate-400 text-sm mt-1">High-severity indicators automatically summarized for analyst review</p>
        </div>
        <div className="flex gap-2">
          {['unacknowledged', 'acknowledged', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition capitalize ${
                filter === f
                  ? 'bg-accent/15 text-accent border-accent/30'
                  : 'bg-bg-card text-slate-400 border-white/10 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? <Spinner /> : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <Panel key={alert.id} className="!p-4">
              <div className="flex items-start gap-4">
                <div className="mt-1 shrink-0">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                    <h4 className="font-semibold text-slate-100 text-sm">{alert.title}</h4>
                    <SeverityBadge severity={alert.severity} />
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed">{alert.summary}</p>
                  <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    {new Date(alert.created_at).toLocaleString()}
                  </div>
                </div>
                {!alert.acknowledged && (
                  <button
                    onClick={() => handleAck(alert.id)}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-severity-low/10 text-severity-low border border-severity-low/30 text-xs font-medium hover:bg-severity-low/20 transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Acknowledge
                  </button>
                )}
                {!!alert.acknowledged && (
                  <span className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 text-slate-500 text-xs font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Resolved
                  </span>
                )}
              </div>
            </Panel>
          ))}
          {alerts.length === 0 && (
            <Panel>
              <div className="text-center py-12 text-slate-500 text-sm">
                No {filter !== 'all' ? filter : ''} alerts. Run an ingestion cycle to generate new alerts from high-severity indicators.
              </div>
            </Panel>
          )}
        </div>
      )}
    </div>
  )
}
