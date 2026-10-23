---
phase: 01-midgame-survival
plan: 03
subsystem: testing
tags: [bench, seeded, replay, paired-statistics, ladder, reports]

requires: []
provides:
  - "scripts/seeded_report.py verdict: exit-coded lookup of a finished experiment's stored verdict by ref (0 / 3 none / 4 expect-forbid violated)"
  - "scripts/seeded_report.py pairs: n, n10, n01, discordance q, diff, interval, half-width, mde80 for any rate metric over stored seeded games"
  - "scripts/seeded_report.py ladder / killers / deaths: 17-rung table for exactly seeds 0..N-1, killer table, per-death context rows"
  - "scripts/replay_check.py: seed-by-seed comparison of two commits' stored games (exit 0 / 1 mismatch / 2 missing seeds)"
  - "scripts/benchmark.py --seeds A-B / --field NAME: local seeded smoke runs reporting any GameResult field"
affects: [01-04, 01-05, 01-06, 01-07, 01-08]

actuals:
  tokens: 12300
  tasks: 3
  commits: 3
plan_head_before: ff586994c355c70d82de583e69540c762674b436
plan_head_after: 04f8bfbb2c1bd2dba8ce5107e18dfa005f294445
commits: 3

tech-stack:
  added: []
  patterns:
    - "Analysis scripts import the bench's own definitions (judge_paired, METRICS, killer, ladder_rows, reference.summary) instead of re-deriving statistics"
    - "Scripts only call Store read methods; a test greps their source for write methods"
    - "Tests build a temporary Store and call main(argv) directly; scripts/ is put on sys.path by the test module"

key-files:
  created: [scripts/seeded_report.py, scripts/replay_check.py, tests/test_seeded_scripts.py]
  modified: [scripts/benchmark.py]

key-decisions:
  - "Killer-table category rows are not exclusive: each row's count equals the matching bench metric (starved, ants, crashed); wand, rays and breath split the bench's rays metric; 'other killers' are names no category row matched"
  - "replay_check counts a seed as mismatched once however many of its fields differ; its exit code and 'M mismatched' are per seed"
  - "benchmark.py -n now defaults to None (treated as 50) so --seeds with an explicit -n can be refused; unseeded output is unchanged"

patterns-established:
  - "One command per question: verdict, pairs, ladder, killers, deaths, replay_check - later plans cite these in their verify blocks"

requirements-completed: [MEAS-01, MEAS-02]

coverage:
  - id: D1
    description: "verdict looks up a finished experiment's stored verdict by ref with exit codes 0/3/4"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py#test_verdict_expect_and_forbid_look_at_the_newest_job"
        status: pass
      - kind: other
        ref: "uv run python scripts/seeded_report.py verdict 0c7acbc --baseline 2653410 --metric rung2 --expect 'no measurable difference' (job 8, exit 0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "replay_check compares two commits seed by seed and exits 0/1/2"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py -k replay (10 tests)"
        status: pass
      - kind: other
        ref: "uv run python scripts/replay_check.py 2653410 0c7acbc --min 1 (exit 2, missing seeds)"
        status: pass
    human_judgment: false
  - id: D3
    description: "pairs computes the paired comparison exactly as bench/stats.py judge_paired does"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py#test_pairs_matches_judge_paired"
        status: pass
    human_judgment: false
  - id: D4
    description: "ladder prints the 17-rung table for seeds 0..N-1 and reproduces 2653410's 634 / 309 of 1152"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py -k ladder (5 tests)"
        status: pass
      - kind: other
        ref: "uv run python scripts/seeded_report.py ladder 2653410 --all-games (rung 1: 634, rung 2: 309, n = 1152)"
        status: pass
    human_judgment: false
  - id: D5
    description: "killers and deaths print killer tables and per-death context rows"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py -k 'killers or deaths' (7 tests)"
        status: pass
    human_judgment: false
  - id: D6
    description: "benchmark.py plays chosen seeds and reports any GameResult field including events counters"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py#test_seeds_option_plays_the_chosen_seeds_and_reports_fields"
        status: pass
      - kind: other
        ref: "uv run python scripts/benchmark.py --seeds 3 -j 1 --field events.rest_turns --field turns (real game, seed 3)"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-23
status: complete
---

# Phase 1 Plan 03: Read-only seeded bench tools Summary

**Six read-only commands over the bench store (verdict by ref, paired statistics, 17-rung table for exact seeds, killer tables, per-death rows, seed-by-seed replay check) plus seeded local smoke runs in benchmark.py, built on the bench's own stats and metric definitions.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-23T16:34:44Z
- **Completed:** 2026-10-23T16:42:54Z
- **Tasks:** 3
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments

- `seeded_report.py verdict` finds the stored verdict of a candidate (optionally by baseline and metric) and its exit code answers "exists / matches the expected state": job 8 (`0c7acbc` vs `2653410`, rung2) prints "no measurable difference", exit 0; `--expect better` exits 4; a commit with no experiment exits 3.
- `replay_check.py` is the A/A proof tool for MEAS-01: it compares role, race, turns, score, end_reason, rung, ladder and all plan 01-01 context fields seed by seed, skips fields only one side recorded (listed once), can leave out `watchdog` endings, and reports missing seeds (exit 2) instead of passing vacuously.
- `seeded_report.py pairs` prints n, n10, n01, q, diff, interval, half-width and mde80 (2.8 * half-width / 1.96), using `judge_paired` so it can never disagree with the bench server.
- `ladder` reproduces the known `2653410` numbers on its unseeded games (rung 1: 634, rung 2: 309, n = 1152) and, with `--seeds N`, uses exactly seeds 0..N-1 (the `/api/results` all-games summary is avoided on purpose; RESEARCH Pitfall 4).
- `killers` and `deaths` use the bench's `killer`, `ANTS`, `RAYS` and `METRICS`; `deaths` prints hp, hunger, food, prayers, zaps and the last two messages per game.
- `benchmark.py --seeds 0-21` (also `5`, `0,3,7`) plays seeded games and `--field events.rest_turns` (repeatable, dotted) prints the value per game and "NAME>0: k of n games" at the end; a real seeded game (seed 3) was played end to end as a smoke check.

## Task Commits

1. **Task 1: Verdict lookup by ref (tracer)** - `b49260c` (feat)
2. **Task 2: Replay check and paired statistics** - `da1289f` (feat)
3. **Task 3: Ladder, killers, deaths, seeded smoke runs** - `04f8bfb` (feat)

Tracer gate: Task 1's automated verify (9 tests plus the real-database `verdict` call) was re-run before expansion; it passed, so Tasks 2 and 3 followed.

**Plan metadata:** committed with this SUMMARY (docs).

## Files Created/Modified

- `scripts/seeded_report.py` - subcommands verdict, pairs, ladder, killers, deaths; `_sha`, `_store`, `main(argv)`
- `scripts/replay_check.py` - seed-by-seed comparison of two commits' stored games
- `scripts/benchmark.py` - `--seeds`, `--field`, `parse_seeds`, `field_value`; `main(argv=None)`
- `tests/test_seeded_scripts.py` - 42 tests against a temporary Store, fake games and a serial fake Pool

## Decisions Made

- Killer-table category rows overlap by design so every count equals the bench's own metric (a game that starved while an ant bit it is in both `starved` and `ants`); the header line says so. wand / rays / breath are the three parts of the bench `rays` metric.
- `replay_check` counts mismatches per seed (a seed with three differing fields prints three lines but counts once).
- `benchmark.py -n` default moved from 50 to `None` (meaning 50) so `--seeds -n 5` can be refused; unseeded runs behave and print as before (a test pins this).

## Deviations from Plan

None - plan executed exactly as written. Small additions inside the plan's scope: `--data`/`--repo` on `replay_check` (so tests and other databases work), a `verdict=... z=...` line in `pairs`, and a refusal of `--seeds` together with an explicit `-n`.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** none.

## Issues Encountered

- `Store.__init__` runs `PRAGMA journal_mode=WAL` and the idempotent `CREATE TABLE IF NOT EXISTS` script on open, so even the read-only scripts touch the database file's schema layer; on an existing database both are no-ops (T-01-05: no row is ever written, and the source contains no write-method call, pinned by a test).
- The full suite `uv run pytest -q -m ""` ran 313 passed, 5 skipped, 5 xfailed, 1 xpassed (3 min).

## Known Stubs

None.

## Threat Flags

None - no new network, auth or file-write surface; no package added (`pyproject.toml` and `uv.lock` untouched).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plans that need the A/A proof can run `seeded_report.py verdict`, `replay_check.py A B --min 576 --skip-end watchdog` and `seeded_report.py pairs`; no seeded games are stored yet, so all three currently report "missing seeds" / "no finished experiment" for the real data.
- `ladder`/`killers`/`deaths` need only the stored games; with `--seeds 576` they refuse to report on incomplete seed sets.

## Self-Check: PASSED

All four files exist; commits b49260c, da1289f, 04f8bfb are ancestors of HEAD; task acceptance criteria and the plan-level verification (full suite) pass.

---
*Phase: 01-midgame-survival*
*Completed: 2026-10-23*
