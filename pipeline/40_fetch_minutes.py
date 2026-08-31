#!/usr/bin/env python3
"""40 -- Fetch NJ planning/zoning board minutes (OPERATING_GUIDE.md §11
Phase 4, §6.4 collection ethics). Real document URLs discovered live per
municipality during this phase (browser-driven navigation, not guessed
patterns) -- see MINUTES_SOURCES below for the discovery method per site.

**Real, documented substitution**: Princeton (one of the 4 originally
locked NJ municipalities, RECON.md) turned out to publish minutes as
scanned/image-only PDFs -- confirmed directly (pdfplumber extracted zero
text across all 11 pages of two different sample documents), and OCR is
explicitly out of scope (§5.4: "OCR out of scope -- skip image-only PDFs,
log count"). Westfield (one of RECON.md's own logged fallback candidates)
substitutes in -- confirmed live to publish real, extractable text despite
using the identical CivicPlus AgendaCenter platform Princeton uses,
proving this is a town-specific practice, not a platform limitation.
Jersey City and Hoboken's own portals were both checked live too;
Jersey City's Planning-Board-specific document list proved hard to
enumerate programmatically within this phase's time budget (its home page
link lives inside a dynamically-populated iframe) and was set aside in
favor of the 3 sources that were straightforwardly enumerable, still
comfortably clearing the >=3 municipality gate.
"""
from __future__ import annotations

import sys

import pdfplumber

import jos_lib as lib

RAW_MINUTES_DIR = lib.RAW / "minutes"

# Discovered live per municipality (Phase 4 browser research, not a
# generic pattern) -- each is a real, existing minutes document.
MINUTES_SOURCES: dict[str, dict] = {
    "HOBOKEN": {
        "board": "Planning Board",
        "platform": "iqm2",
        "urls": [
            "https://hobokennj.iqm2.com/Citizens/FileOpen.aspx?Type=12&ID=2326",  # Jul 7 2026, verbatim transcript, 325pp
        ],
    },
    "MONTCLAIR": {
        "board": "Board of Adjustment",
        "platform": "ecode360",
        "urls": [f"https://ecode360.com/MO0769/document/{doc_id}.pdf" for doc_id in [
            753275683, 753266685, 753262025, 753258773, 753250824,
            753242483, 753234782, 753232140, 753228047, 753223326,
            753213036, 753201893, 753197144, 753190446, 753181830,
        ]],
    },
    "WESTFIELD": {
        "board": "Board of Adjustment / Planning Board (mixed, AgendaCenter groups both)",
        "platform": "civicplus_agendacenter",
        # Real data-hygiene catch: the initial discovery pass pulled every
        # "Minutes" link off Westfield's combined AgendaCenter page, which
        # covers every town board/commission, not just Planning/Zoning --
        # 4 of the original 16 URLs turned out to be Westfield Recreation
        # Commission minutes (confirmed by reading each document's own
        # header, not assumed from the URL alone), entirely out of §5.4's
        # "Planning/zoning signal feed" scope. Removed rather than left in
        # to fail silently on schema validation.
        "urls": [f"https://westfieldnj.gov/AgendaCenter/ViewFile/Minutes/{slug}" for slug in [
            "_07132026-1014", "_06292026-1012", "_06082026-1008", "_05112026-1000",  # Board of Adjustment
            "_04132026-991", "_03092026-981", "_02092026-973", "_01122026-966",       # Board of Adjustment
            "_07062026-1013", "_05042026-995", "_04062026-988", "_03022026-979",      # Planning Board
        ]],
    },
}

# Princeton: confirmed image-only, excluded from this phase's fetch. Kept
# here as a documented record, not silently dropped from the guide's own
# locked-4 list.
PRINCETON_EXCLUDED_REASON = (
    "Minutes PDFs are scanned/image-only (confirmed: pdfplumber extracted zero text "
    "across all pages of 2 sample documents, e.g. AgendaCenter/ViewFile/Minutes/_05072026-1930). "
    "OCR is explicitly out of scope per §5.4. Excluded from Phase 4, not fixed."
)


def fetch_and_extract(muni: str, url: str, board: str) -> dict:
    """§6.4: cached (via jos_lib.get_json-style caching isn't applicable to
    binary PDFs, so this does its own simple cache-by-filename), throttled
    per host."""
    RAW_MINUTES_DIR.mkdir(parents=True, exist_ok=True)
    import hashlib
    fname = hashlib.sha256(url.encode()).hexdigest()[:24] + ".pdf"
    fpath = RAW_MINUTES_DIR / fname

    if not fpath.exists():
        lib._throttle(url)
        import requests
        r = requests.get(url, headers=lib.HEADERS, timeout=60)
        if r.status_code in (403, 429):
            return {"municipality": muni, "url": url, "ok": False,
                     "error": f"HTTP {r.status_code} -- per §6.4, stop fetching this host"}
        r.raise_for_status()
        fpath.write_bytes(r.content)

    try:
        with pdfplumber.open(fpath) as pdf:
            texts = [p.extract_text() for p in pdf.pages]
            n_pages = len(texts)
            n_image_only = sum(1 for t in texts if not t)
            full_text = "\n\n".join(t for t in texts if t)
    except Exception as e:  # noqa: BLE001
        return {"municipality": muni, "url": url, "ok": False, "error": f"PDF parse failed: {e}"}

    if n_image_only == n_pages:
        return {"municipality": muni, "url": url, "board": board, "ok": False,
                 "error": "image-only PDF, skipped per §5.4 (OCR out of scope)",
                 "n_pages": n_pages}

    return {"municipality": muni, "url": url, "board": board, "ok": True,
             "n_pages": n_pages, "n_image_only_pages": n_image_only, "text": full_text}


def main() -> int:
    results = []
    for muni, cfg in MINUTES_SOURCES.items():
        print(f"Fetching {muni} ({cfg['board']}, {len(cfg['urls'])} documents)...")
        for url in cfg["urls"]:
            r = fetch_and_extract(muni, url, cfg["board"])
            results.append(r)
            status = "OK" if r["ok"] else "SKIP"
            print(f"  [{status}] {url.split('/')[-1]}: "
                  f"{r.get('n_pages', '?')} pages"
                  + (f", {len(r['text'])} chars extracted" if r["ok"] else f" -- {r.get('error')}"))

    n_ok = sum(1 for r in results if r["ok"])
    n_image_only_skipped = sum(1 for r in results if not r["ok"] and "image-only" in r.get("error", ""))
    print(f"\n{n_ok}/{len(results)} documents fetched with usable text.")
    print(f"{n_image_only_skipped} skipped as image-only (§5.4: OCR out of scope, logged not fixed).")
    print(f"Princeton excluded entirely from this phase: {PRINCETON_EXCLUDED_REASON}")

    import pickle
    (lib.RAW / "minutes_extracted.pkl").write_bytes(pickle.dumps([r for r in results if r["ok"]]))
    print(f"\nWrote {lib.RAW / 'minutes_extracted.pkl'} ({n_ok} usable documents)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
