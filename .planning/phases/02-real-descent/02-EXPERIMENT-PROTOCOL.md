# Phase 2 Experiment Protocol (deltas to Phase 1)

Every step of `.planning/phases/01-midgame-survival/01-EXPERIMENT-PROTOCOL.md` applies to Phase 2 plans
(02-03 .. 02-08 and gap-closure plans), with these substitutions. Where a plan says "run the experiment
protocol", it means sections 3-5 of the Phase 1 file read with this table.

## 1. Fixed names

| Name | Kind | Meaning | Created by |
|------|------|---------|------------|
| `p2-baseline` | local tag | Phase 2 baseline code SHA (main after 02-01 and 02-02); never moved | 02-03 |
| `p2-final` | local tag | Code SHA of `main` judged for the Phase 2 done bar | 02-08 |
| `exp/mines-end`, `exp/stuck-1`, `exp/stuck-2`, `exp/quest-portal` | branches | One bot change each | 02-04 .. 02-07 |
| `exp/stuck-<n>` | branches | Gap-closure experiments (CONTEXT D-08 loop) | later plans |

## 2. Ledger lines

In `autoascend/PORTING.md`, section `## Phase 2: real descent` (created by 02-03):
- `Phase 2 baseline: \`<40-hex sha>\`` - written once by 02-03.
- `Current baseline: \`<40-hex sha>\`` - the Phase 1 line is renamed `Phase 1 final baseline:` by 02-03,
  so exactly one `Current baseline:` line exists in the file at any time.

## 3. Changes to the steps

- Step 4 (smoke): seeds are taken from the stuck rows of the current baseline (`seeded_report.py stuck
  <sha> --rows`) or, for the Quest plan, from games that reached Dlvl 11+.
- Step 6 (pre-register): the primary metric is the one the plan names; mechanism metrics always include
  `starved` and `free5` (CONTEXT D-08, RESEARCH Pitfall 5).
- Step 9 (decide): unchanged - keep only on `better` of the pre-registered primary metric.
- Measurement-only changes (02-01, 02-02) are not experiments: they are merged after the full suite and a
  smoke run, and judged by the replay check in 02-03.
