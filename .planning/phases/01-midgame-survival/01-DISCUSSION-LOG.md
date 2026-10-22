# Phase 1: Midgame Survival - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-22
**Phase:** 1-Midgame Survival
**Areas discussed:** GSD vs superpowers, Experiment order, Starvation approach, Old branches + done bar

---

## GSD vs superpowers

| Option | Description | Selected |
|--------|-------------|----------|
| GSD | discuss -> plan-phase -> execute-phase; plans in .planning/phases/ | ✓ |
| superpowers | brainstorm -> spec -> plan -> build in docs/superpowers/ | |
| Hybrid | GSD for roadmap; superpowers specs per experiment | |

**User's choice:** GSD

| Option | Description | Selected |
|--------|-------------|----------|
| Point to STATE.md | STATUS.md/handoff.txt become a pointer; "save" updates STATE.md | ✓ |
| Keep both in sync | Update STATUS.md + handoff.txt and STATE.md | |
| Freeze STATUS.md | Keep as history; handoff.txt copies STATE.md | |

**User's choice:** Point to STATE.md

---

## Experiment order

| Option | Description | Selected |
|--------|-------------|----------|
| Stacked | New baseline after each merged win | ✓ |
| One fixed baseline | All changes judged against the same baseline | |

| Option | Description | Selected |
|--------|-------------|----------|
| Starvation | ~13% of games, most mechanical | ✓ |
| Rest to full HP | Cheapest, backed by human data | |
| Ants and bees | ~8%, hardest | |
| You decide | Order by gain per bench hour | |

| Option | Description | Selected |
|--------|-------------|----------|
| Full 1152 | Max sensitivity unless early checkpoint is clear | |
| Stop at 576 | Faster, may miss small gains | |
| You decide per change | 1152 promising, 576 long shots | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| One at a time | Fits stacked baselines | ✓ |
| Two in parallel | Faster, loosens stacking | |

**User's choices:** Stacked; starvation first; Claude decides run size per change; one at a time.

---

## Starvation approach

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnose first | Classify starvation deaths, fix biggest bucket | ✓ |
| Carry more food | Go straight to a food fix | |
| Pray smarter | Save prayer for hunger, exact cooldown | |

| Option | Description | Selected |
|--------|-------------|----------|
| Anything goes | Cheesy tactics allowed | ✓ |
| Safe fixes only | Nothing that can add deaths | |

| Option | Description | Selected |
|--------|-------------|----------|
| One cause each | One change per experiment | ✓ |
| One starvation bundle | All fixes together | |

| Option | Description | Selected |
|--------|-------------|----------|
| Only if bot data is unclear | Human games as fallback | |
| Yes, always compare | Compare with NLD-NAO survivors | ✓ |
| No | Bot data only | |

---

## Old branches + done bar

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, rebase and re-judge | All three, once, on the seeded bench | ✓ |
| Only flee-upstairs | Human-data-backed branch only | |
| No, keep them dropped | Remove SURV-05 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Delete after logging | Log verdict + SHA in PORTING.md, delete; survival-tuning now | ✓ |
| Keep all branches | Leave in place | |

| Option | Description | Selected |
|--------|-------------|----------|
| Keep going, new ideas | Phase stays open until rung2 is better | ✓ |
| Close and move on | Accept gains, start Phase 2 | |
| Lower the bar | Any of rungs 2-6 better | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stop and fix the bench | No experiments until A/A passes | ✓ |
| Proceed with caution | Log, widen bar, continue | |

---

## Claude's Discretion

- Games per side for each experiment (576 vs 1152), recorded per experiment.
- Order of killers after starvation.
- Implementation of each fix, within the dropped-ideas rule.

## Deferred Ideas

None.
