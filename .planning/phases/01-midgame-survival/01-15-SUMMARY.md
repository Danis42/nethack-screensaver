---
phase: 01-midgame-survival
plan: 15
subsystem: measurement
tags: [done-bar, surv-06, judgement]
requires: [01-14]
provides:
  - "tag p1-final = 3fca503 (Current baseline, code-identical to main)"
  - "five paired verdicts p1-final vs p1-baseline (jobs 28-32) in PORTING.md ### Phase 1 result (SURV-06)"
affects: [01-16, phase-02]
key-decisions:
  - "Phase 1 result: met (D-14): rung2 better +3.1 [+0.8, +5.4]; rung3-rung6 all better too"
---

# Plan 01-15 Summary: Phase 1 done bar

`p1-final` (`3fca503`, exp/shop-door the only kept change) against `p1-baseline` (`0b09707`):

| metric | job | verdict | checkpoint | diff [lo, hi] points |
|--------|-----|---------|------------|----------------------|
| rung2 | 28 | better | 384 | +3.1 [+0.8, +5.4] |
| rung3 | 29 | better | 576 | +1.7 [+0.2, +3.3] |
| rung4 | 30 | better | 1152 | +0.9 [+0.2, +1.6] |
| rung5 | 31 | better | 1152 | +1.0 [+0.2, +1.8] |
| rung6 | 32 | better | 384 | +1.8 [+0.1, +3.6] |

All jobs ran on stored games (no new games played). Acceptance checks pass: `--expect better` on rung2,
`--forbid worse` on rung3-6. No bot code, package or bar changed. Next: 01-16 branch cleanup.
