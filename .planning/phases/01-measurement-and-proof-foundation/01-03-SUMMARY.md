---
phase: 01-measurement-and-proof-foundation
plan: 03
subsystem: tooling
tags: [claim-checker, stop-hook, proof, sqlite-readonly, audit-log]

requires:
  - phase: none
    provides: stands alone (stdlib only; reads bench results.db schema from bench/store.py)
provides:
  - "scripts/check_claims.py: Stop-hook checker that finds start and result claims with fixed regexes and verifies cited job IDs, full 40-hex commits and [query: ... => value] proofs against results.db and git"
  - ".claude/settings.json: project Stop hook running the checker on the final message of every turn (timeout 30 s)"
  - "Audit log .claude/claim-checks.jsonl (gitignored): one record per pass, block or crash"
  - "Hand-written labelled corpus tests/data/claims_positive.txt (24) and claims_negative.txt (24)"
affects: [every later plan's owner-facing replies, 01-14..01-16 handoff wording ("job N queued, not started")]

actuals:
  tasks: 3
  commits: 5     # MEASURED: git rev-list --count a482c15..86d3dbd before the SUMMARY commit
plan_head_before: a482c154676315ee5c6b02336c0340ea2dffd476
plan_head_after: 86d3dbd

tech-stack:
  added: []
  patterns:
    - "Claims are matched per sentence after dropping fenced code and inline code; proofs are matched per paragraph (backticks stripped, so `job 12` in code formatting still counts as proof)"
    - "Model-supplied SQL runs under four locks: mode=ro URI, PRAGMA query_only, an authorizer allowing only SELECT/READ/FUNCTION, one statement, plus a 2 s progress-handler cap"

key-files:
  created:
    - scripts/check_claims.py
    - tests/test_check_claims.py
    - tests/data/claims_positive.txt
    - tests/data/claims_negative.txt
    - .claude/settings.json
  modified:
    - .gitignore

key-decisions:
  - "Negated progress phrases (not started, hasn't finished, not yet running) are removed before matching, so 'Job 5 queued, not started.' is not a claim"
  - "A start claim needs a cited job, and every job cited in its paragraph must have a game row (games or tool_games)"
  - "Hook uses shell form python3 \"${CLAUDE_PROJECT_DIR}\"/scripts/check_claims.py (system python3, quoted placeholder per the hooks docs)"

requirements-completed: [MEAS-09]

coverage:
  - id: D1
    description: "Start and result claims are blocked without a verified job proof; a start needs a game row; queued handoffs pass; DB opened read-only"
    requirement: MEAS-09
    verification:
      - kind: unit
        ref: "tests/test_check_claims.py (Task 1 tests, incl. subprocess end-to-end)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Commit proofs need exactly 40 hex chars resolving in git; query proofs are re-run read-only and writes, ATTACH, PRAGMA and multi-statement SQL are refused with the file unchanged; slow queries abort"
    requirement: MEAS-09
    verification:
      - kind: unit
        ref: "tests/test_check_claims.py (Task 2 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Checker crash exits 0, prints 'check_claims crashed' to stderr and logs a crash record; empty message passes and is logged; multiple failures listed in message order; 48-sentence corpus fully classified"
    requirement: MEAS-09
    verification:
      - kind: unit
        ref: "tests/test_check_claims.py (crash, edge and corpus tests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Stop hook fires in a real Claude Code session and blocks 'Baseline job 999999 started.'"
    requirement: MEAS-09
    human_judgment: true
    rationale: "Only a live session can show the hook is loaded; the configured command string was exercised through sh -c, not through Claude Code"

duration: 5 min
completed: 2026-11-12
---

# Phase 1 Plan 03: Stop-hook claim checker Summary

**A stdlib-only Stop hook blocks any reply that claims a run started or produced a result unless it cites a job with a game row, a full commit hash that resolves in git, or a read-only query that reproduces the number.**

## Performance

- **Duration:** 5 min (wall clock between plan start and end markers)
- **Completed:** 2026-11-12T17:38Z
- **Tasks:** 3 (one tracer, two auto; Tasks 1-2 TDD)
- **Files:** 5 created, 1 modified
- **Executed:** inline in the main session (no executor subagent), at the owner's request

## Accomplishments

- `scripts/check_claims.py` with `main`, `run`, `split_paragraphs`, `find_claims`, `find_proofs`, `verify_job`, `verify_commit`, `verify_query`; constants `START_RE`, `RESULT_VERB_RE`, `RESULT_NOUN_RE`, `JOB_RE`, `COMMIT_RE`, `QUERY_RE`, `QUERY_SECONDS = 2.0`.
- Proof is checked against reality, not format: job rows in results.db (read-only URI), `git cat-file -e <sha>^{commit}`, and re-run SQL.
- Every pass, block and crash goes to `.claude/claim-checks.jsonl`.
- Project Stop hook registered in `.claude/settings.json`.

## Task Commits

1. **Task 1 (tracer, TDD)**: RED `b32fbe2`, GREEN `c79e594`
2. **Task 2 (TDD)**: RED `b065551`, GREEN `e38f3da`
3. **Task 3**: `86d3dbd`

## Files Created/Modified

- `scripts/check_claims.py`: the checker (stdlib only).
- `tests/test_check_claims.py`: 81 tests (behaviour, proofs, refusals, crash, edges, corpus).
- `tests/data/claims_positive.txt`, `tests/data/claims_negative.txt`: 24 + 24 hand-written sentences in project wording; no transcript text.
- `.claude/settings.json`: the Stop hook.
- `.gitignore`: `.claude/claim-checks.jsonl`.

## Decisions Made

See `key-decisions` in the frontmatter.

## Limits to know (for the owner)

- The hook sees only the **final message** of a turn; text written before tool calls is not checked.
- After **eight consecutive blocks** Claude Code overrides the next block and ends the turn. The hooks docs add that the count **resets each time Claude calls a tool**. `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it. The audit log still records every block.
- A **crash** of the checker passes the reply (D-18), loudly on stderr and as a `crash` audit record.
- Detection is regex-based. It is a tripwire for the common failure (a claimed start or result with no proof), not a guarantee that no unproven claim slips through. Read `.claude/claim-checks.jsonl` to audit.

## TDD Gate Compliance

- Task 1 RED `b32fbe2`: 8 failed, 4 passed (the passing four are pass-cases that a do-nothing placeholder satisfies). A placeholder `scripts/check_claims.py` was committed with the tests so they fail on assertions, not on import.
- Task 2 RED `b065551`: 7 failed, 74 passed. The corpus tests already passed on the Task 1 regexes, and the write-refusal tests passed vacuously against the stub that refused every query; both are real checks after GREEN (refusal reasons confirmed as "not authorized" / "only one statement is allowed").
- GREEN commits `c79e594`, `e38f3da`; no REFACTOR needed.

## Deviations from Plan

**1. [Rule 2 - Missing critical] Proofs inside inline code still count**
- Found during: Task 1
- Issue: the plan drops inline code spans before matching. Applied to proofs too, a reply writing `` `job 12` `` or a commit in backticks would be blocked even though it cites proof.
- Fix: claims are matched with inline code removed; proofs are matched on the paragraph with backticks stripped (fenced blocks still dropped).
- Files: scripts/check_claims.py. Commit: c79e594.

**2. [Rule 1 - Bug] Negated progress words**
- Found during: Task 1
- Issue: "Job 5 queued, not started." contains "started", which would make the required handoff wording a start claim.
- Fix: `NEGATED_RE` removes "not/n't/never/no longer (yet) (been) <progress word>" before matching. Covered by the behaviour test and two corpus negatives.
- Commit: c79e594.

**3. [Docs-confirmed form] Hook command uses `${CLAUDE_PROJECT_DIR}` in quotes**
- The plan's `python3 "$CLAUDE_PROJECT_DIR"/...` is equivalent in `sh -c`; the docs' shell-form example quotes the braced placeholder, so that form is used.
- Commit: 86d3dbd.

**Total deviations:** 3 (1 Rule 2, 1 Rule 1, 1 form). **Impact:** none on scope.

## Threat Flags

T-01-07..T-01-11 mitigations are in place and tested (read-only open, query_only, authorizer, single statement, time cap, hex-only git argument, timeouts). T-01-10 (repudiation via cap/crash/final-message-only) is accepted and listed under "Limits to know".

## Issues Encountered

None.

## Verification output

- `.venv/bin/python -m pytest -q tests/test_check_claims.py`: 81 passed.
- Full non-slow suite: 705 passed, 6 skipped, 16 deselected.
- Configured command via `sh -c` blocks "Baseline job 999999 started." (grep count 1) and prints nothing for "Baseline job 1 started." against a scratch DB where job 1 has a game row.
- `git check-ignore -q .claude/claim-checks.jsonl`: ignored. `settings.local.json` sha256 unchanged.
- Network/LLM import grep: 0. Stdlib-only AST check: `stdlib only`.

## User Setup Required

None. Human check at end of phase: in a new Claude Code session, end a turn with "Baseline job 999999 started." and confirm it is blocked and a `block` line appears in `.claude/claim-checks.jsonl`.

## Next Phase Readiness

Ready for 01-04. Every later reply in this repo goes through the checker.

## Self-Check: PASSED
