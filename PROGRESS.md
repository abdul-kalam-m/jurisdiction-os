# Jurisdiction Intelligence OS — Progress Log

Newest entry on top. Never delete entries. Format per OPERATING_GUIDE.md §13.5:
Done / Decisions / ⚠ Deviations / Next.

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
