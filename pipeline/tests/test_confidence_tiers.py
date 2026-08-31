"""§12: confidence-tier boundary tests (§5.1). Tier A is documented as
genuinely unreachable by this pipeline's current sources (no cross-city
status-history field) -- this test locks that fact in so a future change
that silently starts returning "A" gets caught, not just eyeballed."""
from __future__ import annotations

import importlib

scorecards = importlib.import_module("20_scorecards")


def test_tier_b_at_exact_thresholds():
    assert scorecards.confidence_tier(n_years=3, avg_per_year=50) == "B"


def test_tier_c_just_under_years_threshold():
    assert scorecards.confidence_tier(n_years=2, avg_per_year=1000) == "C"


def test_tier_c_just_under_volume_threshold():
    assert scorecards.confidence_tier(n_years=10, avg_per_year=49.9) == "C"


def test_tier_a_is_unreachable_by_this_function():
    """Locks in the module docstring's own claim: with no status-history
    signal wired in, this function can never return "A", no matter how
    much volume/history is passed."""
    assert scorecards.confidence_tier(n_years=100, avg_per_year=1_000_000) != "A"


def test_trend_slope_needs_at_least_two_years():
    assert scorecards.trend_slope({2024: 100}) is None


def test_trend_slope_sign_matches_direction():
    growing = scorecards.trend_slope({2022: 100, 2023: 150, 2024: 200})
    shrinking = scorecards.trend_slope({2022: 200, 2023: 150, 2024: 100})
    assert growing > 0
    assert shrinking < 0
