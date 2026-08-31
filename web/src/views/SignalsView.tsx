import { useEffect, useMemo, useState } from 'react'
import { DATA_BASE_URL } from '../config'
import type { Action, SignalItem } from '../types'

const ACTION_COLORS: Record<Action, string> = {
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300',
  denied: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
  carried: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300',
  heard: 'bg-sky-100 text-sky-800 dark:bg-sky-900/50 dark:text-sky-300',
  withdrawn: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
}

export default function SignalsView() {
  const [items, setItems] = useState<SignalItem[]>([])
  const [muniFilter, setMuniFilter] = useState('')
  const [actionFilter, setActionFilter] = useState('')

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/signals.json`).then((r) => r.json()).then(setItems).catch(() => setItems([]))
  }, [])

  const municipalities = useMemo(() => [...new Set(items.map((i) => i.municipality))].sort(), [items])

  const filtered = useMemo(
    () =>
      items.filter(
        (i) => (!muniFilter || i.municipality === muniFilter) && (!actionFilter || i.action === actionFilter)
      ),
    [items, muniFilter, actionFilter]
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Planning &amp; Zoning Signal Feed</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          LLM-extracted board actions from real NJ meeting minutes (§5.4). {items.length} items across{' '}
          {municipalities.length} municipalities.
        </p>
        <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">
          ⚠ Extraction precision on the `action` field is 84.6% on a 30-item hand-verified gold set,
          below the project&apos;s own 90% target &mdash; see <a href="/methods" className="underline">Methods &amp; Data</a> for
          the full eval writeup before relying on any single item&apos;s action label.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select aria-label="Filter by municipality" value={muniFilter} onChange={(e) => setMuniFilter(e.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900">
          <option value="">All municipalities</option>
          {municipalities.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <select aria-label="Filter by board action" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900">
          <option value="">All actions</option>
          {(['approved', 'denied', 'carried', 'heard', 'withdrawn'] as Action[]).map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
      </div>

      <ul className="flex flex-col gap-3">
        {filtered.slice(0, 100).map((item, i) => (
          <li key={i} className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <span className="font-medium text-slate-900 dark:text-slate-100">{item.municipality}</span>
                <span>&middot;</span>
                <span>{item.board}</span>
                <span>&middot;</span>
                <span>{item.meeting_date}</span>
                {item.case_ref && <><span>&middot;</span><span className="font-mono">{item.case_ref}</span></>}
              </div>
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ACTION_COLORS[item.action]}`}>{item.action}</span>
            </div>
            <p className="mt-2 text-sm">{item.project_desc}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span className="rounded bg-slate-100 px-2 py-0.5 text-slate-700 dark:bg-slate-800 dark:text-slate-300">{item.use_type}</span>
              {item.variances_mentioned.map((v) => (
                <span key={v} className="rounded bg-slate-100 px-2 py-0.5 text-slate-700 dark:bg-slate-800 dark:text-slate-300">{v}</span>
              ))}
              <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="ml-auto underline">source</a>
            </div>
          </li>
        ))}
      </ul>
      {filtered.length > 100 && (
        <p className="text-center text-sm text-slate-500 dark:text-slate-400">Showing first 100 of {filtered.length} matching items.</p>
      )}
    </div>
  )
}
