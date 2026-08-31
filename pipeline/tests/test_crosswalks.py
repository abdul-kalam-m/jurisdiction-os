"""§12: crosswalk mapping tests. The real regression this guards against:
a typo'd or stale class name in one of the per-city crosswalk dicts (an
easy mistake with 6 independently-maintained mappings) that would silently
produce permits with an unrecognized shared_class, invisible until someone
notices a scorecard class is missing data it should have."""
from __future__ import annotations

import crosswalks as xw

CROSSWALK_NAMES = [
    "NYC_LEGACY_JOB_TYPE", "NYC_DOBNOW_JOB_TYPE", "CHICAGO_PERMIT_TYPE",
    "AUSTIN_WORK_CLASS", "SF_PERMIT_TYPE_DEFINITION", "SEATTLE_PERMIT_TYPE_DESC",
    "LA_PERMIT_TYPE",
]

# "new-construction" (no suffix) is a valid *intermediate* value for
# crosswalks that later get split into -res/-com by classify_row() based on
# a city-specific signal (see 10_permit_etl.py) -- not a final shared_class.
VALID_VALUES = set(xw.CLASSES) | {"new-construction", None}


def test_all_crosswalks_exist():
    for name in CROSSWALK_NAMES:
        assert hasattr(xw, name), f"crosswalks.py is missing {name}"


def test_every_mapped_value_is_a_recognized_class():
    for name in CROSSWALK_NAMES:
        crosswalk: dict = getattr(xw, name)
        assert crosswalk, f"{name} is empty"
        for raw_type, mapped in crosswalk.items():
            assert mapped in VALID_VALUES, (
                f"{name}[{raw_type!r}] = {mapped!r} is not a recognized shared_class "
                f"(valid: {sorted(v for v in VALID_VALUES if v)})"
            )


def test_classes_list_matches_scorecards_module():
    """crosswalks.CLASSES must stay in sync with 20_scorecards.py's own
    CLASSES list -- they were historically two separate copies and drifting
    silently would misclassify or drop a class from the scorecard UI."""
    import importlib
    scorecards = importlib.import_module("20_scorecards")
    assert set(xw.CLASSES) == set(scorecards.CLASSES)
