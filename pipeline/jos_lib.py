"""Shared helpers for the Jurisdiction Intelligence OS pipeline
(OPERATING_GUIDE.md §6). Same discipline as the owner's other portfolio
projects: cached, retried HTTP so every stage is idempotent; verify live,
don't trust a platform's documentation. Collection ethics (§6.4, NON-
NEGOTIABLE) are enforced here, not left to each caller to remember.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        pass

import requests

PIPELINE_DIR = Path(__file__).resolve().parent
REPO = PIPELINE_DIR.parent
RAW = REPO / "data" / "raw"
MANIFEST = REPO / "data" / "MANIFEST.json"
PLAYBOOKS = REPO / "playbooks"
WEB_DATA = REPO / "web" / "public" / "data"
EVAL_DIR = REPO / "eval"

OWNER_EMAIL = "ar.abdulkalam.mustaq@gmail.com"
UA = f"jurisdiction-os/1.0 (portfolio project; {OWNER_EMAIL})"
HEADERS = {"User-Agent": UA}

# §6.4 collection ethics -- non-negotiable, applies to §4.2 municipal
# fetches (agendas/minutes). §4.1 benchmark-city open-data APIs are
# public bulk/API endpoints, not the kind of polite-crawl target this
# pacing is aimed at, but the cache-everything rule applies everywhere.
MIN_SECONDS_BETWEEN_REQUESTS_PER_HOST = 5.0
_last_request_time: dict[str, float] = {}


def _cache_path(url: str, params: dict | None) -> Path:
    key = url + "?" + json.dumps(params or {}, sort_keys=True)
    h = hashlib.sha256(key.encode()).hexdigest()[:24]
    return RAW / "_http_cache" / f"{h}.json"


def _throttle(url: str) -> None:
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    now = time.time()
    last = _last_request_time.get(host, 0.0)
    wait = MIN_SECONDS_BETWEEN_REQUESTS_PER_HOST - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_request_time[host] = time.time()


def get_json(url: str, params: dict | None = None, force: bool = False,
             retries: int = 3, timeout: int = 60, backoff_base: float = 1.5,
             throttle: bool = False) -> dict | list:
    """Cached, retried GET returning parsed JSON. `throttle=True` for §4.2
    municipal-site fetches (§6.4's 5s/host pacing); benchmark-city open-data
    APIs (§4.1) don't need it -- they're built for bulk API traffic."""
    cpath = _cache_path(url, params)
    if cpath.exists() and not force:
        return json.loads(cpath.read_text(encoding="utf-8"))
    last: Exception | None = None
    for attempt in range(retries):
        try:
            if throttle:
                _throttle(url)
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if r.status_code in (403, 429):
                raise RuntimeError(f"HTTP {r.status_code} from {url} -- per §6.4, stop fetching this host")
            r.raise_for_status()
            data = r.json()
            cpath.parent.mkdir(parents=True, exist_ok=True)
            cpath.write_text(json.dumps(data), encoding="utf-8")
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(backoff_base * (attempt + 1))
    raise RuntimeError(f"GET JSON failed after {retries}: {url} params={params}: {last}")


def check_url(url: str, params: dict | None = None, timeout: int = 30) -> dict:
    """Non-raising status probe for recon -- returns status info instead of
    throwing, since Phase 0's job is to find out what's actually reachable."""
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        return {"ok": r.status_code == 200, "status_code": r.status_code}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status_code": None, "detail": str(e)}


def manifest_add(name: str, source_url: str, local_path: Path | None,
                  license_note: str, extra: dict | None = None) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    entry = {
        "source_url": source_url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "license_note": license_note,
    }
    if local_path is not None and local_path.exists():
        entry["sha256"] = hashlib.sha256(local_path.read_bytes()).hexdigest()
        entry["local_path"] = str(local_path.relative_to(REPO))
    if extra:
        entry.update(extra)
    data[name] = entry
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --- §4.1 benchmark cities (LOCKED after Phase 0, §13.3) --------------------
# Socrata dataset ids verified live in Phase 0 (RECON.md) -- schema pulled
# from each dataset's own metadata endpoint, not inferred from a sampled
# row (Socrata's SODA API omits null-valued fields per row, which produced
# one false negative during recon, caught before locking this set).
BENCHMARK_CITIES: dict[str, dict] = {
    "NYC": {
        "platform": "socrata", "domain": "data.cityofnewyork.us",
        "datasets": [
            {"id": "ipu4-2q9a", "name": "DOB Permit Issuance (legacy BIS, 2007-2020)",
             "filed_field": "filing_date", "issued_field": "issuance_date", "type_field": "permit_type"},
            {"id": "rbx6-tga4", "name": "DOB NOW: Build - Approved Permits (current)",
             "filed_field": "approved_date", "issued_field": "issued_date", "type_field": "work_type"},
        ],
    },
    "CHICAGO": {
        "platform": "socrata", "domain": "data.cityofchicago.org",
        "datasets": [{"id": "ydr8-5enu", "name": "Building Permits",
                      "filed_field": "application_start_date", "issued_field": "issue_date",
                      "type_field": "permit_type"}],
    },
    "AUSTIN": {
        "platform": "socrata", "domain": "data.austintexas.gov",
        "datasets": [{"id": "3syk-w9eu", "name": "Issued Construction Permits",
                      "filed_field": "applieddate", "issued_field": "issue_date",
                      "type_field": "permit_type_desc"}],
    },
    "SAN FRANCISCO": {
        "platform": "socrata", "domain": "data.sfgov.org",
        "datasets": [{"id": "i98e-djp9", "name": "Building Permits",
                      "filed_field": "filed_date", "issued_field": "issued_date",
                      "type_field": "permit_type_definition"}],
    },
    "SEATTLE": {
        "platform": "socrata", "domain": "data.seattle.gov",
        "datasets": [{"id": "76t5-zqzr", "name": "Building Permits",
                      "filed_field": "applieddate", "issued_field": "issueddate",
                      "type_field": "permitclassmapped"}],
    },
    "LOS ANGELES": {
        "platform": "socrata", "domain": "data.lacity.org",
        "datasets": [{"id": "pi9x-tg5x", "name": "Building and Safety - Permits Issued 2020-Present",
                      "filed_field": "submitted_date", "issued_field": "issue_date",
                      "type_field": "permit_type"}],
    },
}

# §4.2 NJ deep-dive municipalities (locked, §13.3). Meeting-portal platform
# per municipality -- confirmed live in Phase 0, exact per-board URL/scrape
# path is a Phase 4 concern (§6.4's polite-fetch rules apply there).
NJ_MUNICIPALITIES: dict[str, dict] = {
    "JERSEY CITY": {"platform": "civicweb", "url": "https://cityofjerseycity.civicweb.net/portal/"},
    "HOBOKEN": {"platform": "iqm2", "url": "https://hobokennj.iqm2.com/Citizens/Board/1017-Planning-Board"},
    "PRINCETON": {"platform": "civicplus_agendacenter", "url": "https://www.princetonnj.gov/AgendaCenter/Planning-Board-14/"},
    "MONTCLAIR": {"platform": "custom_cms", "url": "https://www.montclairnjusa.org/Government/Advisory-Committee-Boards-and-Commissions/Planning-Board/Minutes-Video"},
}


def socrata_resource_url(domain: str, dataset_id: str) -> str:
    return f"https://{domain}/resource/{dataset_id}.json"
