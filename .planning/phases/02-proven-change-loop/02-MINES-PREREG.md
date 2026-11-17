# Leave unwanted Mines: pre-registration (plan 02-05, SURV-04)

Written and committed before any candidate game of this change is played. The owner approved this proposal in
advance (2026-11-17, chat: "yes and i pre approve that"): metric stage_sokoban, MDE set from the fresh baseline's
rates, rule SPRT, trigger mines_unwanted, guardrail died. Every number below is fixed by a rule written here, so
nothing is chosen after seeing experiment games. Changes after this commit are new commits with a reason.

## Comparison

- Baseline: fresh baseline job 23, main b2b2bbe6d1c9341319b02e937aac7f37ec4db14d (`mon-hum-mal-neu`, visit log),
  seeds 1,000-10,999, lgen off.
- Candidate: branch `mines-follow-plan` (draft cd99a5f839ab717e9190e5633f7bc746b6714f22) rebased onto that
  baseline commit, labelled `Kind: behavior`, `Stage: stage_sokoban`, `Metric: stage_sokoban`, `Experiment: pending`.
  Its `stairs.MINES_MILESTONES` must equal `bench.triggers.MINES_WANTED` (checked by a test on the branch).
- Metric: `stage_sokoban` (reached Sokoban). The Monk's plan is BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES,
  FIND_MINETOWN, FIND_SOKOBAN, ...: the change acts on Mines levels once the plan wants something else, mostly on
  the way back from Minetown to Sokoban.
- Guardrail (not a decision metric): `died`. If the candidate's `died` is worse with exact McNemar p < 0.05 on the
  same pairs, the owner reviews before any merge, even with a "better" verdict.

## Settings (each fixed by a rule)

- Rule: SPRT (`bench/sprt.py`, `rule="sprt"`), one comparison, alpha 0.05, declared power 0.8 (actual about 0.79,
  see quick task 261117-kpa), block 96.
- MDE: 10% of job 23's final `stage_sokoban` rate (relative), rounded to the nearest 0.005, at least 0.01.
  If the SPRT plan's n_planned exceeds 10,000 (the stored baseline window), the MDE is the smallest 0.005 step
  above it whose plan fits 10,000.
- Discordance psi: from a pilot on seeds 1,000-1,959 (10 blocks) with the trigger, psi only (the share of seeds
  whose `stage_sokoban` differs; untriggered skipped seeds count as concordant): its Wilson 95% upper bound,
  rounded up to 0.005, and at least MDE + 0.005. Win rates of the pilot are not read. Added here in a second
  commit before the experiment starts.
- Trigger: `mines_unwanted` (bench/triggers.py), audit every seed % 10 == 0; an audit divergence fails the job.
  Partial measure, not a setting: it fired in 282 of the first 634 job 23 games (44.5%).
- Window: dev seeds from 1,000 to 1,000 + n_planned; pilot games are reused.

## Decision rule

- Dev experiment "better" on stage_sokoban -> confirm run on seeds from 100,000 with gate `phase2-mines`
  (D-22, `allow_new_baseline=true`), same rule, MDE and psi.
- Confirm "better" -> the change is kept (merge with `Experiment: job <dev>, job <confirm>`), subject to the
  guardrail review above.
- Dev or confirm not "better" -> the change is not merged as a win; the owner decides whether to keep it.
