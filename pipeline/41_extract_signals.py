#!/usr/bin/env python3
"""41 -- LLM structured extraction (OPERATING_GUIDE.md §11 Phase 4, §5.4).
Owner-directed provider deviation from the guide's locked `anthropic`
(PROGRESS.md, logged): GPT-4o-mini via the OpenAI API, chosen after NVIDIA's
free tier hit real model-availability failures across 4 different model
IDs (deprecated or account-restricted) while GPT-4o-mini extracted the
schema correctly on the first try in a live test.

Cost cap (§5.4): <=$10/month. GPT-4o-mini pricing (~$0.15/1M input,
~$0.60/1M output tokens) makes the full ~1M-character corpus fetched in
Phase 4 cost well under $1 total -- tracked and reported below, not
assumed safe.
"""
from __future__ import annotations

import json
import os
import pickle
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

import jos_lib as lib
from signal_schema import ACTIONS, SignalItem

load_dotenv(lib.REPO / ".env")

MODEL = "gpt-4o-mini"
# Single source of truth for the prompt's iteration label (§12: "any prompt
# or model change requires re-running eval" -- CI checks this string
# against eval/results/LATEST's own prompt_version, see
# check_prompt_version.py). Bump this whenever EXTRACTION_PROMPT_TEMPLATE
# changes; eval_runner.py imports this constant rather than hardcoding its
# own copy, which is exactly the drift that let an earlier version of that
# file silently claim "v2" after the prompt had already moved to v3.
PROMPT_VERSION = "v3-mechanical-vote-check"
CHUNK_CHARS = 40000  # keeps each call well within context + leaves room for a large JSON response
OUT_JSON = lib.WEB_DATA / "signals.json"
COST_PER_1M_INPUT = 0.15
COST_PER_1M_OUTPUT = 0.60

# {meeting_date} is passed in explicitly, parsed once from the document's
# own header before chunking -- NOT left for the model to infer per chunk.
# Real bug found and fixed here: the original version asked the model to
# "infer from context if not restated," which works for a chunk that
# happens to include the document's own date header, but for a long
# single-meeting transcript split into many 40K-char chunks (e.g. Hoboken's
# 325-page, 13-chunk document), only the FIRST chunk carries that header --
# every later chunk fabricated a plausible-looking but entirely invented
# date (multiple 2023 dates that appear literally zero times anywhere in a
# transcript of a 2026 meeting, confirmed via direct text search) rather
# than correctly inheriting the one true date. Caught while building the
# eval gold set, not assumed correct because the JSON parsed cleanly.
EXTRACTION_PROMPT_TEMPLATE = """Extract structured data from this excerpt of planning/zoning board meeting minutes.
This excerpt is from a meeting held on {meeting_date} -- use this exact date for every item's
meeting_date field; do not infer or guess a different date from the excerpt's own content.

For EACH case, application, or agenda item discussed (not procedural items like roll call or
adjournment), return one JSON object with these exact fields:
- meeting_date: "{meeting_date}" (always this exact value)
- board (string, e.g. "Planning Board", "Board of Adjustment")
- case_ref (string or null -- a case/application number if stated)
- applicant_type (string, e.g. "LLC", "individual", "corporation" -- infer from applicant name if not explicit)
- project_desc (string -- describe the PROJECT/PROPOSAL itself, never the applicant's or any private individual's name)
- use_type (string, e.g. "multifamily", "single-family", "retail", "restaurant", "office", "industrial")
- action (one of exactly: approved, denied, carried, heard, withdrawn)
- variances_mentioned (array of strings, empty array if none)
- confidence (float 0-1, your own confidence in this specific extraction)

Rules for determining `action` -- read this carefully, it is the field most often
mislabeled:
- "approved" requires an EXPLICIT motion-and-vote result on the substantive application
  itself -- e.g. "a motion to approve the application was made... and approved", or a
  "VOTE: IN FAVOR..." roll call. This also applies under an "APPROVAL EXTENSION" heading:
  if the board voted to grant a one-year (or other) extension of a previously-approved
  variance, that IS an "approved" action (the extension itself was approved), not "heard".
- "carried" applies whenever a hearing or application is explicitly postponed, continued,
  or adjourned to a future date -- e.g. "Hearing Postponed to [date]", "the application
  would be carried to [date]", "continued to the next available hearing date". This is
  true even if the postponement itself was approved by a procedural motion -- the
  SUBSTANTIVE application's status is "carried", not "approved" or "heard".
- "heard" is ONLY for an item where testimony, discussion, or exhibits are presented but
  NO vote and NO continuance/postponement is stated in this excerpt -- i.e. genuinely
  undetermined as of this excerpt. Do not infer "approved" from a positive tone, board
  members expressing support, or an applicant's testimony alone -- those without an
  actual recorded vote are still "heard". This holds NO MATTER HOW LONG OR DETAILED the
  testimony is -- extensive, technical testimony (traffic studies, parking counts, expert
  witnesses) is not evidence of an outcome by itself. Mechanically: search the excerpt for
  the literal phrase "called for a motion" or "a motion... was made" followed by a stated
  result -- if you cannot point to that specific sentence pair, the action is "heard".
- "denied"/"withdrawn" require the same explicit standard as "approved": a stated vote
  result or an explicit withdrawal statement.

Other rules:
- Never include a private individual's personal name in project_desc -- describe the project only.
- If a case/application is only referenced in passing (e.g. listed in an index, agenda summary,
  or as a cross-reference) without any actual discussion or vote in THIS excerpt, do not extract
  it as a separate item -- only extract items with real substantive content in this excerpt.
- Return ONLY a JSON array, no markdown fences, no other text. Empty array if no real agenda items in this excerpt.

WORKED EXAMPLE -- an excerpt that ends with testimony and expressions of support, but NO
vote, still gets "heard", not "approved" (this exact pattern was the most common real error
found during eval -- read it carefully):

  Example input excerpt:
  "ZBA 25-099 – Jane Smith, 12 Elm Street. Applicant sought variance relief for a rear
  addition. The Applicant's architect described the proposed plans. Chairman Sontz asked
  for members of the public; none came forward. Chairman Sontz discussed the application
  with the Board Members. Ms. Molnar expressed her support for the application, as did
  other board members."

  Correct output for this example: action = "heard" -- NOT "approved". There is no motion,
  no "VOTE: IN FAVOR" roll call, and no stated result anywhere in this excerpt. Board members
  voicing support during discussion is not the same as a recorded vote -- the very next
  sentence in a real transcript is often "Chairman Sontz called for a motion," and if that
  sentence and the vote that follows it are NOT present in your excerpt, the outcome is
  genuinely undetermined here and must be "heard".

MEETING MINUTES EXCERPT:
{text}
"""

DATE_PATTERN = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+20\d{2}\b"  # ordinal suffix optional: real sources use both "July 7, 2026" and "April 6th, 2026"
)
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def find_meeting_date(full_text: str, fallback: str | None = None) -> str:
    """Parse the real meeting date once from the document's own header
    (first ~3000 chars, where every source in this corpus states it
    plainly, e.g. 'JULY 7, 2026' or 'February 4, 2026') rather than
    trusting a per-chunk model guess."""
    m = DATE_PATTERN.search(full_text[:3000])
    if not m:
        m = DATE_PATTERN.search(full_text[:3000].title())  # handles ALL-CAPS headers
    if m:
        month, day_year = m.group(0).split(None, 1)
        day, year = re.match(r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", day_year).groups()
        return f"{year}-{MONTHS[month.title()]:02d}-{int(day):02d}"
    return fallback or "unknown"


def chunk_text(text: str, size: int = CHUNK_CHARS) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


def extract_chunk(client: OpenAI, text: str, meeting_date: str) -> tuple[list[dict], dict]:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT_TEMPLATE.format(text=text, meeting_date=meeting_date)}],
        temperature=0,
        max_tokens=4000,
    )
    content = resp.choices[0].message.content.strip()
    content = re.sub(r"^```(json)?|```$", "", content, flags=re.MULTILINE).strip()
    usage = {"input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens}
    try:
        items = json.loads(content)
        if not isinstance(items, list):
            return [], usage
        return items, usage
    except json.JSONDecodeError:
        return [], usage


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("FATAL: OPENAI_API_KEY not set (checked .env)")
        return 1
    client = OpenAI(api_key=api_key)

    docs = pickle.loads((lib.RAW / "minutes_extracted.pkl").read_bytes())
    print(f"Loaded {len(docs)} documents ({sum(len(d['text']) for d in docs):,} total chars)")

    all_items = []
    n_validation_failures = 0
    total_input_tokens = 0
    total_output_tokens = 0

    n_deduped = 0
    for doc in docs:
        meeting_date = find_meeting_date(doc["text"])
        chunks = chunk_text(doc["text"])
        doc_items: dict[str, dict] = {}  # case_ref (or a synthetic key) -> item, for within-document dedup
        n_no_case_ref = 0
        for chunk in chunks:
            raw_items, usage = extract_chunk(client, chunk, meeting_date)
            total_input_tokens += usage["input_tokens"]
            total_output_tokens += usage["output_tokens"]
            for raw in raw_items:
                raw["source_url"] = doc["url"]
                raw["municipality"] = doc["municipality"]
                raw.setdefault("board", doc["board"])
                try:
                    item = SignalItem(**raw)
                except ValidationError:
                    n_validation_failures += 1
                    continue
                # A long single-meeting transcript split across many chunks
                # (e.g. Hoboken's 13-chunk document) discusses the same case
                # across multiple chunks -- without this, each chunk that
                # touches a case re-extracts it as if it were a new item.
                # Items with no case_ref at all (rare, mostly Westfield's
                # non-board community items) each get their own key instead
                # of colliding into one dedup bucket.
                key = item.case_ref or f"__no_ref_{n_no_case_ref}"
                if item.case_ref is None:
                    n_no_case_ref += 1
                if key in doc_items:
                    n_deduped += 1
                else:
                    doc_items[key] = item.model_dump()
        all_items.extend(doc_items.values())
        print(f"  {doc['municipality']} {doc['url'].split('/')[-1]} (meeting_date={meeting_date}): "
              f"{len(chunks)} chunk(s), {len(doc_items)} items, {len(all_items)} total so far")

    cost = (total_input_tokens / 1e6 * COST_PER_1M_INPUT) + (total_output_tokens / 1e6 * COST_PER_1M_OUTPUT)
    print(f"\nExtraction done: {len(all_items)} valid items, {n_validation_failures} dropped for "
          f"schema validation failure (never patched by hand, per §5.4), "
          f"{n_deduped} deduped (same case re-extracted across chunks of the same long document).")
    print(f"Cost: {total_input_tokens:,} input + {total_output_tokens:,} output tokens "
          f"= ${cost:.4f} (cap: $10/month)")

    action_counts = {a: sum(1 for i in all_items if i["action"] == a) for a in ACTIONS}
    muni_counts = {}
    for i in all_items:
        muni_counts[i["municipality"]] = muni_counts.get(i["municipality"], 0) + 1
    print(f"By action: {action_counts}")
    print(f"By municipality: {muni_counts}")

    all_items.sort(key=lambda i: i["meeting_date"], reverse=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(all_items, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_JSON}")

    lib.write_meta("signals", {
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "n_items": len(all_items),
        "n_municipalities": len(muni_counts),
        "n_validation_failures": n_validation_failures,
        "cost_usd": round(cost, 4),
    })

    n_munis = len(muni_counts)
    print(f"\nGate check (§1.4: '>=100 items from >=3 municipalities'): "
          f"{len(all_items)} items, {n_munis} municipalities -- "
          f"{'PASS' if len(all_items) >= 100 and n_munis >= 3 else 'FAIL'}")
    return 0 if len(all_items) >= 100 and n_munis >= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
