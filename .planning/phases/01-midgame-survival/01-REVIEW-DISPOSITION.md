---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Concurrent first build of the time() shim can read a half-written C file"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "judge_paired_numeric gives a zero-width interval for a single pair"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "benchmark.py detects --seeds by substring over the whole command line"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "meal \"open\" pattern can count non-food lines"
  - id: IN-04
    severity: info
    disposition: skipped
    title: "cohort WHERE clause is interpolated into SQL"
open: 0
total: 5
recorded: 2026-10-25T12:40:21.968Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | commit 2f9f211 |
| IN-01 | info | fixed | commit 2f9f211 |
| IN-02 | info | fixed | commit 2f9f211 |
| IN-03 | info | deferred | changing the meal pattern changes the recorded study numbers; revisit with the food-stock check (STATE todo) |
| IN-04 | info | skipped | where already comes only from COHORTS keys (nld_study.py:581) or constants; read-only DB |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
