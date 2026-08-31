#!/usr/bin/env python3
"""10 -- Permit ETL (OPERATING_GUIDE.md §11 Phase 1). Fetches the last
LOOKBACK_YEARS of permits for each of the 6 locked benchmark cities,
classifies every record into the shared crosswalk classes (§5.1), computes
filing->issuance duration, applies the exclusion rule (negative/zero or
>5yr duration, §5.1), and writes everything to a DuckDB working store.

NYC needs two datasets joined (RECON.md/jos_lib.py already document why:
the current "DOB NOW: Build" permits dataset has no job-type field of its
own -- that lives in a companion "Job Application Filings" dataset, joined
by job_filing_number). Its own legacy 2007-2020 dataset is skipped
entirely for this ETL window: DOB NOW alone spans 2016-2026 (confirmed
live), more than covering LOOKBACK_YEARS with margin, so the join
complexity of also blending in the legacy dataset buys nothing here.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

import crosswalks as xw
import duckdb
import jos_lib as lib
import pandas as pd

LOOKBACK_YEARS = 4
PAGE_SIZE = 50000
DB_PATH = lib.REPO / "data" / "jurisdiction_os.duckdb"


def cutoff_date() -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=365 * LOOKBACK_YEARS)
    return dt.strftime("%Y-%m-%dT00:00:00")


def fetch_socrata_paginated(domain: str, dataset_id: str, select_fields: list[str],
                             date_field: str | None, cutoff: str | None,
                             extra_where: str | None = None) -> list[dict]:
    """`date_field=None` fetches the whole dataset unfiltered -- used for
    NYC's Job Application Filings table (86,130 rows total, far smaller
    than the Approved Permits table it's joined to, since one job filing
    can spawn many separate trade permits): filtering it by filing_date
    against the *permits*' cutoff window is the wrong filter entirely --
    a permit issued within the window can trace back to a filing made
    years earlier, so a date-filtered fetch massively undercounted joins
    (12,558 of the permits' own 649,150 rows matched a filing on the
    first attempt; fetching this whole, genuinely small table instead
    fixes the join without needing a wider but still-arbitrary cutoff)."""
    url = lib.socrata_resource_url(domain, dataset_id)
    select = ",".join(select_fields)
    where = f"{date_field} >= '{cutoff}'" if date_field else None
    if extra_where:
        where = f"({where}) AND ({extra_where})" if where else extra_where
    order_field = date_field or select_fields[0]
    rows: list[dict] = []
    offset = 0
    while True:
        params = {"$select": select, "$order": order_field, "$limit": PAGE_SIZE, "$offset": offset}
        if where:
            params["$where"] = where
        page = lib.get_json(url, params=params, timeout=120, retries=3)
        if not page:
            break
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def _parse_date(v: str | None) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def classify_row(city: str, ds_cfg: dict, row: dict) -> tuple[str | None, str]:
    """Returns (shared_class or None, raw_type_value) for one row, applying
    the city's own crosswalk + res/com split logic (crosswalks.py)."""
    crosswalk_name = ds_cfg.get("crosswalk")
    type_field = ds_cfg.get("type_field")
    raw_type = row.get(type_field, "") if type_field else ""
    if not crosswalk_name:
        return None, raw_type

    crosswalk = getattr(xw, crosswalk_name)
    base_class = crosswalk.get(raw_type)
    if base_class != "new-construction":
        return base_class, raw_type

    # Split new-construction into -res/-com per city's own available signal.
    if city == "NYC":
        is_res = row.get("residential") == "YES"
        return ("new-construction-res" if is_res else "new-construction-com"), raw_type
    if city == "NYC_FILINGS":
        try:
            units = int(float(row.get("proposed_dwelling_units") or 0))
        except ValueError:
            units = 0
        return ("new-construction-res" if units > 0 else "new-construction-com"), raw_type
    if city == "AUSTIN":
        cls = row.get("permit_class_mapped")
        return ("new-construction-res" if cls == "Residential" else "new-construction-com"), raw_type
    if city == "SEATTLE":
        cls = row.get("permitclass")
        if cls in xw.SEATTLE_RESIDENTIAL_CLASSES:
            return "new-construction-res", raw_type
        if cls in xw.SEATTLE_COMMERCIAL_CLASSES:
            return "new-construction-com", raw_type
        return None, raw_type  # Vacant Land / N/A -- not a real new-construction record, log unmapped rather than guess
    if city == "LOS ANGELES":
        use_desc = (row.get("use_desc") or "").lower()
        is_res = any(k in use_desc for k in xw.LA_RESIDENTIAL_KEYWORDS)
        return ("new-construction-res" if is_res else "new-construction-com"), raw_type
    if city == "SAN FRANCISCO":
        existing = (row.get("existing_use") or "").lower()
        proposed = (row.get("proposed_use") or "").lower()
        res_keywords = ("family", "apartment", "dwelling", "residential")
        is_res = any(k in existing or k in proposed for k in res_keywords)
        return ("new-construction-res" if is_res else "new-construction-com"), raw_type
    if city == "CHICAGO":
        return None, raw_type  # documented gap (RECON.md/crosswalks.py) -- no res/com signal available, logged not guessed
    return base_class, raw_type


def process_city(city: str, cfg: dict, con: duckdb.DuckDBPyConnection, cutoff: str) -> dict:
    ds = cfg["datasets"][0]
    select_fields = [ds["filed_field"], ds["issued_field"], ds["id_field"]]
    if ds.get("type_field"):
        select_fields.append(ds["type_field"])
    select_fields += ds.get("extra_fields", [])
    select_fields = [f for f in dict.fromkeys(select_fields) if f]  # dedupe, drop Nones

    print(f"  Fetching {city} ({ds['name']})...")
    rows = fetch_socrata_paginated(ds["domain"] if "domain" in ds else cfg["domain"], ds["id"],
                                    select_fields, ds["issued_field"], cutoff,
                                    ds.get("where_extra"))
    print(f"    {len(rows)} rows fetched")

    # NYC needs a job_type join from the companion filings dataset.
    job_type_by_filing: dict[str, tuple[str, dict]] = {}
    if city == "NYC":
        filings_cfg = lib.BENCHMARK_CITIES["NYC_FILINGS"]
        fcfg = filings_cfg["datasets"][0]
        print(f"  Fetching NYC_FILINGS ({fcfg['name']}) for job_type join -- whole table, not date-filtered...")
        ffields = [fcfg["filed_field"], fcfg["id_field"], fcfg["type_field"]] + fcfg.get("extra_fields", [])
        frows = fetch_socrata_paginated(filings_cfg["domain"], fcfg["id"], ffields, None, None)
        print(f"    {len(frows)} filing rows fetched")
        for fr in frows:
            key = fr.get(fcfg["id_field"])
            if key:
                job_type_by_filing[key] = (fcfg["type_field"], fr)

    n_total = len(rows)
    n_excluded = 0
    n_unmapped = 0
    classified = []
    for row in rows:
        filed = _parse_date(row.get(ds["filed_field"]))
        issued = _parse_date(row.get(ds["issued_field"]))

        if city == "NYC":
            fr = job_type_by_filing.get(row.get(ds["id_field"]))
            shared_class, raw_type = (None, None)
            if fr:
                _, filing_row = fr
                shared_class, raw_type = classify_row("NYC_FILINGS", lib.BENCHMARK_CITIES["NYC_FILINGS"]["datasets"][0], filing_row)
                filed = filed or _parse_date(filing_row.get("filing_date"))
        else:
            shared_class, raw_type = classify_row(city, ds, row)

        if shared_class is None:
            n_unmapped += 1

        duration_days = (issued - filed).days if (filed and issued) else None
        excluded = False
        exclusion_reason = None
        if duration_days is not None:
            if duration_days <= 0:
                excluded, exclusion_reason = True, "non-positive duration"
            elif duration_days > 365 * 5:
                excluded, exclusion_reason = True, "duration > 5 years"
        else:
            excluded, exclusion_reason = True, "missing filed or issued date"
        if excluded:
            n_excluded += 1

        classified.append({
            "city": city, "permit_id": str(row.get(ds["id_field"], "")),
            "filed_date": filed, "issued_date": issued, "duration_days": duration_days,
            "shared_class": shared_class, "raw_type": raw_type,
            "excluded": excluded, "exclusion_reason": exclusion_reason,
        })

    if classified:
        df = pd.DataFrame(classified)[["city", "permit_id", "filed_date", "issued_date", "duration_days",
                                        "shared_class", "raw_type", "excluded", "exclusion_reason"]]
        con.execute("INSERT INTO permits SELECT * FROM df")

    exclusion_rate = round(n_excluded / n_total, 4) if n_total else 0.0
    unmapped_rate = round(n_unmapped / n_total, 4) if n_total else 0.0
    return {"city": city, "n_total": n_total, "n_excluded": n_excluded, "exclusion_rate": exclusion_rate,
            "n_unmapped": n_unmapped, "unmapped_rate": unmapped_rate}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", help="Comma-separated city names, or omit for all 6.")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cities = ([c.strip().upper() for c in args.city.split(",")] if args.city
              else [c for c in lib.BENCHMARK_CITIES if not c.endswith("_FILINGS")])

    # --force re-fetches only the cities named on this run (or all 6 if
    # --city was omitted) -- it must NEVER drop the whole database file,
    # which would silently wipe out every other already-loaded city. This
    # was a real bug once: `DB_PATH.unlink()` ran unconditionally on
    # --force regardless of --city, and a `--city NYC --force` re-run
    # deleted all 5 other cities' already-fetched data along with it,
    # caught only by a post-hoc "why does the DB only have NYC now" check.
    lib.REPO.joinpath("data").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("""
        CREATE TABLE IF NOT EXISTS permits (
            city VARCHAR, permit_id VARCHAR, filed_date TIMESTAMP, issued_date TIMESTAMP,
            duration_days INTEGER, shared_class VARCHAR, raw_type VARCHAR,
            excluded BOOLEAN, exclusion_reason VARCHAR
        )
    """)

    cutoff = cutoff_date()
    print(f"Cutoff date (last {LOOKBACK_YEARS} years): {cutoff}\n")

    results = []
    for city in cities:
        if args.force or con.execute("SELECT count(*) FROM permits WHERE city = ?", [city]).fetchone()[0] == 0:
            con.execute("DELETE FROM permits WHERE city = ?", [city])
            r = process_city(city, lib.BENCHMARK_CITIES[city], con, cutoff)
            results.append(r)
            print(f"  {city}: {r['n_total']} total, {r['n_excluded']} excluded ({r['exclusion_rate']:.1%}), "
                  f"{r['n_unmapped']} unmapped ({r['unmapped_rate']:.1%})\n")
            lib.manifest_add(f"permits_{city.lower().replace(' ', '_')}", ds_url_for(city), None,
                              "Public open-data portal, city government", extra={"row_count": r["n_total"]})
        else:
            print(f"  {city}: [cached]\n")

    print("\nGate check (§11 Phase 1: 'all cities ingested >=3yrs; exclusion rates logged'):")
    for r in results:
        flag = "OK" if r["exclusion_rate"] < 0.5 else "HIGH EXCLUSION -- investigate"
        print(f"  {r['city']}: {flag}")

    con.close()
    return 0


def ds_url_for(city: str) -> str:
    ds = lib.BENCHMARK_CITIES[city]["datasets"][0]
    domain = ds.get("domain") or lib.BENCHMARK_CITIES[city]["domain"]
    return lib.socrata_resource_url(domain, ds["id"])


if __name__ == "__main__":
    sys.exit(main())
