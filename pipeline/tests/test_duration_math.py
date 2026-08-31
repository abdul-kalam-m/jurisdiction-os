"""§12: duration math against 5 hand-verified real cases per city, committed
as fixtures (tests/fixtures/duration_cases.json) -- not synthetic data.
Each fixture's expected_duration_days/expected_excluded was computed by
hand (see each row's `note`) against the real filed_date/issued_date pulled
from the pipeline's own DuckDB output, independent of the code under test.
Exercises `classify_duration()`, the actual production function (10 --
digit-prefixed filenames aren't importable as identifiers, hence
importlib), not a reimplementation that could silently drift from it.
"""
from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path

import pytest

etl = importlib.import_module("10_permit_etl")

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "duration_cases.json").read_text())


def _parse(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str)


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: f"{c['city']}/{c['permit_id']}")
def test_duration_and_exclusion(case):
    filed = _parse(case["filed_date"])
    issued = _parse(case["issued_date"])
    duration_days, excluded, _reason = etl.classify_duration(filed, issued)
    assert duration_days == case["expected_duration_days"], case["note"]
    assert excluded == case["expected_excluded"], case["note"]


def test_fixture_covers_all_six_cities():
    cities = {c["city"] for c in FIXTURES}
    assert cities == {"NYC", "CHICAGO", "AUSTIN", "SAN FRANCISCO", "SEATTLE", "LOS ANGELES"}
    for city in cities:
        assert sum(1 for c in FIXTURES if c["city"] == city) == 5, f"{city} needs exactly 5 fixture cases"


def test_missing_date_is_excluded():
    duration_days, excluded, reason = etl.classify_duration(None, datetime(2024, 1, 1))
    assert duration_days is None
    assert excluded is True
    assert reason == "missing filed or issued date"


def test_exactly_five_years_is_not_excluded():
    # EXCLUSION_MAX_DAYS is a fixed day-count (365*5), not a calendar "5
    # years" -- use timedelta directly rather than .replace(year=+5), which
    # would silently absorb 1-2 leap days depending on the start date.
    from datetime import timedelta
    filed = datetime(2020, 1, 1)
    issued = filed + timedelta(days=etl.EXCLUSION_MAX_DAYS)
    duration_days, excluded, _ = etl.classify_duration(filed, issued)
    assert duration_days == etl.EXCLUSION_MAX_DAYS
    assert excluded is False


def test_one_day_over_five_years_is_excluded():
    from datetime import timedelta
    filed = datetime(2020, 1, 1)
    issued = filed + timedelta(days=etl.EXCLUSION_MAX_DAYS + 1)
    duration_days, excluded, reason = etl.classify_duration(filed, issued)
    assert duration_days == etl.EXCLUSION_MAX_DAYS + 1
    assert excluded is True
    assert reason == "duration > 5 years"
