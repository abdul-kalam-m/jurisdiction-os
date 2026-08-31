# Jurisdiction Intelligence OS

**"Bloomberg Terminal for local permitting risk"** — a portfolio demonstration of a B2B proptech
product: jurisdiction scorecards benchmarking real permit cycle times, a project-fit checker and
dynamic submission checklist driven by curated jurisdiction playbooks, an AI signal feed
extracting planning-board actions from NJ meeting minutes, and a delay-alert monitor backtested
on real historical data.

**Live:** [jurisdiction-os.pages.dev](https://jurisdiction-os.pages.dev)

> **Demonstration product.** Jurisdiction Intelligence OS is a portfolio project built entirely
> from public records. Benchmarks are estimates from published permit data; requirements
> summaries are curated from official sources and may be outdated. Nothing here is legal advice
> or a substitute for confirming requirements with the jurisdiction. See the app's own
> [Methods & Data](https://jurisdiction-os.pages.dev/methods) page for sources, vintages, and caveats.

## What's actually in it

- **Scorecards** — ~1.2M permits across 6 benchmark cities (NYC, Chicago, Austin, San Francisco,
  Seattle, Los Angeles), median/p25/p75 cycle times by permit class and year, confidence tiers
  derived from real data coverage (tier A is disclosed as unreachable with this pipeline's
  current sources — not silently claimed).
- **Fit Checker & Checklist** — jurisdiction + asset type → likely permit path, hearing
  likelihood, and a citation-backed submission checklist for 5 NJ jurisdictions (Jersey City,
  Hoboken, Princeton, Montclair) plus NYC as a benchmark contrast.
- **Signal feed** — 114 LLM-extracted planning/zoning board actions from real Hoboken, Montclair,
  and Westfield meeting minutes. Extraction precision is disclosed honestly at 84.6% on a
  30-item hand-verified gold set (below the project's own 90% target) — see below.
- **Delay alerts** — a backtested rule (90-day median cycle time vs. trailing-year baseline,
  ≥1.25× and ≥20 permits triggers an alert) run over full permit history, not just the current
  week. 4 jurisdiction × class combinations are alerting live right now.

## The centerpiece: an honestly eval-gated LLM pipeline

The signal-feed extraction is the project's actual point, not a side feature. A 30-item gold set
was hand-verified against real quoted source text (never derived from the model's own output).
Three rounds of prompt iteration moved precision from 73.3% → 80.8% → 84.6%, fixing every
misclassification pattern that responded to a clearer instruction. One pattern didn't: cases with
long, technical testimony and no actual vote in the excerpt get mislabeled "approved" regardless
of an explicit worked example and a mechanical "find the literal vote sentence" instruction. The
owner reviewed this result and chose to document the gap and ship rather than force a workaround
— that decision, the full iteration history, and the specific failure pattern are disclosed on
the app's own [Methods & Data](https://jurisdiction-os.pages.dev/methods) page, not buried in a
commit log. `eval/eval_runner.py` + `eval/results/` carry the mechanics; `PROGRESS.md` carries the
narrative.

## Repository layout

- `OPERATING_GUIDE.md` — the canonical build manual.
- `PROGRESS.md` — session log (newest entry on top; every deviation, bug, and owner decision
  logged here, not silently absorbed).
- `RECON.md` — Phase 0 data-source recon, including 4 rejected benchmark-city candidates and why.
- `pipeline/` — Python pipeline (recon → permit ETL → scorecards → playbooks/fit-checker →
  signal-feed extraction → delay alerts) + `tests/` (pytest against real hand-verified fixtures,
  not synthetic-only) + `check_prompt_version.py` (CI gate: a shipped prompt change without a
  re-run eval fails the build, not silently drifts).
- `playbooks/` — `{jurisdiction}.yaml`, curated and cited jurisdiction rules; every submission
  requirement carries a citation URL, enforced at compile time.
- `eval/` — gold-set evaluation for the LLM extraction module; `results/LATEST` points to the
  canonical committed result.
- `data/` — `raw/` (gitignored), `MANIFEST.json` (source provenance, committed).
- `web/` — Vite + React + TypeScript strict app; `public/data/` artifacts are committed (small,
  static, no external data store needed) + `e2e/` (Playwright + axe-core smoke suite).
- `.github/workflows/` — `ci.yml` (pytest/ruff/lint/typecheck/build/Playwright on every push),
  `refresh.yml` (weekly permit + scorecard + delay-alert refresh), `signals.yml` (weekly signal
  extraction). See PROGRESS.md's Phase 6 entry for exactly which repo secrets are still needed
  before the last two run unattended.

## Status

Phases 0–6 complete (recon → permit ETL → scorecards → playbooks/fit-checker → signal feed →
delay alerts + automation). Phase 7 (hardening + launch) in progress. See `PROGRESS.md` for the
full per-phase log, every bug caught and fixed (or explicitly documented as a real, accepted
limitation), and every owner decision.

## Pipeline

```bash
cd pipeline
uv sync --extra dev
uv run pytest              # 49 tests against real hand-verified fixtures
uv run ruff check .
uv run python 10_permit_etl.py
uv run python 20_scorecards.py
uv run python 30_playbooks.py
uv run python 50_delay_alerts.py
```

Signal-feed extraction needs `OPENAI_API_KEY` (owner-directed deviation from the guide's
originally-locked model — see PROGRESS.md):

```bash
uv run python 40_fetch_minutes.py
uv run python 41_extract_signals.py
uv run python check_prompt_version.py   # fails loudly if the shipped prompt outran its eval
```

## Web app

```bash
cd web
npm install
npm run lint
npm run build
npx playwright install --with-deps chromium
npm run test:e2e            # smoke + axe accessibility, zero serious/critical violations
```

## Data sources

Open municipal permit data (Socrata) for the 6 benchmark cities; NJ municipal meeting portals
(CivicWeb/IQM2/CivicPlus/custom CMS) for the NJ deep-dive municipalities. Full source table, exact
dataset IDs, and field mappings: `RECON.md`. Full methodology, vintages, and caveats (including
the ones that don't fit in a README): the app's own Methods & Data page.
