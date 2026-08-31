import { useEffect, useState } from 'react'
import { DATA_BASE_URL } from '../config'
import { MUNI_SLUGS } from '../types'
import type { AssetType, Playbook } from '../types'

const MUNI_LABELS: Record<string, string> = {
  'jersey-city': 'Jersey City, NJ',
  hoboken: 'Hoboken, NJ',
  princeton: 'Princeton, NJ',
  montclair: 'Montclair, NJ',
  nyc: 'New York City, NY',
}

export default function ChecklistView() {
  const [slug, setSlug] = useState<string>('jersey-city')
  const [assetType, setAssetType] = useState<AssetType>('multifamily')
  const [playbook, setPlaybook] = useState<Playbook | null>(null)

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/playbooks/${slug}.json`).then((r) => r.json()).then(setPlaybook).catch(() => setPlaybook(null))
  }, [slug])

  const path = playbook?.permit_paths[assetType]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-3 print:hidden">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dynamic Submission Checklist</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Compiled from the jurisdiction playbook, filtered by asset type, grouped for printing (§5.3).
          </p>
        </div>
        <button
          onClick={() => window.print()}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Print checklist
        </button>
      </div>

      <div className="flex flex-wrap gap-3 print:hidden">
        <select value={slug} onChange={(e) => setSlug(e.target.value)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900">
          {MUNI_SLUGS.map((s) => <option key={s} value={s}>{MUNI_LABELS[s]}</option>)}
        </select>
        <select value={assetType} onChange={(e) => setAssetType(e.target.value as AssetType)} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900">
          <option value="multifamily">Multifamily</option>
          <option value="small-commercial">Small Commercial</option>
        </select>
      </div>

      {path && playbook && (
        <div className="rounded-lg border border-slate-300 p-6 print:border-black">
          <h2 className="text-xl font-bold">{playbook.jurisdiction} &mdash; {assetType} submission checklist</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 print:text-black">
            Review body: {path.review_body} &middot; Hearing likelihood: {path.hearing_likelihood}
          </p>
          {!playbook.verified && (
            <p className="mt-2 text-sm font-medium text-amber-700 print:text-black">
              ⚠ Draft &mdash; not yet verified by the owner.
            </p>
          )}
          <ol className="mt-4 flex flex-col gap-2">
            {path.submission_requirements.map((r, i) => (
              <li key={r.item} className="flex items-start gap-3 border-b border-slate-200 pb-2 text-sm print:border-black">
                <span aria-hidden="true" className="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-slate-400 text-xs">{i + 1}</span>
                <span className="flex-1">
                  {r.item}
                  <br />
                  <a href={r.citation} target="_blank" rel="noopener noreferrer" className="text-xs text-brand-600 underline dark:text-accent-400 print:text-black">
                    {r.citation}
                  </a>
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-6 text-xs text-slate-400 print:text-black">
            Demonstration product &mdash; not a substitute for confirming requirements with {playbook.jurisdiction}.
          </p>
        </div>
      )}
    </div>
  )
}
