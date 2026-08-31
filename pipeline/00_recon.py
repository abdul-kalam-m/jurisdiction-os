#!/usr/bin/env python3
"""00 -- Phase 0 recon (OPERATING_GUIDE.md §11). Re-verifies the LOCKED
§4.1/§4.2 sets are still live and structurally sound, and regenerates
RECON.md -- the rejected-candidates investigation (why Philadelphia,
Boston, DC, and Mesa failed) is preserved as static reference data below
rather than re-derived every run, since re-litigating already-rejected
candidates on every recon pass would just repeat work with no decision
left to make; the locked sets ARE re-verified live, every run, since
those are what the rest of the pipeline actually depends on.
"""
from __future__ import annotations

import sys

import jos_lib as lib

RECON_MD = lib.REPO / "RECON.md"

# Preserved from the original Phase 0 investigation -- not re-verified
# every run (out of scope once rejected, §13.3 locks the set), but kept
# here so a future session doesn't waste time re-investigating the same
# dead ends. See each entry's note for the specific reason.
REJECTED_CANDIDATES = [
    ("Philadelphia", "Carto (phl.carto.com)",
     "`permits` table (932,588 rows) has `permitissuedate` only -- no filing/application "
     "date field exists anywhere in its ~48-column schema (confirmed via SELECT *, not "
     "row-sampling)."),
    ("Boston", "CKAN (data.boston.gov)",
     "`Approved Building Permits` CSV has `issued_date` only, no filing date, across all "
     "24 columns in the CSV header."),
    ("Washington DC", "ArcGIS (maps2.dcgis.dc.gov)",
     "`Building Permits in {year}` layers have ISSUE_DATE and CREATED_DATE -- CREATED_DATE "
     "looked like a plausible filing-date proxy until checked against real data: it's "
     "identical across every sampled record (a batch-load/ETL timestamp, not a per-permit date)."),
    ("Mesa AZ", "Socrata (data.mesaaz.gov)",
     "`opened_date`/`finaled_date` turn out to be issuance/completion, not filing/issuance -- "
     "per the dataset's own description, `permit_year` = \"the year the permit was issued\", "
     "matching opened_date's year in every sample."),
]


def verify_benchmark_city(city: str, cfg: dict) -> dict:
    results = []
    for ds in cfg["datasets"]:
        url = lib.socrata_resource_url(cfg["domain"], ds["id"])
        try:
            # $limit=1 fetch is kept for its live-verification side effect
            # (confirms the endpoint actually returns row data, not just a
            # count) -- the rows themselves aren't otherwise needed here.
            _ = lib.get_json(url, params={"$limit": 1}, throttle=False)
            count_resp = lib.get_json(url, params={"$select": "count(*)"}, throttle=False)
            n = int(count_resp[0]["count"]) if count_resp else 0
            results.append({"dataset": ds["name"], "id": ds["id"], "ok": True, "row_count": n,
                             "filed_field": ds["filed_field"], "issued_field": ds["issued_field"]})
        except Exception as e:  # noqa: BLE001
            results.append({"dataset": ds["name"], "id": ds["id"], "ok": False, "error": str(e)})
    return {"city": city, "datasets": results, "all_ok": all(r["ok"] for r in results)}


def verify_nj_municipality(name: str, cfg: dict) -> dict:
    status = lib.check_url(cfg["url"])
    return {"municipality": name, "url": cfg["url"], "platform": cfg["platform"], **status}


def main() -> int:
    print("Verifying locked §4.1 benchmark cities...")
    city_results = [verify_benchmark_city(c, cfg) for c, cfg in lib.BENCHMARK_CITIES.items()]
    n_city_ok = sum(1 for r in city_results if r["all_ok"])
    for r in city_results:
        status = "OK" if r["all_ok"] else "FAIL"
        print(f"  [{status}] {r['city']}: {r['datasets']}")

    print("\nVerifying locked §4.2 NJ municipalities...")
    muni_results = [verify_nj_municipality(m, cfg) for m, cfg in lib.NJ_MUNICIPALITIES.items()]
    n_muni_ok = sum(1 for r in muni_results if r["ok"])
    for r in muni_results:
        print(f"  [{'OK' if r['ok'] else 'FAIL'}] {r['municipality']} ({r['platform']}): {r['url']}")

    print(f"\nBenchmark cities: {n_city_ok}/{len(city_results)} live (need >=6 locked, have "
          f"{len(lib.BENCHMARK_CITIES)} locked)")
    print(f"NJ municipalities: {n_muni_ok}/{len(muni_results)} live (need >=3 locked, have "
          f"{len(lib.NJ_MUNICIPALITIES)} locked)")

    write_recon_md(city_results, muni_results)
    print(f"\nWrote {RECON_MD}")

    ok = n_city_ok == len(city_results) and n_muni_ok == len(muni_results)
    if not ok:
        print("\nWARNING: at least one locked source is no longer live -- investigate before "
              "advancing (a locked source going dead after Phase 0 needs the same live "
              "re-verification discipline this recon itself used, not a silent skip).")
    return 0 if ok else 1


def write_recon_md(city_results: list[dict], muni_results: list[dict]) -> None:
    lines = [
        "# RECON — Phase 0",
        "",
        "Every source below was checked live against the real API/page (not assumed from "
        "documentation or general knowledge) — schema pulled from each platform's own metadata "
        "endpoint where possible, not inferred from a single sampled row (Socrata's SODA API "
        "omits null-valued fields per row, which produced one false negative below, caught and "
        "corrected before locking the set).",
        "",
        "## §4.1 Benchmark jurisdictions — locked set, re-verified live on every recon run",
        "",
        "| City | Datasets | Status |",
        "|---|---|---|",
    ]
    for r in city_results:
        ds_desc = "; ".join(f"{d['dataset']} ({d.get('row_count', '?')} rows)" for d in r["datasets"])
        lines.append(f"| **{r['city']}** | {ds_desc} | {'✅ OK' if r['all_ok'] else '❌ FAIL — investigate'} |")

    lines += [
        "",
        "### Rejected candidates (from the original Phase 0 investigation, not re-verified — out of scope once rejected, §13.3)",
        "",
        "| City | Platform | Why rejected |",
        "|---|---|---|",
    ]
    for name, platform, reason in REJECTED_CANDIDATES:
        lines.append(f"| {name} | {platform} | {reason} |")

    lines += [
        "",
        "**Pattern worth remembering**: four of the five rejected cities fail for the *same* "
        "reason — their public permit feed tracks issuance (and sometimes completion) but not "
        "the original filing/application date. This isn't a fetch or access problem, it's what "
        "these cities actually publish.",
        "",
        "## §4.2 NJ deep-dive municipalities — locked set, re-verified live on every recon run",
        "",
        "| Municipality | Platform | URL | Status |",
        "|---|---|---|---|",
    ]
    for r in muni_results:
        lines.append(f"| **{r['municipality']}** | {r['platform']} | {r['url']} | "
                     f"{'✅ OK' if r['ok'] else '❌ FAIL'} |")

    lines += [
        "",
        "3 more candidates (New Brunswick, Morristown, Westfield) are available as fallback if "
        "any of the 4 locked municipalities develops access friction once Phase 4's fetcher "
        "runs against it for real.",
        "",
        "## Anthropic API note (for Phase 4, not needed yet)",
        "",
        "§5.4's LLM extraction module needs an owner-provided `ANTHROPIC_API_KEY` (never "
        "committed, §6.4/§13.4) and \"the current Sonnet-tier model at build time from "
        "docs.claude.com, never hardcode a guessed model id\" — to be selected when Phase 4 "
        "actually starts, not now.",
    ]
    RECON_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
