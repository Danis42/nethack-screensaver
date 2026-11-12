---
phase: 01-measurement-and-proof-foundation
plan: 14
subsystem: bench
tags: [walking-skeleton, fresh-clone, lgen-pilot, pre-registration]

requires:
  - phase: 01-13
    provides: the full Phase 1 bench (funnel, keyed rows, env fingerprint, sequential test)
provides:
  - "01-SKELETON-PROOF.md: fresh-clone install of commit A, jobs 1 and 2 on the spare commit, funnel, claim-check pass/block"
  - "Branch proof/fresh-clone (spare commit e0229dc28b9895f5ec37265cc0b7db4d1968d299 on commit A)"
  - "Branch pilot/lgen-b (commit B c65c27011a737e33fc218350e1680460ed19f859 = A + exp/elbereth-respect), not merged"
  - "01-LGEN-PILOT.md pre-registered in 09b79fbb306764b9fae898b2c00a2e22158e4587; pilot jobs 3-6 (3 started, 4-6 queued)"
affects: [01-15 pilot analysis and baseline, 01-16 proof index]

actuals:
  tasks: 3
  commits: 5     # MEASURED: e5b5a7f (owner choices) excluded; 356e569, 09b79fb, a52f1b7 on main plus c65c270 on pilot/lgen-b and the spare commit-tree e0229dc
plan_head_before: e5b5a7f525bc51b8008f665173600aba80de466d
plan_head_after: a52f1b7adf12384f92e13c732560335712ae2f79

tech-stack:
  added: []
  patterns:
    - "Pilot decisions are committed before the jobs that test them; the job created_at values postdate the rule commit (checked)"

key-files:
  created:
    - .planning/phases/01-measurement-and-proof-foundation/01-SKELETON-PROOF.md
    - .planning/phases/01-measurement-and-proof-foundation/01-LGEN-PILOT.md
  modified: []

key-decisions:
  - "Owner: commit B = exp/elbereth-respect, rule-strict; the primary metric dlvl10 was delegated to Claude and argued in 01-LGEN-PILOT.md (B's triggers fire mostly at Dlvl 5-8, so dlvl6 would be settled before it acts)"
  - "Paired intervals in the pre-registration are Wald intervals on per-seed differences (named explicitly, so 01-15 cannot choose after seeing data)"

requirements-completed: []

coverage:
  - id: D1
    description: "Fresh clone of commit A installs with uv sync --locked without reference/, tests pass, NLE cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72"
    requirement: MEAS-01
    verification:
      - kind: integration
        ref: "scripts/fresh_clone_check.py JSON line in 01-SKELETON-PROOF.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "Jobs 1 (lgen off) and 2 (lgen seed) on the spare commit: done, started, 10 keyed rows each with env_id; funnel of job 2 has 18 rows with Wilson bounds"
    requirement: MEAS-01
    verification:
      - kind: integration
        ref: "plan 01-14 Task 1 automated check printed `ok 1 2`"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pilot pre-registered before its jobs; jobs 3-6 have the right modes and window; job 3 started"
    requirement: MEAS-04
    verification:
      - kind: integration
        ref: "plan 01-14 Task 3 automated check printed `ok [3, 4, 5, 6]`"
        status: pass
    human_judgment: false

duration: not measured
completed: 2026-11-13
---

# Phase 1 Plan 14: Walking-skeleton proof and lgen pilot start Summary

**The skeleton works end to end from a fresh clone on the live database. Jobs 1 and 2 played the spare commit e0229dc28b9895f5ec37265cc0b7db4d1968d299 with lgen off and on: 10 keyed rows each, with the env fingerprint. The claim checker passes the proof and blocks a forged copy. The lgen pilot (A = e5b5a7f525bc51b8008f665173600aba80de466d, B = c65c27011a737e33fc218350e1680460ed19f859) was pre-registered in 09b79fbb306764b9fae898b2c00a2e22158e4587 before its four jobs were created. Job 3 has started, and jobs 4-6 are queued.**

## Performance

- **Duration:** not measured
- **Completed:** 2026-11-13
- **Tasks:** 3 (tracer, owner decision, auto)
- **Executed:** inline in the main session

## Task Commits

1. **Task 1:** spare commit `e0229dc` (branch `proof/fresh-clone`), proof `356e569`
2. **Task 2 (owner decision):** recorded in STATE.md, `e5b5a7f`
3. **Task 3:** commit B `c65c270` (branch `pilot/lgen-b`), pre-registration `09b79fb`, job record `a52f1b7`

## Claim-check output (Task 1, step 8)

- The real proof paragraph: no output, exit 0 (pass; the audit log records `"decision": "pass"`).
- The copy citing job 999999: `{"decision": "block", "reason": "Unproven progress claim(s):\n1. \"Both jobs finished with 10 keyed game rows each, ...\": job 999999 does not exist in results.db ..."}`.

## Deviations from Plan

**1. [Process] The live server was not running at the start, so step 2 stopped nothing**
- After the owner's reboot nothing answered on :8765. The precondition (idle, nothing interrupted) held trivially. The clone server was started directly, and the live server was started afterwards from the main checkout (`serve --resume`).

**2. [Process] Commit B was built while the skeleton jobs ran**
- B's worktree, port and test suite ran in parallel with jobs 1 and 2. It touched no server or bench data. Every pilot job is still created after the rule commit (checked).

**3. [Rule 3 - Blocking] Port conflicts resolved as unions**
- `exp/elbereth-respect` conflicted with commit A in `autoascend/stats_logger.py` (one new counter) and `tests/test_fight_heur.py` (new tests). Both sides were kept. The resulting diff matches the archived branch (4 files, +43/-3). The worktree suite: 827 passed, 7 skipped.

**Total deviations:** 3. **Impact:** none on scope.

## Verification output

- Task 1 check: `ok 1 2`; live `/api/status` answers (`"slots"` count 1); `git rev-parse proof/fresh-clone^` = commit A.
- Task 3 check: `ok [3, 4, 5, 6]`; `git rev-parse pilot/lgen-b^` = commit A; `git merge-base --is-ancestor pilot/lgen-b main` exits 1.
- The live server reports env_id a8f58c2fda006264, the same as the fresh clone.

## Next Phase Readiness

Plan 01-15 needs jobs 3-6 done (about 55 minutes at 30 games per minute from 00:05). Wait with `.venv/bin/python -m bench.cli wait 6`, then re-run `/gsd-execute-phase 1`.

## Self-Check: PASSED
