import React, { useEffect, useState } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import { BrainCircuit, Activity, Gauge, ListChecks } from 'lucide-react'
import { getIndicators } from '../api'
import { Panel, Spinner, SeverityBadge, MLBadge, StatCard } from '../components/UI'

const FEATURES = [
  { key: 'length', label: 'String Length', desc: 'Total character length of the indicator value (URL/domain). Unusually long values often indicate obfuscation.' },
  { key: 'digit_ratio', label: 'Digit Ratio', desc: 'Proportion of digits in the value. High ratios are common in algorithmically generated domains.' },
  { key: 'special_count', label: 'Special Characters', desc: 'Count of non-alphanumeric characters — frequent in phishing URLs with query strings.' },
  { key: 'entropy', label: 'Shannon Entropy', desc: 'Measures randomness of characters. High entropy suggests DGA (Domain Generation Algorithm) malware.' },
  { key: 'subdomain_depth', label: 'Subdomain Depth', desc: 'Number of dot-separated segments. Deep nesting is often used to evade detection.' },
  { key: 'has_keyword', label: 'Suspicious Keywords', desc: "Presence of phishing-related terms like 'login', 'verify', 'secure', 'bank'." },
  { key: 'risky_tld', label: 'Risky TLD', desc: "Whether the domain uses a TLD frequently abused by attackers (.xyz, .top, .tk, etc)." },
  { key: 'confidence', label: 'Source Confidence', desc: 'Confidence score reported by the originating threat feed (0-100).' },
]

export default function MLInsights() {
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getIndicators({ limit: 200 }).then(setIndicators).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  const scored = indicators.filter((i) => i.ml_score != null)
  const anomalous = scored.filter((i) => i.ml_label === 'anomalous')
  const avgScore = scored.length ? scored.reduce((a, b) => a + b.ml_score, 0) / scored.length : 0

  const scatterData = scored.map((i) => ({
    x: i.confidence,
    y: i.ml_score,
    severity: i.severity,
    value: i.value,
    label: i.ml_label,
  }))

  const severityColor = { critical: '#ef4444', high: '#f97316', medium: '#eab308', low: '#22c55e', unknown: '#64748b' }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">ML Insights</h2>
        <p className="text-slate-400 text-sm mt-1">Anomaly detection model trained on lexical features of every indicator</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Indicators Scored" value={scored.length} icon={Gauge} accent="accent" sub={`out of ${indicators.length} loaded`} />
        <StatCard label="Flagged Anomalous" value={anomalous.length} icon={Activity} accent="purple-400" sub={`${scored.length ? ((anomalous.length / scored.length) * 100).toFixed(1) : 0}% of scored set`} />
        <StatCard label="Avg Anomaly Score" value={avgScore.toFixed(1)} icon={BrainCircuit} accent="severity-medium" sub="0 (normal) – 100 (anomalous)" />
        <StatCard label="Model Type" value="IsolationForest" icon={ListChecks} accent="severity-low" sub="150 estimators, contamination=0.15" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Panel title="Confidence vs. Anomaly Score" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" dataKey="x" name="Source Confidence" unit="%" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <YAxis type="number" dataKey="y" name="ML Anomaly Score" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <ZAxis range={[40, 40]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ background: '#161e2e', border: '1px solid #2a3550', borderRadius: 8, fontSize: 12 }}
                content={({ payload }) => {
                  if (!payload?.length) return null
                  const d = payload[0].payload
                  return (
                    <div className="bg-bg-card border border-white/10 rounded-lg p-2 text-xs max-w-[220px]">
                      <p className="font-mono text-slate-300 truncate mb-1">{d.value}</p>
                      <p className="text-slate-400">Confidence: {d.x?.toFixed(0)}% · Anomaly: {d.y?.toFixed(0)}</p>
                      <p className="text-slate-400">Label: {d.label}</p>
                    </div>
                  )
                }}
              />
              <Scatter data={scatterData} fillOpacity={0.7}>
                {scatterData.map((d, i) => (
                  <Cell key={i} fill={severityColor[d.severity] || '#64748b'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-xs text-slate-500 mt-2">Each point is one indicator, colored by severity. Points in the upper-right are high-confidence threats that also look structurally unusual — these are the highest priority.</p>
        </Panel>

        <Panel title="Top Anomalous Indicators">
          <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
            {anomalous
              .sort((a, b) => b.ml_score - a.ml_score)
              .slice(0, 8)
              .map((ind) => (
                <div key={ind.id} className="p-2.5 rounded-lg bg-white/5 border border-white/5">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-mono text-xs text-slate-300 truncate">{ind.value}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={ind.severity} />
                    <MLBadge label={ind.ml_label} score={ind.ml_score} />
                  </div>
                </div>
              ))}
            {anomalous.length === 0 && <p className="text-sm text-slate-500 py-8 text-center">No anomalies detected in current dataset.</p>}
          </div>
        </Panel>
      </div>

      <Panel title="How the Model Works">
        <p className="text-sm text-slate-400 mb-4 leading-relaxed">
          Every indicator's raw value (URL, domain, IP, or hash) is converted into 8 lexical features below.
          An <span className="text-slate-200 font-medium">IsolationForest</span> model — an unsupervised algorithm that
          isolates outliers by randomly partitioning the feature space — is trained on these features across all collected
          indicators. Indicators that are "easy to isolate" (few partitions needed) receive a high anomaly score and are
          flagged for analyst review, even if the originating feed didn't mark them as high severity.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {FEATURES.map((f) => (
            <div key={f.key} className="p-3 rounded-lg bg-white/5 border border-white/5">
              <p className="text-xs font-semibold text-accent mb-1">{f.label}</p>
              <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
