import { useEffect, useState } from 'react'
import { DATA_BASE_URL } from '../config'
import { MUNI_SLUGS } from '../types'
import type { AssetType, Playbook } from '../types'

const MUNI_LABELS: Record<string, string> = {
  'jersey-city': 'Jersey City, NJ',
  hoboken: 'Hoboken, NJ',
  princeton: 'Princeton, NJ',
  montclair: 'Montclair, NJ',
  nyc: 'New York City, NY (benchmark contrast)',
}

export default function FitCheckerView() {
  const [slug, setSlug] = useState<string>('jersey-city')
  const [assetType, setAssetType] = useState<AssetType>('multifamily')
  const [playbook, setPlaybook] = useState<Playbook | null>(null)

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/playbooks/${slug}.json`).then((r) => r.json()).then(setPlaybook).catch(() => setPlaybook(null))
  }, [slug])

  const path = playbook?.permit_paths[assetType]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Project Fit Checker</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Jurisdiction + asset type &rarr; likely permit path, hearing likelihood, and dependencies &mdash;
          driven entirely by the playbook, no hidden logic (§5.2).
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          {MUNI_SLUGS.map((s) => (
            <option key={s} value={s}>{MUNI_LABELS[s]}</option>
          ))}
        </select>
        <select
          value={assetType}
          onChange={(e) => setAssetType(e.target.value as AssetType)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="multifamily">Multifamily</option>
          <option value="small-commercial">Small Commercial</option>
        </select>
      </div>

      {playbook && !playbook.verified && (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          ⚠ Draft &mdash; not yet verified. This playbook was drafted with LLM-assisted research from
          cited official sources but has not been reviewed and approved by the owner (§5.3).
        </div>
      )}

      {path && playbook && (
        <div className="rounded-lg border border-slate-200 p-5 dark:border-slate-800">
          <h2 className="text-lg font-semibold">{playbook.jurisdiction} &mdash; {assetType}</h2>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Likely permits</h3>
              <ul className="mt-1 list-disc pl-5 text-sm">
                {path.likely_permits.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Review body</h3>
              <p className="mt-1 text-sm">{path.review_body}</p>
            </div>
          </div>

          <div className="mt-4">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Hearing likelihood</h3>
            <p className="mt-1 rounded-md bg-slate-50 px-3 py-2 text-sm font-medium dark:bg-slate-900">{path.hearing_likelihood}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{path.hearing_likelihood_basis}</p>
          </div>

          <div className="mt-4">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400">Submission requirements</h3>
            <ul className="mt-2 flex flex-col gap-1.5">
              {path.submission_requirements.map((r) => (
                <li key={r.item} className="flex items-start justify-between gap-3 rounded border border-slate-200 px-3 py-2 text-sm dark:border-slate-800">
                  <span>{r.item}</span>
                  <a href={r.citation} target="_blank" rel="noopener noreferrer" className="shrink-0 text-xs text-brand-600 underline dark:text-accent-400">
                    source
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
