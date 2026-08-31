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

EVAL_DIR = __import__("pathlib").Path(__file__).resolve().parent
GOLD_SET = EVAL_DIR / "gold_set.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
PRECISION_GATE = 0.90


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
        "model": "gpt-4o-mini",
        "prompt_version": "v2-explicit-meeting-date",  # bumped after the meeting_date fabrication fix
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
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
