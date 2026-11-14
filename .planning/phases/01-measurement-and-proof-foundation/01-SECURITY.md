---
phase: "01"
slug: "measurement-and-proof-foundation"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-11-14"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Verification depth: ASVS L1 (grep-level). Register authored at plan time in all 16 plans; every `mitigate` control was located in code, tests or phase records on 2026-11-14. Auditor subagent skipped per the workflow short-circuit (threats_open 0, plan-time register, ASVS 1).

---

## Trust Boundaries

| Plan | Boundary | Description |
|------|----------|-------------|
| 01-01 | build -> www.lua.org | NLE's CMake downloads the Lua 5.4.8 tarball during `uv sync` |
| 01-01 | bench server -> worker interpreter | provenance runs a probe in an interpreter given by path |
| 01-01 | local bare repo -> uv | the NLE source is taken from `~/git/nle-screens.git` by commit |
| 01-02 | stored game results -> verdict | outcomes from games become better/worse decisions |
| 01-03 | model reply -> check_claims.py | the reply text (model-authored) supplies SQL, hashes and job IDs |
| 01-03 | check_claims.py -> results.db | live database opened by a hook process |
| 01-03 | check_claims.py -> git | cited hashes passed to git |
| 01-04 | ledger text -> file reads | evidence paths in the ledger decide which files `check --source` opens |
| 01-05 | bench server -> worker process | the stdin protocol line carries seed and lgen |
| 01-06 | hand game -> committed fixtures | boards recorded from a wizard-mode tool game become test data |
| 01-07 | web pages -> ledger | wiki and forum text (often 3.6) informs fact entries |
| 01-07 | executor -> web search | search queries leave the machine |
| 01-08 | HTTP/MCP client -> App | job parameters (refs, windows, modes) come from Claude or a browser on localhost |
| 01-08 | worker result -> Store | game results written as rows keyed by seed and env |
| 01-09 | web pages -> ledger | wiki and forum text (often 3.6) informs fact entries |
| 01-09 | executor -> web search | search queries leave the machine |
| 01-10 | HTTP/MCP client -> App | job windows, kinds and gates come from Claude or a browser on localhost |
| 01-10 | scheduler -> worker | seeds handed to workers |
| 01-10 | any writer -> Store | game rows from the scheduler or `bench import results` |
| 01-11 | HTTP/MCP client -> resume route | job state transitions requested over localhost |
| 01-11 | tool scripts -> results.db | a second process writes tool rows into the live database |
| 01-12 | stored game JSON -> dashboard HTML | end reasons and titles rendered in the browser |
| 01-12 | HTTP client -> /api/funnel | query parameters |
| 01-13 | HTTP/MCP client -> start_experiment / power | numeric parameters and refs from Claude or the browser |
| 01-14 | fresh-clone server -> live results.db | a second checkout's server writes into the live database |
| 01-14 | owner decision -> pilot rule | the decision rule must exist before the data |
| 01-15 | pilot data -> bench policy | measured numbers become the lgen mode and the default discordance |
| 01-16 | live database -> written evidence | numbers copied into planning docs must stay re-runnable |

---

## Threat Register

| Plan | Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|------|-----------|----------|-----------|----------|-------------|------------|--------|
| 01-01 | T-01-01 | Tampering | Lua download in the NLE build | medium | mitigate | Keep the existing `URL_HASH SHA256=4f18ddae...` pin in the fork's CMakeLists.txt (unchanged by this plan); a tampered tarball fails the build | closed |
| 01-01 | T-01-02 | Tampering | NLE source substitution | medium | mitigate | `rev` is the full 40-hex commit; uv.lock records it; `fresh_clone_check.py` uses `uv sync --locked`, which refuses a lock that does not match | closed |
| 01-01 | T-01-03 | Information disclosure | `.mcp.json` machine-specific interpreter override | low | mitigate | Remove the override so workers use the project venv the lock describes (ASVS V14) | closed |
| 01-01 | T-01-04 | Tampering | `lock_blob(repo, sha)` git call | medium | mitigate | Accept only `[0-9a-f]{40}` before calling git, so no option injection through the argument | closed |
| 01-01 | T-01-SC | Tampering | uv build of the NLE git source (scikit-build-core, pybind11, setuptools-scm) | high | mitigate | No new packages (RESEARCH Package Legitimacy Audit: none new); build deps come from the existing lock; `--locked` installs refuse drift | closed |
| 01-02 | T-01-05 | Repudiation | `judge_sequential` false wins under peeking | medium | mitigate | Mixture rule validated by `scripts/sim_sequential.py` with a committed report; tests pin the rejection bound at the exact threshold | closed |
| 01-02 | T-01-06 | Tampering | power numbers used to size experiments | low | mitigate | Exact MDE values pinned to the research table in tests; simulated power is seeded and deterministic | closed |
| 01-02 | T-01-SC | Tampering | package installs | low | accept | No new packages: scipy and numpy are existing locked dependencies (RESEARCH Package Legitimacy Audit) | closed |
| 01-03 | T-01-07 | Tampering | `verify_query` re-running model-supplied SQL | high | mitigate | `mode=ro` URI, `PRAGMA query_only=ON`, authorizer allowing only SELECT/READ/FUNCTION, single statement, progress-handler time cap; tests prove refusal and an unchanged file | closed |
| 01-03 | T-01-08 | Information disclosure | `verify_query` reading other files via ATTACH | medium | mitigate | ATTACH denied by the authorizer; test covers it | closed |
| 01-03 | T-01-09 | Tampering | `verify_commit` git option injection | medium | mitigate | Only `[0-9a-f]{40}` reaches git, passed as `<sha>^{commit}` in an argument list | closed |
| 01-03 | T-01-10 | Repudiation | unproven claims passing (8-block cap, crash pass, final message only) | medium | accept | Documented limits reported to the owner; every pass/block/crash is in the audit log for review | closed |
| 01-03 | T-01-11 | Denial of service | hook hanging a turn | low | mitigate | Hook timeout 30 s; query time cap 2 s; git timeout 10 s | closed |
| 01-03 | T-01-SC | Tampering | package installs | low | accept | No packages: the script is stdlib only | closed |
| 01-04 | T-01-12 | Information disclosure | `check_sources` path handling | medium | mitigate | Refuse absolute paths, `..` segments and paths outside `reference/nethack-5.0.0/` and `reference/nle-src/` (ASVS V12); tests for each case | closed |
| 01-04 | T-01-13 | Tampering | 3.6 or invented facts tagged as 5.0 | medium | mitigate | 5.0-source requires evidence plus a verbatim quote that `check --source` finds in the cited lines | closed |
| 01-04 | T-01-SC | Tampering | package installs | low | accept | No packages: `tomllib`, `tokenize`, `sqlite3` are stdlib | closed |
| 01-05 | T-01-18 | Tampering | lgen = 0 silently meaning "off" | medium | mitigate | `run_game` raises on lgen 0; the bench derives lgen as seed + LGEN_OFFSET (plan 01-08) | closed |
| 01-05 | T-01-19 | Repudiation | telemetry or ladder change altering play, invalidating the baseline | medium | mitigate | play_compare on 20 seeds before Task 2 vs after Task 3, ignoring only events, ladder and rung; result recorded | closed |
| 01-05 | T-01-20 | Tampering | malformed worker protocol lines | low | mitigate | `parse` accepts at most two integers; anything else is ignored as today | closed |
| 01-05 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-06 | T-01-21 | Repudiation | a computed or simulated board passed off as a played game | medium | mitigate | No computed fallback exists: an unsolved game stops at a blocking checkpoint; fixtures are recorded observations whose note says "played" | closed |
| 01-06 | T-01-22 | Tampering | staged/hand games leaking into natural results | low | mitigate | Hand games are never written to the bench store (handplay has no store access); tool seed 7 is in the reserved block | closed |
| 01-06 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-07 | T-01-23 | Tampering | 3.6 or wiki claims entering as 5.0 facts | medium | mitigate | Web-sourced facts stay `unverified` unless a 5.0 quote is found; `check --source` verifies quotes; 5.0 source wins (D-14) | closed |
| 01-07 | T-01-24 | Information disclosure | web queries | low | mitigate | Queries use NetHack terms only; no owner, project or path names (privacy rule) | closed |
| 01-07 | T-01-SC | Tampering | package installs | low | accept | No packages | closed |
| 01-08 | T-01-15 | Tampering | job parameters (lo, hi, lgen, replicate) | medium | mitigate | `int()` coercion, lo < hi, allow-listed lgen/replicate values (ASVS V5) | closed |
| 01-08 | T-01-16 | Repudiation | games mixed across NLE builds or lgen modes | medium | mitigate | env_id and lgen mode in every reuse/pairing query; env fingerprint stored per job and per row | closed |
| 01-08 | T-01-17 | Tampering | schema 1 -> 2 migration of the live database | low | mitigate | Migration only adds columns and backfills from JSON; full env JSON kept so env_id can be recomputed; tested on a schema-1 file | closed |
| 01-08 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-09 | T-01-47 | Tampering | 3.6 or wiki claims in research notes entering as 5.0 facts | medium | mitigate | Web-sourced facts stay `unverified` unless a 5.0 quote is found; `check --source` verifies quotes (D-14) | closed |
| 01-09 | T-01-48 | Information disclosure | web queries | low | mitigate | Queries use NetHack terms only; no owner, project or path names | closed |
| 01-09 | T-01-SC | Tampering | package installs | low | accept | No packages | closed |
| 01-10 | T-01-14 | Elevation of privilege | final-range seeds via HTTP/MCP | high | mitigate | `check_window` in App, kind allow-list on POST /api/jobs, `check_seed` at dispatch, final guard in `Store.add_game`; clean_attempt not creatable over HTTP/MCP (ASVS V4) | closed |
| 01-10 | T-01-49 | Tampering | the gate field | low | mitigate | `GATE_RE` allow-list; the gate is recorded in the job spec so every confirm-range job is auditable (D-22) | closed |
| 01-10 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-11 | T-01-25 | Elevation of privilege | `POST /api/jobs/<id>/resume` | low | mitigate | Same Host and Content-Type checks as other writes; only the interrupted -> queued transition is possible | closed |
| 01-11 | T-01-26 | Repudiation | a job reported started without games | high | mitigate | `started` derived only from rows (`EXISTS` over games/tool_games); tests assert running-but-not-started | closed |
| 01-11 | T-01-27 | Tampering | tool results mixed into natural rates | high | mitigate | `add_game` refuses staged results; tool rows only in tool_games; reads of games never touch tool_games; tests both directions | closed |
| 01-11 | T-01-28 | Repudiation | a tool run recorded against uncommitted code | medium | mitigate | `--record` refuses a dirty tree, so every tool job maps to a commit | closed |
| 01-11 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-12 | T-01-29 | Tampering | funnel table rendering | low | mitigate | All strings pass through the existing `esc()` helper | closed |
| 01-12 | T-01-30 | Tampering | /api/funnel parameters | low | mitigate | `int()` coercion of lo/hi/job, allow-listed lgen, window checks (ASVS V5) | closed |
| 01-12 | T-01-31 | Repudiation | games silently dropped from rates | medium | mitigate | Exclusions and flags counted and returned with every funnel | closed |
| 01-12 | T-01-32 | Repudiation | rung creeping back into decisions | low | mitigate | `test_no_decision_path_reads_rung` | closed |
| 01-12 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-13 | T-01-33 | Repudiation | experiments without a declared MDE or judged on completion order | high | mitigate | mde required; `declared` stored before the run; judging only on contiguous prefixes (tested with a withheld seed) | closed |
| 01-13 | T-01-34 | Tampering | refs starting with "-" reaching git (known concern) | medium | mitigate | `gitrefs.resolve` refuses them before git | closed |
| 01-13 | T-01-35 | Repudiation | baseline orphaned by an unrelated commit | medium | mitigate | Refuse experiments whose baseline has no stored games unless `allow_new_baseline` | closed |
| 01-13 | T-01-36 | Denial of service | expensive power simulations on request | low | accept | Simulations are bounded (reps 4000, n_cap 100,000) and run only on explicit calls on a local single-user server | closed |
| 01-13 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-14 | T-01-37 | Denial of service | stopping the live server for the swap | low | mitigate | Precondition: server idle; restart with `--resume`; no MCP bench calls during the swap (MCP would start the old server) | closed |
| 01-14 | T-01-38 | Repudiation | pilot rule written after results | high | mitigate | Rule committed first; verify checks the rule commit time precedes every pilot job's created_at | closed |
| 01-14 | T-01-39 | Tampering | fresh-clone games mixing into baseline rows | low | mitigate | Proof jobs run on the spare commit `proof/fresh-clone`, a different sha from A, so no row is reused by pilot or baseline | closed |
| 01-14 | T-01-40 | Tampering | importing archived branches | low | mitigate | Bundle refs fetched into `refs/archive/*` only; nothing merged into main; B lives on its own branch | closed |
| 01-14 | T-01-SC | Tampering | package installs in the fresh clone | medium | mitigate | `uv sync --locked` from the committed lock; no new packages | closed |
| 01-15 | T-01-41 | Repudiation | lgen decision not following the rule | high | mitigate | Rule applied mechanically; results block plus script reproduce it; all four job IDs recorded | closed |
| 01-15 | T-01-42 | Repudiation | A/A identity definition changed after seeing data, or watchdog endings used to hide differences | high | mitigate | Definition and exact command committed (prereg_commit) before the A/A job exists; one-sided watchdog counts as a mismatch; verify checks commit time against job creation time | closed |
| 01-15 | T-01-43 | Tampering | baseline on the wrong sha, window or mode | medium | mitigate | Verify compares the job spec with 01-BASELINE.md | closed |
| 01-15 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |
| 01-16 | T-01-44 | Repudiation | evidence documents with unproven numbers | high | mitigate | Every number carries a job ID or `[query: ...]`; each section of 01-PROOF.md passes check_claims | closed |
| 01-16 | T-01-45 | Repudiation | archive numbers presented as current | medium | mitigate | Archive figures only in labelled archive sections; acceptance criterion checks the label | closed |
| 01-16 | T-01-46 | Repudiation | A/A verdict bent after seeing the data | high | mitigate | Verdict computed with the pre-registered definition and command; mismatches reported as a determinism bug | closed |
| 01-16 | T-01-SC | Tampering | package installs | low | accept | No new packages | closed |

*Status: open · closed · open — below high threshold (non-blocking)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-10 | Claim checker limits (8-block cap, crash pass-through D-18, final message only); every pass/block/crash is in the audit log | owner (plan 01-03, D-18) | 2026-11-12 |
| AR-01-02 | T-01-36 | Power simulations bounded (reps 4000, n_cap 100,000), explicit calls only, local single-user server | plan 01-13 | 2026-11-12 |
| AR-01-03 | T-01-SC (accept rows) | No new packages added in those plans; stdlib or already-locked dependencies only | plans 01-02..01-16 | 2026-11-12 |

---

## Notes from the 2026-11-14 UAT

- Owner dropped prohibitions #4-#7 (01-04 source quote, 01-10 final-seed surface, 01-15 dungeon screening, 01-16 archive import) and reworded #2 (local LLM allowed in claim checking). The threat mitigations above (T-01-12/13, T-01-14, T-01-45) remain in code as tooling; they are no longer owner prohibitions.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-14 | 65 | 65 | 0 | /gsd-secure-phase 01 (inline, L1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-14
