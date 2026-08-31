#!/usr/bin/env python3
"""20 -- Jurisdiction scorecards (OPERATING_GUIDE.md §11 Phase 2, module M1
per §5.1). Per city x shared-class x year: median/p25/p75 cycle-time days,
annual volume, 3-yr trend, confidence tier. Writes the §6.3 committed
artifact contract: jurisdictions.json (registry) + scorecards/{slug}.json.

Confidence tier note (a real scope decision, not a shortcut): §5.1's tier A
requires "status history" (per-permit review-stage timestamps) on top of
the volume/years thresholds -- none of Phase 1's 6 sources provide that in
a normalized cross-city form, so tier A is genuinely unreachable with this
pipeline's current scope. Every jurisdiction x class caps at B or C. This
is disclosed on the scorecard itself, not silently omitted.
"""
from __future__ import annotations

import json
import sys

import duckdb
import jos_lib as lib

DB_PATH = lib.REPO / "data" / "jurisdiction_os.duckdb"
SCORECARDS_DIR = lib.WEB_DATA / "scorecards"
JURISDICTIONS_JSON = lib.WEB_DATA / "jurisdictions.json"
CLASSES = ["new-construction-res", "new-construction-com", "alteration-major",
           "alteration-minor", "demolition", "site/civil"]

CITY_SLUGS = {
    "NYC": "nyc", "CHICAGO": "chicago", "AUSTIN": "austin",
    "SAN FRANCISCO": "san-francisco", "SEATTLE": "seattle", "LOS ANGELES": "los-angeles",
}


def confidence_tier(n_years: int, avg_per_year: float) -> str:
    # Tier A (needs status history, unavailable this pipeline -- see module docstring)
    if n_years >= 3 and avg_per_year >= 50:
        return "B"
    return "C"


def trend_slope(year_volumes: dict[int, int]) -> float | None:
    """Simple least-squares slope of annual volume over the available
    years -- positive = growing, negative = shrinking. None if <2 years."""
    years = sorted(year_volumes)
    if len(years) < 2:
        return None
    n = len(years)
    mean_x = sum(years) / n
    mean_y = sum(year_volumes[y] for y in years) / n
    num = sum((x - mean_x) * (year_volumes[x] - mean_y) for x in years)
    den = sum((x - mean_x) ** 2 for x in years)
    return round(num / den, 2) if den else None


def compute_city_scorecard(con: duckdb.DuckDBPyConnection, city: str) -> dict:
    total = con.execute("SELECT count(*) FROM permits WHERE city = ?", [city]).fetchone()[0]
    n_excl = con.execute("SELECT count(*) FROM permits WHERE city = ? AND excluded", [city]).fetchone()[0]
    overall_exclusion_rate = round(n_excl / total, 4) if total else 0.0

    classes_out = {}
    for cls in CLASSES:
        rows = con.execute("""
            SELECT extract(year from issued_date) as yr, duration_days
            FROM permits WHERE city = ? AND shared_class = ? AND NOT excluded
        """, [city, cls]).fetchall()
        if not rows:
            classes_out[cls] = {"coverage": "no_data"}
            continue

        durations = sorted(r[1] for r in rows)
        n = len(durations)
        median = durations[n // 2] if n % 2 else (durations[n // 2 - 1] + durations[n // 2]) / 2
        p25 = durations[int(n * 0.25)]
        p75 = durations[min(int(n * 0.75), n - 1)]

        year_volumes: dict[int, int] = {}
        for yr, _ in rows:
            year_volumes[int(yr)] = year_volumes.get(int(yr), 0) + 1
        n_years = len(year_volumes)
        avg_per_year = n / n_years if n_years else 0

        classes_out[cls] = {
            "coverage": "ok",
            "n_permits": n,
            "median_days": round(median, 1),
            "p25_days": p25,
            "p75_days": p75,
            "annual_volume": year_volumes,
            "trend_slope_per_year": trend_slope(year_volumes),
            "n_years": n_years,
            "confidence_tier": confidence_tier(n_years, avg_per_year),
        }

    return {
        "city": city,
        "total_permits_in_window": total,
        "overall_exclusion_rate": overall_exclusion_rate,
        "data_quality_flag": overall_exclusion_rate > 0.15,
        "classes": classes_out,
    }


def main() -> int:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    SCORECARDS_DIR.mkdir(parents=True, exist_ok=True)

    registry = {}
    for city in lib.BENCHMARK_CITIES:
        if city.endswith("_FILINGS"):
            continue
        print(f"Computing scorecard for {city}...")
        card = compute_city_scorecard(con, city)
        slug = CITY_SLUGS[city]
        (SCORECARDS_DIR / f"{slug}.json").write_text(json.dumps(card, indent=2, default=str), encoding="utf-8")

        tiers_present = {c["confidence_tier"] for c in card["classes"].values() if c.get("coverage") == "ok"}
        registry[slug] = {
            "city": city,
            "total_permits_in_window": card["total_permits_in_window"],
            "overall_exclusion_rate": card["overall_exclusion_rate"],
            "data_quality_flag": card["data_quality_flag"],
            "best_confidence_tier": min(tiers_present) if tiers_present else "C",
            "classes_with_data": sorted(c for c, v in card["classes"].items() if v.get("coverage") == "ok"),
        }
        print(f"  {slug}: {card['total_permits_in_window']} permits, "
              f"{len(registry[slug]['classes_with_data'])}/{len(CLASSES)} classes have data, "
              f"data_quality_flag={card['data_quality_flag']}")

    JURISDICTIONS_JSON.write_text(json.dumps({
        "note": "Confidence tier A (status-history-backed) is not reachable by this pipeline's "
                "current data sources -- every jurisdiction caps at B or C. See PROGRESS.md Phase 2.",
        "jurisdictions": registry,
    }, indent=2), encoding="utf-8")
    print(f"\nWrote {JURISDICTIONS_JSON}")

    n_pass = sum(1 for r in registry.values() if r["classes_with_data"])
    print(f"\nGate check (§1.4: 'Scorecards live for >=6 benchmark jurisdictions'): "
          f"{n_pass}/{len(registry)} jurisdictions have at least one scored class")
    con.close()
    return 0 if n_pass >= 6 else 1


if __name__ == "__main__":
    sys.exit(main())
