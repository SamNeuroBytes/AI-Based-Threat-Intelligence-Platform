import React from 'react'

export function StatCard({ label, value, icon: Icon, accent = 'accent', sub }) {
  return (
    <div className="glass glow-border rounded-2xl p-5 fade-in">
      <div className="flex items-center justify-between mb-2">
        <p className="text-slate-400 text-sm font-medium">{label}</p>
        {Icon && <Icon className={`w-5 h-5 text-${accent}`} />}
      </div>
      <p className="text-3xl font-bold text-white tracking-tight">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

const severityColors = {
  critical: 'bg-severity-critical/15 text-severity-critical border-severity-critical/30',
  high: 'bg-severity-high/15 text-severity-high border-severity-high/30',
  medium: 'bg-severity-medium/15 text-severity-medium border-severity-medium/30',
  low: 'bg-severity-low/15 text-severity-low border-severity-low/30',
  unknown: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
}

export function SeverityBadge({ severity }) {
  const cls = severityColors[severity] || severityColors.unknown
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cls} uppercase tracking-wide`}>
      {severity}
    </span>
  )
}

export function TypeBadge({ type }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-mono font-medium bg-white/5 text-slate-300 border border-white/10">
      {type}
    </span>
  )
}

export function MLBadge({ label, score }) {
  if (!label) return <span className="text-slate-500 text-xs">—</span>
  const isAnomalous = label === 'anomalous'
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
        isAnomalous
          ? 'bg-purple-500/15 text-purple-300 border-purple-500/30'
          : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
      }`}
    >
      {isAnomalous && <span className="w-1.5 h-1.5 rounded-full bg-purple-400 pulse-dot" />}
      {label} {score != null && `· ${score.toFixed(0)}`}
    </span>
  )
}

export function Panel({ title, children, action, className = '' }) {
  return (
    <div className={`glass rounded-2xl p-5 fade-in ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-sm font-semibold text-slate-200 tracking-wide">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-8 h-8 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
    </div>
  )
}
