# Ascension ladder (sub-project 0) — design

Date: 2026-10-21. Part of the real-ascension objective, see `docs/ROADMAP.md`.

## Goal

Measure how far up the road to an ascension each game gets, so every later sub-project
can be judged by the bench server. This sub-project only measures: the bot plays exactly
as before.

## Decisions (from the brainstorm)

- Success is a ladder: each rung is progress, a real ascension is the top rung.
- 17 rungs in the median order of the 687 real ascensions (the yardstick).
- A game's result is the highest rung it reached; lower rungs need not all be reached
  (a Sokoban-first pilgrim that skipped the Mines still counts rung 5).
- The bot records rungs live while it plays (not from the end screen, not from recordings).
- Rungs 1-8 must be accurate now (our games end there). Rungs 9-17 are simple proxies with
  a unit test each, refined when a sub-project first brings real games near them.
- Sightseer and treasure keep their escape goals; their games get a ladder value too.

## Rungs

NetHack numbers its dungeons in `dungeon.def` order: 0 Dungeons of Doom, 1 Gehennom,
2 Gnomish Mines, 3 Quest, 4 Sokoban, 5 Fort Ludios, 6 Vlad's Tower, 7 Elemental Planes
(Astral Plane is level 1 there). The bot reads (dungeon, level) from `blstats`.

| # | key | Reached when | Kind | Yardstick event (median turn) |
|---|-----|--------------|------|-------------------------------|
| 1 | `mines` | in dungeon 2 | exact | entered the Gnomish Mines (1173) |
| 2 | `minetown` | `global_logic.minetown_level` is set | bot | reached Mine Town (3538) |
| 3 | `oracle` | `global_logic.oracle_level` is set | bot | — |
| 4 | `sokoban` | in dungeon 4 | exact | entered Sokoban (9022) |
| 5 | `sokoban_solved` | on (4, 1), no trap left (see below) | bot | completed 4th Sokoban level (12412) |
| 6 | `mines_end` | the bottom Mines level, see below | proxy | acquired the Mines' End luckstone (10853) |
| 7 | `dlvl15` | level 15+ in dungeon 0 | exact | — |
| 8 | `quest` | in dungeon 3 | exact | entered Home 1, the Quest (22426) |
| 9 | `medusa` | dungeon 0, level 21+, and Medusa seen or more than a third of the seen map is water | proxy | killed Medusa (29317) |
| 10 | `castle` | dungeon 0 and a drawbridge glyph seen | proxy | — |
| 11 | `gehennom` | in dungeon 1 | exact | entered Gehennom (34155) |
| 12 | `vlad` | in dungeon 6 | exact | destroyed Vlad the Impaler (44189) |
| 13 | `wizard_tower` | "Book of the Dead" in inventory | proxy | acquired the Book of the Dead (49072) |
| 14 | `invocation` | in dungeon 1, deeper than the level where "You feel a strange vibration" appeared | proxy | performed the invocation (49741) |
| 15 | `planes` | in dungeon 7 | exact | entered the Elemental Planes (53180) |
| 16 | `astral` | at (7, 1) | exact | entered the Astral Plane (53518) |
| 17 | `ascended` | the end reason says "ascended" | exact | ascended (53630) |

**Level numbers.** `blstats` gives the level number inside each dungeon (Sokoban 1 is
its top level, Astral is Planes level 1); in the Dungeons of Doom that equals the depth.
All rules above use this number.

**Mines' End.** The Mines have 8 or 9 levels (`(8, 2)` in `dungeon.def`, 8 + rn2(2)).
The bot's own check `(MINES, 9)` (TODO in `global_logic.py`) misses the 8-level Mines and
stays untouched here. Rung 6 counts on Mines level 9, or on Mines level 8 once the bot has
spent 1000 turns there without seeing a down staircase.

**Sokoban solved.** Rung 5 counts on Sokoban level 1 once a trap has been seen there and
none is left (at least 100 squares seen). Arriving with the holes out of sight does not
count.

The yardstick events differ from some rungs (they record killing Medusa or the luckstone,
we record arriving). That is good enough for a turn comparison; the table says which is which.

## Components

**`autoascend/ladder.py` (new, standard library only, so the bench can import it)**
- `RUNGS`: ordered tuple of `Rung(number, key, title, yardstick_event)`.
- `Facts`: a small dataclass of everything a rung needs on one step: turn, dungeon, level,
  oracle seen, Minetown seen, Sokoban solved, Medusa seen, water share, drawbridge
  seen, down stairs seen, inventory names, message. Built by the caller, so no glyph or
  agent code lives in this module.
- One detection function per rung, `(facts, memory) -> bool`; `memory` holds the few
  things that span steps (the current level and the turn the bot arrived there,
  the level of the vibrating square).
- `Ladder.observe(facts)`: records `{key: turn}` for each newly reached rung and skips
  rungs already recorded. `Ladder.finish(end_reason, turn)` adds `ascended`.
  `Ladder.highest()` returns the highest rung number (0 for none).

**`autoascend/global_logic.py`** builds `Facts` in `update()` (next to the Oracle and
Minetown checks, using `G` glyph sets and the parsed inventory) and calls
`self.ladder.observe(...)`. Building facts is guarded: an exception there is logged once
and the ladder stops updating, it never ends a game.

**`nethack_screensaver/game.py`**: `GameResult` gains `ladder: dict[str, int]` (rung key ->
first turn) and `rung: int`. Both go to the screensaver game log and the bench database
through the existing `asdict`. Nothing new on screen.

**`bench/metrics.py`**: `rung` (median of the highest rung) and `rung1` … `rung17`
("reached rung k+ (<title>)"), one line each, generated from `RUNGS`. Old games lack
`rung` and are skipped by the existing KeyError rule. `dlvl6` stays the default verdict;
switching the default is a later one-line change once baselines carry the ladder.

**`bench/report.py` and dashboard**: `summary()` gains `ladder`: per rung its rate, the
median turn our games reached it, and the yardstick median turn (from the reference
timelines, by `yardstick_event`). The dashboard page shows this as one table under the
existing results; `bench_results` returns it unchanged through MCP.

## Error handling

- Hallucination: the Oracle and Minetown facts already ignore it; water share, Medusa and
  drawbridge facts are also left false while hallucinating.
- A detection error must never crash or end a game (guard above). A crashed game still
  reports the rungs reached so far.

## Testing

- Unit tests per rung with hand-made `Facts` (including the Mines' End level 8 vs 9 cases and
  "already recorded rungs are not re-checked").
- `Ladder.finish` with ascension and non-ascension end reasons.
- Metrics: `rung` and `rungN` on dict games, old games skipped.
- Report: ladder rows from a few fake games and fake reference timelines.
- The existing real-game test checks that `GameResult.ladder` only holds known rung keys
  and that `rung` is the highest rung number among them (0 when empty).
- Whole suite before and after (`uv run pytest -q -m ""`).

## Validation

After merging, a 576-game baseline of the new `main` on the bench server. Plausibility
check against what we know: Mines reached in about two thirds of games, Sokoban rarely,
nothing above rung 7 except the odd deep dive. That run is the starting ladder for
sub-project 1 and is written into `autoascend/PORTING.md`.

## Not in this sub-project

Changing what any strategy does; fixing the bot's own Mines' End check; showing rungs on
the screensaver; making a rung metric the default verdict.
