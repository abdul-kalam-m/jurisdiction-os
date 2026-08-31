const TIERS = [
  {
    name: 'Starter',
    buyer: 'Small developer, expediter',
    pricing: 'Per-seat, monthly or annual',
    value: ['Limited jurisdictions', 'Scorecards', 'Checklists', 'Basic AI assistant (roadmap)'],
  },
  {
    name: 'Pro',
    buyer: 'Regional developer, AEC firm',
    pricing: 'Team subscription',
    value: ['More markets', 'Delay alerts', 'CSV/JSON exports', 'Collaboration features'],
  },
  {
    name: 'Enterprise',
    buyer: 'National developers, lenders',
    pricing: 'Custom contract',
    value: ['API access', 'SSO', 'Custom models', 'Dedicated onboarding'],
  },
  {
    name: 'Data Services',
    buyer: 'Consultants, investors, researchers',
    pricing: 'Add-on or project fee',
    value: ['Historical extracts', 'White-label feeds', 'Benchmark reports'],
  },
]

export default function PricingView() {
  return (
    <div className="flex flex-col gap-6">
      <div className="relative">
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <span className="rotate-[-8deg] select-none text-4xl font-black uppercase tracking-widest text-slate-200 dark:text-slate-800">
            Illustrative
          </span>
        </div>
        <div className="relative">
          <h1 className="text-2xl font-bold tracking-tight">Pricing</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            From the source spec&apos;s own tier table (§ Pricing Structure) &mdash; presented as product
            positioning for this portfolio demo, not a live commercial offer.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {TIERS.map((t) => (
          <div key={t.name} className="flex flex-col rounded-lg border border-slate-200 p-5 dark:border-slate-800">
            <h2 className="text-lg font-semibold">{t.name}</h2>
            <p className="mt-1 text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{t.buyer}</p>
            <p className="mt-2 text-sm font-medium text-brand-600 dark:text-accent-400">{t.pricing}</p>
            <ul className="mt-4 flex flex-1 flex-col gap-1.5 text-sm">
              {t.value.map((v) => (
                <li key={v} className="flex items-start gap-1.5">
                  <span aria-hidden="true" className="mt-0.5 text-emerald-600 dark:text-emerald-400">✓</span>
                  {v}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <p className="rounded-md border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
        No accounts, billing, or seats exist in this build (§3.2, out of scope) &mdash; this page is
        product-design positioning only, watermarked accordingly.
      </p>
    </div>
  )
}
