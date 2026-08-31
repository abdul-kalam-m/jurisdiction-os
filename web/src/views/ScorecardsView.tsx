import { useEffect, useState } from 'react'
import { BarChart, Bar, LineChart, Line, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { DATA_BASE_URL } from '../config'
import { CITY_SLUGS, CLASS_LABELS } from '../types'
import type { AlertsPayload, JurisdictionsRegistry, Scorecard } from '../types'

export default function ScorecardsView() {
  const [registry, setRegistry] = useState<JurisdictionsRegistry | null>(null)
  const [selected, setSelected] = useState<string>('nyc')
  const [card, setCard] = useState<Scorecard | null>(null)
  const [alerts, setAlerts] = useState<AlertsPayload | null>(null)

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/jurisdictions.json`).then((r) => r.json()).then(setRegistry).catch(() => setRegistry(null))
    fetch(`${DATA_BASE_URL}/alerts.json`).then((r) => r.json()).then(setAlerts).catch(() => setAlerts(null))
  }, [])

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/scorecards/${selected}.json`).then((r) => r.json()).then(setCard).catch(() => setCard(null))
  }, [selected])

  const selectedAlerts = alerts?.jurisdictions[selected]?.classes

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Jurisdiction Scorecards</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Median permit cycle times by class, year, and confidence tier &mdash; every figure traceable to a
          MANIFEST-recorded source extract (§5.1).
        </p>
      </div>

      {registry && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left dark:bg-slate-900">
              <tr>
                <th className="px-3 py-2">Jurisdiction</th>
                <th className="px-3 py-2">Permits in window</th>
                <th className="px-3 py-2">Exclusion rate</th>
                <th className="px-3 py-2">Data quality flag</th>
                <th className="px-3 py-2">Best confidence tier</th>
              </tr>
            </thead>
            <tbody>
              {CITY_SLUGS.map((slug) => {
                const j = registry.jurisdictions[slug]
                if (!j) return null
                return (
                  <tr
                    key={slug}
                    onClick={() => setSelected(slug)}
                    className={`cursor-pointer border-t border-slate-100 hover:bg-brand-50 dark:border-slate-800 dark:hover:bg-slate-900 ${
                      selected === slug ? 'bg-brand-50 dark:bg-slate-900' : ''
                    }`}
                  >
                    <td className="px-3 py-2 font-medium">{j.city}</td>
                    <td className="px-3 py-2 font-mono">{j.total_permits_in_window.toLocaleString()}</td>
                    <td className="px-3 py-2 font-mono">{(j.overall_exclusion_rate * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2">
                      {j.data_quality_flag ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
                          ⚠ flagged
                        </span>
                      ) : (
                        <span className="text-slate-600 dark:text-slate-400">&mdash;</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <TierBadge tier={j.best_confidence_tier} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {card && (
        <div className="rounded-lg border border-slate-200 p-5 dark:border-slate-800">
          <h2 className="text-lg font-semibold">{card.city} &mdash; by class</h2>
          {card.data_quality_flag && (
            <p className="mt-1 text-sm text-amber-700 dark:text-amber-400">
              ⚠ Data quality flag: exclusion rate exceeds 15% for this jurisdiction (§5.1) &mdash; see{' '}
              <a href="/methods" className="underline">Methods &amp; Data</a> for what this excludes and why.
            </p>
          )}
          {alerts && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Delay-alert rule (§5.5): ratio of 90-day median cycle time to trailing-year baseline &ge;{' '}
              {alerts.rule.ratio_threshold}&times;, with &ge; {alerts.rule.min_n_90d} permits in the 90-day window.
              Backtested over {alerts.summary.total_backtest_points} jurisdiction-class history points
              (sampled every {alerts.rule.backtest_sample_step_days} days; the live rule itself runs {alerts.rule.live_rule_cadence}).
            </p>
          )}
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            {Object.entries(card.classes).map(([cls, m]) => (
              <div key={cls} className="rounded-md border border-slate-200 p-4 dark:border-slate-800">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{CLASS_LABELS[cls] ?? cls}</h3>
                  {m.confidence_tier && <TierBadge tier={m.confidence_tier} />}
                </div>
                {m.coverage === 'no_data' ? (
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">No data for this class in this jurisdiction.</p>
                ) : (
                  <>
                    <dl className="mt-2 grid grid-cols-3 gap-2 text-center font-mono text-sm">
                      <div>
                        <dt className="text-xs text-slate-500">Median</dt>
                        <dd className="font-semibold">{m.median_days}d</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-slate-500">p25</dt>
                        <dd>{m.p25_days}d</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-slate-500">p75</dt>
                        <dd>{m.p75_days}d</dd>
                      </div>
                    </dl>
                    {m.annual_volume && (
                      <div className="mt-3 h-32">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={Object.entries(m.annual_volume).map(([year, n]) => ({ year, n }))}>
                            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 11 }} width={30} />
                            <Tooltip />
                            <Bar dataKey="n" fill="#4f46e5" radius={[3, 3, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                    <AlertPanel result={selectedAlerts?.[cls]} />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function AlertPanel({ result }: { result?: import('../types').AlertClassResult }) {
  if (!result || result.coverage !== 'ok' || !result.timeline || !result.current) {
    return null
  }
  const { current, timeline, n_alert_points } = result
  return (
    <div className="mt-3 border-t border-slate-200 pt-3 dark:border-slate-800">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Delay-alert status</span>
        {current.alert ? (
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800 dark:bg-red-900/50 dark:text-red-300">
            ⚠ Elevated ({current.ratio}&times; baseline)
          </span>
        ) : (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
            ✓ Normal{current.ratio != null ? ` (${current.ratio}×)` : ''}
          </span>
        )}
      </div>
      <div className="mt-2 h-20">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={timeline}>
            <ReferenceLine y={1.25} stroke="#dc2626" strokeDasharray="3 3" />
            <XAxis dataKey="as_of" hide />
            <YAxis hide domain={['dataMin', 'dataMax']} />
            <Tooltip
              formatter={(v: number) => [v, 'ratio']}
              labelFormatter={(l: string) => l}
              contentStyle={{ fontSize: 11 }}
            />
            <Line type="monotone" dataKey="ratio" stroke="#4f46e5" dot={false} strokeWidth={1.5} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
        {n_alert_points} of {result.n_backtest_points} backtested points alerted. Dashed line = 1.25&times; threshold.
      </p>
    </div>
  )
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    A: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300',
    B: 'bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300',
    C: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  }
  return <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${colors[tier] ?? colors.C}`}>Tier {tier}</span>
}
