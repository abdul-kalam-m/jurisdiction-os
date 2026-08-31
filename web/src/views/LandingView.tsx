import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { DATA_BASE_URL } from '../config'
import { CLASS_LABELS } from '../types'
import type { AlertsPayload } from '../types'

export default function LandingView() {
  const [alerts, setAlerts] = useState<AlertsPayload | null>(null)

  useEffect(() => {
    fetch(`${DATA_BASE_URL}/alerts.json`).then((r) => r.json()).then(setAlerts).catch(() => setAlerts(null))
  }, [])

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col gap-4 py-8 text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-accent-600 dark:text-accent-400">
          Portfolio demonstration &middot; permitting &amp; entitlement intelligence
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Bloomberg Terminal <span className="text-brand-600 dark:text-accent-400">for local permitting risk</span>
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-slate-600 dark:text-slate-300">
          Jurisdiction scorecards benchmarking real permit cycle times, a project-fit checker with a
          dynamic submission checklist, and an AI signal feed extracting planning-board actions from
          NJ meeting minutes &mdash; the intelligence layer teams open before land is tied up.
        </p>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          <Link to="/scorecards" className="rounded-md bg-brand-600 px-5 py-2.5 font-semibold text-white hover:bg-brand-700">
            Explore scorecards
          </Link>
          <Link to="/fit-checker" className="rounded-md border border-slate-300 px-5 py-2.5 font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900">
            Try the fit checker
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: 'Jurisdictions benchmarked', value: '6' },
          { label: 'Permits analyzed', value: '~1.2M' },
          { label: 'Signal feed items', value: '117+' },
        ].map((s) => (
          <div key={s.label} className="rounded-lg border border-slate-200 bg-white p-6 text-center dark:border-slate-800 dark:bg-slate-900">
            <p className="font-mono text-3xl font-bold text-brand-600 dark:text-accent-400">{s.value}</p>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{s.label}</p>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Feature
          title="Jurisdiction Scorecards"
          desc="Median, p25/p75 permit cycle times by class and year, volume trends, and a confidence tier derived from real data coverage -- not a marketing number."
          to="/scorecards"
        />
        <Feature
          title="Fit Checker & Checklist"
          desc="Enter a jurisdiction and asset type, get a likely permit path, hearing-likelihood estimate, and a citation-backed submission checklist -- every fact traces to an official source."
          to="/fit-checker"
        />
        <Feature
          title="Planning Signal Feed"
          desc="LLM-extracted planning and zoning board actions from real NJ meeting minutes, gated by a hand-verified precision eval before anything ships."
          to="/signals"
        />
      </section>

      {alerts && alerts.summary.currently_alerting.length > 0 && (
        <section className="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
          <p className="text-sm font-semibold text-red-800 dark:text-red-300">
            ⚠ Live delay alerts ({alerts.summary.currently_alerting.length}) &mdash; module M5 (§5.5)
          </p>
          <ul className="mt-2 flex flex-wrap gap-2 text-xs">
            {alerts.summary.currently_alerting.map(({ jurisdiction, shared_class }) => (
              <li key={`${jurisdiction}-${shared_class}`}>
                <Link
                  to="/scorecards"
                  className="rounded-full bg-red-100 px-2.5 py-1 font-medium text-red-800 hover:bg-red-200 dark:bg-red-900/50 dark:text-red-300 dark:hover:bg-red-900"
                >
                  {jurisdiction} &middot; {CLASS_LABELS[shared_class] ?? shared_class}
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-red-700 dark:text-red-400">
            90-day median cycle time is running &ge; 1.25&times; the trailing-year baseline. See the
            jurisdiction&apos;s Scorecards detail for the full backtested timeline.
          </p>
        </section>
      )}

      <section className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
        <strong>Demonstration product.</strong> Jurisdiction Intelligence OS is a portfolio project built
        entirely from public records. Benchmarks are estimates from published permit data; requirements
        summaries are curated from official sources and may be outdated. Nothing here is legal advice or
        a substitute for confirming requirements with the jurisdiction. See{' '}
        <Link to="/methods" className="underline">Methods &amp; Data</Link> for sources, vintages, and caveats.
      </section>
    </div>
  )
}

function Feature({ title, desc, to }: { title: string; desc: string; to: string }) {
  return (
    <Link to={to} className="block rounded-lg border border-slate-200 p-5 hover:border-brand-400 hover:shadow-sm dark:border-slate-800 dark:hover:border-accent-500">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{desc}</p>
    </Link>
  )
}
