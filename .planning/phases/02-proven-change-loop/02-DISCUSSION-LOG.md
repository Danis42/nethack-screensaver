# Phase 2: Proven Change Loop - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-14
**Phase:** 02-proven-change-loop
**Areas discussed:** Mines staircase behaviour, Character choice, Death triage, Refactor gate & code rules

---

## Mines staircase behaviour

| Question | Options | Selected |
|----------|---------|----------|
| Branch level, once stairs are told apart | Follow the plan / Always Mines first / You decide | Follow the plan |
| On a Mines level the plan does not want | Go back up at once / Keep today's behaviour | Go back up at once |
| Success metric | Pick the metric to fit the behaviour / Keep "more games reach the Mines" | Pick the metric to fit the behaviour |

---

## Character choice

| Question | Options | Selected |
|----------|---------|----------|
| Candidates | Research shortlists 2-3 / Human vs dwarf Valkyrie only / Wide bench sweep | Research shortlists 2-3 |
| Win metric | Reaching Dlvl 10 / Reaching Dlvl 6 / You decide | Reaching Dlvl 10 |
| Order | Character first / Mines fix first | Character first |

---

## Death triage

| Question | Options | Selected |
|----------|---------|----------|
| Scope | Every game ending / Deaths only | Every game ending |
| Method | Recorded data, replay a sample / Replay every death | Recorded data, replay a sample |
| Cause groups | I propose, you review / Fully automatic | I propose, you review |

---

## Refactor gate & code rules

| Question | Options | Selected |
|----------|---------|----------|
| Gate size | 100 seeds ~5 min / 500 seeds ~20 min / You decide | 100 seeds |
| When it runs | On demand per refactor / Every commit | On demand per refactor |
| File size rule | No file may grow / Hard cap now | No file may grow |
| Commit labels | Git hook + test / Test only | Git hook + test |

---

## Claude's Discretion

Gate seed choice, frame-hash format, new-file size cap, triage presentation, replay sample size.

## Deferred Ideas

CODE-03 module split; route change to Mines-first for all races.
