#!/usr/bin/env python3
"""§12 CI enforcement: `web/public/data/meta.json`'s recorded signals
prompt_version must match `eval/results/LATEST`'s prompt_version. If they
diverge, the currently-shipped extraction prompt has moved since the last
committed eval run -- i.e. the gold-set precision figure on the Methods &
Data page may no longer describe what's actually running. Run after
41_extract_signals.py in signals.yml (and locally before committing a
prompt change) via `uv run python check_prompt_version.py`.
"""
from __future__ import annotations

import json
import sys

import jos_lib as lib

EVAL_RESULTS = lib.EVAL_DIR / "results"
LATEST_POINTER = EVAL_RESULTS / "LATEST"


def main() -> int:
    if not lib.META_JSON.exists():
        print(f"META CHECK SKIPPED: {lib.META_JSON} does not exist yet "
              f"(41_extract_signals.py hasn't run in this environment). Not a failure.")
        return 0
    if not LATEST_POINTER.exists():
        print(f"FATAL: {LATEST_POINTER} does not exist -- no canonical eval result is designated.")
        return 1

    meta = json.loads(lib.META_JSON.read_text(encoding="utf-8"))
    signals_meta = meta.get("signals")
    if not signals_meta:
        print("META CHECK SKIPPED: meta.json has no 'signals' section yet. Not a failure.")
        return 0

    latest_result_name = LATEST_POINTER.read_text(encoding="utf-8").strip()
    latest_result = json.loads((EVAL_RESULTS / latest_result_name).read_text(encoding="utf-8"))

    shipped = signals_meta["prompt_version"]
    evaluated = latest_result["prompt_version"]
    if shipped != evaluated:
        print(f"FATAL: meta.json's shipped prompt_version ({shipped!r}) does not match "
              f"{latest_result_name}'s evaluated prompt_version ({evaluated!r}). "
              f"The Methods & Data page's precision figure no longer describes what's running -- "
              f"re-run eval/eval_runner.py against the new prompt, promote its result to "
              f"eval/results/LATEST, and update the Methods & Data page's disclosed figures "
              f"before shipping.")
        return 1

    print(f"OK: meta.json signals.prompt_version ({shipped!r}) matches "
          f"{latest_result_name} ({evaluated!r}), action_precision={latest_result['action_precision']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
