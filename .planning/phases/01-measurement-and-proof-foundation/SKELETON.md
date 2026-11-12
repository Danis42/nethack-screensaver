# Walking Skeleton — NetHack Screensaver: Ascension (measurement and proof)

**Phase:** 1
**Generated:** 2026-11-12

## Capability Proven End-to-End

From a fresh clone of screens on this machine, `uv sync --locked` builds NLE from the pinned bare-repo commit, a bench job on an explicit dev seed window stores game rows tagged with seed and env fingerprint in the schema-2 store, the funnel query reports per-stage reach with Wilson intervals, and a reply citing that job ID passes `check_claims.py`.

Proven by plan 01-14 Task 1 (record: `01-SKELETON-PROOF.md`). There is no web UI and no deployment: the "stack" is install, bench server, worker, store, report and the claim hook.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| NLE source | uv git dependency on the local bare repo `~/git/nle-screens.git`, pinned by `rev` to cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72 (D-01, D-02) | The fork is a ~388k-line diff on upstream NLE; a git source makes a fresh clone install it and puts the commit in `uv.lock` |
| Reproducibility scope | Fresh clone on this machine only (D-03) | The bare repo is a local path; off-machine installs are not a goal |
| Backup | None; the fork lives only on this disk (D-04) | Owner accepted the risk; no backup tooling is built. Recorded risk: losing this disk loses the NLE fork |
| Env fingerprint | `bench/provenance.py`: worker interpreter's NLE commit (from `direct_url.json`), NLE version, python, numpy, numba, plus the checkout's `uv.lock` sha256; `env_id` = 16-hex hash of those fields, interpreter path excluded | Games are only reused or paired inside one environment; a fresh clone with the same lock shares the env_id |
| Data layer | SQLite `results.db`, schema 2: `games(sha, job_id, seed, lgen, env_id, rep, finished_at, json)`, `envs(id, json)`, `tool_games(job_id, tool, sha, seed, json)`, `jobs`, `meta`, `reference_games` | Indexed seed column (the JSON scans did not scale to 10k games); full env JSON kept so env_id can be recomputed |
| Game identity | `(sha, seed, lgen mode, env_id, rep)`; rep 1 = A/A replicate; games stay keyed by commit sha and baselines are named by sha (D-23) | Replicates and other modes never double-count or pair by accident |
| Job contract | spec `seeds = {range, lo, hi}` half-open, `lgen` off/seed, `replicate`, `gate`, `env_id`, `env`, `lock_blob`, `declared` (experiments) | One shape every later phase submits |
| Seed policy | tool 0-999 (never judged, D-17), dev 0-99,999 (natural jobs from 1,000), confirm 100,000-199,999 (needs the `gate` field, no owner token, D-22), final 1,000,000+ (only `clean_attempt`, not creatable over HTTP/MCP) (D-07) | Separation of tuning, phase-gate and clean-attempt seeds, enforced at API, scheduler and store |
| Decision statistics | Exact McNemar (scipy `binomtest`) plus a Beta(1,1)-mixture always-valid test on discordant pairs, judged on contiguous seed prefixes in blocks of 96; MDE and planned n declared before the run (`bench/sequential.py`, `bench/power.py`) | The old checkpoint design gave 7.3-7.7% false verdicts; peeking is now safe (simulation report `01-SIM-SEQUENTIAL.json`) |
| Funnel | Marginal reach per ladder key (18 keys, `autoascend/ladder.py` RUNGS, incl. the separate `quest_portal` stage before `quest`, D-21) with Wilson 95% intervals; `rung` kept only as a stored description | Stages are not nested; decisions use `stage_<key>` metrics |
| "Started" rule | A job is started only when a games or tool_games row with its job_id exists | The failure that broke trust: claiming runs that had not started |
| Proof | Claude Code Stop hook runs `scripts/check_claims.py` (stdlib, deterministic regex detection, read-only verification against `results.db` and git); audit log `.claude/claim-checks.jsonl`; crash passes and is logged (D-09, D-10, D-11, D-18) | Claims in replies are blocked unless backed by a job ID, full commit or re-runnable query |
| Fact ledger | `facts/FACTS.toml` (tags 5.0-source / measured / unverified), `# fact:<id>` in code, `[fact:<id>]` in notes, `scripts/facts.py` check / report / coverage (D-13, D-15, D-16, D-20) | 3.6 or invented knowledge becomes visible; coverage is measured tranche by tranche |
| Surfaces | HTTP API + MCP tools + `screens-bench` CLI + the existing dashboard page | Claude submits over MCP; the owner can check from the CLI and browser |
| Runtime | Local bench server `uv run screens-bench serve --resume`, 10 worker slots, one job at a time, unattended runs; interrupted jobs resume under the same ID (D-08) | Multi-hour runs must survive restarts without orphaning cited job IDs |
| Directory layout | Pure logic in `bench/{seeds,funnel,sequential,power,provenance}.py`; tool-run recording in `bench/toolruns.py`; scripts in `scripts/`; ledger in `facts/`; evidence records in the phase directory | Follows the existing rule: pure modules stdlib/numpy only; the worker never imports `bench` |

## Stack Touched in Phase 1

- [x] Project scaffold: install from a fresh clone (`uv sync --locked`, NLE built from the pinned commit), test runner (pytest)
- [x] Entry points: `screens-bench serve/wait/funnel/power`, MCP tools, `POST /api/jobs`, `GET /api/funnel`
- [x] Database: a real write (game rows with seed and env_id) and a real read (funnel over those rows)
- [x] Interaction: a claim in a reply is checked against the database by the Stop hook
- [x] Local run: `uv run screens-bench serve --resume` plays real NetHack 5.0 games unattended

## Out of Scope (Deferred to Later Slices)

- Off-disk backup of the NLE fork or the repo (D-04; deferred idea in CONTEXT.md)
- Checking commit messages and planning docs with the claim checker (deferred idea in CONTEXT.md)
- Keying games by a bot-tree hash so docs-only commits reuse games (D-23, deferred); Phase 1 names the baseline sha explicitly instead (Pitfall 6)
- Creating `clean_attempt` jobs and the clean-run verifier (Phase 7)
- Any LLM in the bench or in the claim checker (out of scope by project rules)
- Tagging every remaining module and research note in the fact ledger (later tranches, chosen by the coverage report)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without changing its decisions:

- Phase 2: proven change loop (refactor gate, triage, Mines-branch fix and character A/B judged by the sequential test against the named baseline sha)
- Phase 3: LLM analyst and pilot, recorded as tool runs in `tool_games`
- Phase 4: early-wall fixes shown as higher funnel stage rates on confirm seeds (with a `gate`)
- Phase 5: kit and Medusa/Castle staged contracts (staged pass rates in `tool_games` next to natural funnel arrival rates)
- Phase 6: Gehennom to Astral staged contracts
- Phase 7: clean-run verifier and the clean attempt on final-range seeds
