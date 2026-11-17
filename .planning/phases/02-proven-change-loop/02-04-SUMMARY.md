---
phase: 02-proven-change-loop
plan: 04
status: complete
requirements: [SURV-06]
commits:
  - 94b86962c6d057528ff30fa2540af140e9ad2102  # owner approval of the A/B
  - e3d88db5695a746710899a5a4fae742438bc9317  # futility stop (amendment 3)
  - 6e8a2c9a59a3dfddfa77f966efb1627410d93a7c  # CHARACTER = mon-hum-mal-neu
jobs: [12, 14, 15, 17, 18, 19, 20, 21, 23]
---

# 02-04 Summary: character A/B

- Result (02-CHARACTER-RESULT.md): job 21 mon-hum-mal-neu "better" on dlvl10 (+0.110, b 216, c 142, n 672,
  anytime p 0.0070 < 0.0167); job 20 sam-hum-mal-law "worse" (-0.081); job 19 val-dwa-fem-law stopped by futility.
  Rule applied as written: one winner, `CHARACTER = "mon-hum-mal-neu"` (6e8a2c9a59a3dfddfa77f966efb1627410d93a7c).
- Fresh baseline: job 23, main b2b2bbe6d1c9341319b02e937aac7f37ec4db14d, seeds 1,000-10,999, lgen off. This main
  also records the visit log (gate job 22, 100 of 100 identical) and judges new experiments with the SPRT by default.
- Early stop caveat: job 21 stopped at 672 of 8,256 planned seeds; its effect estimate is biased away from zero.
  The job 23 baseline gives the Monk's real dlvl10 rate.
