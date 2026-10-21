# Seeded, paired bench experiments — design

Date: 2026-10-21. The user delegated the details.

## Why

Bench games are unseeded, so each side of an experiment is an independent random sample.
A control test (same code on both sides, 1152 games each) came out -2.3 points, and the
smallest detectable difference is about 3.5 points: real gains of 1-3 points, which most
single survival rules will be, can never be seen. NetHack can be started from fixed seeds
(`set_initial_seeds`; the bot's own RNG is already fixed at seed 0), so game number k of
two commits can be the same character and the same first level. Dungeon luck then
cancels out in a paired comparison.

## Design

- **Game:** `run_game(seed=None)`; with a seed, NetHack's core and display RNGs start
  from `(seed, seed)` (through `type(env.nethack).set_initial_seeds`, because
  `NetHackChallenge` blocks the instance method). `GameResult.seed` records it. A seed
  with a pinned role is refused (`ValueError`): the role loop resets until the role
  matches, which never happens when every reset replays the same seed.
- **Worker protocol:** `play <seed>` (and still `play`). The worker passes the seed when
  the commit's `run_game` accepts one; a result without `seed` means the commit predates
  seeding.
- **Scheduler:** a job needs seeds `0 .. N-1` for each commit (baseline: `N = games`;
  experiment: `N` = current checkpoint, both sides). It hands out the lowest seed neither
  stored nor in flight for that commit; a dead worker's seed is handed out again. A
  result without a seed fails the job ("commit cannot play seeded games").
- **Verdict:** paired: for each seed both sides have, the metric's two values; difference
  of rates `d = (n10 - n01) / n` with the paired (Wald) interval
  `d ± z * sqrt(n10 + n01 - n * d²) / n` (n10: candidate yes / baseline no). Same
  checkpoints and z as now (99% early, 95% at 1152). The rest of the experiment table
  stays as it is but uses the same paired games.
- **Store:** `seeds(sha)` and `games_by_seed(sha, seeds)` read `$.seed` from the stored
  JSON. Unseeded old games stay for statistics and history; jobs ignore them.

## Testing

Paired interval against a hand-computed example and the "no discordant pairs" edge;
scheduler: seeds 0..N-1 handed out once per commit, stored seeds reused, a dead worker's
seed replayed, an old-commit result fails the job, both sides play the same seeds;
store seed queries; worker protocol (`play 7` reaches `run_game(seed=7)`; an old
`run_game` without the parameter runs unseeded); a real game: same seed twice gives the
same first screen; seed plus pinned role is refused.

## After

A seeded A/A control (same code twice) should come out near 0 with a much narrower
interval; then the pilgrim-only baseline.
