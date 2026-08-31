"""§12: M5 delay-rule tests on synthetic series with a known outcome --
a real slowdown must alert, a stable series must not. Exercises
`backtest_group()`, the actual function `50_delay_alerts.py` runs against
real permit data (via importlib -- digit-prefixed filenames aren't
importable identifiers), not a reimplementation of the rule.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timedelta

alerts_mod = importlib.import_module("50_delay_alerts")

DAY0 = datetime(2020, 1, 1)
TOTAL_DAYS = 500  # > BASELINE_TOTAL_DAYS (365) so at least one backtest point exists


def _daily_rows(total_days: int, duration_fn) -> list[tuple[datetime, float]]:
    """One synthetic permit per day for `total_days` days, with
    duration_fn(day_index) -> duration_days."""
    return [(DAY0 + timedelta(days=i), duration_fn(i)) for i in range(total_days)]


def test_known_slowdown_alerts():
    # Flat 30-day baseline everywhere, except the most recent 90 days
    # (relative to the last row) jump to 60 days -- a clean 2x slowdown,
    # comfortably over both the 1.25x ratio gate and the n_90d>=20 gate
    # (90 daily rows fall in that window).
    def duration(i):
        return 60.0 if i >= TOTAL_DAYS - 90 else 30.0

    rows = _daily_rows(TOTAL_DAYS, duration)
    result = alerts_mod.backtest_group(rows)
    assert result["coverage"] == "ok"
    assert result["current"]["alert"] is True
    assert result["current"]["ratio"] >= alerts_mod.RATIO_THRESHOLD
    assert result["current"]["n_90d"] >= alerts_mod.MIN_N_90D


def test_stable_series_does_not_alert():
    rows = _daily_rows(TOTAL_DAYS, lambda i: 30.0)
    result = alerts_mod.backtest_group(rows)
    assert result["coverage"] == "ok"
    assert result["current"]["alert"] is False
    assert result["current"]["ratio"] == 1.0


def test_low_volume_does_not_alert_even_with_a_real_slowdown():
    """The n_90d>=20 gate exists so a handful of slow permits in a
    low-volume jurisdiction x class can't trigger a false alarm -- confirm
    it actually suppresses one. Baseline runs days 0-399 (dense, one
    permit/day); the most recent-90-day window (>= day 400) gets only 6
    sparse permits total (duration=90, a real 3x slowdown by ratio) and
    nothing else, so n_90d is genuinely low, not diluted by leftover
    baseline rows sharing that window.
    """
    baseline = [(DAY0 + timedelta(days=i), 30.0) for i in range(400)]
    sparse_recent = [(DAY0 + timedelta(days=d), 90.0) for d in (450, 460, 470, 480, 490, 495)]
    rows = baseline + sparse_recent
    result = alerts_mod.backtest_group(rows)
    assert result["coverage"] == "ok"
    assert result["current"]["ratio"] >= alerts_mod.RATIO_THRESHOLD  # a real slowdown by ratio...
    assert result["current"]["n_90d"] < alerts_mod.MIN_N_90D  # ...but too thin to count
    assert result["current"]["alert"] is False


def test_insufficient_history_is_reported_not_silently_dropped():
    rows = _daily_rows(100, lambda i: 30.0)  # well under BASELINE_TOTAL_DAYS
    result = alerts_mod.backtest_group(rows)
    assert result["coverage"] == "insufficient_history"


def test_no_data_is_reported():
    result = alerts_mod.backtest_group([])
    assert result["coverage"] == "no_data"


def test_current_is_always_the_true_latest_date_regardless_of_sample_step():
    """Guards the fix logged in PROGRESS.md: `current` must equal the true
    last issued_date in the data, not just whatever the last
    BACKTEST_STEP_DAYS-sampled point happened to land on."""
    rows = _daily_rows(TOTAL_DAYS, lambda i: 30.0)
    result = alerts_mod.backtest_group(rows)
    true_last_date = rows[-1][0].date().isoformat()
    assert result["current"]["as_of"] == true_last_date
