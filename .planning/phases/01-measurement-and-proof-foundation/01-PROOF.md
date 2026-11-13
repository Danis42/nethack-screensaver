# Phase 1 proof index

One section per ROADMAP Phase 1 success criterion. Every statement cites a job ID, a full 40-hex commit, a `[query: ...]` or a test command the owner can re-run.

## 1. Fresh clone runs a bench job and every job records its environment

A fresh clone of commit e5b5a7f525bc51b8008f665173600aba80de466d installed with `uv sync --locked` without `reference/` and its tests passed (`uv run python scripts/fresh_clone_check.py`, output in 01-SKELETON-PROOF.md). Its server played the spare commit e0229dc28b9895f5ec37265cc0b7db4d1968d299 as job 1 (lgen off) and job 2 (lgen seed). Both job specs record `env.nle_commit` cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72, `env.lock_sha256`, `lock_blob` and `env_id` a8f58c2fda006264.

- [query: SELECT COUNT(*) FROM games WHERE job_id = 1 => 10]
- [query: SELECT COUNT(*) FROM games WHERE job_id = 2 => 10]
- Tests: `.venv/bin/python -m pytest -q tests/test_bench_provenance.py`

## 2. Natural baseline of main, A/A rerun, funnel

Baseline job 7 played commit e5b5a7f525bc51b8008f665173600aba80de466d on dev seeds 1,000-10,999 with lgen off; `baseline_rows: total=10000 own=9600 reused=400` (the 400 reused rows are pilot job 3's). A/A job 8 replayed seeds 1,000-2,999 as replicate 1.

- [query: SELECT COUNT(DISTINCT seed) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL => 10000]
- [query: SELECT COUNT(*) FROM games WHERE job_id = 8 => 2000]
- A/A verdict `aa_result: pass` from the command pre-registered in 539b31eabc1b11c90f7f2b84cb5348a0acf1da63, run verbatim: `.venv/bin/python scripts/replay_check.py e5b5a7f525bc51b8008f665173600aba80de466d e5b5a7f525bc51b8008f665173600aba80de466d --rep-b 1 --lo 1000 --hi 3000 --lgen off --min 2000 --skip-both watchdog --json` (exit 0; 1,999 compared, 1,999 identical, seed 2073 watchdog on both replicates). Recorded in 901c3a6570859b50fae20c5b28e10347be359dec.
- Funnel with Wilson intervals for all 18 stage keys: `.venv/bin/python -m bench.cli funnel e5b5a7f525bc51b8008f665173600aba80de466d --lo 1000 --hi 11000 --lgen off` (also `/api/funnel?job=7`).
- No decision path reads `rung`: `.venv/bin/python -m pytest -q tests/test_bench_funnel.py::test_no_decision_path_reads_rung`
- bot_of_main: git diff --stat e5b5a7f525bc51b8008f665173600aba80de466d main -- autoascend nethack_screensaver bench/worker.py bench/runner.py is empty (rechecked at 3b84daa2eeeeebb235df727f2a36dc57e3a0f9bd).

## 3. lgen pilot decision; Sokoban detector and the cause of the zero

The pilot played commit A e5b5a7f525bc51b8008f665173600aba80de466d and commit B c65c27011a737e33fc218350e1680460ed19f859 on seeds 1,000-1,399 as job 3 (A, off), job 4 (A, seed), job 5 (B, off) and job 6 (B, seed). The rule committed in 09b79fbb306764b9fae898b2c00a2e22158e4587 gave `decision: keep-lgen-off` in 01-LGEN-PILOT.md (commit 14493a5b56cda92bb0ecb9eb3bcff3356f0d5217).

- Re-run: `.venv/bin/python scripts/lgen_pilot.py --jobs 3 4 5 6 --metric dlvl10`
- [query: SELECT COUNT(*) FROM games WHERE job_id IN (3, 4, 5, 6) => 1600]
- Detector test: `.venv/bin/python -m pytest -q tests/test_sokoban_detector.py` (hand game in 01-SOKOBAN-DETECTOR.md)
- Cause of the zero: 01-SOKOBAN-CAUSE.md (commit 3b84daa2eeeeebb235df727f2a36dc57e3a0f9bd), from baseline job 7.

## 4. Statistics, simulation, power, seed ranges

- Exact McNemar and the Beta(1,1) mixture sequential test: `.venv/bin/python -m pytest -q tests/test_bench_sequential.py tests/test_bench_stats.py`
- Simulation report: `.planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json`, seed 20261112, re-run with `.venv/bin/python scripts/sim_sequential.py --out <path>` (byte-identical)
- Power and MDE: `.venv/bin/python -m pytest -q tests/test_bench_power.py`; `uv run screens-bench power`
- Seed ranges and the final-range refusal: `.venv/bin/python -m pytest -q tests/test_bench_seeds.py tests/test_bench_server.py tests/test_bench_scheduler.py tests/test_bench_store.py`

## 5. Tool games, claim checks, the first-game-row rule, the fact ledger

- tool_games kept out of the funnel: `.venv/bin/python -m pytest -q tests/test_bench_tool_games.py tests/test_bench_funnel.py`
- Claim checker: `.venv/bin/python -m pytest -q tests/test_check_claims.py`
- A job counts only once its first game row exists: `.venv/bin/python -m pytest -q tests/test_bench_store.py::test_started_means_a_game_row_exists tests/test_bench_mcp.py::test_bench_job_reports_started_and_first_game_at`
- Fact ledger: `.venv/bin/python -m pytest -q tests/test_facts.py` and `.venv/bin/python scripts/facts.py check --source` (exit 0); coverage in `01-FACT-COVERAGE.json`
