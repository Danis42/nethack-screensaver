# Character A/B: result (plan 02-04, SURV-06)

Pre-registration: `02-CHARACTER-PREREG.md` (approved 94b86962c6d057528ff30fa2540af140e9ad2102, futility amendment 3
e3d88db5695a746710899a5a4fae742438bc9317). Baseline e5b5a7f525bc51b8008f665173600aba80de466d (`val-hum-fem-neu`,
job 7 rows), metric dlvl10, MDE 0.04, alpha 0.0167 per finalist, always-valid mixture test, dev seeds from 1,000.

| Job | Finalist | Commit | Verdict | n | b | c | Estimate | Anytime p |
|---|---|---|---|---|---|---|---|---|
| 19 | val-dwa-fem-law | 95be67f1575d7f49bb57860fe22f9bae7dfcc466 | stopped (futility, amendment 3): no win | 3,072 | 700 | 719 | -0.006 | 1.0 |
| 20 | sam-hum-mal-law | 2d43110afc904e431586db7b1cb40a257cb15e2f | worse | 1,152 | 217 | 310 | -0.081 | 0.0049 |
| 21 | mon-hum-mal-neu | e0a949213697906a049a8b6f23da77926311c0d4 | **better** | 672 | 216 | 142 | +0.110 | 0.0070 |

[query: select id, json_extract(result,'$.verdict.state') from jobs where id in (19,20,21) => 19 open (stopped), 20 worse, 21 better]

b = seeds where only the finalist reached Dlvl 10, c = only the baseline. Estimate = (b - c) / n.

## Decision (rule applied as written)

One finalist ended "better" at its alpha: **mon-hum-mal-neu**. `CHARACTER = "mon-hum-mal-neu"` on main:
6e8a2c9a59a3dfddfa77f966efb1627410d93a7c (Kind: behavior, Stage: dlvl10, Metric: dlvl10, Experiment: job 21).

## Notes

- Job 21 decided early (672 of 8,256 planned seeds): the always-valid test allows that; the effect is large
  (+11 points on a 38.8% base). The estimate from an early stop is biased away from zero, so expect the fresh
  baseline's dlvl10 to land below 38.8% + 11.0%.
- Job 20's Samurai is clearly worse at dlvl10 (the test can say "worse"; this rule keeps it out either way).
- Next per the rule: a fresh 10,000-game baseline of main on seeds 1,000-10,999. Before it starts, the visit log
  (quick task 261117-l4a) is gated and merged so the baseline supports trigger-gated experiments in 02-05.
