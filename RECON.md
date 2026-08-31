# RECON — Phase 0

Every source below was checked live against the real API/page (not assumed from documentation or general knowledge) — schema pulled from each platform's own metadata endpoint where possible, not inferred from a single sampled row (Socrata's SODA API omits null-valued fields per row, which produced one false negative below, caught and corrected before locking the set).

## §4.1 Benchmark jurisdictions — locked set, re-verified live on every recon run

| City | Datasets | Status |
|---|---|---|
| **NYC** | DOB Permit Issuance (legacy BIS, 2007-2020) (3990194 rows); DOB NOW: Build - Approved Permits (current) (992002 rows) | ✅ OK |
| **CHICAGO** | Building Permits (845825 rows) | ✅ OK |
| **AUSTIN** | Issued Construction Permits (2373161 rows) | ✅ OK |
| **SAN FRANCISCO** | Building Permits (1294665 rows) | ✅ OK |
| **SEATTLE** | Building Permits (192660 rows) | ✅ OK |
| **LOS ANGELES** | Building and Safety - Permits Issued 2020-Present (408174 rows) | ✅ OK |

### Rejected candidates (from the original Phase 0 investigation, not re-verified — out of scope once rejected, §13.3)

| City | Platform | Why rejected |
|---|---|---|
| Philadelphia | Carto (phl.carto.com) | `permits` table (932,588 rows) has `permitissuedate` only -- no filing/application date field exists anywhere in its ~48-column schema (confirmed via SELECT *, not row-sampling). |
| Boston | CKAN (data.boston.gov) | `Approved Building Permits` CSV has `issued_date` only, no filing date, across all 24 columns in the CSV header. |
| Washington DC | ArcGIS (maps2.dcgis.dc.gov) | `Building Permits in {year}` layers have ISSUE_DATE and CREATED_DATE -- CREATED_DATE looked like a plausible filing-date proxy until checked against real data: it's identical across every sampled record (a batch-load/ETL timestamp, not a per-permit date). |
| Mesa AZ | Socrata (data.mesaaz.gov) | `opened_date`/`finaled_date` turn out to be issuance/completion, not filing/issuance -- per the dataset's own description, `permit_year` = "the year the permit was issued", matching opened_date's year in every sample. |

**Pattern worth remembering**: four of the five rejected cities fail for the *same* reason — their public permit feed tracks issuance (and sometimes completion) but not the original filing/application date. This isn't a fetch or access problem, it's what these cities actually publish.

## §4.2 NJ deep-dive municipalities — locked set, re-verified live on every recon run

| Municipality | Platform | URL | Status |
|---|---|---|---|
| **JERSEY CITY** | civicweb | https://cityofjerseycity.civicweb.net/portal/ | ✅ OK |
| **HOBOKEN** | iqm2 | https://hobokennj.iqm2.com/Citizens/Board/1017-Planning-Board | ✅ OK |
| **PRINCETON** | civicplus_agendacenter | https://www.princetonnj.gov/AgendaCenter/Planning-Board-14/ | ✅ OK |
| **MONTCLAIR** | custom_cms | https://www.montclairnjusa.org/Government/Advisory-Committee-Boards-and-Commissions/Planning-Board/Minutes-Video | ✅ OK |

3 more candidates (New Brunswick, Morristown, Westfield) are available as fallback if any of the 4 locked municipalities develops access friction once Phase 4's fetcher runs against it for real.

## Anthropic API note (for Phase 4, not needed yet)

§5.4's LLM extraction module needs an owner-provided `ANTHROPIC_API_KEY` (never committed, §6.4/§13.4) and "the current Sonnet-tier model at build time from docs.claude.com, never hardcode a guessed model id" — to be selected when Phase 4 actually starts, not now.