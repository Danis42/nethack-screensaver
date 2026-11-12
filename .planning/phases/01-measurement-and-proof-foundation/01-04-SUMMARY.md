---
phase: 01-measurement-and-proof-foundation
plan: 04
subsystem: tooling
tags: [fact-ledger, nethack-facts, citations, coverage, toml]

requires:
  - phase: none
    provides: stands alone (stdlib tomllib, tokenize, sqlite3)
provides:
  - "facts/FACTS.toml: the fact ledger (format in its header) with the first fact sokoban-entry-is-bottom-level, tag 5.0-source"
  - "scripts/facts.py: check [--source], report, coverage [--out PATH]; functions load, citations, check, check_sources, report, coverage"
  - "tests/test_facts.py: ledger rules, citations, source quotes, path refusal, report, coverage"
  - "autoascend/ladder.py: first code citation (comment only)"
affects: [01-07 bot-module fact tranche, 01-09 research-note tranche and coverage report]

actuals:
  tasks: 2
  commits: 4     # MEASURED: git rev-list --count bc2bf1b..c6da889 before the SUMMARY commit
plan_head_before: bc2bf1b9116ad07556ef28d1063861af3925b670
plan_head_after: c6da889

tech-stack:
  added: []
  patterns:
    - "Code cites facts with '# fact:<id>[, <id>]' comments, notes with '[fact:<id>]'; a pytest fails when a cited id is not in the ledger"
    - "5.0-source quotes are matched whitespace-normalised inside the cited line range; at least one cited range must contain the quote, every cited range must exist"

key-files:
  created:
    - facts/FACTS.toml
    - scripts/facts.py
    - tests/test_facts.py
  modified:
    - autoascend/ladder.py

key-decisions:
  - "Coverage scans autoascend/ only for literals (as the plan specifies); citations are scanned in autoascend/, nethack_screensaver/ and bench/"
  - "Literals 0, 1 and 2 are not counted (-1 tokenizes as '-' and 1, so it is excluded too); floats such as 0.5 count"
  - "Files in the coverage report are sorted by literals minus citations, descending"

requirements-completed: [MEAS-10]

coverage:
  - id: D1
    description: "Ledger rules per tag, id format, and every code/note citation resolving to a ledger id"
    requirement: MEAS-10
    verification:
      - kind: unit
        ref: "tests/test_facts.py (Task 1 tests, incl. the real ledger against the real tree)"
        status: pass
    human_judgment: false
  - id: D2
    description: "check --source finds the quote in the cited range; refuses absolute, '..' and out-of-root evidence; errors on missing file, out-of-range lines and quote outside range"
    requirement: MEAS-10
    verification:
      - kind: unit
        ref: "tests/test_facts.py (Task 2 source tests)"
        status: pass
      - kind: command
        ref: ".venv/bin/python scripts/facts.py check --source (exit 0 with reference/ present)"
        status: pass
    human_judgment: false
  - id: D3
    description: "report lists cited unverified facts with sites; coverage counts literals, citations and unverified marks"
    requirement: MEAS-10
    verification:
      - kind: unit
        ref: "tests/test_facts.py (report and coverage tests)"
        status: pass
    human_judgment: false

duration: 3 min
completed: 2026-11-12
---

# Phase 1 Plan 04: Fact ledger Summary

**A TOML fact ledger with three tags (5.0-source, measured, unverified), a pytest that fails on any code citation pointing nowhere, a quote check against the 5.0 source, and reports for unverified dependencies and citation coverage; the first fact (Sokoban's entry is its bottom level) is verified and cited from `ladder.py`.**

## Performance

- **Duration:** 3 min (wall clock between plan start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 2 (one tracer, one auto; both TDD)
- **Files:** 3 created, 1 modified
- **Executed:** inline in the main session (no executor subagent)

## Accomplishments

- `facts/FACTS.toml` with its format documented in the header and the first entry `[sokoban-entry-is-bottom-level]`: evidence `reference/nethack-5.0.0/src/dungeon.c:945-947` and `dat/dungeon.lua:219-233`, quote of the `if (dgn_entry < 0)` assignment of `entry_lev`.
- `scripts/facts.py` subcommands: `check`, `check --source`, `report`, `coverage [--out PATH]`.
- `autoascend/ladder.py` cites the fact on the `sokoban_solved` detector (comment only).

## Baseline numbers for the tagging tranches (D-20)

From `.venv/bin/python scripts/facts.py coverage` at `c6da889`: 55 bot files, 8390 counted numeric literals, 1 fact citation. This counts literals, not facts: most literals are not NetHack facts. It is the starting point that 01-07 and 01-09 move.

## Task Commits

1. **Task 1 (tracer, TDD)**: RED `2705059`, GREEN `5b4e965`
2. **Task 2 (TDD)**: RED `d8e3f48`, GREEN `c6da889`

## Files Created/Modified

- `facts/FACTS.toml`: the ledger.
- `scripts/facts.py`: the tool (stdlib only).
- `tests/test_facts.py`: 23 tests.
- `autoascend/ladder.py`: one `# fact:` comment.

## Decisions Made

See `key-decisions` in the frontmatter.

## TDD Gate Compliance

- Task 1 RED `2705059`: 12 failed against a placeholder. GREEN `5b4e965`: 12 passed.
- Task 2 RED `d8e3f48`: 9 failed, 14 passed (stubs returning empty results satisfy the "no error" cases). GREEN `c6da889`: 23 passed.

## Deviations from Plan

**1. [Rule 3 - Blocking] `citations()` takes the repository root**
- The plan lists `citations(roots)`. To scan both code roots and the notes glob relative to one tree (and to point tests at a tmp tree), the signature is `citations(repo=REPO, code_roots=CODE_ROOTS, notes_glob=NOTES_GLOB)`.
- Commit: 5b4e965.

**2. [Rule 2 - Missing critical] Malformed evidence items are errors**
- An evidence item that is not `path:line` or `path:start-end` is reported, instead of being skipped.
- Commit: c6da889.

**Total deviations:** 2. **Impact:** none on scope.

## Threat Flags

T-01-12 (path handling) mitigated and tested with the three refused paths. T-01-13 mitigated: `5.0-source` needs evidence and a quote that `check --source` finds.

## Issues Encountered

None.

## Verification output

- `.venv/bin/python -m pytest -q tests/test_facts.py`: 23 passed (the real-ledger source test ran; `reference/` is present).
- `.venv/bin/python scripts/facts.py check`: exit 0, no output. `check --source`: exit 0.
- `report` last line: `{"unverified_cited": 0}`. `coverage` last line: `{"files": 55, "literals": 8390, "citations": 1}`.
- `grep -c 'fact:sokoban-entry-is-bottom-level' autoascend/ladder.py`: 1. The word diff of `ladder.py` adds only `# fact:sokoban-entry-is-bottom-level`.
- Full non-slow suite: 728 passed, 6 skipped, 16 deselected.

## Flagged assumption

NLE-fork line numbers can move on a fork rebase, which would make `check --source` fail until the evidence is updated. The first fact cites the pristine `reference/nethack-5.0.0/` tree.

## User Setup Required

None.

## Next Phase Readiness

Wave 1 complete. Ready for wave 2 (01-05, 01-07).

## Self-Check: PASSED
