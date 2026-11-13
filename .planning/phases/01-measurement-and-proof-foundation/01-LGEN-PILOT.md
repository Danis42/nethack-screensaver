commit_a: e5b5a7f525bc51b8008f665173600aba80de466d
commit_b: c65c27011a737e33fc218350e1680460ed19f859
primary_metric: dlvl10
rule: rule-strict
rule_commit: 09b79fbb306764b9fae898b2c00a2e22158e4587
pilot_jobs: a_off=3 a_seed=4 b_off=5 b_seed=6

# lgen pilot: pre-registration (MEAS-04)

Written and committed before any pilot job exists. No pilot result is looked at before all four jobs are done.

## Design

- Commit A (e5b5a7f525bc51b8008f665173600aba80de466d): `main` with every Phase 1 code change, including the lgen plumbing (plan 01-05).
- Commit B (c65c27011a737e33fc218350e1680460ed19f859, branch `pilot/lgen-b`, never merged): commit A plus the archived `exp/elbereth-respect` change. B does not engrave Elbereth against monsters that ignore it (every `S_HUMAN` `@` and minotaurs, per `monmove.c onscary`), and does not wait on Elbereth next to one. Owner's choice (option archived-midgame), 2026-11-12. B is used only to create realistic discordance; the pilot does not evaluate the change itself.
- Four baseline jobs on seeds [1000, 1400): (A, lgen off), (A, lgen seed), (B, lgen off), (B, lgen seed). With lgen on, the NLE level-generation seed is seed + LGEN_OFFSET (10,000,000), never 0.
- Primary metric: **dlvl10** (reached Dlvl 10+). The owner delegated this choice; the reasons:
  1. Games are deterministic per seed, so A and B are identical until B's change first fires. Its triggers are elves (Woodland-elf and Green-elf are `S_HUMAN`, monster levels 4 and 5 in `include/monsters.h`) and Minetown's watch, so it mostly fires around Dlvl 5-8. Most dlvl6 outcomes are settled before that, so psi on dlvl6 would be near zero in both modes and the rule could not decide.
  2. Base rate near the middle: Dlvl 10+ was reached in 26 of 81 screensaver games (32%), against 58 of 81 (72%) for Dlvl 6+. Those games came from mixed commits outside the bench, so this is indicative only.
  3. lgen keeps level layouts fixed after the game RNG diverges. Its benefit can only show when several levels are played after the divergence, which a deeper metric allows.

## Computations (run only after all four jobs are done)

Pairs are formed per seed over the seeds both commits played in the same lgen mode.

Per lgen mode (off, seed), on the primary metric:
- b (A fails, B succeeds), c (A succeeds, B fails), psi = (b + c) / n with a 95% Wilson interval
- exact McNemar p and the mixture (mSPRT) verdict from `bench.sequential`
- the share of seeds whose full results are identical on the replay_check fields (role, race, gender, alignment, max_depth, turns, score, end_reason, ...)

Across modes:
- psi_on - psi_off with a 95% paired interval over seeds. The per-seed indicator is d_s = [discordant with lgen on] - [discordant with lgen off]; the interval is the Wald interval of the mean of d_s (n = number of seeds paired in both modes).
- For commit A, per stage key: reach with lgen on versus off on the same seeds, as a difference with a 95% paired interval (Wald on the per-seed difference of the reach indicators), for every stage with at least 20 hits in either mode.

## Decision rule (rule-strict, verbatim)

Adopt lgen if psi_on < psi_off on the primary metric with the 95% paired interval of psi_on minus psi_off entirely below 0, AND for commit A no stage_<key> reach rate with at least 20 hits in either mode differs between lgen on and off beyond its 95% paired interval on the same seeds.

"Differs beyond its 95% paired interval" means the stage's paired interval of (reach on - reach off) excludes 0. If the rule does not hold, the bench keeps lgen off (`seeds.USE_LGEN = "off"`). The decision and both job pairs go into this file, and the result goes into `bench/seeds.py` in plan 01-15.

## Notes

- Bench lgen pairing is not the "dungeon screening" the owner approved for the final attempt (ASC-02). Screening chooses seeds by dungeon features; this pilot selects no seeds.
- Pitfall 11: psi depends on the candidate change. A later experiment is sized from the upper bound of psi, and this pilot's psi describes a mid-game fight change.

## Jobs

The rule above was committed in 09b79fbb306764b9fae898b2c00a2e22158e4587 before the four jobs were created. Job 3 (A, off) started: its first game row was stored at 2026-11-13 00:05:17. Jobs 4 (A, seed), 5 (B, off) and 6 (B, seed) are queued. At about 30 games per minute the four jobs need roughly 55 minutes; plan 01-15 starts when all four are done.

## Results (plan 01-15)

Produced by `.venv/bin/python scripts/lgen_pilot.py --jobs 3 4 5 6 --metric dlvl10` after `bench.cli wait` exited 0 for jobs 3, 4, 5 and 6 (400 games each, 0 unpaired seeds):

results:
```json
{"jobs": [3, 4, 5, 6], "commit_a": "e5b5a7f525bc51b8008f665173600aba80de466d", "commit_b": "c65c27011a737e33fc218350e1680460ed19f859", "metric": "dlvl10", "games": [400, 400, 400, 400], "unpaired": [0, 0]}
{"metric": "dlvl10", "lgen": "off", "n": 400, "b": 2, "c": 0, "psi": 0.005, "psi_lo": 0.0013722529547103846, "psi_hi": 0.018044918436243156, "mcnemar_p": 0.5, "mixture_state": "no detectable effect >= MDE", "identical_share": 0.69}
{"metric": "dlvl10", "lgen": "seed", "n": 400, "b": 3, "c": 1, "psi": 0.01, "psi_lo": 0.003895483794990993, "psi_hi": 0.025426564652619582, "mcnemar_p": 0.625, "mixture_state": "no detectable effect >= MDE", "identical_share": 0.6975}
{"metric": "dlvl10", "psi_difference": {"n": 400, "psi_off": 0.005, "psi_on": 0.01, "diff": 0.005, "lo": -0.00700729162760329, "hi": 0.01700729162760329}}
{"stage_shift_commit_a": [{"key": "mines", "n": 400, "hits_off": 218, "hits_on": 242, "diff": 0.06, "lo": -0.00772476700300069, "hi": 0.12772476700300067, "judged": true, "shifted": false}, {"key": "minetown", "n": 400, "hits_off": 76, "hits_on": 94, "diff": 0.045, "lo": -0.009452694521113532, "hi": 0.09945269452111352, "judged": true, "shifted": false}, {"key": "oracle", "n": 400, "hits_off": 201, "hits_on": 193, "diff": -0.02, "lo": -0.0879518414607509, "hi": 0.04795184146075089, "judged": true, "shifted": false}, {"key": "sokoban", "n": 400, "hits_off": 101, "hits_on": 99, "diff": -0.005, "lo": -0.06427795350834438, "hi": 0.054277953508344384, "judged": true, "shifted": false}, {"key": "sokoban_solved", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "mines_end", "n": 400, "hits_off": 41, "hits_on": 48, "diff": 0.0175, "lo": -0.026621016208207622, "hi": 0.061621016208207625, "judged": true, "shifted": false}, {"key": "dlvl15", "n": 400, "hits_off": 25, "hits_on": 30, "diff": 0.0125, "lo": -0.023195491097824695, "hi": 0.0481954910978247, "judged": true, "shifted": false}, {"key": "quest_portal", "n": 400, "hits_off": 25, "hits_on": 26, "diff": 0.0025, "lo": -0.031133264739352826, "hi": 0.03613326473935283, "judged": true, "shifted": false}, {"key": "quest", "n": 400, "hits_off": 21, "hits_on": 24, "diff": 0.0075, "lo": -0.023905403453408906, "hi": 0.038905403453408906, "judged": true, "shifted": false}, {"key": "medusa", "n": 400, "hits_off": 1, "hits_on": 3, "diff": 0.005, "lo": -0.00479981992270027, "hi": 0.01479981992270027, "judged": false, "shifted": false}, {"key": "castle", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "gehennom", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "vlad", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "wizard_tower", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "invocation", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "planes", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "astral", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}, {"key": "ascended", "n": 400, "hits_off": 0, "hits_on": 0, "diff": 0.0, "lo": 0.0, "hi": 0.0, "judged": false, "shifted": false}]}
```

## Decision

decision: keep-lgen-off

Rule applied (rule-strict, committed in 09b79fbb306764b9fae898b2c00a2e22158e4587): adopt lgen only if psi_on < psi_off on dlvl10 with the 95% paired interval of psi_on - psi_off entirely below 0, and no judged stage of commit A shifts.

- lgen off (jobs 3 and 5): b 2, c 0, n 400, psi 0.005, Wilson 95% [0.0014, 0.0180], exact McNemar p 0.5, identical full results 69.0%.
- lgen seed (jobs 4 and 6): b 3, c 1, n 400, psi 0.010, Wilson 95% [0.0039, 0.0254], exact McNemar p 0.625, identical full results 69.75%.
- psi_on - psi_off = +0.005, 95% paired interval [-0.0070, +0.0170]. The first condition fails (psi_on is not below psi_off and the interval is not below 0), so the rule does not hold. No judged stage of commit A shifted (all stage intervals include 0), which does not matter once the first condition fails.

Result: `bench/seeds.py` keeps `USE_LGEN = "off"`; `bench/power.py` gets `DEFAULT_DISCORDANCE = 0.019`, the Wilson upper bound of psi with lgen off, rounded up to three decimals.

Commit B's change (Pitfall 11): B stops engraving Elbereth against `S_HUMAN` monsters and minotaurs and stops waiting on Elbereth next to them. It flipped dlvl10 on only 2 of 400 seeds with lgen off, so psi here describes a small mid-game change. A change expected to alter games more must be sized with an explicit `--discordance`, not this default.

This is bench pairing, not the dungeon screening of ASC-02: no seeds were chosen by dungeon features.
