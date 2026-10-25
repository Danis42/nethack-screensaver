---
phase: "01"
slug: "midgame-survival"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-25"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| NetHack screen -> bot | the bot reads game output only (observations, message line) | game text, no user data |
| bench store -> analysis scripts | scripts read results.db read-only | local game results |
| bench HTTP API (localhost) | job submission guarded by Host/Content-Type checks (`bench/server.py` `_refused`) | commit refs, metric names |
| NLD-NAO recordings -> human study | read-only local ttyrecs decoded by NLE | aggregates and anonymised lines only |
| verdicts -> keep/drop and phase status | paired bench verdicts decide merges and the done bar | job ids, SHAs |
| git refs | branch merges and deletions | local repository only, no remotes |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering | `_DeathContext`, `_food_at_end`, `_events` in nethack_screensaver/game.py | high | mitigate | Observer takes only `obs` (signature asserted in acceptance); agent reads happen after `wrapper.main()` returns and are wrapped in try/except; slow replay tests prove identical games with the new fields Evidence: game.py `_DeathContext.observe(self, obs)` only; agent reads wrapped in try/except (01-01 summary) | closed |
| T-01-02 | Information disclosure | `last_messages` / `prayers` in games.jsonl and results.db | low | accept | Local single-user files; message text is game output only (no user data) Evidence: accepted risk, see log | closed |
| T-01-03 | Denial of service | `_solve_live_sokoban` budget | medium | mitigate | Budget measured to about 10 s on this machine; `test_live_budget_stays_within_the_old_time_limit` asserts under 20 s, below the 60 s / 120 s watchdogs Evidence: tests/test_soko_search.py::test_live_budget_stays_within_the_old_time_limit passes | closed |
| T-01-04 | Tampering | `bench/runner.py` worker env | low | accept | Only adds one fixed variable to an environment already built from the server's own; no external input Evidence: accepted risk, see log | closed |
| T-01-05 | Tampering | scripts/seeded_report.py, scripts/replay_check.py | high | mitigate | Only Store read methods are called (acceptance grep for write methods prints 0); Store's schema statements are idempotent on an existing DB Evidence: no Store write call in scripts/seeded_report.py or scripts/replay_check.py (grep) | closed |
| T-01-06 | Repudiation | `verdict` lookup | medium | mitigate | Matching on resolved full SHAs, metric and state; each printed line carries the job id so a PORTING.md entry can cite it Evidence: verdict lines carry job id; PORTING.md cites jobs 17-32 | closed |
| T-01-07 | Tampering | ref argument to git | low | accept | `gitrefs.resolve` passes refs as argv (no shell); local single-user tool Evidence: accepted risk, see log | closed |
| T-01-08 | Information disclosure | 01-HUMAN-STUDY.md | low | mitigate | Only aggregate numbers and anonymised message lines (god names replaced) are written; no gameid, name or uid columns Evidence: `grep -ciE "gameid|uid|playername"` on 01-HUMAN-STUDY.md prints 0 | closed |
| T-01-09 | Tampering | ttyrec decoding via nle.dataset | low | accept | Read-only local files decoded by NLE's own reader; no code from the data is executed Evidence: accepted risk, see log | closed |
| T-01-10 | Repudiation | A/A pass claim in PORTING.md | high | mitigate | Gate line written only after `verdict --expect "no measurable difference"` exit 0 and `replay_check` exit 0; both commands recorded in the subsection Evidence: PORTING.md ### A/A control records verdict and replay_check commands | closed |
| T-01-11 | Tampering | bench API (POST jobs) | medium | accept | Existing `_refused` Host and Content-Type checks unchanged (`bench/server.py` 169-178); hardening is DEBT-01 (canon: route to /gsd-secure-phase) Evidence: accepted risk, see log | closed |
| T-01-12 | Tampering | auto-memory notes | low | mitigate | Only the "save"/status statements change, as decided in D-02; nothing else in the memory files is edited Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-13 | Tampering | merge of calibration branches | high | mitigate | Only `calib/lgen` may be merged and only by the lgen rule; acceptance asserts AGENT_ARGS on main has no bot seed Evidence: only exp/shop-door merged into main; AGENT_ARGS has no bot seed (game.py:32) | closed |
| T-01-14 | Denial of service | server restart for the checkpoint change | medium | mitigate | Restart only after the idle check (protocol section 4); a restart mid-job would mark it interrupted Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-15 | Repudiation | choosing lgen/2304 after seeing numbers | medium | mitigate | Decision thresholds are written in this plan before the runs and quoted in the record with the numbers Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-16 | Repudiation | not-comparable labelling | medium | mitigate | All 16 older sections get the note (count asserted); the baseline table states SHA, seeds and n Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-17 | Tampering (loss) | `git branch -d survival-tuning` | low | mitigate | Ancestor check first, SHA logged first, `-d` refuses unmerged branches; stashes untouched Evidence: survival-tuning deleted with -d after ancestor check (STATE.md) | closed |
| T-01-18 | Repudiation | metric choice / keep decision | high | mitigate | Pre-registration entry committed on main before submission (protocol step 6); verdict cited by job id; keep only on `better` Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-19 | Tampering | merge of exp/starvation-* | high | mitigate | Protocol step 10: ff-only or code-identity check; full suite on main after merge Evidence: only exp/shop-door merged (`git branch --merged main`); main code == 3fca503 | closed |
| T-01-20 | Denial of service | food pickup / prayer change making the bot stall | medium | mitigate | Smoke run before the bench; crash comparison after; new exception type means drop Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-21 | Denial of service | `GlobalLogic.rest_to_full` | medium | mitigate | Per-level cap 400 turns, 20-turn chunks interrupted by monsters, food gate; unit tests cover cap and gates; smoke run before the bench Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-22 | Repudiation | keep/drop of exp/rest-to-full | high | mitigate | Pre-registered metric committed before submission; keep only on `better`; entry cites the job id Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-23 | Repudiation | tactic choice | medium | mitigate | Rule thresholds fixed in this plan before the diagnosis numbers; quoted in PORTING.md with A1/A2 Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-24 | Denial of service | `close_door` / corpse cheese | medium | mitigate | Pure predicates unit-tested; smoke run on insect-death seeds; crash comparison after the bench run; new exception type means drop Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-25 | Tampering | merge of exp/ants-bees | high | mitigate | Keep only on `better`; protocol step 10 merge with code-identity check; full suite on main Evidence: exp/ants-bees dropped, not merged (`git branch --merged main`) | closed |
| T-01-26 | Denial of service | `drop_zap_line_moves` leaving no action | medium | mitigate | Function never returns an empty list when moves existed (unit test); smoke and crash comparison before keeping Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-27 | Tampering | zapper memory from messages | low | accept | Screen text comes from NetHack itself; memory is bounded (300 turns) and only biases moves Evidence: accepted risk, see log | closed |
| T-01-28 | Repudiation | tactic choice / keep decision | high | mitigate | Rule and metric fixed before reading numbers; keep only on `better`; entry cites job id Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-29 | Tampering | rebase conflict resolution of threat-model | high | mitigate | Task 1 verify: `git diff --name-only main...rejudge/threat-model -- autoascend nethack_screensaver` must equal the branch's four own files; full suite including the branch's tests; smoke before the bench Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-30 | Repudiation | judged variant of threat-model | low | mitigate | Entry names the judged variant (fdf6b48) and why Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-31 | Tampering | merge of rejudge/threat-model | high | mitigate | Keep only on `better`; protocol step 10 merge with code-identity check Evidence: rejudge/threat-model dropped, not merged | closed |
| T-01-32 | Repudiation | Phase 1 result line | high | mitigate | Decision rule fixed in this plan; five verdicts cited by job id; acceptance re-checks with `--expect better` / `--forbid worse` when "met" is claimed Evidence: jobs 28-32 cited; `--expect better` / `--forbid worse` exit 0 (01-15) | closed |
| T-01-33 | Tampering | p1-final pointing at non-main code | medium | mitigate | Code-identity check of the Current baseline SHA against main before tagging Evidence: `git diff 3fca503 main` touches only PORTING.md before tagging p1-final | closed |
| T-01-34 | Tampering (loss of work) | `git branch -D` of dropped branches | high | mitigate | Ledger with full SHAs verified against the refs first (task 1 verify); blocking owner decision; archive-tag option offered; recovery command recorded Evidence: ledger SHAs verified vs refs; owner chose archive-tags; six archive/ tags equal logged SHAs | closed |
| T-01-35 | Repudiation | which branches were deleted | low | mitigate | PORTING.md rows carry branch, SHA, verdict, interval, final status and date Evidence: PORTING.md ### Branch cleanup (D-13) rows have branch, SHA, verdict, interval, status, date | closed |
| T-01-36 | Tampering | rebase conflict resolution of choke-points in combat/fight_heur.py | high | mitigate | Task 1 verify: code diff limited to combat/fight_heur.py; keep-main rule preserves kept changes from plans 01-10..01-12; full suite including tests/test_choke_points.py; smoke before the bench Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-37 | Tampering | merge of rejudge/choke-points | high | mitigate | Keep only on `better`; protocol step 10 merge with code-identity check Evidence: rejudge/choke-points dropped, not merged | closed |
| T-01-38 | Tampering | rebase conflict resolution in nethack_screensaver/game.py and stats_logger.py | high | mitigate | Task 1 verify: code diff limited to the five own files; `git diff --numstat` shows 0 deleted lines in game.py and stats_logger.py; full suite; smoke before the bench Evidence: recorded in the plan summary / PORTING.md experiment entry | closed |
| T-01-39 | Tampering | merge of rejudge/flee-upstairs | high | mitigate | Keep only on `better`; protocol step 10 merge with code-identity check Evidence: rejudge/flee-upstairs dropped, not merged | closed |
| T-01-40 | Tampering (loss of work) | deletion list in the SURV-05 summary | high | mitigate | Task 3 verify: every existing unmerged old or rejudge branch appears with its full SHA from `git rev-parse --verify`; plan 01-16 re-checks every SHA against the refs before its blocking owner checkpoint Evidence: all six branch SHAs logged in PORTING.md before deletion (01-16 task 1 verify) | closed |
| T-01-SC | Tampering | package installs | high | mitigate | No package is added: `git log --format=%h <plan-start-sha>..HEAD -- pyproject.toml uv.lock` prints nothing (plan-start-sha = HEAD before task 1); any new dependency must first pass the RESEARCH Package Legitimacy Audit Evidence: `git log --since=2026-10-22 -- pyproject.toml uv.lock` prints nothing | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-02 | Local single-user files; message text is game output only (no user data) | owner (plan-time disposition) | 2026-10-25 |
| AR-02 | T-01-04 | Only adds one fixed variable to an environment already built from the server's own; no external input | owner (plan-time disposition) | 2026-10-25 |
| AR-03 | T-01-07 | `gitrefs.resolve` passes refs as argv (no shell); local single-user tool | owner (plan-time disposition) | 2026-10-25 |
| AR-04 | T-01-09 | Read-only local files decoded by NLE's own reader; no code from the data is executed | owner (plan-time disposition) | 2026-10-25 |
| AR-05 | T-01-11 | Existing `_refused` Host and Content-Type checks unchanged (`bench/server.py` 169-178); hardening is DEBT-01 (canon: route to /gsd-secure-phase) | owner (plan-time disposition) | 2026-10-25 |
| AR-06 | T-01-27 | Screen text comes from NetHack itself; memory is bounded (300 turns) and only biases moves | owner (plan-time disposition) | 2026-10-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-25 | 41 | 41 | 0 | Claude (inline, ASVS L1 grep depth; full suite 416 passed, 5 skipped) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-25
