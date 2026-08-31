# Jurisdiction Intelligence OS — Progress Log

Newest entry on top. Never delete entries. Format per OPERATING_GUIDE.md §13.5:
Done / Decisions / ⚠ Deviations / Next.

---

## 2026-08-31 — Phase 5: web app (agent: sonnet-5) — §1.4 gate PASSES, deployed to production

**Done:**
- Built all 7 §7 pages: Landing, Scorecards (compare table + recharts per-jurisdiction detail,
  tier badges), Fit Checker (playbook-driven, draft banner), Checklist (printable, `window.print()`),
  Signals (filterable feed, `ACTION_COLORS` badges paired with text labels per WCAG 2.2 AA — never
  color-only), Pricing (illustrative watermark), Methods & Data.
- Methods & Data page fulfills the binding owner decision from the prior entry: discloses the
  84.6% action-field precision figure, the 96.2% use_type figure, the 3-round iteration history
  (73.3% → 80.8% → 84.6%), and the specific unresolved failure pattern (long technical testimony
  over-inferred as "approved" absent an actual vote) — plus confidence-tier-A unreachability,
  Princeton's image-only-PDF exclusion, the 4-of-10 benchmark-city recon rejections, and the §5.6
  disclaimer verbatim. The Signals page itself also carries an inline pointer to this disclosure.
- `npm install`, `tsc -b` (clean), `vite build` (clean; one non-blocking chunk-size advisory on the
  recharts bundle — noted, not fixed, out of scope for this phase).
- Verified all 7 routes with real data via the Browser pane dev server (no console errors, no
  network failures) and again against the deployed production URL directly (deep-link `/methods`
  and `/signals` both return **200** from Cloudflare Pages' SPA routing, not a 404 shell — data
  fetches confirmed 200 too).
- Spot-checked light mode + mobile (375×812) — nav wraps correctly, no horizontal overflow.
- Deployed to Cloudflare Pages: `jurisdiction-os` project created, `wrangler pages deploy dist`
  → https://jurisdiction-os.pages.dev (live).

**Decisions (§13.2):** none new this phase — executing the prior entry's binding requirement.

**Next:** Phase 6 — delay alerts (M5 rule + backtest) + GitHub Actions automation
(`refresh.yml`, `signals.yml`).

---

## 2026-08-31 — Owner decision: signal-feed precision gap documented, not force-closed

Owner reviewed the Phase 4 precision-gate shortfall (84.6% action precision vs. the 90% gate,
prior entry) and chose: **document the gap and proceed to Phase 5**, rather than building a
two-pass classifier or trying a stronger model first. `signals.json` ships as-is (117 items,
3 municipalities, item-count gate met).

**Decisions (§13.2):** the 84.6% figure (and the specific 4-case failure pattern: long
technical testimony over-inferred as "approved" with no actual vote present) must be disclosed
on the Methods & Data page (§7) when Phase 5 builds it, alongside the gold-set eval methodology
itself — not quietly omitted. `eval/results/20260831_final_v3.json` is the canonical figure to
cite.

**Next:** Phase 5 — web app.

---

## 2026-08-31 — Phase 4: signal feed (agent: sonnet-5) — §1.4 item count gate PASSES, §5.4 precision gate does NOT

**Done:**
- Provider selection (owner-directed deviation, previously logged): tested NVIDIA's free tier
  live against 4 different model IDs, all failed (2 reached end-of-life 2026-08-26, 2 returned
  account-scoped 404s) — not a hypothetical, an actual attempted live call each time. GPT-4o-mini
  extracted the real schema correctly on the first try. Locked GPT-4o-mini; `pyproject.toml`'s
  `anthropic` dependency swapped for `openai`.
- Fetch (§6.4): discovered real minutes documents live per municipality (browser-driven, not
  guessed URL patterns) for all 4 locked NJ municipalities. **Princeton's minutes are genuinely
  image-only** (confirmed: pdfplumber extracted zero text across all pages of 2 sample
  documents) — excluded per §5.4's own "OCR out of scope" rule, not fixed. **Westfield**
  (a RECON.md-logged fallback candidate) substitutes in — confirmed live to publish real,
  extractable text on the identical CivicPlus platform Princeton uses, proving this is a
  town-specific publishing practice, not a platform limitation. Final locked set: Hoboken,
  Montclair, Westfield (32 documents fetched, all real, ~1.25M characters).
- **A real data-hygiene catch**: the initial Westfield discovery pulled every "Minutes" link off
  its combined AgendaCenter page (all town boards/commissions, not just Planning/Zoning) — 4 of
  16 URLs turned out to be Westfield Recreation Commission minutes, confirmed by reading each
  document's own header, not assumed from the URL. Removed before extraction, not left to fail
  silently on schema validation.
- **A real, significant extraction bug found and fixed**: the original prompt asked the model to
  "infer the meeting date from context if not restated" per chunk. For Hoboken's 325-page,
  13-chunk transcript, only chunk 1 carries the document's own date header — every later chunk
  fabricated a plausible but entirely invented date (multiple "2023" dates that appear literally
  zero times anywhere in a transcript of a 2026 meeting, confirmed via direct text search).
  Fixed by parsing the true meeting date once per document (from its own header) and passing it
  explicitly into every chunk's prompt, never left for the model to guess.
- **A related, still-partial limitation, documented not silently ignored**: the same long-document
  chunking causes a single real case to be re-extracted once per chunk that discusses it (Hoboken's
  HOP-26-3 restaurant case was extracted 5 times across different chunks, only 1 of which carried
  the case_ref needed for within-document dedup). A dedup step keyed on case_ref was added and
  catches same-chunk-cycle duplicates, but cross-chunk duplicates lacking a repeated case_ref
  aren't caught — logged as a known limitation for a future session (a content-similarity or
  address-based dedup key would close this), not fixed in this pass.
- **§1.4 item-count gate PASSES**: 117 valid items, 3 municipalities (need >=100 items, >=3
  municipalities). 10-21 items dropped per run for schema validation failure (never patched by
  hand, per §5.4). Cost: ~$0.08 total, comfortably under the $10/month cap.
- **§5.4 precision gate: 30-item gold set built, hand-verified against real quoted source text
  (not derived from the model's own output) — 8 of 30 were confirmed real LLM errors, not a
  hypothetical adversarial set.** Ran the mandatory 3-round iteration the guide itself
  anticipates ("below gate → iterate prompts/few-shots, re-run eval"):
  - v1 (original prompt): **73.3% action precision** — FAIL. Two clear error patterns: (1)
    "APPROVAL EXTENSION" and hearing-postponement items defaulting to "heard" instead of
    "approved"/"carried"; (2) long testimony-only excerpts over-inferred as "approved" with no
    actual vote present.
  - v2 (explicit extension/postponement rules added): **80.8%** — fixed pattern (1) entirely.
  - v3 (worked few-shot example + mechanical "find the literal vote sentence" instruction added):
    **84.6%** — fixed one more case, but 4 persist, all sharing the same trait: long, detailed,
    technical testimony (traffic studies, parking counts, expert witnesses) with genuinely no
    vote in the excerpt, which the model keeps reading as an implied approval despite three
    rounds of increasingly explicit and mechanical instruction against doing exactly that.
  - **Gate does not pass (84.6% < 90% on `action`; `use_type` passes at 96.2%).** Per §5.4's own
    rule ("never ship below gate"), `signals.json` is published with the item-count gate met but
    the precision gate is explicitly NOT claimed as passing — this progress entry and
    `eval/results/20260831_final_v3.json` are the honest record, not a quiet pass.

**Decisions (§13.2):** did not attempt a 4th prompt-only iteration given three consecutive
rounds plateaued on the identical 4 cases — the likely real fix is architectural (a second,
narrowly-scoped classifier pass asking only "is there an explicit vote sentence for this case in
this excerpt, yes/no" instead of asking one model call to both extract and judge the outcome),
which is a real scope/cost increase to the pipeline, not a prompt tweak, so it's flagged for the
owner rather than built without a decision on it.

**⚠ Deviations / open items:**
- **§5.4's precision gate is not met.** This is the one gate in the entire project so far that
  genuinely fails after real, good-faith iteration, not a data-source limitation logged and
  accepted (like Princeton's image-only PDFs or Chicago's missing res/com split in the earlier
  permit-ETL phase). Owner input needed on how to proceed: accept a second-pass classifier
  architecture change, accept the 84.6% figure with the gap documented on the Methods page
  instead of silently claiming 90%, or hold Phase 4 here pending further work.
- Cross-chunk duplicate extraction (same case re-extracted without a repeated case_ref) is a
  known, logged gap in the dedup logic, not corrected in this pass.
- Jersey City (one of the 4 originally locked NJ municipalities) was not used for the signal feed
  — its Planning-Board-specific document list lives behind a dynamically-populated iframe that
  proved hard to enumerate programmatically within this phase's time budget. The >=3 municipality
  gate is still met via Hoboken/Montclair/Westfield.

**Next:** Phase 4 is functionally built and the item-count gate passes, but the precision gate
needs an owner decision before this phase can be marked fully done. Phase 5 (web app) and Phase
6 (delay alerts + automation) don't strictly depend on signal-feed precision to proceed, so
autonomous work can continue there while this is pending, if the owner prefers.

---

## 2026-08-31 — Phase 3: playbooks + fit/checklist (agent: sonnet-5)

**Done:**
- 5 playbooks (`playbooks/{slug}.yaml`): the 4 locked NJ deep-dive municipalities (Jersey City,
  Hoboken, Princeton, Montclair) + NYC as the one benchmark city for contrast, per §11 Phase 3's
  own scope ("+ one benchmark city"). Every fact researched live and cited to a real official
  source (NJ statutes via nj.gov/justia.com; municipal code via Municode/eCode360; NYC via
  nyc.gov/site/planning) — no fabricated or interpolated content (§13.4).
- **Real, jurisdiction-specific findings surfaced during research, not generic boilerplate per
  town**: Princeton has a dedicated "AH-3" district where multifamily is a *principal permitted
  use* (by-right, not variance-dependent) — a genuine by-right pocket distinct from its own
  general variance-likely default. Montclair has a purpose-built "R-3 Garden Group Zone" for
  multifamily plus a standalone Chapter 213 with real multifamily-specific standards (screening,
  lighting) and a lighter-weight "minor site plan" track via its Development Review Committee.
  Jersey City's site plan review applies citywide across all zones *and* Redevelopment Plan
  areas, not just conventional zoning districts. NYC's own zoning is confirmed to vary
  block-to-block with no town-wide by-right default to lean on, unlike the NJ towns — its
  playbook says so explicitly rather than implying a false certainty.
- `30_playbooks.py`: compiles YAML -> the §6.3 artifact contract (`playbooks/{slug}.json`),
  enforcing §5.3's hard citation gate (every submission requirement needs a real URL — the
  script raises `SystemExit(1)` if any are missing, not a warning) and runs the fit-checker
  logic (§5.2) against 6 test scenarios.
- **Both Phase 3 gates pass**: citation gate (5/5 playbooks, every requirement cited) and
  fit-checker coherence (6/6 test scenarios return a real permit path + hearing likelihood +
  review body + checklist, deliberately covering the by-right pockets and the non-NJ contrast
  city, not 6 near-identical NJ multifamily cases).

**Decisions (§13.2):** every playbook ships `verified: false` — per §5.3's own design, this is
the *intended* state for LLM-assisted drafts pending owner review, not a gap to close in this
phase. Where per-zone dimensional detail (setbacks, FAR, etc.) wasn't resolved to a specific
parcel/zone in this research pass, the playbook says so explicitly (e.g. Jersey City's
Redevelopment-Plan-area dependency, NYC's block-to-block variation) rather than asserting a
generic default as if it were verified fact — matching §13.4's prohibition on fabricating or
interpolating content, applied to *omission* honesty as much as citation honesty.

**⚠ Deviations / open items:** none — this phase's own scope (playbooks + fit-checker
mechanics) is complete; deeper per-zone dimensional research is explicitly deferred to the
owner's own review pass before flipping any `verified` flag, per §13.3 ("playbook `verified`
flags" is owner-only, never an agent decision).

**Next:** Phase 4 — signal feed (LLM extraction from NJ planning-board minutes). Needs the
owner-directed LLM provider decision (already logged above) resolved to a specific model before
building the extraction pipeline.

---

## 2026-08-31 — Phase 2: scorecards (agent: sonnet-5)

**Done:**
- `20_scorecards.py`: per city x shared-class, computes median/p25/p75 cycle-time days, annual
  volume, 3-yr trend slope (least-squares over available years), and confidence tier. Writes
  the §6.3 artifact contract: `jurisdictions.json` (registry) + `scorecards/{slug}.json` per city.
- **Gate passed: 6/6 jurisdictions have at least one scored class** (§1.4's own floor). Coverage
  varies by city per Phase 1's already-documented data gaps: Austin and SF have all 6 classes,
  LA has 6, Seattle 5/6, Chicago 4/6, NYC only 3/6 (its ~3.8% job-type-classification coverage
  means several classes never accumulate enough matched records to report).
- **Spot-checked 3 hand-computed cases against the script's own output, all exact matches**:
  Austin new-construction-res (n=12,674, median=68.0 days), Seattle demolition (n=1,547,
  median=91 days), San Francisco alteration-major (n=5,232, median=250.0 days) — computed
  independently via raw SQL + Python's own `sorted()`/median arithmetic, not re-running the
  same code path, to catch a shared bug the script's own logic might reproduce identically
  across cities.
- Data-quality flag (§5.1: "if >15% exclusion, flag data quality on the scorecard") correctly
  fires for Chicago, San Francisco, and Los Angeles — matching Phase 1's own documented findings
  (SF's OTC-permit mix, LA's missing-date gap, Chicago's high express/easy-permit share).

**Decisions (§13.2):** **Confidence tier A is not reachable by this pipeline at all** — §5.1
defines tier A as needing "status history" (per-permit review-stage timestamps) on top of the
volume/years thresholds, and none of Phase 1's 6 sources provide that in a normalized
cross-city form. Every jurisdiction x class caps at tier B (≥3yrs + ≥50/yr) or C. Disclosed
directly in `jurisdictions.json`'s own top-level note, not silently omitted — a real, permanent
scope boundary of this pipeline, not a bug to fix in a later phase.

**⚠ Deviations / open items:** the 4-year fetch window's first (2022) and last (2026) calendar
years are both partial (cutoff mid-year, and 2026 only through today), so `annual_volume` and
`trend_slope_per_year` treat two non-comparable partial years the same as three full ones —
noted here for Phase 5's web app to label partial years explicitly rather than a pipeline fix,
since the underlying per-permit dates themselves are correct either way.

**Next:** Phase 3 — playbooks + fit/checklist (2 asset types x NJ deep-dive set + one benchmark
city, per §11). This phase is qualitatively different from Phases 0-2: it needs real research
into each jurisdiction's actual zoning/permitting rules with an official citation on every
checklist item (§5.3: "citation: URL to an official source -- required field, build fails
without it"), not just data-pipeline work.

---

## 2026-08-31 — Phase 1: permit ETL, all 6 cities (agent: sonnet-5)

**Done:**
- `crosswalks.py`: per-city permit-type -> shared-class mapping, built from real sampled
  permit-type value distributions pulled live from each dataset (not a generic national
  taxonomy) — every mapping decision cites the actual observed counts.
- `10_permit_etl.py`: fetches the last 4 years, classifies, computes filing->issuance duration,
  applies the §5.1 exclusion rule, writes to a DuckDB working store (`data/jurisdiction_os.duckdb`).
- **All 6 cities ingested, ~1.2M permit rows total:**

  | City | Rows | Excluded | Unmapped | Note |
  |---|---|---|---|---|
  | NYC | 649,150 | 10.1% | 96.2% | see classification-gap note below |
  | Chicago | 132,472 | 36.2% | 5.2% | no res/com split available (RECON.md) |
  | Austin | 47,812 | 8.3% | 0.6% | cleanest of the 6 |
  | San Francisco | 95,387 | 55.0% | 0.4% | see OTC-permit note below |
  | Seattle | 24,290 | 14.3% | 9.0% | |
  | Los Angeles | 253,707 | 49.0% | 0.0% | see missing-date note below |

- **Three real, investigated findings, not glossed over:**
  1. **San Francisco's 55% exclusion is correct behavior, not a bug**: 98.6% of its exclusions
     are §5.1's own "non-positive duration" rule firing on genuine same-day "over-the-counter"
     permits (`filed_date == issued_date`) — confirmed by inspecting real excluded rows before
     assuming anything was wrong. A 0-day duration is definitionally uninteresting for
     cycle-time benchmarking, so excluding it is the guide's own intended behavior; SF's permit
     mix is just unusually OTC-heavy. Flagged for the scorecard's own data-quality note (§5.1: "if
     > 15% [exclusion], flag data quality") rather than "fixed."
  2. **Los Angeles's 49% exclusion is a real, dataset-wide data-completeness gap**: confirmed
     directly against the live API (not just this ETL's own filtered subset) that 161,897 of
     LA's full 408,174-row dataset (39.7%) have a NULL `submitted_date` — LA itself doesn't
     always publish a filing date, not a fetch defect.
  3. **NYC's job-type classification only covers ~3.8% of records** (24,903 of 649,150): the
     join to the companion "Job Application Filings" dataset needed for job_type genuinely
     doesn't cover most permits — spot-checked several unmatched job_filing_numbers directly
     against the filings API and got zero results, ruling out a formatting bug. Most plausibly,
     the filings dataset only tracks jobs requiring formal plan-review, not self-certified ones.
     Documented as a real, honest limitation (same category as Chicago's res/com gap) rather
     than papered over with an unreliable proxy — NYC's per-class scorecard breakdown will only
     be as complete as this 3.8%; its aggregate cycle-time distribution is unaffected.
- **Two real bugs caught and fixed during this phase, not a clean run:**
  1. NYC returned 0 rows on the first attempt: `BENCHMARK_CITIES["NYC"]["datasets"]` listed the
     out-of-window legacy dataset (2007-2020) first, and the ETL script took `datasets[0]`
     positionally — silently fetching the wrong dataset. Fixed by removing the dead legacy
     entry rather than trusting index order (see `jos_lib.py`'s own note for the full story).
  2. `--force` unconditionally deleted the *entire* DuckDB file regardless of `--city`, so a
     `--city NYC --force` re-run to fix bug #1 silently wiped out the other 5 already-loaded
     cities' data along with it — caught by a post-hoc sanity query ("why does the DB only have
     NYC now") rather than assumed fine because NYC's own numbers looked right. Fixed so
     `--force` only ever re-fetches the city/cities actually named on that run.
- `MANIFEST.json`: one entry per city with source URL, retrieval timestamp, row count.

**Decisions (§13.2):** ambiguous permit-type mappings default to the *more conservative* class
where no severity signal exists (e.g. NYC DOB NOW's undifferentiated "Alteration" and Chicago's
"RENOVATION/ALTERATION" both default to alteration-major, not alteration-minor) — a documented
approximation, not a precision claim, logged in `crosswalks.py` itself at the point of the choice.

**⚠ Deviations / open items:** NYC's per-class breakdown coverage (~3.8%) and Chicago's missing
res/com split are real, permanent limitations of these cities' own published data, not scoped to
be fixed later — carried forward into Phase 2's scorecards as documented confidence/coverage
caveats, not chased further.

**Next:** Phase 2 — scorecards (§5.1 metrics + confidence tiers per city × class × year).

---

## 2026-08-31 — Owner deviation: LLM provider for §5.4 (logged, not yet built)

**⚠ Deviation from §6.2's locked stack (owner-directed, not an agent decision):** the guide
locks `anthropic` for §5.4's extraction module. Owner instructed using a free/cheap provider
instead — NVIDIA API, GPT-4o-mini, or a free OpenRouter model, in that preference order, keys
already available in a `.env` (copied into this repo's own gitignored `.env`, values never
read/logged by the agent, only confirmed present: `NVIDIA_API_KEY`, `OPENAI_API_KEY`,
`OPENROUTER_API_KEY`). The exact provider/model choice is deferred to Phase 4 itself (verified
live against the gold-set precision gate then, not guessed now) — Phases 1-3 don't need this at
all. `pipeline/pyproject.toml`'s `anthropic` dependency will be swapped for `openai` (all three
candidate providers are OpenAI-API-compatible) when Phase 4 starts.

---

## 2026-08-31 — Phase 0: bootstrap + recon (agent: sonnet-5)

Owner selected this as the next portfolio project (after NJ Hazard Vulnerability Dashboard).
Repo bootstrapped fresh at the guide's locked location; every candidate jurisdiction verified
live via direct API/page checks, not assumed from the guide's own candidate list or general
knowledge of these cities' open-data reputations.

**Done:**
- Repo structure per §8: `pipeline/` (+ `tests/fixtures/`), `playbooks/`, `eval/results/`,
  `data/raw/` (gitignored), `web/`, `.github/workflows/`. `.gitignore`/`.gitattributes` adapted
  from the owner's other projects; `pyproject.toml` with the guide's locked stack
  (`requests`, `pandas`, `duckdb`, `pydantic`, `anthropic`, `pdfplumber`, `jinja2`); `uv sync` clean.
- `jos_lib.py`: same cached/retried-HTTP pattern as the owner's other projects, plus §6.4's
  collection-ethics pacing (5s/host throttle, 403/429 = stop-and-log) built into `get_json`
  itself rather than left to each caller to remember.
- **§4.1 benchmark cities: 6/10 candidates pass** (need ≥6) — NYC, Chicago, Austin, San
  Francisco, Seattle, Los Angeles. All verified via each Socrata dataset's own metadata
  endpoint (column schema), not row-sampling — row-sampling produced one real false negative
  (Seattle: `applieddate`/`issueddate` didn't appear in a sampled row because Socrata's SODA
  API omits null-valued fields per row; the metadata endpoint confirmed both fields exist in
  the schema) that would have wrongly rejected a real pass if not caught.
- **4 of the 5 rejected cities fail for the identical reason**, not four unrelated problems:
  Philadelphia, Boston, DC, and Mesa all publish permit *issuance* (and sometimes completion)
  dates but never a genuine filing/application date — confirmed via each platform's full
  column schema (Carto `SELECT *`, CKAN's own CSV header, ArcGIS's field list), not assumed
  from an incomplete sample. DC's `CREATED_DATE` looked like a plausible filing-date proxy
  until checked against real sampled records: it was byte-identical across every row, an
  ETL/batch-load timestamp for the GIS layer refresh, not a per-permit date — caught by
  querying real records rather than trusting the field name.
- LA needed two attempts: the first candidate dataset found (`bi25-emib`) had no filing date
  in its schema either; a second, newer dataset (`Building and Safety – Building Permits
  Issued from 2020 to Present`, `pi9x-tg5x`) does, and became the locked source.
- **§4.2 NJ municipalities: 4/4 checked pass** (need ≥3) — Jersey City (CivicWeb), Hoboken
  (IQM2), Princeton (CivicPlus AgendaCenter), Montclair (custom CMS). Stopped at 4 rather than
  checking all 7 candidates — comfortably past the gate; the remaining 3 (New Brunswick,
  Morristown, Westfield) are logged as fallback in `RECON.md` if any of the 4 develops access
  friction once Phase 4's actual fetcher runs against it.
- `00_recon.py`: re-runnable verification script, not just a one-time investigation — re-checks
  every locked source live and regenerates `RECON.md` on each run. All 10 locked sources
  (6 cities' datasets + 4 municipality portals) confirmed live on the actual script run, not
  just during ad-hoc investigation.

**Decisions (§13.2):** locked exactly 6 benchmark cities (the gate minimum) rather than padding
the set further — the 4 rejected candidates all fail on a real, verified data-quality gap
(no filing date), not a fixable access problem, so adding more candidates from outside the
guide's own list wasn't warranted given 6 clean passes were found within it.

**⚠ Deviations / open items:** none. Every §4.1/§4.2 gate met with real margin (NJ) or exactly
at the floor (cities, but for a verified structural reason, not a shortfall in effort).

**Next:** Phase 1 — permit ETL (`J1` fetchers for the 6 locked cities, class crosswalks,
DuckDB store, MANIFEST). Needs `ANTHROPIC_API_KEY` eventually (Phase 4 only, not yet).

---
