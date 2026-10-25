---
phase: "02"
slug: "real-descent"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-25"
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (repo `pyproject.toml`; slow games marked `slow`) |
| **Config file** | `pyproject.toml`, `tests/conftest.py` |
| **Quick run command** | `uv run pytest -q tests/test_ladder.py tests/test_game.py tests/test_plans.py tests/test_dungeon_truth.py` |
| **Full suite command** | `uv run pytest -q -m ""` |
| **Estimated runtime** | ~60 s fast suite, ~2-5 min with slow games |

---

## Sampling Rate

- **After every task commit:** quick run command
- **After every plan wave:** full suite command
- **Before `/gsd-verify-work`:** full suite green; bench verdicts read with `scripts/seeded_report.py verdict`
- **Max feedback latency:** 120 s (bench jobs are verdict evidence, not feedback)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DESC-01 | T-02-02, T-02-03 | bad reads raise, newest env read | unit (real env) | `uv run pytest -q tests/test_dungeon_truth.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DESC-01 | T-02-01 | bot never reads truth | unit | `uv run pytest -q tests/test_ladder.py tests/test_game.py` | ✅ | ⬜ pending |
| 02-02-01 | 02 | 2 | DESC-03 | T-02-04 | report does not change play | unit | `uv run pytest -q tests/test_game.py tests/test_plans.py -k stuck` | ✅ | ⬜ pending |
| 02-02-02 | 02 | 2 | DESC-03 | T-02-05 | capped fields | unit | `uv run pytest -q tests/test_game.py tests/test_bench_metrics.py` | ✅ | ⬜ pending |
| 02-03-01 | 03 | 3 | DESC-03 | — | N/A | unit | `uv run pytest -q tests/test_seeded_scripts.py -k stuck` | ✅ | ⬜ pending |
| 02-03-02 | 03 | 3 | DESC-01 | T-02-06 | baseline plays like p1-final | bench data | `uv run python scripts/replay_check.py p1-final p2-baseline --fields ... --skip-end watchdog --min 2000` | ✅ | ⬜ pending |
| 02-04-01 | 04 | 4 | DESC-01 | T-02-08 | no memory read in bot | unit | `uv run pytest -q tests/test_plans.py -k mines_bottom` | ✅ | ⬜ pending |
| 02-04-02 | 04 | 4 | DESC-02 | T-02-09 | keep only on better | bench | `uv run python scripts/seeded_report.py verdict exp/mines-end` | ✅ | ⬜ pending |
| 02-05-01 | 05 | 5 | DESC-03 | T-02-10 | rule before numbers | doc check | `grep -c "### Stuck diagnosis (DESC-03)" autoascend/PORTING.md` | ✅ | ⬜ pending |
| 02-05-02 | 05 | 5 | DESC-03 | T-02-11, T-02-12 | capped tactic, no town kicks | unit | `uv run pytest -q -m ""` | ✅ | ⬜ pending |
| 02-05-03 | 05 | 5 | DESC-03 | — | keep only on better | bench | `uv run python scripts/seeded_report.py verdict exp/stuck-1` | ✅ | ⬜ pending |
| 02-06-01 | 06 | 6 | DESC-02 | T-02-13 | rule before numbers | doc check | `grep -c "second tactic" autoascend/PORTING.md` | ✅ | ⬜ pending |
| 02-06-02 | 06 | 6 | DESC-02 | T-02-14 | route skip safe | unit | `uv run pytest -q -m ""` | ✅ | ⬜ pending |
| 02-06-03 | 06 | 6 | DESC-04 | — | keep only on better | bench | `uv run python scripts/seeded_report.py verdict exp/stuck-2` | ✅ | ⬜ pending |
| 02-07-01 | 07 | 7 | DESC-05 | T-02-16 | screen-only portal | unit | `uv run pytest -q tests/test_quest_portal.py` | ❌ W0 | ⬜ pending |
| 02-07-02 | 07 | 7 | DESC-05 | T-02-15 | hunt capped | unit + smoke | `uv run pytest -q -m ""` | ✅ | ⬜ pending |
| 02-07-03 | 07 | 7 | DESC-05 | — | keep only on better | bench | `uv run python scripts/seeded_report.py verdict exp/quest-portal` | ✅ | ⬜ pending |
| 02-08-01 | 08 | 8 | DESC-04 | T-02-18 | p2-final = main code | bench | `uv run python scripts/seeded_report.py verdict p2-final --baseline p2-baseline --metric rung7` | ✅ | ⬜ pending |
| 02-08-02 | 08 | 8 | DESC-01..05 | T-02-17 | bar not lowered | doc check | `grep -cE "^Phase 2 result: (met|open - next: )" autoascend/PORTING.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_dungeon_truth.py` — created by 02-01 task 1 (DESC-01)
- [ ] `tests/test_quest_portal.py` — created by 02-07 task 1 (DESC-05)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A recorded game shows a deliberate portal entry | DESC-05 | judging "on purpose" needs the message sequence read by a person | read the seed's `last_messages` named in the 02-07 summary |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
