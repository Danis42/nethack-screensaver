---
quick_id: 261117-kpa
status: complete
date: 2026-11-17
commits:
  - e02665eb5ad4bcb60cdd7e5fde04e682e25857b0  # SPRT code, tests, sim script
---

# 261117-kpa Summary: Wald SPRT decision rule for bench experiments

**Owner decision (2026-11-17):** adopt the efficiency research recommendation: (2) SPRT decision rule now,
(1) skip seeds where a change cannot fire and (4) speed refactors under the gate next.

## What changed

- `bench/sprt.py` (new): SPRT on discordant pairs. H1 theta1 = 1/2 +- mde / (2 psi). Upper bound log(1/alpha)
  ("better", Ville: valid for any declared psi and any number of looks), Wald lower bound ("no win"), cap sized by
  simulation. `judge_declared` dispatches on `declared["rule"]`; `plan`, `power_report` shared by server and CLI.
- `rule="sprt"` is the default for new experiments on HTTP, MCP (`bench_experiment`, `bench_power`) and CLI
  (`power --rule`). `rule="mixture"` keeps the old test. MCP `bench_experiment` now also forwards alpha and power.
- Jobs declared without `rule` (19, 20, 21 and older) are judged by the unchanged mixture code
  (`test_a_plan_without_a_rule_is_judged_by_the_unchanged_mixture_test`). The running server still holds the old
  code in memory; a restart judges 20/21 the same way.
- Ratchets respected: no pinned file grew (server.py 443 -> 432 by folding the duplicate power code).

## Evidence

- `uv run pytest`: 903 passed, 6 skipped.
- `scripts/sim_sprt.py --out 261117-kpa-SIM-SPRT.json` (seed 20261117, 20,000 reps, exit 0): every null cell
  within alpha + 3 se. Worst: 1.39% false "better" with a look after every discordant pair (alpha 1.67%).
  Misdeclared psi (true 0.05/0.2 vs declared 0.46): 0% / 0.6%.
- Seeds played, SPRT vs mixture (character settings psi 0.46, MDE 0.04, alpha 0.0167): at no effect 1,073 vs
  6,034 (5.6x); at half the MDE 2,039 vs 5,831 (2.9x); at the MDE 1,961 vs 3,862 (2.0x).

## Caveats

- Power at the MDE is about 0.79 for a declared 0.80 (Wald's lower bound stops some true-MDE runs early). The plan
  reports out-of-sample power (seed + 1), so the declared number is honest; declare ~0.82 for a true 0.80.
- One-sided: an SPRT never says "worse"; a harmful change ends as "no detectable effect". Keep guardrail metrics
  (crashed, died) in reviews.
- Between 0 and the MDE the SPRT has less power than at the MDE (0.22 at half the MDE vs 0.09 for the mixture).
