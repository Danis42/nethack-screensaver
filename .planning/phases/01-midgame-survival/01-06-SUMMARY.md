---
phase: 01-midgame-survival
plan: 06
subsystem: measurement
tags: [calibration, resolution, valkyrie, checkpoints, screening]

requires: [01-05]
provides:
  - "Measurement code p1-valk-base (0b09707): every game a dwarvish Valkyrie (owner decision); A/A passed (job 13)"
  - "bench/stats.py CHECKPOINTS (192, 384, 576, 1152, 2304); judge_paired(z=) and judge_paired_numeric"
  - "seeded_report.py pairs: numeric metrics, --confidence 80/95/99, sd and standardized half-width"
  - "Protocol step 7a: screen at 384 seeds on rung2 (drop if 80% interval < 0)"
  - "PORTING.md: Bench speed, Bench resolution (calibration), Screening metric"
affects: [01-07, 01-08, 01-09, 01-10, 01-11, 01-12, 01-13, 01-14, 01-15]

key-decisions:
  - "Owner fixed the character to a dwarvish Valkyrie until the first ascension; new A/A (p1-valk-base/twin) replaces p1-aa-base as measurement code"
  - "No turn cap: games past 20k turns use 3.1% of all turns (rule needed >= 25%)"
  - "BLAS env kept at +8% (below the 10% bar): inside the gated SHA, removes a replay risk"
  - "lgen not adopted: half-width 3.77 vs bar 3.73, and two new exception types"
  - "2304 checkpoint adopted: h0 = 3.93 points at 1152 (> 2.0)"
  - "Screening stays on rung2: no numeric metric (rung, depth, turns, score) resolves >= 20% better"
---

# Plan 01-06 Summary: bench speed and resolution

**Result:** the bench's rung2 verdicts resolve about ±2.8 points at 2304 Valkyrie games per side
(MDE80 about 4 points), projected from ±3.93 measured at 1152. A changed bot RNG alone flips the
rung2 outcome of 46% of seeds, so seeding the dungeon removes little noise.

## What happened

1. Speed (Task 0): one BLAS thread +8%; no turn cap (`896f3dc`).
2. All-roles divergence control (job 11): q 0.317, h 3.3. The lgen run (job 12) was stopped when
   the owner fixed the role.
3. Valkyrie switch (`0b09707`), docs twin `00006e4`, A/A job 13: 0 of 1133 seeds mismatched,
   verdict 0.0. Valkyrie ladder: Minetown 44% (was 26%), Medusa reached in 10 games (first ever).
4. Valkyrie calibration jobs 14 and 15; decisions as above; 2304 checkpoint (`b5960c2`), server
   restarted idle; record `67855ed`.
5. Numeric judge and screen-then-confirm (`dc60175`).

## Deviations

- Owner decision mid-plan (Valkyrie only): calibration redone on Valkyrie games; A/A #2 is the
  Valkyrie A/A (tags `p1-valk-base`, `p1-valk-twin`) instead of an lgen A/A.
- `rungmax` is the existing `rung` metric; `deep_turns` skipped (not derivable from stored games).
- Concern for later phases: 19 of 1152 Valkyrie games (all Dlvl 11-28) end on the 120 s
  watchdog, i.e. the bot hangs deep in the dungeon. Same seeds on both sides, so replay holds.
