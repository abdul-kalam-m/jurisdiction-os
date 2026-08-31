#!/usr/bin/env python3
"""50 -- Delay alerts, module M5 (OPERATING_GUIDE.md §5.5, Phase 6 per §11).

Per jurisdiction x shared-class, weekly: median_90d (last 90 days of issued
permits' cycle times) vs median_baseline (trailing 365 days, excluding the
last 90). Alert when ratio >= 1.25 and n_90d >= 20.

Phase 6 backtest requirement: run the rule over the *full* history (not just
the latest week) so the jurisdiction page can show a real historical alert
timeline, not just today's single status -- this both validates the rule
against real cycle-time swings and gives the demo something concrete to
show, per the guide's own reasoning. Writes the §6.3 committed artifact
`alerts.json`.

Delivery note (§5.5: "in-app feed + owner email only"): this script writes
the in-app feed (`alerts.json`, rendered on the Scorecards jurisdiction
detail page) unconditionally. Email delivery is a separate, best-effort
step -- see `send_alert_email()` below and PROGRESS.md for why it's a
documented stub rather than a live send in this build.
"""
from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import timedelta
from email.mime.text import MIMEText

import duckdb

import jos_lib as lib

DB_PATH = lib.REPO / "data" / "jurisdiction_os.duckdb"
ALERTS_JSON = lib.WEB_DATA / "alerts.json"

CLASSES = ["new-construction-res", "new-construction-com", "alteration-major",
           "alteration-minor", "demolition", "site/civil"]
CITY_SLUGS = {
    "NYC": "nyc", "CHICAGO": "chicago", "AUSTIN": "austin",
    "SAN FRANCISCO": "san-francisco", "SEATTLE": "seattle", "LOS ANGELES": "los-angeles",
}

WINDOW_90D_DAYS = 90
BASELINE_TOTAL_DAYS = 365  # trailing 365 days, of which the most recent 90 are excluded
RATIO_THRESHOLD = 1.25
MIN_N_90D = 20

# The *live* rule runs weekly (refresh.yml, §6.2) -- this constant is only
# the sampling interval for the *stored historical backtest timeline*, a
# separate concern. A true weekly backtest over ~4yr x 30 jurisdiction x
# class combos measured 474.9 KB (§6.3 budget: <=500 KB/file) with ~17
# KB/combo/year of organic growth from refresh.yml -- comfortably busts
# the budget within ~1.5 years. 14-day sampling roughly halves both the
# current size and the growth rate while still showing every real swing
# (cycle-time medians don't move meaningfully week-to-week); the "current"
# status below is always computed at the true latest date regardless of
# this constant, so live alerting accuracy is unaffected.
BACKTEST_STEP_DAYS = 14


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    return round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 1)


def backtest_group(rows: list[tuple]) -> dict:
    """rows: list of (issued_date: datetime, duration_days: float), any order.
    Returns the full backtest timeline (sampled every BACKTEST_STEP_DAYS,
    §6.3 file-size budget) plus a rollup. `current` is always evaluated at
    the true latest issued_date in the data, not just the last sampled
    point -- live alert accuracy shouldn't depend on the sampling cadence
    chosen for the stored historical timeline."""
    rows = sorted(rows, key=lambda r: r[0])
    dates = [r[0] for r in rows]
    durations = [r[1] for r in rows]
    n = len(rows)
    if n == 0:
        return {"coverage": "no_data"}

    first_date, last_date = dates[0], dates[-1]
    warmup_start = first_date + timedelta(days=BASELINE_TOTAL_DAYS)
    if warmup_start > last_date:
        return {"coverage": "insufficient_history",
                "detail": f"needs >= {BASELINE_TOTAL_DAYS}d of history before the first backtest point; "
                          f"this jurisdiction x class only spans "
                          f"{(last_date - first_date).days}d"}

    def eval_at(as_of):
        win90_start = as_of - timedelta(days=WINDOW_90D_DAYS)
        base_start = as_of - timedelta(days=BASELINE_TOTAL_DAYS)
        base_end = win90_start  # baseline excludes the most recent 90d

        d90 = [durations[i] for i in range(n) if win90_start <= dates[i] < as_of]
        dbase = [durations[i] for i in range(n) if base_start <= dates[i] < base_end]

        median_90d = _median(d90)
        median_baseline = _median(dbase)
        n_90d = len(d90)
        ratio = round(median_90d / median_baseline, 3) if median_90d is not None and median_baseline else None
        alert = bool(ratio is not None and ratio >= RATIO_THRESHOLD and n_90d >= MIN_N_90D)
        return {
            "as_of": as_of.date().isoformat(),
            "median_90d": median_90d,
            "median_baseline": median_baseline,
            "n_90d": n_90d,
            "ratio": ratio,
            "alert": alert,
        }

    timeline = []
    as_of = warmup_start
    while as_of <= last_date:
        timeline.append(eval_at(as_of))
        as_of += timedelta(days=BACKTEST_STEP_DAYS)

    current = eval_at(last_date) if timeline[-1]["as_of"] != last_date.date().isoformat() else timeline[-1]
    if current is not timeline[-1]:
        timeline.append(current)

    n_alert_points = sum(1 for t in timeline if t["alert"])
    return {
        "coverage": "ok",
        "n_backtest_points": len(timeline),
        "n_alert_points": n_alert_points,
        "current": current,
        "timeline": timeline,
    }


def send_alert_email(fired: list[dict]) -> None:
    """Best-effort owner-only email notification (§5.5). No external
    recipients ever -- `to` is always jos_lib.OWNER_EMAIL, never
    configurable from data or CLI args.

    This is a documented stub, not a live integration: this project's
    .env (per PROGRESS.md's provider log) has no SMTP/email-API
    credentials, and creating a new transactional-email account is an
    owner action, not something this pipeline does for itself. If the
    owner adds SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS to the
    environment (locally or as GitHub Actions secrets), this sends for
    real; otherwise it logs what *would* have been sent and exits 0
    (non-fatal -- the in-app feed in alerts.json is the authoritative
    record either way).
    """
    if not fired:
        print("send_alert_email: no new alerts this run, nothing to send.")
        return

    host, port, user, pw = (os.environ.get(k) for k in
                             ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"))
    body_lines = [f"{a['jurisdiction']} / {a['shared_class']}: ratio={a['ratio']} "
                  f"(n_90d={a['n_90d']}) as of {a['as_of']}" for a in fired]
    body = "Jurisdiction Intelligence OS -- delay alert(s) fired:\n\n" + "\n".join(body_lines)

    if not all((host, port, user, pw)):
        print(f"send_alert_email: SMTP credentials not configured (owner action pending, "
              f"see PROGRESS.md) -- {len(fired)} alert(s) recorded in-app only, not emailed.")
        print(body)
        return

    msg = MIMEText(body)
    msg["Subject"] = f"[Jurisdiction Intelligence OS] {len(fired)} delay alert(s)"
    msg["From"] = user
    msg["To"] = lib.OWNER_EMAIL
    with smtplib.SMTP(host, int(port)) as s:
        s.starttls()
        s.login(user, pw)
        s.sendmail(user, [lib.OWNER_EMAIL], msg.as_string())
    print(f"send_alert_email: sent {len(fired)} alert(s) to {lib.OWNER_EMAIL}")


def main() -> int:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    lib.WEB_DATA.mkdir(parents=True, exist_ok=True)

    jurisdictions_out: dict[str, dict] = {}
    newly_fired: list[dict] = []
    total_backtest_points = 0
    total_alert_points = 0

    for city, slug in CITY_SLUGS.items():
        classes_out: dict[str, dict] = {}
        for cls in CLASSES:
            rows = con.execute("""
                SELECT issued_date, duration_days FROM permits
                WHERE city = ? AND shared_class = ? AND NOT excluded AND issued_date IS NOT NULL
            """, [city, cls]).fetchall()
            result = backtest_group(rows)
            classes_out[cls] = result
            if result.get("coverage") == "ok":
                total_backtest_points += result["n_backtest_points"]
                total_alert_points += result["n_alert_points"]
                if result["current"]["alert"]:
                    newly_fired.append({
                        "jurisdiction": slug, "shared_class": cls,
                        "ratio": result["current"]["ratio"],
                        "n_90d": result["current"]["n_90d"],
                        "as_of": result["current"]["as_of"],
                    })
        jurisdictions_out[slug] = {"city": city, "classes": classes_out}
        n_ok = sum(1 for v in classes_out.values() if v.get("coverage") == "ok")
        print(f"{slug}: {n_ok}/{len(CLASSES)} classes backtested")
    con.close()

    payload = {
        "note": "M5 delay-alert backtest (OPERATING_GUIDE.md §5.5). The live rule runs "
                "weekly (refresh.yml); median_90d vs median_baseline (trailing 365d "
                "excl. the last 90d), alert when ratio >= 1.25 and n_90d >= 20. Full "
                "history backtested (Phase 6 requirement), not just the current week "
                "-- see 'timeline' per jurisdiction x class, sampled every "
                "backtest_sample_step_days for the §6.3 file-size budget (the live "
                "'current' status is always evaluated at the true latest date, "
                "independent of this sampling interval).",
        "rule": {
            "window_90d_days": WINDOW_90D_DAYS,
            "baseline_total_days": BASELINE_TOTAL_DAYS,
            "ratio_threshold": RATIO_THRESHOLD,
            "min_n_90d": MIN_N_90D,
            "live_rule_cadence": "weekly (refresh.yml)",
            "backtest_sample_step_days": BACKTEST_STEP_DAYS,
        },
        "jurisdictions": jurisdictions_out,
        "summary": {
            "total_backtest_points": total_backtest_points,
            "total_alert_points": total_alert_points,
            # NOTE: shared_class values can themselves contain "/" (e.g.
            # "site/civil") -- structured objects here, not a joined
            # string, so the frontend never has to (mis-)split one.
            "currently_alerting": sorted(
                ({"jurisdiction": a["jurisdiction"], "shared_class": a["shared_class"]} for a in newly_fired),
                key=lambda x: (x["jurisdiction"], x["shared_class"]),
            ),
        },
    }
    ALERTS_JSON.write_text(json.dumps(payload, separators=(",", ":"), default=str), encoding="utf-8")
    size_kb = ALERTS_JSON.stat().st_size / 1024
    print(f"\nWrote {ALERTS_JSON} ({size_kb:.1f} KB)")

    lib.write_meta("delay_alerts", {
        "rule": payload["rule"],
        "total_backtest_points": total_backtest_points,
        "currently_alerting_count": len(newly_fired),
        "artifact_size_kb": round(size_kb, 1),
    })

    send_alert_email(newly_fired)

    print(f"\nGate check (§11 Phase 6: 'Backtest timeline rendered'): "
          f"{total_backtest_points} backtest points across "
          f"{sum(1 for j in jurisdictions_out.values() for c in j['classes'].values() if c.get('coverage') == 'ok')} "
          f"jurisdiction x class combos, {total_alert_points} historical alert points. "
          f"artifact written = {'PASS' if total_backtest_points > 0 else 'FAIL'}")
    return 0 if total_backtest_points > 0 and size_kb <= 500 else 1


if __name__ == "__main__":
    sys.exit(main())
