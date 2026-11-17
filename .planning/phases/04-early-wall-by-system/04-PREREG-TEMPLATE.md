# Phase 4: standard pre-registration (owner pre-approved 2026-11-17)

Owner, in chat: "yes, pre-approve the standard setup for phase 4". Each Phase 4 behaviour plan writes its own
`04-NN-PREREG.md` from this template and commits it before any candidate game; the owner is asked only when a
plan departs from it.

- Baseline: the Monk baseline job 23 (b2b2bbe6d1c9341319b02e937aac7f37ec4db14d), or the newest baseline of main if a
  later change has been merged (named by job ID in the plan's pre-registration).
- Metric: the funnel stage closest to the change (dlvl10 for combat kit); for a change aimed at one death cause, that
  cause's death-rate metric (lower is better) with dlvl10 as guardrail.
- MDE: 10% (relative) of the baseline rate for a stage metric; half the baseline rate for a death-cause metric;
  rounded to the nearest 0.005, at least 0.005. If the SPRT plan does not fit the stored baseline window, the
  smallest 0.005 step above that fits.
- Test: SPRT (bench/sprt.py), alpha 0.05, declared power 0.8; trigger where a recorded firing condition exists.
- Discordance psi: 960-seed pilot of the candidate, psi only (Wilson 95% upper bound, rounded up to 0.005, at least
  MDE + 0.005); nothing else is read from the pilot.
- Decision: dev "better" -> confirm on seeds from 100,000 with gate `phase4-<plan>`; a win needs both. A guardrail
  that is worse with exact McNemar p < 0.05 sends the change to the owner before merge.
- Exceptions that go to the owner: no sensible metric, a plan that cannot fit the bench, an exploit or farming rule.
