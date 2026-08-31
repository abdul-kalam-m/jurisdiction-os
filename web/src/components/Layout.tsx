import { NavLink, Outlet } from 'react-router-dom'
import { DISCLAIMER } from '../config'

const NAV_ITEMS = [
  { to: '/scorecards', label: 'Scorecards' },
  { to: '/fit-checker', label: 'Fit Checker' },
  { to: '/checklist', label: 'Checklist' },
  { to: '/signals', label: 'Signals' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/methods', label: 'Methods & Data' },
]

// Terminal-inspired glyph: a simple bracket/cursor mark, evoking a data
// terminal rather than either sibling project's own water-droplet or
// map-pin marks -- distinct visual identity for this product-demo project.
function TerminalMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="shrink-0 text-accent-400">
      <rect x="2" y="3" width="20" height="18" rx="2" stroke="currentColor" strokeWidth="1.75" />
      <path d="M6 9l3 3-3 3" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 15h6" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  )
}

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-brand-700 focus:px-3 focus:py-2 focus:text-white"
      >
        Skip to main content
      </a>
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950 text-slate-100">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <TerminalMark />
            Jurisdiction Intelligence <span className="text-accent-400">OS</span>
          </NavLink>
          <nav aria-label="Main views" className="flex flex-wrap items-center gap-1 text-sm">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded px-3 py-1.5 font-medium transition-colors ${
                    isActive ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main id="main-content" className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        <p className="mx-auto max-w-7xl">
          <strong>Demonstration product.</strong> {DISCLAIMER.replace('Demonstration product. ', '')}
        </p>
      </footer>
    </div>
  )
}
