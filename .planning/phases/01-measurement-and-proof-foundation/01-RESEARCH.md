# Phase 1: Measurement and Proof Foundation - Research

**Researched:** 2026-11-12
**Domain:** Benchmark infrastructure (SQLite, process scheduler, uv packaging), paired/sequential statistics, claim-checking hook, NetHack fact ledger
**Confidence:** HIGH for the code seams and the uv/NLE packaging (read and executed this session); MEDIUM for the claim-detection design (the Stop hook contract is documented, the regex corpus is a design choice); `lgen` discordance and Sokoban root cause stay unmeasured until the pilots run (by design).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**NLE reproducibility (MEAS-01)**
- **D-01:** The NetHack 5.0 NLE fork (branch `screens-nh5`, 21 commits on upstream NLE `70cb9b526`, a ~388k-line diff — too large for a patch series) moves into a **local bare git repo at `~/git/nle-screens.git`**. Nothing is pushed to GitHub or any remote. — **Reversibility:** reversible — repo can later be pushed anywhere.
- **D-02:** `pyproject.toml` depends on it as a **uv git dependency pinned to a commit SHA** (e.g. `nle = { git = "file://$HOME/git/nle-screens.git", rev = "<sha>" }`), replacing the `path = "reference/nle-src"` source. `uv.lock` records the exact NLE commit; every bench job records NLE commit, lock hash and full bot SHA (success criterion 1).
- **D-03:** "Fresh clone" means a fresh clone of screens **on this machine** (the bare repo is a local path). Off-machine reproducibility is not a goal.
- **D-04:** **No off-disk backup step.** Owner accepts the risk that the fork exists only on this disk (verified: neither `archive/screens-v0-final.tar.gz` nor `archive/screens-all-branches.bundle` contains `nle-src`). Record this risk; don't add backup tooling.
- `reference/nle-src` has an untracked `paniclog`; the fork's working tree must be clean/committed before the SHA is pinned.

**Baseline, A/A and seed ranges (MEAS-05, MEAS-07)**
- **D-05:** Fresh natural baseline of `main`: **10,000 games** on dev seeds (~7 h unattended at ~25 games/min on 10 slots).
- **D-06:** A/A rerun: **2,000 seeds, a subset of the baseline seeds**; must show identical per-seed results.
- **D-07:** Seed ranges: **dev 0–99,999 · confirm 100,000–199,999 · final 1,000,000+**. Confirm seeds only at phase gates; final seeds only for clean attempts — the bench refuses final-range seeds otherwise. — **Reversibility:** costly — once games are stored on these ranges, moving boundaries invalidates the separation guarantees.
- **D-08:** **Interrupted jobs become resumable**: on server restart, a job marked `interrupted` (`Store.interrupt_unfinished`) can be resumed and plays only the seeds not yet stored. Supports multi-hour baseline runs surviving reboots.
- Context given to owner: the bench server (`uv run screens-bench serve`) runs jobs unattended; Claude only submits via MCP and receives a job ID.

**Claim checking (MEAS-09)**
- **D-09:** `check_claims.py` checks **Claude's replies to the owner**, run by a **Claude Code Stop hook** on the final message of each turn. Commit messages and planning docs are not checked by it.
- **D-10:** Cited proof is **verified to exist**, not just format-matched: job ID looked up in `results.db`; a "started" claim requires the job's first game row to exist; a commit hash must resolve in git (full hash); a cited query is re-run.
- **D-11:** On failure the hook **blocks** the reply; Claude must add proof or drop the claim.

**Fact ledger (MEAS-10)**
- **D-12:** Scope: **everything now** — all existing NetHack facts in `.planning/research/*.md` and in code (`autoascend/`, constants, thresholds, rules) are tagged during Phase 1, plus every new fact from then on.
- **D-13:** Tags: `5.0-source` (with file:line in `reference/nethack-5.0.0/` or the NLE fork), `measured` (with job ID/query), or `unverified`.
- **D-14:** **Web research step**: facts **not confirmed in the 5.0 source** get a web search (NetHackWiki, forums, bot write-ups) for extra context or better information; sources found are recorded in the entry. Facts already confirmed in 5.0 source skip it. Web material often describes 3.6 — note differences; **the 5.0 source wins on conflict**.
- **D-15:** Format: **one ledger file** (e.g. `.planning/FACTS.md` or a structured TOML/YAML file) with one entry per fact (id, claim, tag, evidence, web sources); code cites facts by ID (e.g. `# fact:prayer-timeout`); a test checks every cited ID exists in the ledger.
- **D-16:** Bot code **may use unverified facts**, but a report lists every unverified fact the bot depends on.

### Claude's Discretion
- Depth of the per-fact web research (left to Claude's judgement by the owner).
- Ledger file format details (Markdown vs TOML/YAML), fact-ID naming.
- How the Stop hook detects a progress claim (should be deterministic — e.g. pattern-based — not an LLM).
- Funnel report presentation (dashboard/CLI/MCP) and `tool_games` schema details.
- Statistical implementation details within MEAS-06.

### Deferred Ideas (OUT OF SCOPE)
- Off-disk backup of the NLE fork and screens repo (bundle to another drive or private mirror) — declined for now; risk accepted.
- Checking commit messages and planning docs with the claim checker — not chosen; could be added later.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEAS-01 | Fresh clone installs and runs bot + bench; NLE reproducible | Verified end to end: a bare clone of `screens-nh5` + `uv` git source + `rev = <full sha>` locks, builds (57 s) and installs; `direct_url.json` carries the commit (see "NLE as a uv git dependency"). Remaining hazards: `.mcp.json` hard-coded interpreter, stale `.venv` NLE (dev19), Lua download, `dungeon_truth.py` struct offsets. |
| MEAS-02 | Natural-game funnel by stage keys with Wilson intervals; `rung` out of decision paths | Funnel derivable from `GameResult.ladder` keys (17 keys listed below); `rung` is read in `bench/metrics.py:75-77` and `bench/report.py:19`; `stats.wilson` exists but divides by zero at n=0. |
| MEAS-03 | `sokoban_solved` detector checked against a known game; 0/2304 explained | Archive query: of 570 Sokoban entries in `72ca0b6`, 515 logged `sokoban_dropped`, 0 `sokoban_live_solved`, and all 52 games that ended in Sokoban ended on its entry level. The bot never clears level 1 of Sokoban, so the zero is most likely real, but the detector has never been exercised on a solved level; needs a staged/known-solution test. |
| MEAS-04 | `lgen` pilot (2 commits x ~400 seeds), effect on pairing, decision recorded | NLE `lgen` mechanics read in `nlernd.c`/`mklev.c`/`allmain.c`; `game.py` never passes `lgen`; worker protocol has no lgen field. Pilot design, plumbing and decision rule below. |
| MEAS-05 | Fresh natural baseline of `main` in the live DB + A/A | Live DB has 0 games; scheduler plays seeds `0..N-1` only; `Store.seeds()` is a full JSON scan (0.10 s per call at 10k rows, measured) and A/A duplicates would double-count in `Store.games()`. Needs seed ranges, a `seed` column, a replicate flag. |
| MEAS-06 | Exact McNemar + always-valid sequential test, validated by simulation; MDE/sample size declared before the run | Existing design (z99 early / z95 final, 5 looks) measured at 7.3-7.7% false verdicts under the null. Beta-mixture mSPRT on discordant pairs measured at 3.7% (alpha .05) under peeking at every pair. MDE table and stopping-time numbers below. |
| MEAS-07 | dev / confirm / final seed ranges; refusal outside clean attempts | Enforce at `App.start_*`, at `Scheduler` dispatch and at `Store.add_game` (defence in depth). Tool seeds 0-19 sit inside the dev range (open question). |
| MEAS-08 | Staged/scenario/rewind runs in a separate `tool_games` table with job IDs | `GameResult.stage` already flags staged games; staged/scenario/rewind scripts bypass the store today (print JSON). Schema and routing below. |
| MEAS-09 | Claim checker; "started" only after first game row | Stop hook contract verified in Claude Code docs (`last_assistant_message`, `stop_hook_active`, `decision: block`, 8-continuation cap). Detection grammar, proof grammar, read-only verification below. |
| MEAS-10 | Fact ledger tagged 5.0-source / measured / unverified | One TOML ledger + `scripts/facts.py` (check, report) + a pytest; scope is large (3,524 research lines, 13.4k bot lines): tranche it. |
</phase_requirements>

## Summary

Phase 1 is almost entirely work on `bench/`, `scripts/`, `pyproject.toml` and the NLE fork, plus two long unattended compute jobs. The existing bench is a good base (seeded games, per-commit worktrees, SQLite, MCP) but has six structural gaps that the requirements expose: (1) NLE comes from a gitignored path; (2) the store has no seed column, no environment fingerprint, no replicate concept, and no table for tool games; (3) the scheduler only knows seeds `0..N-1`; (4) decisions run on the legacy Wald paired interval at five checkpoints, which was measured here at 7.3-7.7% false verdicts under the null (nominal 5%); (5) `rung` feeds metrics and the dashboard; (6) nothing stops a claim without proof. None of these needs a new package: `scipy` (1.18.1 in the venv) gives `binomtest`, the mixture test is 10 lines with `math.lgamma`, TOML ledger parsing is stdlib `tomllib`.

The two long runs have a hard ordering. The `lgen` pilot (about 1,600 games, roughly 1 h) must finish and be decided **before** the 10,000-game baseline (roughly 7 h), because the decision changes how baseline games are seeded; the 2,000-game A/A (roughly 1.3 h) then reruns in the chosen mode. The scheduler runs one job at a time, so about 9-10 h of serial compute sits behind the code work. Pilot discordance also feeds the power calculator, so the MDE defaults cannot be fixed before it.

The most important correctness traps are: peeking by completion order instead of by contiguous seed prefix (long games finish late, so completion order biases toward fast deaths), counting A/A replicate rows as extra natural games, letting a docs-only commit change `main`'s sha and orphan the baseline (games are keyed by commit sha), and the Stop hook's 8-continuation cap (after eight consecutive blocks Claude Code overrides the block, so the checker must also write an audit log).

**Primary recommendation:** Build in this order: (W0) NLE bare repo + git-source `pyproject.toml`/`uv.lock` + fresh-clone check; (W1, parallel) store schema v2 with seed ranges/provenance/`tool_games`/resume, `sequential.py` + `power.py` + simulation, funnel + `rung` removal, `check_claims.py` + Stop hook, `facts.py` ledger tooling; (W2) `lgen` plumbing and Sokoban detector test; (W3, unattended) lgen pilot -> decision -> baseline -> A/A; (W4) analyses and decision records. Do not run any experiment on the live DB before W3.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| NLE build reproducibility | Repo / packaging (`pyproject.toml`, `uv.lock`, bare git repo) | Worker interpreter | The venv that plays games is what the fingerprint must describe |
| Job provenance (NLE commit, lock hash, bot SHA) | Bench server (`App.start_*`) | Worker interpreter (queried once for `direct_url.json`) | Server owns job creation; only the worker interpreter knows which NLE it imports |
| Seed ranges and final-range refusal | Bench server + Store | Scheduler (dispatch guard), `run_game` env guard | Refusal must hold for any path that writes a game row |
| Funnel and `rung` removal | Bench pure-logic module (`bench/funnel.py`) | Server API, MCP tool, dashboard | Pure function over stored JSON, easy to test; presentation is thin |
| Paired stats (McNemar, mSPRT, power) | Bench pure-logic modules (stdlib + scipy) | Scheduler `_judge`, server `start_experiment` | Stats must be testable without games; scheduler only feeds contiguous seed prefixes |
| `tool_games` routing | Store (schema + insert guards) | Scripts (`staged_run`, `scenario_run`, `rewind`) | `add_game` must reject `stage != None`; scripts register a job then insert tool rows |
| Resume of interrupted jobs | Store + Scheduler | CLI `serve --resume`, HTTP/MCP resume | Scheduler already skips stored seeds; only the state transition is missing |
| Claim checking | Claude Code Stop hook -> `scripts/check_claims.py` (stdlib only) | `results.db` read-only, `git` | Runs outside the bench server; must work when the server is down |
| Fact ledger | Repo file (`facts/FACTS.toml`) + `scripts/facts.py` + pytest | Code comments `# fact:<id>` | Citations live in code; checker lives in tests |
| Long compute (baseline, A/A, pilot) | Bench server (unattended) | Claude only submits and reports job IDs | Owner requirement: no dependence on an open Claude session |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.13 (`requires-python = ">=3.13,<3.14"`) | All code | Project constraint; system `python3` is 3.14.7 and has no scipy, so tools must run under `.venv/bin/python` (or be stdlib-only) |
| `sqlite3` (stdlib) | bundled | Store, schema v2, read-only claim queries | Already the store; `set_authorizer` + `mode=ro` give a safe query runner |
| `scipy` | 1.18.1 (installed, `uv.lock`) [VERIFIED: `.venv` import this session] | `scipy.stats.binomtest` = exact McNemar; `binom` for power | Already a dependency; no new package |
| `math.lgamma` (stdlib) | — | Beta-binomial mixture likelihood ratio | 10 lines; avoids a new dependency |
| `tomllib` (stdlib) | — | Fact ledger parsing | Already used by `nethack_screensaver/config.py` |
| `uv` | 0.12.23 installed [VERIFIED: `uv --version`] | git-source dependency, lock, sync | Project tool |
| `pytest` | 9.1.1 | Tests | Existing convention (`tests/test_<module>.py`, flat functions) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `numpy` | 2.5.4 (locked) | Vectorised simulation of sequential tests | `scripts/sim_sequential.py` only |
| `git` | 2.56.0 | Bare repo, `cat-file -e`, `rev-parse sha:uv.lock` | NLE repo, claim verification, lock blob id |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Beta-mixture mSPRT on discordant pairs | `confseq` (Howard et al.) | New dependency for a 10-line formula; not needed |
| Beta-mixture mSPRT | Group-sequential (O'Brien-Fleming) | More power when n_max is known, but only valid at pre-set looks; the bench runs in blocks and owner may stop early, so always-valid is the stated requirement |
| TOML ledger | Markdown ledger | Markdown needs a custom parser; TOML is stdlib-parseable and diff-friendly |
| Path source for NLE | Git source in a local bare repo (locked decision D-01/D-02) | Chosen by owner |

**Installation:** no new packages. NLE source switch only:
```toml
# pyproject.toml [tool.uv.sources]  -- replaces: nle = { path = "reference/nle-src" }
nle = { git = "file://$HOME/git/nle-screens.git", rev = "<40-char sha>" }
```
**Version verification:** `uv --version` -> 0.12.23; scipy 1.18.1 imported from `.venv`; no registry installs added. NLE version after git build: `1.3.1.dev21+gcb9d6572f`.

## Package Legitimacy Audit

No new external packages are recommended (scipy, numpy, pytest, mcp are existing locked dependencies; ledger and statistics use stdlib). The only dependency change is the source of `nle` (local bare git repo, owner-controlled). Build-time dependencies (`scikit-build-core`, `pybind11`, `setuptools-scm`) were already fetched from PyPI for the current build and were fetched again without change in this session's probe build.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none new) | — | — | — | — | — | — |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

One supply-chain note: the NLE build downloads `https://www.lua.org/ftp/lua-5.4.8.tar.gz` and checks it against a pinned SHA256 [VERIFIED: `reference/nle-src/CMakeLists.txt:124-132`, text: `URL https://www.lua.org/ftp/lua-${LUA_VERSION}.tar.gz` / `URL_HASH SHA256=4f18ddae154e793e46eeab727c59ef1c0c0c2b744e7b94219710d76f530629ae`]. A fresh clone needs network access to lua.org once per build; the hash makes a tampered download fail.

## Architecture Patterns

### System Architecture Diagram

```
 owner / Claude (MCP)                 Claude Code Stop hook
        |                                      |
        | bench_baseline / experiment /        | stdin: {last_assistant_message, stop_hook_active}
        | funnel / resume / power              v
        v                              scripts/check_claims.py (stdlib)
 +-----------------+                     | detect claims (regex)   | verify proofs:
 | bench server    |                     |                         |  job id  -> results.db (mode=ro)
 | App (validate:  |                     |                         |  started -> >=1 games row for job
 |  seed range,    |                     |                         |  commit  -> git cat-file -e (40 hex)
 |  declared MDE,  |                     |                         |  query   -> re-run via authorizer
 |  env fingerprint|                     v                         v
 +-------+---------+              exit 0 / {"decision":"block","reason":...}  + audit log
         | submit job (spec incl. seeds range, env, declared)
         v
 +-----------------+  play <seed> [lgen]   +-------------------------+
 | Scheduler       |---------------------->| worker proc (per slot)  |
 | one job at a    |<----------------------| PYTHONPATH=worktree(sha)|
 | time; seed-order|  1 JSON GameResult    | WORKER_PYTHON venv: NLE |
 | contiguous      |                       +-------------------------+
 | prefix looks    |
 +----+-------+----+
      |       |   natural (stage None)                tool runs (staged/scenario/rewind/pilot)
      |       +--> games (sha, seed, lgen, env, rep)    scripts --> jobs(kind=tool) + tool_games
      |                  |
      |                  +--> funnel.py (17 ladder keys, Wilson) --> /api/funnel, MCP, dashboard
      |                  +--> sequential.py (exact McNemar + mSPRT over discordant pairs) --> verdict
      v
 jobs.spec: {sha, seeds:[lo,hi), env:{nle_commit, lock_blob, lock_sha256, ...}, declared:{mde,alpha,power,psi,n}}

 fact ledger:  facts/FACTS.toml <-- "# fact:<id>" in code  <-- tests/test_facts.py (+ scripts/facts.py report)
```

### Recommended Project Structure
```
bench/
├── seeds.py        # DEV/CONFIRM/FINAL ranges, tool-seed reserve, range_of(seed), refuse_final()  (stdlib only)
├── funnel.py       # funnel(games) over ladder keys, Wilson CI, exclusions counted           (stdlib only)
├── sequential.py   # discordance counts, exact McNemar, Beta-mixture mSPRT, verdict          (stdlib + scipy)
├── power.py        # MDE(n, psi), sample_size(mde, psi), planned n_max                         (stdlib + scipy)
├── provenance.py   # env fingerprint: worker NLE commit, lock hashes, python/numba versions
├── store.py        # schema v2: games(seed, lgen, env_id, rep), tool_games, envs, resume()
scripts/
├── check_claims.py # Stop hook entry; stdlib only so it runs under any python3
├── facts.py        # check / report for the ledger
└── sim_sequential.py  # false-positive and power simulation report (writes JSON + prints table)
facts/FACTS.toml    # the ledger (repo root, not .planning: code docstrings already dangle on deleted planning files)
.claude/settings.json  # Stop hook (new file, committed)
tests/test_bench_seeds.py, test_bench_funnel.py, test_bench_sequential.py, test_bench_power.py,
      test_bench_provenance.py, test_bench_tool_games.py, test_check_claims.py, test_facts.py
```
Follow the repo's conventions [VERIFIED: `.claude/CLAUDE.md`]: pure-logic modules are stdlib/numpy only so `bench/` can import them; workers must not import `bench`; scripts print JSON lines; narrow `except` with a comment; no new bare `except`.

### Pattern 1: NLE as a uv git dependency (verified in a scratch project)
**What:** `git clone --bare reference/nle-src ~/git/nle-screens.git`; pin `rev` to the full SHA of `screens-nh5` HEAD. In this session I cloned the fork to a scratch bare repo, wrote a probe `pyproject.toml` with `nle = { git = "file://.../nlebare.git", rev = "cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72" }`, and ran `uv lock` then `uv sync`.
**Observed (verbatim):**
- `uv.lock`: `version = "1.3.1.dev21+gcb9d6572f"` and `source = { git = "file:///…/nlebare.git?rev=cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72#cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72" }`
- `uv sync`: `Prepared 1 package in 56.37s`; `+ nle==1.3.1.dev21+gcb9d6572f (from git+file:///…/nlebare.git@cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72)`
- Installed `direct_url.json`: `{"url":"file:///…/nlebare.git","vcs_info":{"vcs":"git","commit_id":"cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72","requested_revision":"cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72"}}`
- `import nle; nle.__version__` -> `1.3.1.dev21+gcb9d6572f` run from a different cwd with `python -I`.
**Use for the fingerprint:** read `importlib.metadata.distribution("nle").read_text("direct_url.json")` in the **worker interpreter** (`WORKER_PYTHON`) and store `vcs_info.commit_id`. Do not parse `nle.__version__` (it only carries an abbreviated hash and depends on tags).
[VERIFIED: scratch probe run this session; tag: observed output]

### Pattern 2: Job provenance + env fingerprint (success criterion 1)
Record at job creation (server) and per game row (`games.env_id`):
`bot_sha` (full 40 hex, already resolved by `gitrefs.resolve`), `nle_commit` (worker `direct_url.json`), `nle_version`, `lock_blob` (`git rev-parse <sha>:uv.lock`), `lock_sha256` (of the server checkout's `uv.lock`, i.e. what the venv was synced from), `python` version, `numba`/`numpy` versions, and `worker_python` path. Compute the worker facts once at server start by running `WORKER_PYTHON -I -c "..."` (a subprocess; the server must not import `nle` itself). Games reuse ("stored games are reused") must require equal `env_id`; experiments refuse to pair games from different `env_id` (this is Pitfall 9 in `.planning/research/PITFALLS.md`).

### Pattern 3: Store schema v2 (empty live DB, so migration is cheap)
Current schema [VERIFIED: `bench/store.py:8-24`, text: `SCHEMA_VERSION = 1`, `END_STATES = ("done", "stopped", "failed", "interrupted")`, tables `meta`, `games`, `jobs`, `reference_games`]. `games` is `(id, sha, job_id, finished_at, json)`; the seed is only inside `json`, and `Store.seeds(sha)` runs `SELECT DISTINCT json_extract(json, '$.seed') ...` on every scheduler tick and every idle slot.
**Measured:** 10,000 rows of ~9.2 KB JSON, `seeds()` costs 0.10 s per call (in-memory; disk is slower). With `tick` every 0.2 s and several idle slots this holds `app.lock` for most of each tick at 10k games.
**Proposed v2 (bump `SCHEMA_VERSION` to 2, migrate with `ALTER TABLE` + backfill, the live DB has 0 games):**
```sql
ALTER TABLE games ADD COLUMN seed INTEGER;            -- backfill from json
ALTER TABLE games ADD COLUMN lgen INTEGER;            -- NULL = lgen off
ALTER TABLE games ADD COLUMN env_id TEXT;             -- fingerprint id
ALTER TABLE games ADD COLUMN rep INTEGER NOT NULL DEFAULT 0;   -- 0 = the natural row, 1.. = A/A replicates
CREATE INDEX games_by_sha_seed ON games (sha, seed, rep);
CREATE TABLE envs (id TEXT PRIMARY KEY, json TEXT NOT NULL);
CREATE TABLE tool_games (
    id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL, tool TEXT NOT NULL,   -- staged|scenario|rewind|pilot
    sha TEXT NOT NULL, seed INTEGER, finished_at REAL NOT NULL, json TEXT NOT NULL);
CREATE INDEX tool_games_by_job ON tool_games (job_id);
```
- `Store.add_game` must **raise** when `result.get("stage")` is truthy (MEAS-08) or when the seed is in the final range and the job kind is not `clean_attempt` (MEAS-07). `bench import results` (`bench/cli.py:81`) goes through the same method.
- `Store.games()`, `seeds()`, `games_by_seed()`, `count()` filter `rep = 0`; A/A uses `rep = 1` so the funnel and `report.summary` never double-count.
- Natural pairing key is `(sha, seed, lgen, env_id)`; never pair an lgen game with a non-lgen game.
- Add `Store.started(job_id)` -> `EXISTS (SELECT 1 FROM games WHERE job_id = ?)` (also check `tool_games`); expose `started` and `first_game_at` in `/api/jobs/<id>` and `status()` (MEAS-09 "started" rule). A baseline job that finds every seed already stored finishes with no rows of its own; report it as `started: false, games_reused: N` rather than inventing a start.

### Pattern 4: Seed ranges and explicit job seeds
Replace "seeds `0..N-1`" [VERIFIED: `bench/scheduler.py:3-4`, docstring: "a job needs seeds 0 .. N-1 of each commit"] with `spec["seeds"] = {"range": "dev", "lo": L, "hi": H}` and compute `_targets()/_wanted()/_played()` from it. Constants, quoted from D-07: dev `0–99,999`, confirm `100,000–199,999`, final `1,000,000+`. Recommended rules in `bench/seeds.py`:
- `range_of(seed)` -> `"dev" | "confirm" | "final" | "unassigned"`; seeds 200,000-999,999 are `unassigned` and refused (nothing in D-07 allows them).
- Dev: always allowed. Confirm: allowed only when the job spec carries `gate: "<phase gate id>"`. Final: only `kind == "clean_attempt"`, and that kind is **not** creatable through `/api/jobs` or MCP (CLI only). Enforce in `App.start_*`, in `Scheduler._dispatch` (assert before `play`) and in `Store.add_game`.
- `run_game` and worker are unaware of ranges; do not put policy in the worker (old commits must keep working).
This refusal guards accidental misuse, not an adversary: Claude can reach the HTTP API directly. State that in the test docstring and in the final report.

### Pattern 5: Resume interrupted jobs (D-08)
`Store.interrupt_unfinished` [VERIFIED: `bench/store.py:125-128`, SQL text: `UPDATE jobs SET state = 'interrupted', ended_at = ? WHERE state IN ('queued', 'running')`] runs at every server start (`bench/cli.py:28`). Add `Store.resume(job_id)`: only from `interrupted`, sets `state='queued', ended_at=NULL`, keeps the **same job ID** (claims cite job IDs, so a new ID would orphan them). The scheduler already plays only seeds not stored (`_wanted` subtracts `store.seeds(sha)`), so resume needs no scheduler change beyond the new seed-range targets. Add `POST /api/jobs/<id>/resume`, MCP `bench_resume`, and an opt-in `serve --resume` that resumes all interrupted jobs at startup. In-flight games at the kill are lost and replayed (acceptable, deterministic).

### Pattern 6: Funnel replaces `rung` (MEAS-02)
Stage keys, verbatim [VERIFIED: `autoascend/ladder.py:22-40`]: `mines`, `minetown`, `oracle`, `sokoban`, `sokoban_solved`, `mines_end`, `dlvl15`, `quest`, `medusa`, `castle`, `gehennom`, `vlad`, `wizard_tower`, `invocation`, `planes`, `astral`, `ascended` (17 keys; `BY_KEY` and `RUNGS` import without game code).
`rung` readers to remove from decision paths [VERIFIED by grep this session]: `bench/metrics.py:75-77` (`Metric("rung", …, lambda g: g["rung"])` and the generated `rung{N}` rate metrics, which `start_experiment` accepts as rate metrics), `bench/report.py:19` (`g["rung"] >= r.number`), and the dashboard column in `bench/static/index.html:119`. `GameResult.rung` may stay as a stored descriptive field.
Funnel rule: stage `k` is "reached" iff `k in game["ladder"]` (marginal reach; stages are not strictly nested, e.g. `mines_end` does not require `sokoban_solved`). Denominator = all natural started games (rep 0, matching env/lgen, inside the requested seed range). Count separately, never drop silently: games without a `ladder` field, `ladder_error > 0`, `end_reason == "watchdog"`, `end_reason` starting `exception`. Add conditional rates along the pipeline order for the report. Replace metrics by `stage_<key>` rate metrics (`lambda g: key in g["ladder"]`). Guard `wilson` against `n == 0` (current code divides by zero). Add a test that greps `bench/` for `["rung"]`/`rungN` and fails on a decision use.

### Pattern 7: Exact McNemar + always-valid sequential test (MEAS-06)
Data per experiment: for each seed in a contiguous completed prefix, `(cand, base)` booleans for the declared metric. `b` = cand-only successes, `c` = base-only successes, `d = b + c` discordant. Everything depends only on `(b, c)`.
- **Exact McNemar** = conditional exact binomial: `scipy.stats.binomtest(b, b + c, 0.5).pvalue` (two-sided). Valid at one pre-declared sample size only.
- **Always-valid test** = Beta(a,a) mixture over the success probability of a discordant pair against 1/2. The log mixture likelihood ratio is
  `log LR = lgamma(b+a) + lgamma(c+a) - lgamma(b+c+2a) - (2*lgamma(a) - lgamma(2a)) + (b+c)*log(2)`
  and the test rejects when `log LR >= log(1/alpha)`; the anytime-valid p-value is `min(1, 1/max_t LR_t)`. Ville's inequality bounds the chance that the martingale ever reaches 1/alpha by alpha. [CITED: Johari, Pekelis, Walsh, "Always valid inference", arxiv.org/abs/1512.04922; mixture LR is a nonnegative martingale under the null, Ville bound — per the search digest of that paper]. The Beta-binomial form is the standard conjugate special case; its validity here is also checked by simulation below, not only by citation.
- **Look schedule:** looks only at **contiguous completed seed prefixes** (all seeds `lo .. lo+n-1` done on both sides), in blocks (e.g. every 96 or 192 seeds). Never look at "games finished so far": long games finish later, so completion order is outcome-dependent and breaks the martingale argument.
- **Verdicts:** `better`/`worse` when the mixture test crosses (sign of `b - c`; `orient()` still flips for lower-is-better); `no detectable effect >= MDE` at the declared `n_max` when no crossing (power 80% against the declared MDE, so "no difference" is only claimed relative to it); `open` otherwise.
- **Reporting:** `b`, `c`, `n`, point estimate `(b-c)/n`, exact McNemar p at the final look (descriptive if looks were taken earlier), anytime-valid p. A paired Wald interval may be shown but labelled descriptive.

**Simulation results (run this session; seed values in the scripts; `.venv/bin/python`):**

| Check | Result |
|-------|--------|
| Legacy `judge_paired`, z99 at 192/384/576/1152, z95 at 2304, null, discordance 0.05 / 0.2 / 0.4 | false-verdict rate 7.3% / 7.5% / 7.7% (20,000 reps each) |
| mSPRT Beta(1,1), alpha .05, looking after every discordant pair up to 2,000 | 3.7% false positives (20,000 reps) |
| mSPRT looking every 10 discordant pairs | 1.8% |
| Fixed exact McNemar peeked every 20 discordant pairs up to 2,000 | 33.6% false positives (4,000 reps) |
| Fixed exact McNemar at 5 looks (100..500 discordant pairs) | 11.9%; a single look at 500: 4.4% |
| mSPRT power/stopping, psi .2, delta .03, n_max 4,000 | power 0.86, mean stop 2,091 pairs, median 2,003 |
| psi .2, delta .04, n_max 3,000 | power 0.97, median stop 1,034 |
| psi .1, delta .02, n_max 6,000 | power 0.96, median stop 2,160 |
| psi .3, delta .05, n_max 3,000 | power 0.96, median stop 1,053 |
| psi .2, delta .03, looks every 96 seeds | power 0.83, median stop 2,256 |

The planner should turn `scripts/sim_sequential.py` into the committed validation ("a simulation shows its false-positive rate holds under repeated checking") with fixed RNG seeds, writing a JSON report, plus a small fast pytest (few thousand reps, fixed seed) asserting false positives <= alpha + tolerance.

### Pattern 8: Power calculator and declared MDE
Let `n` = paired seeds, `psi` = probability a seed is discordant (cand and base outcomes differ), `delta = P(cand only) - P(base only)`. Number of discordant pairs `ND ~ Binomial(n, psi)`; given `ND`, `b ~ Binomial(ND, theta)` with `theta = (psi + delta) / (2*psi)`. Exact power = sum over `ND` of `P(ND) * P(reject | ND, theta)`, where rejection is the exact two-sided binomial test at alpha. MDE inverts it by bisection; sample size inverts it over `n`.
**MDE table (absolute difference in rate, 80% power, exact McNemar two-sided .05; computed this session):**

| n pairs \ psi | 0.05 | 0.10 | 0.20 | 0.30 | 0.40 |
|---|---|---|---|---|---|
| 400 | 0.0321 | 0.0456 | 0.0644 | 0.0786 | 0.0905 |
| 1,000 | 0.0203 | 0.0287 | 0.0404 | 0.0493 | 0.0569 |
| 2,000 | 0.0144 | 0.0202 | 0.0284 | 0.0348 | 0.0401 |
| 5,000 | 0.0090 | 0.0127 | 0.0179 | 0.0219 | 0.0252 |
| 10,000 | 0.0064 | 0.0089 | 0.0126 | 0.0154 | 0.0178 |

`psi` is the missing input. It is stage- and change-dependent and unknown until the `lgen` pilot and the baseline exist, so `bench_experiment` must **require** `mde` (and accept `discordance`, default from the latest pilot upper bound) and refuse to start without it; store `declared = {metric, mde, alpha, power, psi, n_planned}` in `jobs.spec`. Use the pilot's upper confidence bound on `psi` for sizing (larger `psi` needs more pairs). Provide `screens-bench power` and an MCP `bench_power` tool.

### Pattern 9: `lgen` plumbing and pilot (MEAS-04)
**What the build does** [VERIFIED by reading `reference/nle-src/src/allmain.c:799-801`, `src/mklev.c:1586-1600`, `src/nlernd.c:108-140`]: under lgen, `init_objects()`, `role_init()`, `init_dungeons()`, `init_artifacts()` and `u_init_misc()` (all inside `nle_swap_to_lgen(0)` ... `nle_swap_to_core(0)`) and every `mklev()` run on a per-dungeon ISAAC stream derived from the lgen seed; the core RNG state is stashed and restored around them. So with lgen set, object appearances, dungeon structure and every later level layout (and the monsters/objects placed at level creation) no longer depend on how many core-RNG draws the bot made. Monsters spawned and fights during play still use core, so paired games still diverge after the first behavioural difference.
**Seed API:** `set_initial_seeds(self, core, disp, reseed=False, lgen=None)` [VERIFIED: `nle/nethack/nethack.py:298`]. Today `game.py:317` calls `type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False)` (no lgen) [VERIFIED: file read]. The fork's last commit makes `lgen == 0` mean "dice only" in `nle_set_seed` (`if (lgen) { ... }`, `src/nlernd.c`), so **never pass `lgen=0`** for "on"; use a nonzero derived value, e.g. `lgen = seed + LGEN_OFFSET` (record it).
**Plumbing needed (all backwards compatible):** `run_game(..., lgen=None)` passes it to `set_initial_seeds`; `GameResult.lgen: int | None = None` (default keeps old log lines loadable); worker accepts `play <seed> [lgen]` and passes `lgen` only if `"lgen" in inspect.signature(run_game).parameters` (same pattern as `can_seed` at `bench/worker.py:26`); job spec `lgen: "off" | "seed"`; store column `games.lgen`.
**Pilot design (success criterion 3):** two commits A and B that **both** contain the lgen plumbing (so `main` after the plumbing commit, and the same plus one small real behaviour change; pick a mid-game change, an early-acting one inflates discordance). 4 runs: {A, B} x {lgen off, on} on the same ~400 seeds (about 1,600 games, roughly 1 h at 25 games/min). Primary outputs per mode: discordance `psi` for the declared metric (plus a few stage metrics), the share of seeds with identical full results, and the exact McNemar / mSPRT outcome; compare `psi_off` vs `psi_on` with a paired interval on the same seeds. Also compare per-stage reach rates lgen-on vs lgen-off on the same seeds (Wilson) to check lgen does not shift the game distribution. **Write the decision rule before the run** (e.g. adopt lgen if `psi_on` is lower than `psi_off` with the interval excluding no change and no stage rate shifts beyond its interval). Record the decision with both pairs of job IDs in a committed file and in a `USE_LGEN` constant in `bench/seeds.py`. Note for the decision record: bench `lgen` pairing is not the "dungeon screening" the owner approved for the final attempt; screening means choosing seeds by dungeon features, which is separate (ASC-02).

### Pattern 10: Baseline, A/A and the commit-SHA trap
Games are keyed by **commit sha** [VERIFIED: `bench/store.py:13-16`, `games.sha`]. Any commit, including a docs-only one, gives `main` a new sha with zero stored games. The baseline must therefore be run on a **named commit** (the last Phase-1 commit that touches bot-affecting code: `game.py`, `autoascend/`, worker, `pyproject.toml`/`uv.lock`), and Phase 2 experiments must name that sha as their baseline, not `main`. Tag it or write it in the decision record. Optional improvement (open question): key games by a "bot tree hash" so docs/bench-only commits reuse them.
A/A (D-06): a new job kind `aa` (or `baseline` with `replicate: 1`) that plays 2,000 of the baseline's seeds into `rep = 1` rows and compares with the `rep = 0` rows. Reuse the comparison semantics of `scripts/replay_check.py` [VERIFIED: file read]: compare a fixed field list and treat `watchdog` endings separately, because a watchdog ending "depends on machine load, not on the seed" (its own docstring, `--skip-end`). Report "identical on K of N seeds, M watchdog-affected seeds excluded and listed".

### Pattern 11: `tool_games` routing (MEAS-08)
`scripts/staged_run.py` states its results "never go into the bench store" (docstring) but only prints JSON; `scenario_run.py` and `rewind.py` likewise. Add a shared helper (e.g. `bench/toolruns.py`) used by all three with `--record`: it opens the store (WAL + 30 s timeout allow a second process), creates a job `kind in {"staged","scenario","rewind"}` with the spec (tool, args, sha, seed list), inserts each result into `tool_games`, sets the job `done`, and prints the job ID. Job IDs share the single `jobs.id` sequence so claims stay unambiguous. Funnel/results/dashboard read only `games`. Test both directions: a staged result passed to `add_game` raises; a tool run never appears in `funnel()`. `GameResult.stage` [VERIFIED: `nethack_screensaver/game.py:82`, text: `stage: str | None = None  # staged (wizard-mode) game: never mixed into natural-play rates`] is the routing key.

### Pattern 12: Claim checker as a Stop hook (MEAS-09, D-09..D-11)
**Hook contract** [CITED: https://code.claude.com/docs/en/hooks, "Stop" section, read this session]:
- Stop input adds `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons`. `last_assistant_message` "contains the text content of Claude's final response".
- Block with `{"decision": "block", "reason": "..."}` on stdout (exit 0), or exit 2 with the reason on stderr.
- Loop protection: "`stop_hook_active` is `true` when Claude Code is already continuing as a result of a stop hook", and "after stop hooks have continued the turn eight times in a row, Claude Code overrides the next block and ends the turn" (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it).
- Stop hooks take no matcher; project hooks go in `.claude/settings.json`; command hooks default to a 600 s timeout, so set an explicit small `timeout`.
```json
{"hooks": {"Stop": [{"hooks": [{"type": "command",
  "command": "${CLAUDE_PROJECT_DIR}/.venv/bin/python ${CLAUDE_PROJECT_DIR}/scripts/check_claims.py",
  "timeout": 30}]}]}}
```
(Verify the exact argument form of `command` against the docs page during implementation; the doc example used `"args": []` alongside `command`.)
**Consequences for design:**
1. The 8-block cap means a persistent violation eventually gets through. The checker must append every decision (pass/block, claim, reason) to an audit log (e.g. `.claude/claim-checks.jsonl`, gitignored) so the owner can audit; report the cap limitation to the owner.
2. Only the **final** message of a turn is seen; text before tool calls is not. Document it.
3. `stop_hook_active = true` is not a reason to skip checking; it is a reason to include a "drop the claim or add proof" instruction and to avoid unbounded repetition.
4. The script must be stdlib-only (system `python3` is 3.14.7 with no scipy; the hook should not depend on `uv run` startup) and must fail safe on its own crashes: print a warning, exit 0, log loudly (a crash is not a failed claim). Flag this to the owner because D-11 says "block on failure".
**Detection grammar (deterministic, tested against a corpus):** a *progress claim* is a sentence matching (verb of progress) AND (bench noun or number-with-metric), for example `started|launched|kicked off|queued|running|finished|completed|passes|passed|improved|reduced|raised|reached|fixed` together with `job|run|baseline|experiment|A/A|bench|games|seeds|funnel|rate|%|\d+/\d+`. Explicit sub-rules: a *start claim* (`started|launched|running|kicked off|queued` + job/run/baseline/experiment) requires a verified job ID with at least one `games` (or `tool_games`) row; a *result claim* (percentages, n/N, "rate", "significant") requires a verified job ID, full commit hash or re-runnable query. Build `tests/data/claims_*.txt` with at least 40 labelled positives and negatives from real past owner-visible replies; tune patterns until false positives are rare, because a hook that blocks on every "fixed" gets disabled.
**Proof grammar (canonical, so verification is mechanical):** `job 123` or `job #123`; a 40-hex commit hash (abbreviated hashes do not count, per MEAS-09); `[query: <SELECT ...> => <expected>]`.
**Verification:** job ID -> read-only open `file:<db>?mode=ro` (`sqlite3.connect(uri=True)`), `SELECT` by id; started -> `EXISTS` in `games`/`tool_games`; commit -> `git -C <repo> cat-file -e <40hex>^{commit}` (hex-validated, so no option injection); query -> open read-only, `PRAGMA query_only=ON`, `set_authorizer` allowing only `SQLITE_SELECT`/`SQLITE_READ`/`SQLITE_FUNCTION`, one statement, progress-handler time cap, compare the first cell with the expected value.

### Pattern 13: Fact ledger (MEAS-10, D-12..D-16)
**Format (discretion, recommended):** `facts/FACTS.toml` in the repo root, one table per fact:
```toml
[prayer-timeout-too-soon]
claim = "Praying with timeout > 200 and major trouble is 'too soon' (p_type 0)"
tag = "5.0-source"                       # 5.0-source | measured | unverified
evidence = ["reference/nethack-5.0.0/src/pray.c:LINE"]   # 5.0-source: file:line, quote must be in the range
quote = "verbatim line(s) from the source"
# measured: job = 123  and/or  query = "SELECT ..."
web = ["https://..."]                    # sources consulted (D-14); required when tag != 5.0-source
notes = "3.6 differs: ..."               # optional
```
Reason for the repo root instead of `.planning/`: `.claude/CLAUDE.md` already records that code docstrings point at deleted planning files (e.g. `autoascend/prayer.py` cites `.planning/phases/01-midgame-survival/...`, which does not exist).
**`scripts/facts.py`:** `check` (always runs in pytest): TOML parses; ids unique and `[a-z0-9-]+`; `tag` valid; required fields per tag; every `# fact:<id>[, <id>]` in `autoascend/`, `nethack_screensaver/`, `bench/` resolves; `measured` facts cite a job that exists in a DB when available, else a query text. `check --source` (local only, skipped when `reference/` is absent because `reference/` is gitignored): the cited file exists, the line range exists and `quote` occurs in it. `report`: every `unverified` fact that some code cites (D-16). Citations in code are comments, not imports, so no runtime coupling.
**Scope control (D-12 says everything now):** 3,524 lines of research notes plus 13.4k bot lines. Tranche by decision impact and time-box each: (1) tool + tests; (2) the ~10 modules that already cite NetHack source (`castle`, `medusa`, `passtune`, `digging`, `telepathy`, `prayer`, `stair_escape`, `character`, `glyph/__init__`, `global_logic`, `agent`, plus the generated `objects/data.py` as one entry whose evidence is its generator `scripts/gen_objects_data.py` and `include/objects.h`); (3) rules and thresholds in the rest of `autoascend/`; (4) the research notes, starting with the ones that carry `UNVERIFIED` marks (16 marks across 6 files). Produce a coverage report (files with game-number literals and no `fact:` citation) so "everything" is measurable, and state plainly that the checker cannot detect untagged facts, only measure citation coverage.
**Authority for `5.0-source`:** `reference/nethack-5.0.0/` is the pristine source; the code actually run is `reference/nle-src` (NetHack 5.0 plus NLE patches). Allow both path prefixes and, once the fork lives in the bare repo, prefer the fork for "what the bot really plays". Both directories are gitignored, so source checks cannot run in a fresh clone (accepted by D-03/D-04).
**Seed facts already verified this session** (use as the first ledger entries): Sokoban entry level is the **last** dunlev: `reference/nethack-5.0.0/src/dungeon.c:945-947`, text `if (dgn_entry < 0) { svd.dungeons[dngidx].entry_lev = svd.dungeons[dngidx].num_dunlevs + dgn_entry + 1;` with `entry = -1` and `base = 4` for Sokoban in `dat/dungeon.lua:219-233`; so dunlev 4 is the entry and dunlev 1 (`soko1`) is the top, matching the `ladder.py` docstring ("Sokoban 1 is its top level") [VERIFIED: files read this session].

### Pattern 14: Sokoban detector and the 0/2304 (MEAS-03)
**Detector** [VERIFIED: `autoascend/ladder.py:83-84, 111-112`]: `sokoban_solved` fires only when `(f.dungeon, f.level) == (SOKOBAN, 1)`, at least `SOKOBAN_DRAWN = 100` squares seen, a trap glyph was seen on that level, and none is left; the facts come from `ladder_facts()` (`global_logic.py:737`, `sokoban_traps=bool(utils.isin(level.objects, G.TRAPS).any())`).
**Archive evidence (read-only query of `archive/screens-v0-final.tar.gz` -> `results.db`, sha `72ca0b63de44c38af34650ab6c7141b44f868425`, 2,304 seeded games; run this session):** `mines` key in 1,343; `sokoban` key in 570; `sokoban_dropped` event in 515 of those; `sokoban_live_solved` in 0; `sokoban_solved` key in 0; games ending inside Sokoban: 52, **all on level 4** (the entry level). The bot's code path that logs `sokoban_dropped` is `global_logic.py:887-889` (`self.agent.stats_logger.log_event('sokoban_dropped')`; `self.plan.drop_sokoban()`; `raise AgentPanic('sokomap unsolvable')`).
**Reading:** the bot never gets past the first Sokoban level, so the detector (which sits on the top level, dunlev 1) is never reached; the zero is most likely a real bot failure, not a detector bug. But the detector has never been exercised on a solved top level, so it still needs its own test. The stored solution replays pass (`tests/test_soko_solver.py`) and real-board fixtures exist (`tests/data/soko_real_between_pits.json`, `soko_real_bottom_timeout.json`), so the failure is in matching or executing on a live board, not in the stored solutions.
**Plan the check as two parts:** (a) a *detector test on a known solved game*: stage the Sokoban top level in wizard mode (staging.py already does wizard-mode ^V level teleport for `medusa`/`castle`/`valley`; whether a Sokoban level is selectable in the ^V menu needs a short spike) and replay a stored solution for that level while `Ladder.observe(ladder_facts())` runs, asserting `sokoban_solved` appears and appears once; if the spike fails, fall back to feeding the recorded real-board JSON through `Facts`; (b) a *written cause* for the 0/2304 from the fresh baseline: count `sokoban_dropped`, group by the failing branch (`sokomap not found` assert vs "unsolvable"), and state per-level stage reach. The event counter does not distinguish the two drop causes, so add a distinguishing event (this changes bot telemetry only, so it must be bit-identical in play; run it before the baseline so the baseline already carries it).

### Anti-Patterns to Avoid
- **Peeking by completion order:** biases toward short games; use contiguous seed prefixes.
- **Putting the lgen/seed policy in the worker:** old commits lack `bench`; keep policy in server/store/scheduler.
- **`Store.games(sha)` without a `rep` filter:** A/A rows would double-count in the funnel.
- **Pairing across env fingerprints or lgen modes:** silently invalid.
- **Reading `rung` anywhere in `bench/` decision code** after this phase.
- **Letting Claude create `clean_attempt` jobs over MCP.**
- **A claim checker that calls an LLM** (explicitly excluded; also non-deterministic).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Exact McNemar | A custom binomial tail | `scipy.stats.binomtest(b, b+c, 0.5)` | Exact, tested, already a dependency |
| Wilson/Newcombe | New interval code | `bench/stats.wilson`, `newcombe` (add an `n == 0` guard) | Existing and tested (`tests/test_bench_stats.py`) |
| Resolving commits/worktrees | Custom git plumbing | `bench/gitrefs.resolve`, `ensure_worktree` | Existing; add `--` / hex validation |
| NLE reproducibility | Patch series or vendored copy | uv git source on a local bare repo | Owner decision D-01/D-02; verified to build |
| Env fingerprint of NLE | Parsing `nle.__version__` | `direct_url.json` `vcs_info.commit_id` | Full 40-hex, written by uv |
| Read-only SQL | Regex-sanitising SQL | `mode=ro` URI + `PRAGMA query_only` + `set_authorizer` | The database enforces it |
| A/A comparison | New diff logic | `scripts/replay_check.py` field list and `--skip-end` semantics | Already encodes the watchdog caveat |
| Ledger parsing | Markdown parser | `tomllib` | stdlib |
| Run-until-done in tests | `sleep` loops | `tests/conftest.py::run_until_idle`, `FakeWorker` from `tests/bench_fakes.py` | Established fixtures |

**Key insight:** every statistical or plumbing piece here is small; the risk is in semantics (what counts as a look, a replicate, a started job, a natural game), not in code volume. Encode each semantic as a tested predicate in one module.

## Runtime State Inventory

> This phase switches the NLE source and changes the DB schema/MCP environment, so the runtime state categories apply.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Live `~/.local/share/screens-bench/results.db`: 0 games, 0 jobs, `meta.schema = 1` [VERIFIED: sqlite3 query this session]. Archive DB (146,743 games) is read-only history | Schema v1 -> v2 migration is cheap (empty); keep the archive read-only; never import it into the live DB |
| Live service config | A bench server is running (`.venv/bin/python -m bench.cli serve`, PID 21189 at research time) plus an MCP server (`bench.mcp_server`) holding old code | Stop and restart the server after the code change; `interrupt_unfinished` runs on start; resume (D-08) makes this safe |
| OS-registered state | zsh idle hook sources `zsh/nethack-screensaver.zsh` (untouched by this phase). No systemd/pm2 entries found for the bench | None; optionally add a user service later (not required by CONTEXT) |
| Secrets/env vars | `.mcp.json` sets `"SCREENS_BENCH_PYTHON": "~/.cache/screens-nh5/venv/bin/python"` [VERIFIED: file read]; `SCREENS_BENCH_DATA/CACHE/URL` have defaults in `bench/cli.py` | Remove the hard-coded interpreter so workers use the project `.venv` (after it is rebuilt from the git NLE), otherwise jobs run on a different NLE than the lock says |
| Build artifacts / installed packages | `.venv` has `nle 1.3.1.dev19+gc03cfdf73` (stale: two commits behind HEAD `cb9d6572f`), installed from `file://reference/nle-src` with `"editable":false`; `~/.cache/screens-nh5/venv` has `dev21+gcb9d6572f` (the one jobs actually use today). Worktree cache `~/.cache/screens-bench/` does not exist yet | `uv sync` after the pyproject change rebuilds `.venv` at the pinned SHA; compare a sample of seeds old-venv vs new-venv to prove the rebuild is behaviour-identical before the baseline |

The canonical question: after every file is updated, the old venv at `~/.cache/screens-nh5/venv` and the running server still hold the old NLE path and old code; both must be retired so no job silently uses them.

## Common Pitfalls

### Pitfall 1: A fresh clone cannot reproduce NLE for a reason other than the source
**What goes wrong:** `uv sync` needs `cmake`, `cc`, network access to lua.org, and `~/git/nle-screens.git` to exist; a fresh clone also has no `reference/` (gitignored).
**How to avoid:** the fresh-clone test clones the repo to a temp dir, runs `uv sync`, runs the unit tests and one small real bench job there; record the job ID. Verify no runtime code needs `reference/` (grep this session: only scripts and the wiki sweep mention it).
**Warning signs:** build errors mentioning `lua`; `ModuleNotFoundError: nle._pynethack` (happens when Python is started inside `reference/nle-src`, it imports the unbuilt source tree; this session hit it by running from that cwd).

### Pitfall 2: `dungeon_truth.py` depends on struct offsets of one build
**What goes wrong:** `nethack_screensaver/dungeon_truth.py` reads NLE memory with hard-coded offsets (`SVD_TOPOLOGY = 1472`, `TOPOLOGY_MINEEND = 106`, ...) "measured with offsetof()" against the installed library. The `mines_end` funnel stage uses it. A rebuilt NLE at another commit or compiler setting can shift layouts silently.
**How to avoid:** after the rebuild run `tests/test_dungeon_truth.py` and compare `mines_end` stage counts on a sample against the old venv; add the check to the fresh-clone procedure.

### Pitfall 3: Scheduler and DB scale with 10,000 games
**What goes wrong:** `Store.seeds()` full-scans JSON on every tick/slot (0.10 s per call measured at 10k rows); `App.job()` and `/api/results` load all games.
**How to avoid:** the indexed `seed` column (schema v2) and `COUNT`/`EXISTS` queries; keep JSON loads for reports only.

### Pitfall 4: A/A replicates double-counted
Covered by `rep`; add a test that a baseline plus its A/A yields the same `funnel()` as the baseline alone.

### Pitfall 5: Watchdog endings are load-dependent
`replay_check.py` states it. An A/A over 2,000 seeds on 10 loaded slots can legitimately differ on watchdog endings. Define "identical" as: all compared fields equal on all non-watchdog seeds, with the watchdog seeds listed and counted; pre-register this definition. If a non-watchdog seed differs, that is a determinism bug to investigate, not noise.

### Pitfall 6: Baseline orphaned by an unrelated commit
Covered in Pattern 10. Add the baseline sha to the baseline's job record and to the decision record; make `start_experiment` fail with a clear message when its baseline sha has no stored games for the requested seed range.

### Pitfall 7: Hook blocks too often or too little
A regex hook can be both. Mitigations: corpus-driven tests, an audit log, a documented bypass is *not* provided (D-11), a crash-safe exit 0. State the guarantee honestly: it is a tripwire for the common failure (claiming a start with no game rows), not proof that no unproven claim was ever made.

### Pitfall 8: Tool seeds overlap dev seeds
Hand games, rewind (`--seeds 0-19`), scenario and staged runs use seeds 0-19, inside dev (0–99,999). They are in `tool_games` so they never reach the funnel, but a baseline on seeds 0-9,999 includes those same seeds in natural play, so any fix tuned on those layouts leaks into the dev measurement (Pitfall 8 of `PITFALLS.md`). See Open Question 1.

### Pitfall 9: `lgen = 0` means "off" in the fork
Because of the fork's `if (lgen)` guard, a pilot that uses `lgen=seed` for seed 0 silently runs lgen-off. Use an offset (`seed + LGEN_OFFSET`) or start seeds at 1.

### Pitfall 10: The weekend run dies with the server
`bench/mcp_server.py` starts the server with `start_new_session=True`, so closing Claude does not kill it, but a reboot does. Use D-08 resume and tell the owner to start `uv run screens-bench serve --resume`.

### Pitfall 11: Pilot discordance depends on the candidate change
`psi` for a late-acting change is much smaller than for an early one. Report `psi` with its interval and state the candidate; size experiments from the upper bound.

## Code Examples

### Always-valid mixture test (stdlib only)
```python
# Source: derived from the Beta-binomial mixture martingale (Johari et al., arxiv 1512.04922); checked by simulation in this research
import math

def log_mixture_lr(b, c, a=1.0):
    """log of the Beta(a,a)-mixture likelihood ratio of b wins / c losses against p = 1/2."""
    n = b + c
    return (math.lgamma(b + a) + math.lgamma(c + a) - math.lgamma(n + 2 * a)
            - (2 * math.lgamma(a) - math.lgamma(2 * a)) + n * math.log(2))

def anytime_p(running_max_log_lr):
    return min(1.0, math.exp(-running_max_log_lr))
# reject when log_mixture_lr(b, c) >= math.log(1 / alpha)
```

### Exact McNemar
```python
# Source: scipy.stats.binomtest, exact conditional test on discordant pairs
from scipy.stats import binomtest
p = binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
```

### Funnel row with Wilson
```python
from bench.stats import wilson, Z95
def funnel(games, keys):
    n = len(games)
    rows = []
    for key in keys:
        k = sum(1 for g in games if key in g["ladder"])
        lo, hi = wilson(k, n, Z95) if n else (None, None)   # wilson() divides by zero at n == 0
        rows.append({"key": key, "hits": k, "n": n, "rate": k / n if n else None, "lo": lo, "hi": hi})
    return rows
```

### Stop hook output
```python
# Source: https://code.claude.com/docs/en/hooks (Stop decision control)
import json, sys
print(json.dumps({"decision": "block", "reason": "Claim 'baseline started' has no job with a game row. Cite job <id> or drop the claim."}))
sys.exit(0)
```

### Resume (store)
```python
def resume(self, job_id):
    """interrupted -> queued, same id, so cited job IDs stay valid; returns True if it was interrupted."""
    return self._write("UPDATE jobs SET state = 'queued', ended_at = NULL WHERE id = ? AND state = 'interrupted'",
                       (job_id,)).rowcount == 1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Wald interval at 5 checkpoints, z99 early / z95 final (`bench/stats.py`) | Exact McNemar at a declared n plus a mixture-martingale always-valid test over seed-prefix looks | This phase | False verdicts 7.5% -> 3.7% (measured), peeking is safe |
| `rung` (highest rung reached) as metric | Per-stage reach by ladder key with Wilson CIs | This phase | `rung` hid that stage reach is not nested |
| NLE from gitignored path | NLE from pinned git commit in a local bare repo | This phase | Fresh clone installs; commit recorded per job |
| Seeds `0..N-1` | Named ranges, explicit seed windows | This phase | dev/confirm/final separation enforceable |

**Deprecated/outdated:** `bench.stats.judge`, `judge_paired`, `judge_paired_numeric` and `CHECKPOINTS` as decision machinery (keep numerically for reporting or remove with their tests); `rung`/`rung{N}` metrics; `.mcp.json` interpreter override.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Beta(1,1) prior is a reasonable default mixing prior for the mSPRT | Pattern 7 | Different priors change power, not validity; tune by simulation if power is poor |
| A2 | Paired outcomes across distinct integer seeds behave as independent draws (martingale argument needs it) | Pattern 7 | If consecutive seeds correlate, false-positive rate could exceed alpha; test with an A/A on different seed sets |
| A3 | `lgen = seed + LGEN_OFFSET` gives a stream independent of the core stream | Pattern 9 | Correlated level/dice streams; pilot could check a few stage rates against lgen-off |
| A4 | The exact `command` field syntax in `.claude/settings.json` (with or without `args`) | Pattern 12 | Hook silently not firing; verify with a live test during implementation |
| A5 | Sokoban top level is selectable in wizard-mode ^V menu for the detector test | Pattern 14 | Fall back to replaying recorded real-board fixtures |
| A6 | A rebuilt NLE at the same commit plays bit-identically to the existing `~/.cache/screens-nh5` build | Runtime State | Baseline would not be comparable to history; sample-compare seeds before the baseline |
| A7 | The baseline can be run with `lgen` either way and the pilot decides; baseline throughput stays about 25 games/min | Summary | Compute estimates shift |
| A8 | `[CITED]` mSPRT validity statements come from the search digest of the Johari paper; the paper's text for the Bernoulli/Beta case was not read | Pattern 7 | Mitigated by the simulation (3.7% false positives) |

## Open Questions (RESOLVED)

All resolved on 2026-11-12: Q1 → D-17, Q2 → D-22, Q3 → owner checkpoint in plan 01-12 (commit B and adoption rule committed before any pilot job), Q4 → D-23 (orchestrator default: keep commit-sha keying, deferral recorded; not an owner answer), Q5 → D-19, Q6 → D-18, Q7 → D-20. See 01-CONTEXT.md.

1. **Which dev seeds does the 10,000-game baseline use?**
   - What we know: D-05/D-07 give "dev seeds 0–99,999" and 10,000 games; rewind, staged, scenario and hand games use seeds 0-19 (inside dev).
   - What's unclear: whether fixes already tuned on 0-19 may contaminate the baseline.
   - Recommendation: reserve 0-999 as the tool-seed block (never judged) and baseline on 1,000-10,999; confirm with the owner because it refines, not contradicts, D-05.
2. **Where do `confirm` seeds get their gate authorisation?**
   - Recommendation: spec field `gate` naming the phase gate; refuse when absent. Owner to say whether anything stronger is wanted.
3. **How is the lgen pilot's second commit chosen?** Recommendation: a small real mid-game behaviour change ported from the archived experiment branches (bundle `archive/screens-all-branches.bundle`); planner to pick one with the owner, and write the adoption rule before running.
4. **Should games be keyed by bot-tree hash instead of commit sha?** Avoids re-baselining after docs/bench commits. Not required by any MEAS item; decide before Phase 2 or accept naming a baseline sha.
5. **Where does the fresh-clone job's ID live?** Success criterion 1 asks for a job ID from a fresh clone, but a fresh clone's server writes to its own data dir. Recommendation: stop the live server briefly, run the clone's server against the live `--data` dir on a spare commit sha, then restart; the ID then resolves in `results.db` for `check_claims`.
6. **Claim checker on crash:** exit 0 with loud log (recommended) vs block. Owner to confirm.
7. **Ledger scope time-box:** D-12 says everything; propose tranches with a coverage report and accept that completeness cannot be machine-checked.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | sync, lock, git source | yes | 0.12.23 | — |
| Python 3.13 (uv-managed) | project | yes | 3.13.15 | — |
| git | bare repo, worktrees, claim checks | yes | 2.56.0 | — |
| cmake, cc | NLE build, fixed_clock shim | yes | `/usr/bin/cmake`, `/usr/bin/cc` | — |
| sqlite3 CLI | debugging, queries | yes | `/usr/bin/sqlite3` | stdlib `sqlite3` |
| Network to pypi.org | build deps, wheels | yes | worked in probe | — |
| Network to www.lua.org | NLE build (Lua 5.4.8 tarball) | yes (probe build succeeded) | — | Place the tarball where ExternalProject can use it; hash-pinned |
| CPU | 10 worker slots | yes | 12 cores | — |
| `~/git/` directory | bare repo | no (does not exist) | — | `mkdir -p ~/git` |
| System `python3` | hook fallback | 3.14.7, no scipy | — | Use `.venv/bin/python`; keep `check_claims.py` stdlib-only |
| Ollama | not needed this phase | — | — | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** `~/git` (create it).

## Security Domain

Config: `security_enforcement` true, `security_asvs_level` 1, `security_block_on` high.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (local, single user) | Existing `Host` header check; unchanged |
| V3 Session Management | no | — |
| V4 Access Control | yes (seed-range gates, clean-attempt kind) | Server-side validation in `App.start_*`, scheduler and store; `clean_attempt` not creatable over HTTP/MCP |
| V5 Input Validation | yes | Integer coercion of job ids and seeds; hex-only commit regex before any git call; allow-listed `kind`, `range`, `metric`; SQL only via read-only authorizer |
| V6 Cryptography | no (SHA-256 for fingerprints via `hashlib`, no secrets) | stdlib `hashlib` |
| V7 Error handling and logging | yes | Audit log for claim decisions; hook fails safe and loud |
| V12 Files | yes | Ledger/source checks read only repo-relative paths; reject `..` in `evidence` paths |
| V14 Configuration | yes | Remove machine-specific interpreter from `.mcp.json`; pin NLE commit in lock |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Re-running model-supplied SQL in `check_claims.py` | Tampering / Information disclosure | `mode=ro` URI, `PRAGMA query_only=ON`, `set_authorizer` (SELECT/READ/FUNCTION only), single statement, time cap, no `ATTACH` |
| Git option injection via a cited "commit" | Tampering | Accept only `[0-9a-f]{40}`; pass after `--`/as a rev with `cat-file -e` |
| `bench/gitrefs` refs starting with `-` (known concern in CONCERNS.md) | Tampering | Reject refs beginning with `-` before `rev-parse` (touches the same code the claim checker may reuse) |
| Mutating HTTP endpoints without auth (known) | Elevation of privilege | Keep `Host` check; new resume/clean-attempt paths follow the same checks; clean-attempt not exposed |
| Final-range seed misuse | Repudiation (invalid proof) | Triple enforcement (API, scheduler, store) plus audit of jobs by range |
| Tampered Lua download in NLE build | Tampering | Existing `URL_HASH SHA256=` pin |
| Ledger entry citing a source file outside the repo | Information disclosure | Resolve against allowed roots (`reference/`), refuse absolute paths and `..` |

## Sources

### Primary (HIGH confidence)
- Repo files read this session: `bench/{stats,store,scheduler,server,metrics,report,runner,worker,cli,mcp_server,gitrefs}.py`, `nethack_screensaver/game.py`, `autoascend/ladder.py`, `pyproject.toml`, `.mcp.json`, `uv.lock`, `tests/conftest.py`, `tests/bench_fakes.py`, `scripts/{staged_run,rewind,scenario_run,replay_check,handplay}.py`
- NLE fork source: `reference/nle-src/src/{nlernd,allmain,mklev}.c`, `nle/nethack/nethack.py`, `nle/env/base.py`, `CMakeLists.txt`, `pyproject.toml`
- NetHack 5.0 source: `reference/nethack-5.0.0/src/dungeon.c:933-956`, `dat/dungeon.lua:219-233`
- Executed this session: scratch `uv lock`/`uv sync` of a git-source NLE probe; archive DB queries (`72ca0b6`); sqlite `json_extract` timing; statistical simulations (`sim.py`, `sim2.py`, `sim3.py` in the session scratchpad)
- Claude Code hooks reference: https://code.claude.com/docs/en/hooks (Stop input, decision control, 8-continuation cap, matcher/timeout notes)

### Secondary (MEDIUM confidence)
- Johari, Pekelis, Walsh, "Always valid inference: continuous monitoring of A/B tests" https://arxiv.org/abs/1512.04922 (via search digest; normal-mixture version; Beta form not read)
- Exact conditional McNemar power: SAS PROC POWER PAIREDFREQ and R `desmon::mcnemar.pow`, `pwrss` documentation pages (search snippets only; the power function was recomputed independently here)

### Tertiary (LOW confidence)
- Search snippets on always-valid power loss (single course page); not relied on

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new packages; versions read from the environment
- Architecture: HIGH for store/scheduler/NLE packaging (read and executed); MEDIUM for claim detection and ledger scope (design judgement)
- Pitfalls: HIGH for items measured or read in code; MEDIUM for hook behaviour beyond the documented contract

**Research date:** 2026-11-12
**Valid until:** 2026-12-12 (Claude Code hook behaviour and uv minor versions can change; re-check the hook contract before wiring it)

## Project Constraints (from CLAUDE.md)

- Python 3.13 with uv; packages `autoascend`, `nethack_screensaver`, `bench`; NLE from the local NetHack 5.0 fork (branch `screens-nh5`); hardware one Linux machine with 10 bench slots.
- Bench must stay deterministic per seed; any non-deterministic component needs a measurement plan.
- No progress claim without a job ID, commit or query result the owner can check.
- No paid API tokens or cloud services; LLM work is local (Ollama) or the existing Claude subscription.
- Exploits and farming need owner approval before use.
- Code style: keep the style of the file you edit; 4-space indent, lines up to about 120 columns; snake_case; no formatter or linter configured; do not reformat unrelated code; remove obsolete commented code you touch.
- Errors: catch specific exception types with an inline comment; no new bare `except:`; use `except Exception:` at minimum when unavoidable.
- Tests: `tests/test_<module>.py`, flat functions, `pytest.mark.parametrize` for tables, shared helpers as plain modules (`from bench_fakes import ...`), `run_until_idle` instead of sleeps; slow tests marked `slow`; avoid new `sys.path` hacks.
- Pure-logic modules stay stdlib/numpy-only so the bench server can import them; `autoascend` must not import `nethack_screensaver` or `bench`; the worker must not import `bench`.
- Scripts print JSON lines for machine consumption.
- Edits go through a GSD command (`/gsd-execute-phase` for planned phase work); no direct repo edits outside a GSD workflow.
- Project memory notes: unverified NetHack facts are web-checked and the 5.0 source wins over wiki claims (the Ledger's D-14 step).
