---
phase: "1"
slug: "midgame-survival"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-22"
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (`addopts = "-m 'not slow'"`, slow marker, overflow warnings as errors) |
| **Quick run command** | `uv run pytest -q` |
| **Full suite command** | `uv run pytest -q -m ""` |
| **Estimated runtime** | ~116 seconds (full); bench jobs are separate evidence (~15+ min per 576 games per side) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q` plus the touched test file
- **After every plan wave:** Run `uv run pytest -q -m ""`
- **Before each behaviour-change bench job:** full suite green; behaviour-neutral commits additionally pass a 192-seed exact-replay check
- **Per bench job:** read `job.result.verdict`; check `crashes` for new exception types
- **Before `/gsd-verify-work`:** Full suite must be green and SURV-06 judgements recorded in `autoascend/PORTING.md`
- **Max feedback latency:** 120 seconds (unit/integration); bench verdicts are asynchronous

---

## Per-Task Verification Map

Filled in by the planner per task. Requirement → test map from RESEARCH.md §Validation Architecture:

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| MEAS-01 | A/A verdict "no measurable difference" at 1152 | bench job | `uv run screens-bench wait <id>` | n/a | ⬜ pending |
| MEAS-01 | Same-commit refusal, paired-interval math | unit | `uv run pytest -q tests/test_bench_stats.py tests/test_bench_server.py` | ✅ | ⬜ pending |
| MEAS-02 | Baseline stored, rung table in PORTING.md | bench + doc check | `curl -s ".../api/results?ref=<sha>"`; grep `autoascend/PORTING.md` | ❌ W0 | ⬜ pending |
| MEAS-03 | Seed replays frame-for-frame | slow integration | `uv run pytest -q -m slow tests/test_replay.py` | ❌ W0 | ⬜ pending |
| MEAS-03 | Seeded game uses `fix_moon_phase` | unit | `uv run pytest -q tests/test_game.py -k moon` | ❌ W0 | ⬜ pending |
| MEAS-03 | Sokoban solver ignores wall-clock in bench mode | unit | `uv run pytest -q tests/test_soko_search.py` | ✅ (extend) | ⬜ pending |
| SURV-01 | Rest trigger conditions | unit | `uv run pytest -q tests/test_rest.py` | ❌ W0 | ⬜ pending |
| SURV-02 | Prayer gating, failure detection | unit | `uv run pytest -q tests/test_prayer.py` | ❌ W0 | ⬜ pending |
| SURV-03 | Zapper / off-line handling | unit | `uv run pytest -q tests/test_fight_heur.py` | ✅ (extend) | ⬜ pending |
| SURV-04 | New ant/bee tactic | unit | `uv run pytest -q tests/test_fight_heur.py` | ✅ (extend) | ⬜ pending |
| SURV-05 | Rebased branches pass their tests | unit | `uv run pytest -q -m ""` on each rebase branch | ✅ | ⬜ pending |
| SURV-06 | Paired `better` on rung2; rung3-6 not worse | bench jobs | MCP `bench_experiment(..., metric="rungN")` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_replay.py` (slow) — seeds replay frame-for-frame (fresh process with other `PYTHONHASHSEED`; same process A,B,A) — MEAS-03
- [ ] `scripts/replay_check.py` — compare two SHAs' stored games per seed (turns, end_reason, rung, role) — MEAS-01/03, instrumentation neutrality
- [ ] unit tests for `fix_moon_phase` wiring and the Sokoban deadline switch — MEAS-03
- [ ] per-fix unit tests (`tests/test_rest.py`, `tests/test_prayer.py`, fight_heur extensions) written with each change — SURV-01..04

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bench verdicts (A/A, baseline, experiments) | MEAS-01, MEAS-02, SURV-01..06 | Long asynchronous bench jobs, verdict is statistical evidence | Submit via MCP/CLI, `screens-bench wait <id>`, record verdict + interval + SHAs in `autoascend/PORTING.md` |
| Human-game comparison | SURV-02 (D-10) | Exploratory data study on NLD-NAO | Query `/ssd2/nethackFiles/db/nld.db` via `nle.dataset`; record findings in PORTING.md |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
