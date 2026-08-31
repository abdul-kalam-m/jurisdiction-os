# Jurisdiction Intelligence OS — Operating Guide

**Project:** Jurisdiction Intelligence OS (JIOS) — Permitting & Entitlement Intelligence Platform (portfolio demo release)
**Owner:** Abdul Kalam Azad Mustaq (ar.abdulkalam.mustaq@gmail.com)
**Guide version:** 1.0 — written 2026-07-18
**Status:** Not started (no repository exists yet)
**Guide location (canonical):** `I:\My Drive\RUTGERS\Portfolio Projects\7. JURISDICTION INTELLIGENCE OS\OPERATING_GUIDE.md`
**Source spec:** `jurisdiction-intelligence-os-product-spec.md` (same folder) — the product vision. **This guide is the build manual and wins on any conflict** (see §2, Deviations).

---

## 0. How to use this document

Written so a coding agent (Opus/Sonnet) can build the project across sessions with **no conversation history**.

1. Read this guide, then the source spec (for product voice/positioning only), then `PROGRESS.md` in the repo root (§13.5).
2. One phase (§11) per session; meet all exit criteria before advancing.
3. This guide wins over the spec, chat history, and your own scope instincts. External facts drift — fix per §13.2, log in `PROGRESS.md`.
4. §13.3 items are hard-locked. §5.6 honesty rules and §6.4 collection-ethics rules are non-negotiable.

---

## 1. Project identity

### 1.1 What is being built

**One-liner:** A working demo of "Bloomberg Terminal for local permitting risk": jurisdiction scorecards benchmarking real permit cycle times from open municipal records, a project-fit checker and dynamic submission checklist driven by curated jurisdiction playbooks, and an AI signal feed that extracts planning-board actions from NJ meeting minutes — deployed as a public product demo.

This is a **portfolio demonstration of a B2B SaaS product**, not a commercial launch. It must look and read like a real product (landing page, positioning, illustrative pricing page from the spec) while every number in it is honestly derived from public records. The spec's five MVP modules map to §5's modules M1–M5.

### 1.2 Why it exists (portfolio narrative)

Flagship candidate for the portfolio's **Data Engineering & Applied AI** section: multi-city open-data ETL, statistical benchmarking, a rules engine, and a production-shaped LLM extraction pipeline with a measured evaluation set — wrapped in product thinking (the spec's positioning, tiers, and GTM are presented as product design work). It complements the flood projects (government-data analytics) with a private-sector product lens.

### 1.3 Audiences

1. Hiring managers/reviewers assessing product + data + AI engineering (primary).
2. Developers/expediters as the fictive target user — UX copy speaks to them.
3. The owner, potentially evolving this into a real venture later.

### 1.4 Success criteria (measurable)

- [ ] Scorecards live for **≥ 6 benchmark jurisdictions** with median cycle times by permit class and year, volume trends, and a confidence tier per §5.1 — every figure traceable to a MANIFEST-recorded source extract.
- [ ] Fit checker + checklist working for **2 asset types** (multifamily, small commercial) across all playbook jurisdictions; every checklist item carries a citation link to an official source.
- [ ] Signal feed contains **≥ 100 extracted board items** from **≥ 3 NJ municipalities**; extraction precision **≥ 0.90** on the 30-item gold set (§5.4) for `action` and `use_type` fields.
- [ ] Delay monitor backtested on historical data (§5.5) and running weekly via GitHub Actions.
- [ ] Landing + pricing pages present the spec's positioning, clearly marked "demonstration".
- [ ] Every page shows the §5.6 disclaimer; deployed on Cloudflare Pages; CI green.

---

## 2. Deviations from the source spec (deliberate — do not "fix" back)

| Spec says | This build does | Why |
|---|---|---|
| Buy data from BatchData, Shovels.ai, Zoneomics | Open municipal permit data + curated public rules + own LLM extraction | Zero budget; the spec itself says the moat is normalization/extraction — we demonstrate exactly that layer |
| Nationwide coverage ambition | 6–10 benchmark cities + 3–5 NJ deep-dive municipalities | The spec's own GTM: "narrow geography and asset type" wedge |
| SaaS billing, seats, SSO, enterprise API | Static demo; pricing page is illustrative; no auth | Out of scope for a portfolio demo (§3.2) |
| "Basic AI assistant" (Starter tier) | Not built; noted on pricing page as roadmap | Scope control; the AI budget goes to the signal feed where it proves more |

---

## 3. Scope contract

### 3.1 In scope (v1)

Modules M1–M5 (§5); the marketing shell (landing, pricing, methods); weekly automated data refresh; JSON export of scorecards and signals; owner-only alert email.

### 3.2 Out of scope (hard)

Accounts/auth/billing; paid data sources; nationwide scope; legal-advice features; scraping anything behind logins or paywalls; automated filing/submission; a chatbot; real-time anything.

### 3.3 Stretch (after Phase 6)

Zoning-fit map layer for NJ deep-dive towns (public zoning GIS); resubmittal-loop metrics where status histories allow; a third asset type.

---

## 4. Jurisdictions & data sources

### 4.1 Benchmark jurisdictions (open permit records — Phase 0 verifies, need ≥ 6 passing)

Candidates: **NYC** (DOB permit issuance datasets), **Philadelphia** (L&I permits), **Chicago**, **Boston**, **Seattle**, **Austin**, **San Francisco**, **Washington DC**, **Los Angeles**, **Mesa AZ**. Pass criteria: bulk/API access (Socrata/CKAN/ArcGIS open data); fields including filing/application date **and** issuance date; permit type/class; ≥ 3 years of history; ≥ 200 relevant permits/yr. Record pass/fail + field mappings in `RECON.md`.

### 4.2 NJ deep-dive municipalities (playbooks + signal feed — need ≥ 3 passing)

Candidates: Jersey City, Hoboken, New Brunswick, Princeton, Montclair, Morristown, Westfield. Pass criteria: planning/zoning board agendas & minutes published on the municipal site as text-searchable HTML/PDF with stable URLs; land-use application requirements published. NJ chosen for the fragmented-process narrative (spec's wedge) and owner familiarity.

### 4.3 Source table

| # | Dataset | Access | Fallback |
|---|---|---|---|
| J1 | Permit records per benchmark city | Socrata/CKAN/ArcGIS APIs (app tokens optional, free) | bulk CSV downloads |
| J2 | NJ board agendas/minutes | Polite fetch per §6.4 | manual download by owner |
| J3 | Official permit requirements/fee schedules per jurisdiction | Official municipal pages/PDFs (cited in playbooks) | — (no citation → item cannot ship) |
| J4 | NJ zoning GIS (stretch) | Municipal/NJOGIS open data | omit |

MANIFEST rules as in the owner's other projects: `data/MANIFEST.json` entry per artifact `{name, source_url, retrieved_utc, sha256, license_note}`; raw data gitignored; processed, size-budgeted artifacts committed.

---

## 5. Modules (LOCKED definitions)

### 5.1 M1 — Jurisdiction scorecards

Per jurisdiction × permit class (crosswalk each city's permit types into shared classes: `new-construction-res`, `new-construction-com`, `alteration-major`, `alteration-minor`, `demolition`, `site/civil`; mapping table per city committed and cited): median and p25/p75 **days from filing to issuance**, annual volume, trend (3-yr slope), and review-stage visibility where status logs exist. **Confidence tier** (locked): A = ≥3 yrs + ≥200/yr + status history; B = ≥3 yrs + ≥50/yr; C = anything less (shown with caveat). Exclude records with negative/zero durations or > 5 yrs (log exclusion rate; if > 15%, flag data quality on the scorecard).

### 5.2 M2 — Project fit checker

Input: jurisdiction, asset type (multifamily | small-commercial), scale band, scope flags (new build / addition / change of use / site work). Output: likely permit path (ordered permits + reviews), hearing likelihood (by-right vs variance-likely — heuristic from playbook rules), dependencies, and the M1 benchmark for each step where data exists. Driven entirely by **playbook YAML** (§5.3) — no hidden logic.

### 5.3 M3 — Jurisdiction playbooks & dynamic checklists (the curated core)

`playbooks/{jurisdiction}.yaml`: permit types, triggering conditions, submission requirements (each with `citation:` URL to an official source — **required field, build fails without it**), review bodies, hearing triggers, typical sequence. The dynamic checklist is compiled from the playbook filtered by the fit-checker inputs, grouped by stage, printable. Playbooks are authored with LLM assistance but every playbook carries `verified: true|false`; unverified playbooks render with a prominent "draft — not yet verified" banner. Only the owner flips `verified` to true.

### 5.4 M4 — Planning/zoning signal feed (LLM extraction)

Pipeline: fetch (§6.4) → text extraction (pdfplumber; OCR out of scope — skip image-only PDFs, log count) → LLM structured extraction via the **Anthropic API** (select the current Sonnet-tier model at build time from docs.claude.com; never hardcode a guessed model id) → schema validation → publish. Extraction schema per item: `{meeting_date, board, case_ref?, applicant_type, project_desc, use_type, action: approved|denied|carried|heard|withdrawn, variances_mentioned[], source_url, confidence}`. Items failing schema validation are dropped and counted, never patched by hand.
**Gold set:** 30 hand-labeled items (built in Phase 4 from real minutes, labels justified by quoted text). Gate: precision ≥ 0.90 on `action` and `use_type`; below gate → iterate prompts/few-shots, re-run eval; never ship below gate. **Cost cap:** ≤ $10/month API spend; batch weekly; `ANTHROPIC_API_KEY` is an owner-provided secret, never committed.

### 5.5 M5 — Delay alerts

Per jurisdiction × permit class, weekly: `median_90d` (rolling last 90 days of issued permits' cycle times) vs `median_baseline` (trailing 365 days excluding the last 90). **Alert when ratio ≥ 1.25 and n_90d ≥ 20.** Backtest requirement (Phase 6): run the rule over the full history and include the resulting historical alert timeline on the jurisdiction page — this both validates the rule and gives the demo something to show. Delivery: in-app feed + **owner email only** (no external recipients, ever, without owner action).

### 5.6 Honesty rules & disclaimer (verbatim; restyle only)

Every metric shows source + vintage + confidence tier. No number may appear that cannot be traced to a MANIFEST extract or a cited playbook line. Footer on every page:

> **Demonstration product.** Jurisdiction Intelligence OS is a portfolio project built entirely from public records. Benchmarks are estimates from published permit data; requirements summaries are curated from official sources and may be outdated. Nothing here is legal advice or a substitute for confirming requirements with the jurisdiction.

---

## 6. Architecture & stack

### 6.1 Shape

Python pipeline (batch + weekly Actions) → DuckDB working store → **small committed JSON artifacts** → static React app. Jurisdiction-level data is tiny; no backend and no runtime API calls — fully static.

### 6.2 Stack (LOCKED)

Python 3.11+ (`uv`): `requests`, `pandas`, `duckdb`, `pydantic` (schemas), `anthropic`, `pdfplumber`, `jinja2`, `pytest`, `ruff`. Web: Vite + React 18 + TypeScript strict + Tailwind v4 (owner's standard), Cloudflare Pages; charts via recharts. Scheduler: GitHub Actions — `refresh.yml` weekly (Mon 09:00 UTC: permits refresh → scorecards → delay rule) and `signals.yml` weekly (Tue: fetch minutes → extract → publish). Public repo.

### 6.3 Committed artifact contracts (`web/public/data/`)

`jurisdictions.json` (registry + confidence tiers) · `scorecards/{slug}.json` (M1 metrics by class × year) · `playbooks/{slug}.json` (compiled from YAML) · `signals.json` (validated feed items, newest first) · `alerts.json` (delay-rule history) · `meta.json` (vintages, extract dates, model + prompt version used for extraction). Budget: any file ≤ 500 KB.

### 6.4 Collection ethics (NON-NEGOTIABLE)

Respect robots.txt; identify with a UA string containing the owner's contact email; ≥ 5 s between requests per host; cache everything (never refetch unchanged docs — ETag/Last-Modified or content hash); public documents only; stop fetching any host that returns 403/429 and log it; no logins, no paywalls; strip personal names of private individuals from published extractions (`project_desc` must describe the project; board members acting as public officials may be named in raw data but published items reference the board, not individuals).

---

## 7. Web application spec

Pages: **Landing** (spec's product summary/positioning) · **Scorecards** (compare table across jurisdictions; per-jurisdiction detail with trends, stage visibility, alert history) · **Fit Checker** (form → permit path result) · **Checklist** (per jurisdiction × asset type, printable, citations) · **Signals** (filterable feed) · **Pricing** (spec's tier table, watermarked "illustrative") · **Methods & Data** (sources, crosswalks, extraction eval results incl. gold-set precision, §5.6 disclaimer). WCAG 2.2 AA; responsive; confidence/status never color-only.

---

## 8. Repository

**Location (LOCKED):** `C:\Users\abdul\projects\jurisdiction-os` (local disk, never Google Drive). Public GitHub repo `jurisdiction-os`. This Drive folder (`7. JURISDICTION INTELLIGENCE OS\`) holds the spec, this guide, and case-study assets only.

```
jurisdiction-os/
├── OPERATING_GUIDE.md  PROGRESS.md  RECON.md  README.md
├── pipeline/            # Python package + tests/ + fixtures/
├── playbooks/           # {jurisdiction}.yaml (curated, cited)
├── eval/                # gold_set.jsonl + eval runner + results history
├── data/                # raw/ (gitignored), MANIFEST.json
├── web/                 # Vite app; public/data/ artifacts committed
└── .github/workflows/   # refresh.yml, signals.yml, ci.yml
```

Conventions as the owner's other repos: `ruff`, strict TS, conventional commits, `main` protected by CI.

---

## 11. Phased build plan

| Phase | Work | Exit criteria (gates) |
|---|---|---|
| **0. Bootstrap + recon** | Repo, envs, CI skeleton; verify §4.1 candidates (≥6 pass) and §4.2 candidates (≥3 pass); field mappings | `RECON.md` complete; jurisdiction set locked + logged |
| **1. Permit ETL** | J1 fetchers, class crosswalks, DuckDB store, MANIFEST | All benchmark cities ingested ≥ 3 yrs; exclusion rates logged |
| **2. Scorecards** | M1 metrics + confidence tiers + artifacts | §5.1 gates; numbers spot-checked against 5 hand-computed cases per city |
| **3. Playbooks + fit/checklist** | 2 asset types × NJ deep-dive set (+ one benchmark city for contrast); M2/M3 compile + UI logic | Every item cited; unverified banner works; fit checker returns coherent paths for 6 test scenarios |
| **4. Signal feed** | Fetcher (§6.4), extraction, schema validation, gold set + eval | ≥ 100 valid items; eval ≥ 0.90 precision gate met; cost within cap |
| **5. Web app** | All pages §7, deployed preview | §7 complete; a11y checks pass |
| **6. Delay alerts + automation** | M5 rule + backtest + both workflows live | Backtest timeline rendered; two consecutive scheduled runs green |
| **7. Hardening + launch** | Perf, tests, README, portfolio assets (§14) | All §1.4 boxes checked; production URL live |

---

## 12. Testing & verification

Pipeline: pytest on crosswalk mappings, duration math (5 hand-verified cases per city committed as fixtures), confidence tiers, delay rule (synthetic series with a known slowdown → must alert; stable series → must not). Extraction: schema validation on every item; eval runner against gold set, results committed to `eval/results/`; any prompt or model change requires re-running eval (CI enforces: `meta.json` prompt version must match latest eval result). Web: lint, typecheck, build, Playwright smoke (each page renders; fit checker returns a path; signals filter works), axe zero serious violations. Weekly workflows: failure notifies owner.

---

## 13. Instructions for coding agents

### 13.1 Session protocol

Guide → spec (voice only) → `PROGRESS.md` → env check (`git status` clean, `uv sync`, `pnpm install`) → one phase → phase tests → PROGRESS entry → commit, push.

### 13.2 Decision rules (apply without asking)

Dead portal/API → fallback in §4.3; candidate city fails recon → next candidate; ambiguous permit-type mapping → nearest class + note in the committed crosswalk; extraction below gate → iterate prompt (log attempts), never lower the gate; a playbook fact without an official citation → leave it out; anything visual unspecified → owner's portfolio design language.

### 13.3 Never change without owner approval

Module definitions and constants (§5.1 tiers, §5.5 rule constants, §5.4 precision gate and cost cap); disclaimer wording (§5.6); collection-ethics rules (§6.4); jurisdiction set after Phase 1; the deviations table (§2); stack; repo location; playbook `verified` flags.

### 13.4 Prohibited at all times

Fabricating or interpolating any metric or extraction; publishing unvalidated extractions; scraping in violation of §6.4; presenting the demo as an operating business or its numbers as guarantees; committing keys or raw scraped documents; emailing anyone but the owner; force-pushing `main`.

### 13.5 PROGRESS.md format

Dated entries, newest first: **Done / Decisions / ⚠ Deviations / Next**. Never delete entries.

---

## 14. Portfolio integration

Flagship for **Data Engineering & Applied AI** (`/data-ai/`). Phase 7: save to `7. JURISDICTION INTELLIGENCE OS\case-study-assets\`: screenshots (scorecard compare, fit-checker result, signal feed, eval results table), the gold-set precision figure, a ≤90 s walkthrough recording, and draft `CASE_STUDY.md` (problem → data → method → eval → product framing → limitations). The eval-gated LLM pipeline is the case study's centerpiece — lead with it.

---

## 15. Glossary

**Entitlement** — discretionary approvals (zoning, site plan, variances) before building permits. **By-right** — permitted without discretionary hearings. **Permit cycle time** — filing→issuance duration; the core benchmark. **Expediter** — consultant who navigates permitting for applicants. **Playbook** — this project's curated, cited YAML of a jurisdiction's rules. **Gold set** — hand-labeled evaluation sample gating the LLM extractor. **Socrata/CKAN** — common open-data portal platforms with APIs.

---

*End of guide. When in doubt: §13.2. When a number lacks a source: it doesn't ship.*
