---
phase: 01-measurement-and-proof-foundation
verified: 2026-11-14T01:30:00Z
status: human_needed
score: 5/5 must-haves verified
covered_files: [".planning/phases/01-measurement-and-proof-foundation/01-01-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-01-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-02-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-02-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-03-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-03-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-04-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-04-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-05-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-05-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-06-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-06-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-07-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-07-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-08-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-08-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-09-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-09-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-10-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-10-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-11-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-11-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-12-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-12-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-13-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-13-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-14-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-14-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-15-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-15-SUMMARY.md", ".planning/phases/01-measurement-and-proof-foundation/01-16-PLAN.md", ".planning/phases/01-measurement-and-proof-foundation/01-16-SUMMARY.md", "bench/funnel.py", "bench/power.py", "bench/provenance.py", "bench/scheduler.py", "bench/seeds.py", "bench/sequential.py", "bench/server.py", "bench/store.py", "bench/toolruns.py", "facts/FACTS.toml", "pyproject.toml", "scripts/check_claims.py", "scripts/facts.py", "scripts/fresh_clone_check.py", "scripts/lgen_pilot.py", "scripts/replay_check.py", "scripts/sim_sequential.py", "uv.lock"]
covered_digest: "v4:sha256:10f3d29b2ede26104c102f725242f6d362386e4ecc6dce0f63793ba23a9e3324"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Prohibition review (7 flagged judgment-tier prohibitions from the plan frontmatter): 01-01 no push of the NLE fork or screens repo to a remote and no backup tooling; 01-03 no LLM, network or paid API in claim detection; 01-03 no bypass switch for the claim checker; 01-04 no 5.0-source fact tag without file:line and verbatim quote; 01-10 no Claude-reachable surface creates clean_attempt jobs or plays final-range seeds; 01-15 no dungeon screening in lgen pairing or seed choice; 01-16 no archive games imported or archive numbers shown as current"
    expected: "Owner accepts or rejects the verifier's non-authoritative verdict for each: all seven held on the evidence listed under 'Prohibitions' below"
    why_human: "unverified-prohibition: judgment-tier statements are never silently passed; the verifier's check is an LLM judgment plus greps and tests, not an authoritative proof"
  - test: "Restart the bench server so it runs the review-fix code: `uv run screens-bench serve --resume`, then GET /api/results?ref=e5b5a7f525bc51b8008f665173600aba80de466d"
    expected: "games = 10000 (one game key), matching /api/funnel?job=7 n = 10000"
    why_human: "The running server (pid 16993, started Nov 13) still serves the pre-fix code and answers games = 10400 for commit A today (curl, read-only). Restarting a service the owner uses is the owner's call; the fix itself is verified from code and tests"
advisory:
  - finding: "Open review items WR-02 (partly), WR-03 (partly), WR-04, IN-01..IN-05 are documented as open in 01-REVIEW-DISPOSITION.md"
    category: other
    reason: "None blocks a success criterion; see Anti-Patterns. WR-02 is the most relevant to 'claims without proof are rejected': a result claim (finished, improved) citing any existing job still passes"
    evidence_status: "reproduced by this verification: `Job 7 finished; see job 7.` passes"
---

# Phase 1: Measurement and Proof Foundation Verification Report

**Phase Goal:** The owner can check every progress number against a fresh, reproducible natural-game funnel of `main`, and claims without proof are rejected automatically
**Verified:** 2026-11-14T01:30:00Z
**Status:** human_needed
**Re-verification:** No, initial verification

All five ROADMAP success criteria hold against the live database, the code and a re-run test suite. The status is `human_needed` and not `passed` for two reasons only: seven plan-level prohibitions are flagged judgment-tier and need the owner's acceptance, and the running bench server has not been restarted onto the review fixes.

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A fresh clone runs `uv sync` and finishes a small bench job without the gitignored `reference/nle-src`; every job records the NLE commit, lock hash and full bot SHA | VERIFIED | `scripts/fresh_clone_check.py` re-run by me at HEAD 8e17b1f535b707ee0c40a1bf72ad86b63e54d1df: exit 0, `nle_commit` cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72, `env_id` a8f58c2fda006264, `tests: passed`. `pyproject.toml` pins `nle = { git = "file://$HOME/git/nle-screens.git", rev = "cb9d6572..." }` and `uv.lock` records the same rev; the bare repo holds that commit (`git cat-file -t` = commit); `reference/` is gitignored. Live DB jobs 1 and 2 (fresh-clone worker_python path in their env) have 10 game rows each. All eight jobs carry a 40-char `sha`, `env.nle_commit`, `env.lock_sha256`, `lock_blob`, `env_id` (query on `jobs`). The NLE source is a machine-local bare repo (owner decision D-01), so "fresh clone" means fresh clone on this machine. |
| 2 | Natural baseline of `main` on dev seeds plus an A/A rerun with identical per-seed results; funnel lists every stage key with Wilson intervals; no decision path reads `rung` | VERIFIED | `SELECT COUNT(DISTINCT seed) FROM games WHERE sha='e5b5a7f5...' AND rep=0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL` = 10000 (job 7: 9,600 own rows, 400 reused from pilot job 3). Job 8: 2000 rows, rep 1, seeds 1000-2999, played 22:12-23:35 after job 7 finished. I re-ran the pre-registered A/A command verbatim: exit 0, `{"compared": 1999, "identical": 1999, "mismatched": 0, "skipped": {"watchdog": [2073]}, "common": 2000}`. `bench.cli funnel ... --lgen off` returns 18 rows (mines through ascended), n = 10000, each with `lo`/`hi` Wilson bounds; `/api/funnel?job=7` on the live server agrees. `test_no_decision_path_reads_rung` passes; `rung` remains only as a compared field in `replay_check`/`play_compare` and as display in `seeded_report`. `git diff --stat e5b5a7f5... main -- autoascend nethack_screensaver bench/worker.py bench/runner.py` is empty, so the baseline is of main's bot. |
| 3 | `lgen` pilot reports paired discordance with and without lgen and the decision is recorded; `sokoban_solved` detector run against a known hand game; 0/2304 has a written cause | VERIFIED | `01-LGEN-PILOT.md`: pre-registered rule committed (09b79fbb...) before jobs 3-6 existed; jobs 3/4/5/6 hold 400 games each (1600 in the DB); psi off 0.005 (b=2, c=0), psi seed 0.010 (b=3, c=1), paired difference 0.005 with interval [-0.007, 0.017], `decision: keep-lgen-off`, and `bench/seeds.py` has `USE_LGEN = "off"`. Detector: `tests/test_sokoban_detector.py` (in the 177-test subset run, all pass) replays the hand-played `soko-top` game; `sokoban_solved` fires once at T882. Cause: `01-SOKOBAN-CAUSE.md`. I re-ran its queries on job 7's rows: reached Sokoban 2544, solved 0, dropped 2256, all 2256 via `sokoban_unsolvable` on dunlev 4, `sokoban_live_solved` 0, ended inside Sokoban 262. The cause is stated as a bot failure (stored solution stops fitting the 5.0 board), with the first-failing push honestly left as an open question for Phase 2. |
| 4 | Exact McNemar and an always-valid sequential test, simulation shows false-positive rate holds under repeated checking, power calculator gives MDE and sample size before a run; dev/confirm/final ranges fixed; final-range seeds refused outside clean attempts | VERIFIED | `bench/stats.py`/`bench/sequential.py`/`bench/power.py` tests pass. Simulation: `scripts/sim_sequential.py --out /tmp/sim_check.json` is byte-identical (`cmp`) to `01-SIM-SEQUENTIAL.json` (seed 20261112, 20,000 reps). The mixture test under repeated checking rejects 2.2% (96-seed blocks) and 3.7% (every pair) at psi 0.05, both flagged `ok: true` against their bound; the legacy Wald checkpoints (7.0%) and a peeking McNemar (32.9%) show what the test fixes. `screens-bench power --mde 0.01` prints `n_planned` 2400; `start_experiment` raises when `mde` is not declared. Ranges in `bench/seeds.py`: tool 0-999, dev 0-99,999, confirm 100,000-199,999, final from 1,000,000. I called `check_window`: baseline and experiment windows at 1,000,000 are refused; confirm needs a gate; the tool block is refused for natural jobs. `Store.add_game` also refuses final-range seeds (store.py:127); `KINDS_OVER_HTTP` excludes `clean_attempt`. 97 tests in seeds/server/store/scheduler pass. |
| 5 | Tool runs land in `tool_games` with job IDs and never reach the funnel; `check_claims.py` rejects a claim without proof; a job is started only once its first game row exists; facts carry a ledger tag | VERIFIED | `tool_games` exists in the live schema; `staged_run.py`, `scenario_run.py`, `rewind.py` call `toolruns.record_run`/`add_result`; `Store` refuses a staged game in `games` (store.py:125); `test_bench_tool_games.py` and `test_bench_funnel.py` pass. The live table holds 0 rows, because no tool run has been recorded since the mechanism landed; it is proven by tests only. Claim checker (wired as the Stop hook in `.claude/settings.json`) exercised by me: "I started the baseline run." blocked (no proof); "Job 99999 finished; see job 99999." blocked (job does not exist); "Job 99999 has started; next I'll check the funnel." blocked (the CR-03 fix); a query with a wrong value blocked; an abbreviated hash blocked; a full 40-hex hash, "Job 5 is queued, not started" and forward-looking text pass. No network or LLM import in the script. Fact ledger: `facts/FACTS.toml` holds 64 `5.0-source` facts and 3 `unverified`; `scripts/facts.py check --source` exits 0; `tests/test_facts.py` passes. Started-from-first-row: `test_started_means_a_game_row_exists` passes. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `bench/provenance.py`, `scripts/fresh_clone_check.py` | env fingerprint, fresh-clone check | VERIFIED | check re-run, exit 0 |
| `bench/seeds.py`, `bench/store.py`, `bench/scheduler.py`, `bench/server.py` | ranges, refusal, game key, resume guard | VERIFIED | called directly; tests pass |
| `bench/funnel.py` | 18-stage funnel with Wilson intervals | VERIFIED | CLI and live `/api/funnel` agree |
| `bench/sequential.py`, `bench/power.py`, `scripts/sim_sequential.py` | sequential test, power, simulation | VERIFIED | simulation byte-identical |
| `bench/toolruns.py` | tool runs in `tool_games` | VERIFIED (mechanism) | 0 live rows |
| `scripts/check_claims.py` | claim checker, Stop hook | VERIFIED | adversarial probes above |
| `facts/FACTS.toml`, `scripts/facts.py` | fact ledger | VERIFIED | 67 entries, check exits 0 |
| `scripts/replay_check.py`, `scripts/lgen_pilot.py` | A/A and pilot tooling | VERIFIED | commands re-run |
| `01-PROOF.md`, `01-BASELINE.md`, `01-LGEN-PILOT.md`, `01-SOKOBAN-CAUSE.md`, `01-SOKOBAN-DETECTOR.md`, `01-SIM-SEQUENTIAL.json` | written evidence | VERIFIED | numbers re-derived from the DB |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `.claude/settings.json` Stop hook | `scripts/check_claims.py` | command hook | WIRED | script blocks on stdin payloads |
| `bench/server.py` results/games/dashboard | one game key | `_key()` (lgen mode, env, rep 0) | WIRED in code | live server not restarted, still pre-fix |
| `scripts/replay_check.py` | `Store.games_by_seed(rep=...)` | per-side rep | WIRED | A/A re-run |
| scheduler | seed guard | `check_seed` per game | WIRED | scheduler.py:236 |
| experiments | power plan and sequential judge | `powerlib.plan`, prefix judging | WIRED | start_experiment, tests |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| funnel rows | hits per stage | `games.json` ladder field of 10,000 stored games | yes (6081 mines ... 0 ascended) | FLOWING |
| Sokoban cause | event counts | `games.json` events of job 7 | yes (2256 drops) | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite | `.venv/bin/python -m pytest -q` | 856 passed, 6 skipped, 16 deselected | PASS |
| A/A | pre-registered `replay_check.py` command | exit 0, 1999/1999 identical | PASS |
| Fresh clone | `scripts/fresh_clone_check.py` | exit 0, tests passed | PASS |
| Simulation | `scripts/sim_sequential.py` vs stored report | byte-identical | PASS |
| Funnel | `bench.cli funnel ... --lgen off` | 18 rows, n 10000 | PASS |
| Final-range refusal | `seeds.check_window(1_000_000, ..., "baseline"/"experiment")` | ValueError | PASS |
| Fact ledger | `scripts/facts.py check --source` | exit 0 | PASS |

### Probe Execution

SKIPPED: no `scripts/*/tests/probe-*.sh` files and no probes declared in the plans.

### Requirements Coverage

All ten IDs appear in PLAN frontmatter and in ROADMAP Phase 1; no orphaned requirement.

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| MEAS-01 | 01-01, 01-08, 01-14 | SATISFIED | fresh clone, env recording in jobs 1-8 |
| MEAS-02 | 01-05, 01-12, 01-16 | SATISFIED | 18-stage funnel with Wilson intervals; rung out of decisions |
| MEAS-03 | 01-05, 01-06, 01-16 | SATISFIED | detector test on hand game; written cause with re-run queries |
| MEAS-04 | 01-05, 01-08, 01-14, 01-15 | SATISFIED | jobs 3-6, decision keep-lgen-off recorded |
| MEAS-05 | 01-08, 01-11, 01-15, 01-16 | SATISFIED | jobs 7 and 8 done; A/A pass |
| MEAS-06 | 01-02, 01-13 | SATISFIED | sequential test, simulation, power |
| MEAS-07 | 01-08, 01-10, 01-15 | SATISFIED | ranges and refusal at API, scheduler and store |
| MEAS-08 | 01-11 | SATISFIED | `tool_games`, store refusal (mechanism; 0 live rows) |
| MEAS-09 | 01-03, 01-11, 01-14, 01-16 | SATISFIED | claim checker probes, first-row start rule |
| MEAS-10 | 01-04, 01-07, 01-09 | SATISFIED | ledger with 64 source-quoted facts |

REQUIREMENTS.md still shows MEAS-01 to MEAS-09 as `[ ]` / Pending (only MEAS-10 is Complete). That is stale bookkeeping, not a code gap.

### Prohibitions (judgment-tier, non-authoritative verdicts)

| Prohibition | Plan | Verifier verdict | Evidence |
|-------------|------|------------------|----------|
| No push to a remote, no backup tooling | 01-01 | held | `git remote -v` empty; bare repo has no remote |
| No LLM, network or paid API in claim checking | 01-03 | held | script imports only json, re, sqlite3, subprocess and similar; grep finds no urllib, requests or socket |
| No bypass switch for the checker | 01-03 | held | only env vars are `SCREENS_BENCH_DATA`, `CLAUDE_PROJECT_DIR`, `CLAIM_CHECK_AUDIT` (path settings); `stop_hook_active` is logged, not a pass-through. A process that could set these could point at a different database, which is a limit of a tripwire |
| 5.0-source tag needs file:line and verbatim quote | 01-04 | held, weakly enforced | `check --source` exit 0; IN-03 (whitespace or one-character quotes accepted) is open |
| No clean_attempt or final seeds via HTTP or MCP | 01-10 | held | `KINDS_OVER_HTTP`, server.py:395 refusal, store refusal, tests |
| No dungeon screening | 01-15 | held | baseline is the contiguous window 1000-10999; no seed selection by features |
| No archive games imported or shown as current | 01-16 | held | `reference_games` has 0 rows; games table holds jobs 1-8 only; archive numbers in `01-SOKOBAN-CAUSE.md` are labelled "Archive history" |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `scripts/check_claims.py` | result-claim path | A result claim passes with any existing job whatever its state or numbers (review WR-02, partly fixed) | Warning | Weakens "claims without proof are rejected", but the stated criterion (no job ID, hash or query) is enforced |
| `scripts/replay_check.py` | options | No `--env-id`; `--lgen` defaults to any mode (WR-03, partly fixed) | Warning | The pre-registered A/A passes `--lgen off`, and all rows share one env, so the result stands |
| `scripts/facts.py` | check | Measured facts' queries not executed (WR-04); the ledger has no `measured` fact yet | Warning | Latent, deferred to the next fact tranche |
| `bench/cli.py` / `bench/power.py` | power | `--mde 0.05` (and the help example 0.03) traceback at the 0.019 default discordance (IN-02) | Info | Valid MDEs work (`--mde 0.01`) |
| `bench/funnel.py` | rows | `prev`/conditional rates chain in stage order, so `mines_end` shows `cond_n 0` after `sokoban_solved` | Info | Unconditional `rate` and Wilson bounds are correct; conditional columns can mislead |
| funnel data | flagged | 74 of 10,000 baseline games ended by exception and 2 by watchdog; they are flagged, not excluded | Info | Disclosed in the report |
| TBD/FIXME/XXX markers | n/a | none found in phase files | none | none |

### Human Verification Required

#### 1. Prohibition review

**Test:** Read the Prohibitions table above and accept or reject each non-authoritative verdict.
**Expected:** All seven accepted.
**Why human:** Judgment-tier prohibitions are never silently passed.

#### 2. Restart the bench server onto the fixed code

**Test:** Restart with `uv run screens-bench serve --resume` (no job is running), then `curl -s 'http://127.0.0.1:8765/api/results?ref=e5b5a7f525bc51b8008f665173600aba80de466d'`.
**Expected:** `games` = 10000. Today it returns 10400 because the process (started Nov 13) predates commits 79f6c85, dd023ff and d4f96b2.
**Why human:** The server is the owner's running service.

### Gaps Summary

No success-criterion gap. The foundation holds: the baseline, the A/A and the funnel re-derive from the live database, the statistics and seed guards are code-enforced and tested, and the claim checker blocked every unproven claim I tried that matched the stated criterion. Remaining caveats, all non-blocking: the live server still reports the pre-fix pooled count at `/api/results` until restarted; the claim checker accepts a result claim that cites any existing job; the NLE source lives in a single-disk local bare repo by owner decision; `tool_games` and measured facts are proven by tests but hold no live rows; ROADMAP (plans 01-15 and 01-16 unchecked, "14/16 plans executed", Phase 1 unchecked) and REQUIREMENTS (MEAS-01 to MEAS-09 pending) need updating by the orchestrator.

---

_Verified: 2026-11-14T01:30:00Z_
_Verifier: Claude (gsd-verifier)_
