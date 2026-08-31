"""Per-city permit-type -> shared-class crosswalks (OPERATING_GUIDE.md §5.1).

Shared classes (LOCKED): new-construction-res, new-construction-com,
alteration-major, alteration-minor, demolition, site/civil.

Every mapping below is built from real sampled permit-type value
distributions pulled live from each city's own dataset during Phase 1 (not
assumed from a generic national permit-type taxonomy) -- see the comment on
each city for the actual counts observed. Ambiguous values map to the
nearest class per §13.2's own rule ("ambiguous permit-type mapping ->
nearest class + note in the committed crosswalk"); values with no
reasonable match return None and are logged as unmapped, never silently
dropped or force-fit.
"""
from __future__ import annotations

CLASSES = ["new-construction-res", "new-construction-com", "alteration-major",
           "alteration-minor", "demolition", "site/civil"]


# --- NYC ---------------------------------------------------------------
# Two datasets, two different classification systems (RECON.md/PROGRESS.md
# already document why both are needed for full date coverage):
# - Legacy "DOB Permit Issuance" (2007-2020) has a clean job-level job_type:
#   NB=New Building (571,719), A1/A2/A3=Alteration tiers 1/2/3 (434,777 /
#   2,389,778 / 413,625 -- NYC's own severity convention: A1 = major,
#   changes use/egress/occupancy; A2 = general, by far the most common;
#   A3 = minor), DM=Demolition (102,288), SG=Sign (78,007, no clean target
#   class -- mapped to site/civil as the nearest fit, not a real match).
#   Residential split via that dataset's own `residential` Y/N field.
# - "DOB NOW: Build" (current) only classifies coarsely at job level
#   (job_type: "Alteration" 77,911, "New Building" 3,347, no severity
#   tier) -- Alteration defaults to alteration-major per §13.2 (nearest
#   class, documented approximation, not a precision claim) since there's
#   no signal to split further; residential split via dwelling-unit count.
NYC_LEGACY_JOB_TYPE: dict[str, str | None] = {
    "NB": "new-construction",  # split by `residential` field at apply time
    "A1": "alteration-major",
    "A2": "alteration-major",  # NYC's own "general alteration" -- treated as major, not minor, since A2 covers substantial scope-of-work changes, not the trivial repairs A3 covers
    "A3": "alteration-minor",
    "DM": "demolition",
    "SG": "site/civil",  # nearest fit -- signs aren't in the 6 target classes at all
}
NYC_DOBNOW_JOB_TYPE: dict[str, str | None] = {
    "Alteration": "alteration-major",  # no severity signal available -- documented approximation
    "New Building": "new-construction",
    "Alteration CO": "alteration-major",
    "ALT-CO - New Building with Existing Elements to Remain": "new-construction",
    "No Work": None,
}


# --- Chicago -------------------------------------------------------------
# permit_type values (real counts, all-time): EXPRESS PERMIT PROGRAM
# (322,451) / EASY PERMIT PROCESS (207,655) -- both are Chicago's own fast-
# track programs for low-complexity work, treated as alteration-minor.
# RENOVATION/ALTERATION (167,367) -- no major/minor split field found
# (review_type doesn't carry it either, checked live) -- defaults to
# alteration-major as the more conservative/informative default per
# §13.2, logged as an approximation.
# NEW CONSTRUCTION (31,826) -- **no residential/commercial split available
# in this dataset at all** (checked review_type, no other candidate field
# exists) -- logged as a real, documented data-coverage gap in RECON.md/
# PROGRESS.md, not silently guessed.
CHICAGO_PERMIT_TYPE: dict[str, str | None] = {
    "PERMIT – EXPRESS PERMIT PROGRAM": "alteration-minor",
    "PERMIT - EASY PERMIT PROCESS": "alteration-minor",
    "PERMIT - RENOVATION/ALTERATION": "alteration-major",
    "PERMIT - SIGNS": "site/civil",
    "PERMIT - NEW CONSTRUCTION": "new-construction",  # res/com split unavailable, see note above
    "PERMIT - ELEVATOR EQUIPMENT": "alteration-minor",
    "PERMIT - WRECKING/DEMOLITION": "demolition",
    "PERMIT - SCAFFOLDING": "site/civil",
    "PERMIT - REINSTATE REVOKED PMT": None,
    "PERMIT - PORCH CONSTRUCTION": "alteration-minor",
    "PERMIT - FOR EXTENSION OF PMT": None,
}


# --- Austin ----------------------------------------------------------- (cleanest of the 6)
# Two-step: filter to permit_type_desc == "Building Permit" (519,786 of
# 2.37M rows -- Electrical/Plumbing/Mechanical/Driveway permits are trade
# permits, not construction-class permits, excluded from the class
# crosswalk entirely, not force-mapped), then classify by work_class
# (real counts within Building Permit: New 193,137 / Remodel 187,342 /
# Repair 50,730 / Addition 29,437 / Addition and Remodel 22,178 /
# Demolition 21,360 / Interior Demo Non-Structural 4,289 / Life Safety
# 2,499 / Relocation 1,886). Residential/commercial split via the
# dataset's own permit_class_mapped field (clean, no ambiguity: 1,620,166
# Residential / 752,995 Commercial).
AUSTIN_WORK_CLASS: dict[str, str | None] = {
    "New": "new-construction",  # split by permit_class_mapped at apply time
    "Remodel": "alteration-major",
    "Addition and Remodel": "alteration-major",
    "Addition": "alteration-major",  # additions typically trigger structural/zoning review -- treated as major, not minor
    "Repair": "alteration-minor",
    "Interior Demo Non-Structural": "alteration-minor",
    "Life Safety": "alteration-minor",
    "Demolition": "demolition",
    "Relocation": "site/civil",
}


# --- San Francisco -------------------------------------------------------
# permit_type_definition (real counts): "otc alterations permit" (973,571,
# SF's own over-the-counter/simple-review track) / "additions alterations
# or repairs" (271,413, requires full plan review -- more substantial) /
# "new construction wood frame" (13,124) + "new construction" (2,496) /
# "demolitions" (7,310) / signs + excavation (site/civil-ish).
# Residential split for new-construction via the dataset's own
# existing_use/proposed_use fields at apply time (contains values like
# "1 family dwelling", "apartments", "office", etc.).
SF_PERMIT_TYPE_DEFINITION: dict[str, str | None] = {
    "otc alterations permit": "alteration-minor",
    "additions alterations or repairs": "alteration-major",
    "new construction wood frame": "new-construction",
    "new construction": "new-construction",
    "demolitions": "demolition",
    "sign - erect": "site/civil",
    "wall or painted sign": "site/civil",
    "grade or quarry or fill or excavate": "site/civil",
}


# --- Seattle ---------------------------------------------------------------
# permittypedesc (real counts): Addition/Alteration (111,429, no further
# major/minor split field found) / New (32,043) / Demolition (9,379) /
# Tenant Improvement (4,865, treated as alteration-minor -- typically
# interior, non-structural) / Environmentally Critical Area Exemption,
# Shoreline Exemption/Permit, Relief from Prohibition on Steep Slope,
# Temporary (all site/environmental-review permits, not building-class
# permits -- mapped to site/civil). Residential/commercial split via the
# dataset's own permitclass field (Single Family/Duplex + Multifamily =
# residential; Commercial/Institutional/Industrial = commercial;
# Vacant Land/N/A excluded).
SEATTLE_PERMIT_TYPE_DESC: dict[str, str | None] = {
    "Addition/Alteration": "alteration-major",  # no severity signal available -- documented approximation, same pattern as NYC DOB NOW and Chicago
    "New": "new-construction",
    "Demolition": "demolition",
    "Tenant Improvment": "alteration-minor",  # [sic] -- typo in the source dataset's own field value, preserved verbatim for exact matching
    "Environmentally Critical Area Exemption": "site/civil",
    "Shoreline Exemption": "site/civil",
    "Shoreline Permit Exemption": "site/civil",
    "Relief from Prohibition on Steep Slope": "site/civil",
    "Temporary": None,
}
SEATTLE_RESIDENTIAL_CLASSES = {"Single Family/Duplex", "Multifamily"}
SEATTLE_COMMERCIAL_CLASSES = {"Commercial", "Institutional", "Industrial"}


# --- Los Angeles -----------------------------------------------------------
# permit_type (real counts): Bldg-Alter/Repair (273,040) / Bldg-Addition
# (34,220) / Bldg-New (26,223) / Grading (20,285) / Swimming-Pool/Spa
# (16,493) / Nonbldg-New (12,749) / Bldg-Demolition (12,245) / Sign
# (8,970) / Nonbldg-Alter/Repair (3,740) / Nonbldg-Addition (121).
# Residential split via keyword match on the dataset's own use_desc field
# (e.g. "Dwelling - Single Family", "Duplex", "Apartment", "Accessory
# Dwelling Unit" all residential; anything else defaults commercial) --
# a heuristic, not a clean flag like Austin/Seattle have, logged as such.
LA_PERMIT_TYPE: dict[str, str | None] = {
    "Bldg-New": "new-construction",  # split by use_desc keyword match at apply time
    "Nonbldg-New": "site/civil",  # non-building structures (fences, retaining walls, etc.) -- not residential/commercial construction
    "Bldg-Alter/Repair": "alteration-major",
    "Nonbldg-Alter/Repair": "alteration-minor",
    "Bldg-Addition": "alteration-major",
    "Nonbldg-Addition": "alteration-minor",
    "Bldg-Demolition": "demolition",
    "Grading": "site/civil",
    "Swimming-Pool/Spa": "site/civil",
    "Sign": "site/civil",
}
LA_RESIDENTIAL_KEYWORDS = ("dwelling", "duplex", "apartment", "accessory dwelling", "residential")
