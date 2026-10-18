# Secret Strategies — Design

Date: 2026-10-18
Status: Approved design, pending spec review

## Goal

Every screensaver game starts with a random character (role, race, gender,
alignment — NLE already rolls these) and is secretly assigned one of four bot
strategies. Each strategy aims at a different NetHack ending and plays a
visibly different route. On screen it looks like a normal game; the goal only
shows in how the bot plays, and optionally in a reveal on the game-over screen.

Success: the four strategies play visibly differently, the two escape
strategies actually win some runs, and nothing gets less stable.

## Reality check

The two Amulet endings (ascension, escape in celestial disgrace) need the full
late game: Quest, Castle, Gehennom, Vlad's Tower, the invocation, the Planes.
AutoAscend's best runs reach Dlvl 10-13 and its plan ends at Mines' End. Those
two strategies therefore keep their ending as the stated goal but play only the
part that is reachable: they never contain Amulet code. Plain escape (leave by
the Dlvl 1 upstairs) is reachable and is what Sightseer and Treasure hunter
aim for.

## Decisions

| Topic | Decision |
|---|---|
| Character | Unchanged: NLE's random role/race/gender/alignment; `role` config can still pin a role |
| Strategy pick | Uniformly random per game in `run_game`; `strategy` config can force one |
| Secrecy | Never shown during play; recorded in `games.jsonl` |
| Reveal | Off by default; `reveal_goal = true` shows one line on the game-over screen |
| Mechanism | A strategy is an ordered list of milestones, replacing today's single fixed order |
| Amulet steps | Not implemented (unreachable); Pilgrim and Daredevil end in "descend forever" |
| Pacing | Unchanged; the return trip over known levels fast-forwards by itself |

## Strategies

Every plan starts with `BE_ON_FIRST_LEVEL` (explore Dlvl 1, leave when Hungry),
so the opening never gives the goal away.

| Name | Target ending | Milestones |
|---|---|---|
| `pilgrim` | ascension | BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN, FIND_SOKOBAN, SOLVE_SOKOBAN, FIND_MINES_END, GO_DOWN |
| `daredevil` | escape in celestial disgrace | BE_ON_FIRST_LEVEL, GO_DOWN |
| `sightseer` | escape | BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN, EXPLORE_MINETOWN, RETURN_TO_SURFACE, LEAVE_DUNGEON |
| `treasure` | escape with loot | BE_ON_FIRST_LEVEL, FIND_SOKOBAN, SOLVE_SOKOBAN, LOOT_SOKOBAN_PRIZE, RETURN_TO_SURFACE, LEAVE_DUNGEON |

`pilgrim` is today's upstream order, so it doubles as the baseline.

### New milestones

- `EXPLORE_MINETOWN`: explore the Minetown level (existing exploration
  strategy on `minetown_level`) for 1,000 turns, then advance. A turn budget,
  because the explorer never reports a level as done (it keeps searching).
- `LOOT_SOKOBAN_PRIZE`: explore the top Sokoban level `(SOKOBAN, 1)`; the bot's
  own fighting and item gathering clear the zoo and pick up the prize. Advance
  once a possible prize (bag of holding / amulet of reflection) is in the
  inventory, or after 1,500 turns on that level.
- `RETURN_TO_SURFACE`: travel by known stairs to `(DUNGEONS_OF_DOOM, 1)`
  (existing `go_to_level_strategy` path finding), then advance.
- `LEAVE_DUNGEON`: walk to the Dlvl 1 upstairs and go up. NetHack asks
  "Beware, there will be no return! Still climb?"; the agent already answers
  every `[yn]` prompt with `y`, so the game ends as an escape.

### Advancing

`GlobalLogic` holds the plan and an index. "Advance" moves to the next
milestone in the plan instead of `Milestone(int + 1)`. When Sokoban is dropped
as unsolvable (today's `sokoban_dropped` path), the plan skips
`LOOT_SOKOBAN_PRIZE` if it comes next, so Treasure hunter goes home empty-handed.
The last milestone of a plan never advances (`GO_DOWN` and `LEAVE_DUNGEON` end
the game by themselves).

## Data flow

```
player.main ── cfg.strategy ──► run_game(strategy=None|name)
                                  │ picks name if None (random.choice)
                                  ▼
                       EnvWrapper(agent_args={..., plan=PLANS[name]})
                                  ▼
                       Agent ──► GlobalLogic(plan)
                                  ▼
            GameResult(+ strategy, gender, outcome) ──► games.jsonl
                                  ▼
            player: end screen + reveal line (if cfg.reveal_goal)
```

`farming` for pacing stays "current milestone is BE_ON_FIRST_LEVEL".

## Results and log

`GameResult` and each `games.jsonl` record gain:

- `strategy`: `pilgrim` | `daredevil` | `sightseer` | `treasure`
- `gender`: from the character string the result already parses
- `outcome`:
  - escape strategies that escaped: `escaped` (sightseer), `escaped with loot`
    or `escaped empty-handed` (treasure; loot = bag of holding or amulet of
    reflection in the inventory at the end)
  - any death: `died on Dlvl N` (N = max depth)
  - exception or watchdog: `crashed`

An escape is recognised from the final screen text ("escaped"), not assumed to
be a death. `_parse_end_reason` must report it as an escape.

Old log records without the new fields still load (`read_stats` ignores
missing keys).

## Reveal

With `reveal_goal = true`, during the `end_pause` hold the bottom row of the
final screen shows:

```
Secret goal: Sightseer · escape the dungeon · ESCAPED!
Secret goal: Daredevil · escape in celestial disgrace · died on Dlvl 11
```

Format: `Secret goal: <Name> · <target ending> · <outcome>`, with a successful
escape outcome in capitals plus `!`.

## Config

```toml
strategy = "random"    # or pilgrim / daredevil / sightseer / treasure
reveal_goal = false
```

Validated like `role`: unknown values warn and fall back to the default.

## Testing

Unit (fast suite):
- each plan advances through its milestones in order; a dropped Sokoban skips
  `LOOT_SOKOBAN_PRIZE`; the last milestone does not advance
- strategy pick: random covers all four over many draws; a forced name is used
- config: valid and invalid `strategy` / `reveal_goal`
- outcome text for each strategy and end kind; reveal line formatting
- `_parse_end_reason` on a recorded "escaped" final screen

Slow:
- one real game each for `sightseer` and `treasure` with a step limit: no
  crash, and the plan moves past `BE_ON_FIRST_LEVEL`

Benchmark: `scripts/benchmark.py --strategy NAME` (default: random) prints per
strategy the median max depth, the share of games reaching the Mines, Minetown
and Sokoban, and outcome counts. Run 24-48 games per strategy.

Acceptance:
1. `sightseer` and `treasure` escape in at least some runs (rate measured, not
   promised).
2. Strategies differ: `daredevil` has the deepest median, `sightseer` reaches
   Minetown most often, `treasure` reaches Sokoban far more often than today's 2%.
3. `pilgrim` matches the current baseline (median Dlvl 5, Mines in about two
   thirds of games).
4. No new exception types; all existing tests pass.

## Out of scope

- Any Amulet, Quest, Castle or Gehennom logic.
- Showing the strategy during play.
- Weighting strategies unevenly.
