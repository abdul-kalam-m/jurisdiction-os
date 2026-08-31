#!/usr/bin/env python3
"""30 -- Playbooks + fit checker (OPERATING_GUIDE.md §11 Phase 3, modules
M2/M3). Compiles playbooks/{jurisdiction}.yaml into the §6.3 committed
artifact contract (web/public/data/playbooks/{slug}.json), enforcing
§5.3's hard gate ("citation: URL to an official source -- required
field, build fails without it") for every submission requirement, then
runs the fit-checker logic against 6 test scenarios per the Phase 3 exit
criteria ("fit checker returns coherent paths for 6 test scenarios").
"""
from __future__ import annotations

import json
import sys

import yaml

import jos_lib as lib

PLAYBOOKS_DIR = lib.PLAYBOOKS
OUT_DIR = lib.WEB_DATA / "playbooks"

SLUG_MAP = {
    "Jersey City": "jersey-city", "Hoboken": "hoboken", "Princeton": "princeton",
    "Montclair": "montclair", "New York City": "nyc",
}


def load_playbook(path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_citations(pb: dict) -> list[str]:
    """§5.3 hard gate: every submission requirement needs a citation URL.
    Returns a list of violations (empty = passes)."""
    violations = []
    jurisdiction = pb.get("jurisdiction", "?")
    for asset_type, path_data in pb.get("permit_paths", {}).items():
        for i, req in enumerate(path_data.get("submission_requirements", [])):
            if not req.get("citation"):
                violations.append(f"{jurisdiction}/{asset_type}[{i}]: '{req.get('item')}' has no citation")
            elif not req["citation"].startswith("http"):
                violations.append(f"{jurisdiction}/{asset_type}[{i}]: citation '{req['citation']}' is not a URL")
    return violations


def compile_playbooks() -> dict[str, dict]:
    compiled = {}
    all_violations = []
    for path in sorted(PLAYBOOKS_DIR.glob("*.yaml")):
        pb = load_playbook(path)
        violations = validate_citations(pb)
        all_violations.extend(violations)
        slug = SLUG_MAP.get(pb["jurisdiction"], path.stem)
        compiled[slug] = pb

    if all_violations:
        print("FATAL: §5.3 citation gate failed -- build cannot proceed:")
        for v in all_violations:
            print(f"  {v}")
        raise SystemExit(1)
    print(f"Citation gate passed: every submission requirement across {len(compiled)} "
          f"playbooks has a real URL citation.")
    return compiled


def fit_check(compiled: dict, slug: str, asset_type: str) -> dict:
    """M2: jurisdiction + asset_type -> likely permit path, hearing
    likelihood, review body, dependencies -- driven entirely by the
    playbook YAML, no hidden logic (§5.2)."""
    pb = compiled.get(slug)
    if not pb:
        return {"error": f"unknown jurisdiction slug: {slug}"}
    path_data = pb.get("permit_paths", {}).get(asset_type)
    if not path_data:
        return {"error": f"no playbook data for {asset_type} in {pb['jurisdiction']}"}
    return {
        "jurisdiction": pb["jurisdiction"],
        "asset_type": asset_type,
        "verified": pb.get("verified", False),
        "likely_permits": path_data.get("likely_permits", []),
        "hearing_likelihood": path_data.get("hearing_likelihood"),
        "hearing_likelihood_basis": path_data.get("hearing_likelihood_basis"),
        "review_body": path_data.get("review_body"),
        "checklist": path_data.get("submission_requirements", []),
    }


TEST_SCENARIOS = [
    ("jersey-city", "multifamily"),
    ("jersey-city", "small-commercial"),
    ("hoboken", "multifamily"),
    ("princeton", "multifamily"),  # exercises the AH-3 by-right pocket
    ("montclair", "small-commercial"),
    ("nyc", "multifamily"),  # exercises the benchmark-city, non-NJ path
]


def main() -> int:
    compiled = compile_playbooks()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, pb in compiled.items():
        (OUT_DIR / f"{slug}.json").write_text(json.dumps(pb, indent=2), encoding="utf-8")
    print(f"Wrote {len(compiled)} compiled playbooks to {OUT_DIR}")

    print(f"\nRunning {len(TEST_SCENARIOS)} fit-checker test scenarios "
          f"(§11 Phase 3 exit criteria: 'coherent paths for 6 test scenarios')...")
    n_ok = 0
    for slug, asset_type in TEST_SCENARIOS:
        result = fit_check(compiled, slug, asset_type)
        if "error" in result:
            print(f"  [FAIL] {slug}/{asset_type}: {result['error']}")
            continue
        coherent = bool(result["likely_permits"] and result["hearing_likelihood"] and result["checklist"])
        status = "OK" if coherent else "INCOHERENT"
        if coherent:
            n_ok += 1
        print(f"  [{status}] {result['jurisdiction']} / {asset_type}: "
              f"{result['hearing_likelihood']} -- {len(result['checklist'])} checklist items, "
              f"review by {result['review_body']}")

    print(f"\nGate check: {n_ok}/{len(TEST_SCENARIOS)} scenarios returned a coherent path")
    return 0 if n_ok == len(TEST_SCENARIOS) else 1


if __name__ == "__main__":
    sys.exit(main())
