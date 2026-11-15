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
