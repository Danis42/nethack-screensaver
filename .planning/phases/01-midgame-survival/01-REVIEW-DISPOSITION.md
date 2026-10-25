---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "Concurrent first build of the time() shim can read a half-written C file"
  - id: IN-01
    severity: info
    disposition: open
    title: "judge_paired_numeric gives a zero-width interval for a single pair"
  - id: IN-02
    severity: info
    disposition: open
    title: "benchmark.py detects --seeds by substring over the whole command line"
  - id: IN-03
    severity: info
    disposition: open
    title: "meal \"open\" pattern can count non-food lines"
  - id: IN-04
    severity: info
    disposition: open
    title: "cohort WHERE clause is interpolated into SQL"
open: 5
total: 5
recorded: 2026-10-25T12:40:21.968Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
