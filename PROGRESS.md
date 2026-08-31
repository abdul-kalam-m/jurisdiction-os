# Jurisdiction Intelligence OS — Progress Log

Newest entry on top. Never delete entries. Format per OPERATING_GUIDE.md §13.5:
Done / Decisions / ⚠ Deviations / Next.

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
