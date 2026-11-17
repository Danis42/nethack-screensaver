# Character A/B: pre-registration (plan 02-04, SURV-06)

Written and committed before any finalist game is played. Changes after this commit are new commits with a reason.

## Comparison

- Baseline: commit e5b5a7f525bc51b8008f665173600aba80de466d (`val-hum-fem-neu`), its job 7 rows, dev seeds from 1,000.
- Finalists (research: `.planning/research/CHARACTER-NH5.md`), each a branch off the baseline that changes only the
  `CHARACTER` line:

| Finalist | Branch | Commit |
|---|---|---|
| val-dwa-fem-law | `char/val-dwa-fem-law` | 95be67f1575d7f49bb57860fe22f9bae7dfcc466 |
| sam-hum-mal-law | `char/sam-hum-mal-law` | d67530e6b4aa56db3ccc7d9425f40baa86029e6f |
| mon-hum-mal-neu | `char/mon-hum-mal-neu` | e0a949213697906a049a8b6f23da77926311c0d4 |

- Metric: `dlvl10` (reached Dlvl 10+; baseline 38.76%), each character with its own `plan_for` route (D-03).
- MDE: 0.03 absolute (proposed; the owner confirms or changes it before the runs).
- alpha per comparison: 0.05 / 3 = 0.0167 (Bonferroni over the three finalists). Power 0.8, block 96.
- Discordance psi per finalist: measured on seeds 1,000-1,199 (pilot of 200 games per finalist, compared with the
  baseline's rows on the same seeds: share of seeds where dlvl10 differs). Only psi is read from the pilot, never
  the win rates. psi is rounded up to the next 0.05 and added here in a second commit before the experiments start.
- Window: starts at seed 1,000 and runs to 1,000 + n_planned (from `bench_power`); the pilot games are reused.
- Test: the bench experiment (always-valid sequential test, MEAS-06), one job per finalist.

## Decision rule

- A finalist wins if its experiment ends "better" at its alpha.
- Several winners: the one with the largest dlvl10 effect.
- No winner: `CHARACTER` stays `val-hum-fem-neu`.
- The winner goes into the one `CHARACTER` constant on main as a `Kind: behavior` commit naming its experiment job,
  then a fresh 10,000-game baseline of main on seeds 1,000-10,999 follows. No confirm-seed run is part of SURV-06.

## Amendment 1 (2026-11-15, before any experiment game)

The Samurai pilot (job 13) ended all 200 games on turn 1 with a bot crash: NetHack 5.0 shows a Samurai's
discoveries with Japanese names (`* shito [knife]`, `* potion of sake [booze] (fizzy)`, harp appearance "koto",
`src/objnam.c:105-119, 211-213`) and the bot's discoveries parser asserted on them. Its pilot measured nothing.

- Fix: branch `fix/japanese-names` off the baseline, `autoascend/item/item_manager.py` only. It must play exactly
  like the baseline for the Valkyrie: refactor gate job 15 against e5b5a7f525bc51b8008f665173600aba80de466d.
- The Samurai finalist is rebuilt on top of the fix (fix + `CHARACTER` line) and its pilot re-run on seeds
  1,000-1,199. The Samurai comparison is therefore "Samurai with the parser fix" against the baseline; for the
  baseline character the fix is proven a no-op by the gate.
- The other two finalists are unchanged; their pilots (jobs 12 and 14) stand.

## Amendment 2 (2026-11-15, before any experiment game)

The re-run Samurai pilot (job 16) still crashed in 33 of 200 games, 31 of them on "a potion of sake": the bot's
Japanese-name list lacked sake, koto and magic koto. Branch `fix/samurai-names` (on the first fix) replaces that
list with one table from `src/objnam.c:105-119, 211-213`; refactor gate job 17 against
d869b5f09f002637ce44f5a4ad69db049b4846ac must show it plays exactly the same for the Valkyrie. The Samurai finalist is
rebuilt on it and its pilot re-run once more on seeds 1,000-1,199 (games of earlier Samurai commits are not reused:
other sha). If the new pilot still crashes in more than 5% of games, the Samurai is dropped from the A/B and alpha
becomes 0.05 / 2 = 0.025 for the other two.

## Discordance from the pilots (seeds 1,000-1,199, dlvl10 against job 7 rows)

| Finalist | Pilot job | Commit | Seeds that differ | psi | psi used |
|---|---|---|---|---|---|
| val-dwa-fem-law | 12 | 95be67f1575d7f49bb57860fe22f9bae7dfcc466 | 100 of 200 | 0.500 | 0.50 |
| sam-hum-mal-law | 18 | 2d43110afc904e431586db7b1cb40a257cb15e2f | 98 of 200 | 0.490 | 0.50 |
| mon-hum-mal-neu | 14 | e0a949213697906a049a8b6f23da77926311c0d4 | 113 of 200 | 0.565 | 0.60 |

Samurai pilot 18: 3 of 200 games crashed (1.5%, under the 5% limit of amendment 2); it stays a finalist. Earlier
Samurai pilots (jobs 13 and 16, older commits) are void. Only psi and crash counts were read from the pilots.

Planned games per finalist at alpha 0.0167, power 0.8 (`/api/power`):

| MDE | psi 0.50 | psi 0.60 |
|---|---|---|
| 0.03 | 12,096 | 14,784 |
| 0.04 | 6,624 | 8,256 |
| 0.05 | 4,224 | 5,184 |

The MDE is set by the owner at the approval step; the window is [1000, 1000 + n_planned). Where n_planned exceeds
10,000, the baseline commit plays the extra seeds above 10,999 (`allow_new_baseline`).

## Owner approval (2026-11-16)

MDE 0.04; all three finalists; alpha 0.0167 each. Planned sizes: val-dwa-fem-law 6,624 (psi 0.50), sam-hum-mal-law
6,624 (psi 0.50), mon-hum-mal-neu 8,256 (psi 0.60), all windows from seed 1,000, so every baseline game is a job 7 row.
Owner note: hostile Mines dwarves give food, experience and pick-axes, which a dwarvish hero loses; the dlvl10
comparison measures that trade-off as part of the net effect. The finalist stays in.

## Amendment 3 (2026-11-17, during the experiments): futility stop

Owner decision 2026-11-17 01:4x, after seeing job 19's interim counts (n 3,072, b 700, c 719). This adds a stop rule
that can only end a finalist *without* a win; it never creates a "better", so the false-win rate stays at most
alpha.

- Check: `scripts/futility.py <job>` simulates the rest of the planned window in 96-seed blocks, assuming the true
  dlvl10 effect from now on equals the MDE (0.04) and the observed discordance rate, at alpha 0.0167 (4,000 runs,
  fixed RNG seed).
- Rule: a job whose verdict is still "open" and whose simulated P(better) is below 0.05 is stopped. It counts as
  "no win" in the decision rule. The check runs every 15 minutes on each running job.
- The decision rule itself (winner = "better"; largest effect among winners; none -> `val-hum-fem-neu`) is unchanged.
- First use: job 19 (val-dwa-fem-law) at n 3,072: P(better at MDE) 0.013 -> stopped.
