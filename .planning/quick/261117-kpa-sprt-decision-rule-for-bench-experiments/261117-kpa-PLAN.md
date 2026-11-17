---
quick_id: 261117-kpa
slug: sprt-decision-rule-for-bench-experiments
date: 2026-11-17
mode: quick (inline, owner preference: no subagents)
---

# Quick task: Wald SPRT decision rule for bench experiments

**Owner decision (2026-11-17, chat):** approve the efficiency recommendation: (2) SPRT decision rule for future
experiments, (1) skip seeds where a change cannot fire, (4) speed refactors under the gate. This task is (2) only.
Running jobs 20 and 21 keep their pre-registered mixture rule (declared without `rule` -> mixture, unchanged code path).

## Design

Per discordant pair, theta = chance it favours the candidate. H0: theta = 1/2. H1: theta1 = 1/2 + s * mde / (2 psi),
with psi the declared discordance and s = -1 for a lower-is-better metric (so "better" is always the improvement).

log LR after (b, c) discordant pairs: w * log(2 theta1) + l * log(2 (1 - theta1)), w/l = pairs for/against the
improvement.

- Upper bound log(1/alpha): stop, "better". Under H0 the LR is a nonnegative martingale for ANY fixed theta1, so
  Ville's inequality gives P(false "better") <= alpha at any number of looks, whatever the true psi. psi only moves power.
- Lower bound log((1 - power) / (1 - alpha)) (Wald's B): stop, NO_EFFECT ("no win"). Does not affect type I error.
- Cap n_planned: smallest block multiple where the simulated, truncated SPRT reaches the declared power at the MDE.
- One-sided: no "worse" verdict. A no-win change is not kept, which is all the owner's keep rule needs.

## Tasks

1. `bench/sequential.py`: `sprt_theta1`, `log_sprt_lr`, `judge_sprt(looks, alpha, power, n_planned, mde, psi,
   lower_is_better)` returning `SeqVerdict` (oriented state). Tests in `tests/test_bench_sequential.py`:
   bounds, orientation, cap, H0 martingale-free sanity.
2. `bench/power.py`: `sprt_power`, `sprt_sample_size`, `plan(..., rule="sprt")` adding `rule`, `theta1`,
   expected seeds under H0 and H1. `bench/scheduler.py`: judge with `judge_sprt` when `declared["rule"] == "sprt"`,
   skip `orient` there; missing rule keeps the mixture path byte-for-byte. `bench/server.py` / `bench/cli.py` /
   `bench/mcp_server.py`: `rule` parameter, default "sprt" for new experiments, `alpha` exposed on MCP.
3. `scripts/sim_sprt.py`: validation report (null false-positive rate at psi 0.05/0.2/0.46 with psi misdeclared,
   power and mean seeds at MDE, comparison with the mixture). Committed JSON report in this directory.

## Done when

- `uv run pytest` passes; sim report shows every null cell rate <= alpha + 3 se.
- Jobs 20/21 judged by the unchanged mixture path (test: a declared dict without `rule` gives the same verdict).
