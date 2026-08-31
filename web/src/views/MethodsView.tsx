import { DISCLAIMER } from '../config'

export default function MethodsView() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Methods &amp; Data</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Sources, vintages, scoring logic, and known limitations &mdash; including the extraction eval
          results, disclosed honestly rather than omitted.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold">M1 &mdash; Jurisdiction scorecards</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Per jurisdiction &times; permit class: median and p25/p75 days from filing to issuance, annual
          volume, 3-year trend slope. Records with a negative/zero duration or a duration exceeding 5
          years are excluded from cycle-time statistics (§5.1) &mdash; a 0-day duration reflects genuine
          same-day/over-the-counter issuance, not a data error, and isn&apos;t informative for benchmarking
          review time. A jurisdiction with &gt;15% exclusion carries a data-quality flag on its scorecard.
        </p>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          <strong>Confidence tiers:</strong> A requires &ge;3 years, &ge;200 permits/year, and per-permit
          status-history data; B requires &ge;3 years and &ge;50/year; C is anything less. None of the six
          benchmark cities&apos; public datasets carry the status-history field tier A needs &mdash; every
          jurisdiction in this build caps at tier B or C. This is disclosed here rather than silently
          assumed better than it is.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Benchmark cities &amp; source data</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          6 of 10 candidate cities passed recon (NYC, Chicago, Austin, San Francisco, Seattle, Los
          Angeles) &mdash; the other 4 (Philadelphia, Boston, Washington DC, Mesa AZ) publish permit
          issuance dates but not filing/application dates, so cycle-time benchmarking isn&apos;t possible
          from their public data. Chicago&apos;s dataset has no residential/commercial split field, so its
          new-construction figures aren&apos;t broken out by that dimension.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold">M3 &mdash; Playbooks</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Playbooks are drafted with LLM-assisted research from real, cited official sources (state
          statute, municipal code) and every submission-requirement item carries a citation URL &mdash; a
          build-time gate rejects any item without one. Every playbook ships marked{' '}
          <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">verified: false</code> until the
          owner reviews it; unverified playbooks show a draft banner throughout the app.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold">M4 &mdash; Signal feed extraction</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Fetched from Hoboken, Montclair, and Westfield&apos;s real planning/zoning board meeting minutes
          (§6.4 polite-fetch rules). Princeton was excluded &mdash; its minutes are published as
          scanned/image-only PDFs, and OCR is out of scope for this build. Extraction uses GPT-4o-mini
          (an owner-directed deviation from the guide&apos;s originally-locked model, logged in
          PROGRESS.md) via a structured prompt, validated against a schema before publishing &mdash; items
          failing validation are dropped and counted, never hand-patched.
        </p>
        <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm dark:border-amber-800 dark:bg-amber-950/40">
          <p className="font-semibold text-amber-900 dark:text-amber-300">Extraction precision &mdash; honest result, gate not met</p>
          <p className="mt-1 text-amber-900 dark:text-amber-300">
            Evaluated against a 30-item gold set hand-verified against real quoted source text (not
            derived from the model&apos;s own output): <strong>84.6%</strong> precision on the{' '}
            <code className="rounded bg-white/50 px-1 dark:bg-black/20">action</code> field
            (approved/denied/carried/heard/withdrawn), against a 90% project target.{' '}
            <code className="rounded bg-white/50 px-1 dark:bg-black/20">use_type</code> precision is 96.2%.
          </p>
          <p className="mt-2 text-amber-900 dark:text-amber-300">
            Three rounds of prompt iteration were run (73.3% &rarr; 80.8% &rarr; 84.6%), fixing a clear
            "approval extension mislabeled as heard" pattern entirely. A second pattern persists on
            cases with long, technical testimony (traffic studies, expert witnesses) and no actual vote
            in the excerpt &mdash; the model tends to infer approval from the volume of engagement rather
            than a stated result, despite an explicit worked example and a mechanical instruction to
            find the literal vote sentence. The owner reviewed this result and chose to document it
            rather than build a second-pass verification architecture for this build. Treat any single
            signal feed item&apos;s <code className="rounded bg-white/50 px-1 dark:bg-black/20">action</code> field
            as indicative, not authoritative &mdash; verify against the linked source before relying on it.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold">M5 &mdash; Delay alerts</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Per jurisdiction &times; permit class, weekly: the median cycle time of permits issued in the
          last 90 days versus the median of the trailing 365 days excluding that same 90-day window.
          An alert fires when the ratio is &ge; 1.25&times; and at least 20 permits fall in the 90-day
          window (below that count a swing is more likely noise than signal).
        </p>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          The rule is backtested over each jurisdiction &times; class&apos;s full permit history (not
          just the current week) &mdash; 2,369 sampled history points (every 14 days, a file-size
          budget tradeoff &mdash; the live rule itself still runs weekly) across 30 combinations with
          enough history to backtest, of which 253 points (&asymp;10.7%) would have alerted. That
          backtested timeline is what renders on each jurisdiction&apos;s Scorecards detail page, both
          to validate the rule against real historical cycle-time swings and to make the delay-alert
          feature demonstrable without waiting for a live swing to occur. The live &ldquo;current&rdquo;
          status shown alongside it is always evaluated at the true latest date in the data, independent
          of that 14-day sampling interval.
        </p>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          <strong>Delivery:</strong> in-app only in this build. The rule also emits an owner-only email
          hook (never external recipients), but this project&apos;s environment has no transactional-email
          credentials configured &mdash; setting one up means creating a new external account, which is
          an owner action, not something the pipeline does for itself. Until the owner supplies SMTP
          credentials, a firing alert is logged and recorded in <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">alerts.json</code> (the
          in-app feed) but not emailed.
        </p>
      </section>

      <section>
        <h2 className="text-lg font-semibold">Refresh cadence</h2>
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
          Static build, no live backend. Weekly automated refresh via GitHub Actions is planned for
          permit data (Mon 09:00 UTC) and signal-feed extraction (Tue) &mdash; see PROGRESS.md for current
          automation status.
        </p>
      </section>

      <section className="rounded-md border border-slate-300 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-900">
        <strong>{DISCLAIMER}</strong>
      </section>
    </div>
  )
}
