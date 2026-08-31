#!/usr/bin/env python3
"""Gold-set eval runner (OPERATING_GUIDE.md §5.4). Gate: precision >= 0.90
on `action` and `use_type` fields, independently. Every gold label in
gold_set.jsonl was hand-verified against the real source excerpt (not
re-derived from the model's own output) -- 8 of 30 are documented
mismatches found by that verification, not a hypothetical adversarial set.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
GOLD_SET = EVAL_DIR / "gold_set.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
LATEST_POINTER = RESULTS_DIR / "LATEST"
PRECISION_GATE = 0.90

# Import the extraction script's own PROMPT_VERSION rather than
# hardcoding a copy here -- an earlier version of this file hardcoded
# "v2-explicit-meeting-date" and it silently went stale once the prompt
# moved to v3, which is exactly the drift §12's CI check exists to catch.
sys.path.insert(0, str(EVAL_DIR.parent / "pipeline"))
import importlib
extract_mod = importlib.import_module("41_extract_signals")
PROMPT_VERSION = extract_mod.PROMPT_VERSION
MODEL = extract_mod.MODEL


def main() -> int:
    items = [json.loads(line) for line in GOLD_SET.read_text(encoding="utf-8").splitlines() if line.strip()]
    n = len(items)
    action_correct = sum(1 for i in items if i["action_correct"])
    use_type_correct = sum(1 for i in items if i["use_type_correct"])
    action_precision = action_correct / n
    use_type_precision = use_type_correct / n

    print(f"Gold set: {n} items (hand-labeled, justified by quoted source text)")
    print(f"action precision:   {action_correct}/{n} = {action_precision:.3f} "
          f"({'PASS' if action_precision >= PRECISION_GATE else 'FAIL'}, gate {PRECISION_GATE})")
    print(f"use_type precision: {use_type_correct}/{n} = {use_type_precision:.3f} "
          f"({'PASS' if use_type_precision >= PRECISION_GATE else 'FAIL'}, gate {PRECISION_GATE})")

    print("\nMismatches (action):")
    for i in items:
        if not i["action_correct"]:
            print(f"  {i['municipality']} {i['case_ref']} ({i['meeting_date']}): "
                  f"LLM said '{i['llm_action']}', gold is '{i['gold_action']}'")
    print("\nMismatches (use_type):")
    for i in items:
        if not i["use_type_correct"]:
            print(f"  {i['municipality']} {i['case_ref']} ({i['meeting_date']}): "
                  f"LLM said '{i['llm_use_type']}', gold is '{i['gold_use_type']}'")

    passed = action_precision >= PRECISION_GATE and use_type_precision >= PRECISION_GATE
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "n_gold_items": n,
        "action_precision": round(action_precision, 4),
        "use_type_precision": round(use_type_precision, 4),
        "gate": PRECISION_GATE,
        "passed": passed,
    }
    result_path = RESULTS_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {result_path}")
    print(f"\nOverall: {'PASS' if passed else 'FAIL'} -- {'never ship below gate' if not passed else 'meets §5.4 gate'}")

    # This run's own result is NOT auto-promoted to LATEST -- the eval set
    # here is pre-labeled correctness flags in gold_set.jsonl (built by
    # hand-verifying real extraction output against source text), not a
    # live re-extraction, so a mechanical re-run of this script produces
    # the *same* numbers as last time unless gold_set.jsonl itself was
    # re-annotated for a genuinely new prompt/model run. Promoting LATEST
    # is a deliberate, logged step (see PROGRESS.md) -- not silently
    # automatic here.
    print(f"\nNote: LATEST currently points to "
          f"{LATEST_POINTER.read_text(encoding='utf-8').strip() if LATEST_POINTER.exists() else '(unset)'} "
          f"-- update it by hand if this run supersedes that one.")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
