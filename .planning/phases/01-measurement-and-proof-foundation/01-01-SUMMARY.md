---
phase: 01-measurement-and-proof-foundation
plan: 01
subsystem: infra
tags: [uv, nle, git-source, provenance, env-fingerprint, reproducibility]

requires:
  - phase: none
    provides: first plan of the phase
provides:
  - "NLE (NetHack 5.0 fork) built from a local bare git repo, pinned by full commit in pyproject.toml and uv.lock"
  - "bench/provenance.py: env fingerprint of the worker interpreter and lock (worker_facts, lock_sha256, lock_blob, env_fingerprint, env_id)"
  - "scripts/fresh_clone_check.py: fresh clone installs with uv sync --locked and reports the NLE commit"
  - "scripts/play_compare.py: seed-by-seed comparison of two interpreter/tree configurations"
affects: [01-08 job provenance recording, 01-14 fresh-clone bench job, every later plan that runs uv sync]

actuals:
  tokens: 4180   # chars/4 over the realized diff of the files changed, uv.lock excluded (16718 chars)
  tasks: 3
  commits: 4     # MEASURED: git rev-list --count ebd3a61..7fc16d8 before the SUMMARY commit
plan_head_before: ebd3a61a2d5c53d2033533275431514c45f09c3d
plan_head_after: 7fc16d8af64bbd0f744ed5d6b7de7d67f8e0a0ce

tech-stack:
  added: []
  patterns:
    - "NLE comes from a git source pinned by rev; the commit is read back from direct_url.json of the installed distribution"
    - "env_id hashes (nle_commit, lock_sha256, python, numpy, numba) and ignores the interpreter path"

key-files:
  created:
    - bench/provenance.py
    - tests/test_bench_provenance.py
    - scripts/fresh_clone_check.py
    - scripts/play_compare.py
  modified:
    - pyproject.toml
    - uv.lock
    - .mcp.json

key-decisions:
  - "nle git source file://$HOME/git/nle-screens.git at rev cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72 (D-01, D-02); the bare repo has no remote and nothing was pushed"
  - "No backup tooling added (D-04); the single-disk risk for ~/git/nle-screens.git is accepted"
  - "The .mcp.json worker-interpreter override was removed, so bench workers use the project .venv built from the pinned commit"
  - "env_id excludes worker_python and nle_version so a fresh clone and the main checkout share an env_id"

requirements-completed: [MEAS-01]

coverage:
  - id: D1
    description: "A fresh clone installs with uv sync --locked without reference/ and reports NLE commit cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72"
    requirement: MEAS-01
    verification:
      - kind: integration
        ref: "uv run python scripts/fresh_clone_check.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "pyproject.toml pins nle by git source and rev; uv.lock records the commit; .mcp.json has no worker interpreter override"
    requirement: MEAS-01
    verification:
      - kind: other
        ref: "Task 1 verify commands (direct_url.json commit check, tomllib/json assertion, uv lock --check)"
        status: pass
    human_judgment: false
  - id: D3
    description: "bench/provenance.py fingerprints the worker interpreter and the lock without importing NLE"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_bench_provenance.py (15 tests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "The rebuilt .venv plays seeds 1000-1009 identically to the previous build of the same NLE commit"
    requirement: MEAS-01
    verification:
      - kind: integration
        ref: "uv run python scripts/play_compare.py --python-a ~/.cache/screens-nh5/venv/bin/python --python-b .venv/bin/python --seeds 1000-1009 --jobs 10"
        status: pass
      - kind: unit
        ref: "tests/test_dungeon_truth.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "The bare repo has no remote and nothing is pushed (D-01)"
    requirement: MEAS-01
    verification:
      - kind: other
        ref: "git -C ~/git/nle-screens.git remote (prints nothing)"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-11-12
status: complete
---

# Phase 1 Plan 01: NLE pinned to a local bare repo, with an env fingerprint Summary

**NLE (NetHack 5.0 fork) installs from a local bare git repo pinned to cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72 through uv.lock, with a stdlib-only bench/provenance.py that fingerprints the worker interpreter.**

## Performance

- **Duration:** about 10 min wall clock (start not recorded by the executor; STATE.md shows execution start 2026-11-12T17:15Z, finished 2026-11-12T17:26Z; the run was paused once at the commit guard)
- **Started:** about 2026-11-12T17:15:20Z
- **Completed:** 2026-11-12T17:26Z
- **Tasks:** 3
- **Files modified:** 7 (6 in the repo diff excluding uv.lock, plus uv.lock)

## Accomplishments

- NLE builds from `~/git/nle-screens.git` (bare clone of `screens-nh5`, `git remote` prints nothing); `uv sync` took about 29 s and installed `nle==1.3.1.dev21+gcb9d6572f`. The project `.venv` before this change held `1.3.1.dev19+gc03cfdf73.d20261027` (path source), so it was not on the pinned commit.
- `bench/provenance.py` returns `nle_commit`, `nle_version`, `python`, `numpy`, `numba` read from the worker interpreter and `lock_sha256` plus `worker_python` from the checkout. `env_id` of the main checkout and of a fresh clone are both `a8f58c2fda006264`.
- `scripts/fresh_clone_check.py` and `scripts/play_compare.py` exist; both were run (output below).
- Full non-slow test suite on the rebuilt venv: `584 passed, 6 skipped, 16 deselected in 61.16s`.

## Verification output (verbatim)

Fresh clone (`uv run python scripts/fresh_clone_check.py`):
```
{"dest": "/tmp/screens-fresh-pt5fcgw3", "sha": "7fc16d8af64bbd0f744ed5d6b7de7d67f8e0a0ce", "nle_commit": "cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72", "env_id": "a8f58c2fda006264", "tests": "passed"}
```
The clone's `uv sync --locked` took about 7 s total because uv reused its build cache; the clone had no `reference/` directory (the script asserts this). The temporary clone directory was removed afterwards.

A6 (same NLE commit built twice plays identically), `play_compare.py` against the old venv `~/.cache/screens-nh5/venv/bin/python` (also `1.3.1.dev21+gcb9d6572f`):
```
{"compared": 10, "identical": 10, "watchdog_skipped": [], "differing_seeds": []}
```
All ten per-seed lines (seeds 1000-1009) printed `"same": true, "diffs": []`. The wall-clock exit code was not captured (the command was wrapped in `time`), but the summary line has an empty `differing_seeds` and no `error` line, which is what exit 0 prints.

Pitfall 2 (struct offsets on the rebuilt library), `uv run python -m pytest -q tests/test_dungeon_truth.py`:
```
6 passed in 0.32s
```

Task 1 checks: `direct_url.json` commit_id printed `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72`; seeded game `run_game(seed=1000, max_steps=300)` printed `ok 198`; `uv lock --check` clean; `git -C ~/git/nle-screens.git rev-parse screens-nh5` printed `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72`.

## Task Commits

1. **Task 1: NLE builds from the pinned bare-repo commit (tracer)** - `937ef5c` (chore)
2. **Task 2: Env fingerprint of the worker interpreter (TDD)**
   - RED: `d5e7117` (test)
   - GREEN: `78337fc` (feat)
   - REFACTOR: none needed
3. **Task 3: Fresh-clone check and rebuilt-NLE identity check** - `7fc16d8` (feat)

**Plan metadata:** the SUMMARY commit that contains this file (docs: complete plan), followed by a STATE/ROADMAP commit.

## Files Created/Modified

- `pyproject.toml` - `nle` source is the git URL plus full-commit `rev`; comment rewritten
- `uv.lock` - nle entry is a git source with `?rev=cb9d6572...#cb9d6572...`, version `1.3.1.dev21+gcb9d6572f`
- `.mcp.json` - `env` object removed from the `screens-bench` server
- `bench/provenance.py` - env fingerprint module (standard library only)
- `tests/test_bench_provenance.py` - 15 tests (10 test functions, one parametrized over 6 bad shas)
- `scripts/fresh_clone_check.py` - fresh-clone install check, prints one JSON line
- `scripts/play_compare.py` - two-configuration seed comparison with `COMPARED_FIELDS` and repeatable `--ignore`

## Non-repo actions

- `reference/nle-src/paniclog` moved to `~/.local/state/nethack-screensaver/nle-paniclog-2026-11-12` so the fork tree was clean before pinning (`git -C reference/nle-src status --porcelain` printed nothing).
- `~/git/nle-screens.git` created by `git clone --bare reference/nle-src`, then `git remote remove origin`. Nothing was pushed anywhere. The old venv `~/.cache/screens-nh5` was left in place.

## Decisions Made

- D-01/D-02 followed as planned: git source by full commit, no remote, no push.
- D-04 followed: no backup step or script. The single-disk risk (the bare repo and `reference/nle-src` live on this one machine) is accepted by the owner; the plan says to write it into SKELETON.md, which this plan does not edit.
- The `nle` comment in `pyproject.toml` avoids repeating the repo name so `grep -c 'nle-screens.git' pyproject.toml` prints 1 as the acceptance criterion requires.

## TDD Gate Compliance

- **RED** `d5e7117`: `tests/test_bench_provenance.py` with a placeholder `bench/provenance.py` whose functions return empty values, so the run fails on the planned assertions and not on import. Command: `uv run python -m pytest -q tests/test_bench_provenance.py --junitxml=red.xml`, exit 1, 15 failed. The JUnit report was classified by `gsd_run check tdd-red-evidence` (target `test_lock_sha256_hashes_the_file_bytes`) and returned `RED_EVIDENCE_OK` (`target_test_failed`).
  - Semantic assessment: the target test executed and failed on `assert '' == '<sha256 hex>'`, the planned assertion that `lock_sha256` equals the sha256 of the file bytes; failure reason is the missing behavior, not a setup, import or fixture fault.
  - The RED record file was kept outside the repository (scratchpad), not committed.
- **GREEN** `78337fc`: 15 passed.
- **REFACTOR:** none; no commit.
- The RED commit includes the placeholder module (not only a test file) so the failure is on assertions; this is a deliberate reading of "tests first".
- The plan-level gate grep `git log --grep='^(test|feat)\(0*1-0*1\):'` also matches commits from an earlier, unrelated project history that used the same `01-01` scope (`918a44e`, `90a08b3`); the commits of this plan are the four listed above.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Docstring made the "no import nle" acceptance check fail**
- **Found during:** Task 2 (acceptance criteria)
- **Issue:** a docstring line began with `import nle itself`, so `grep -cE '^(import|from) nle' bench/provenance.py` printed 1 instead of 0.
- **Fix:** reworded to "load the game library".
- **Files modified:** bench/provenance.py
- **Committed in:** `78337fc`

**2. [Rule 1 - Bug] pyproject comment broke the `grep -c 'nle-screens.git'` criterion**
- **Found during:** Task 1 (acceptance criteria)
- **Issue:** first comment wording named the repo, so the count was 2 instead of 1.
- **Fix:** comment rewritten without the repo name.
- **Files modified:** pyproject.toml
- **Committed in:** `937ef5c`

**3. [Rule 1 - Bug] Stale plan-head ledger**
- **Found during:** SUMMARY writing
- **Issue:** `.git/gsd-plan-head-before-01-01` already existed from an earlier project history and held `191e4af...`, so the first `rev-list` count was 409. The coordinator's base for this plan is `ebd3a61`.
- **Fix:** overwrote the ledger with `ebd3a61a2d5c53d2033533275431514c45f09c3d`; `commits: 4` is measured from it.
- **Files modified:** none (a file under `.git/`)

---

**Total deviations:** 3 auto-fixed (3 Rule 1)
**Impact on plan:** none on scope; all were checks that failed against the literal acceptance wording.

## Process note

The first attempt stopped at the Step 0 commit guard because `main` is a protected branch and `git.allow_default_branch_commits` was unset. The owner set it to `true` (via the coordinator); the guard then passed (`git.base-branch --is-protected main` printed `false`) and execution resumed with no work redone. Pre-existing uncommitted `.planning/config.json` and untracked `.planning/state.json` were not staged.

## Authentication Gates

None.

## Known Stubs

None. The placeholder `bench/provenance.py` of the RED commit was replaced in GREEN.

## Threat Flags

None. `bench/provenance.py` runs a probe in an interpreter given by path (covered by the plan's trust boundary) and `lock_blob` validates its sha argument (T-01-04). `scripts/fresh_clone_check.py` and `scripts/play_compare.py` run local subprocesses only. T-01-01 is unchanged: the Lua `URL_HASH` pin in the fork's CMakeLists.txt was not touched, and the build succeeded with it. T-01-02: `rev` is the full 40-hex commit and `uv sync --locked` succeeded in the fresh clone.

## Issues Encountered

None beyond the deviations above. Open item for later plans: the fresh clone installed quickly because uv's build cache was warm, so a cold build of NLE in a clone (about 29 s here) was not separately timed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `uv sync --locked` works in any checkout on this machine without `reference/`. Plan 01-08 can record `env_fingerprint` per job; plan 01-14 can run the fresh-clone bench job.
- Single-disk risk for `~/git/nle-screens.git` stays accepted (D-04); if the file is missing `uv sync` fails (not tested here).

---
*Phase: 01-measurement-and-proof-foundation*
*Completed: 2026-11-12*

## Self-Check: PASSED

- Files found: bench/provenance.py, tests/test_bench_provenance.py, scripts/fresh_clone_check.py, scripts/play_compare.py, pyproject.toml, uv.lock, .mcp.json
- Commits found on HEAD: 937ef5c, d5e7117, 78337fc, 7fc16d8 (`evaluation-scope --commits-only` resolved with commits)
