commit_a: e5b5a7f525bc51b8008f665173600aba80de466d
commit_b: c65c27011a737e33fc218350e1680460ed19f859
primary_metric: dlvl10
rule: rule-strict

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
