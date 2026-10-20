# Where we are (2026-10-20, end of day)

Version 0.2.0 is released; everything below is on local `main` after it (not yet released).
Benchmark numbers and every experiment: `autoascend/PORTING.md`.

## New main objective: a bot that really wins NetHack

Decided 2026-10-20. Pilgrim (ascension) and daredevil (ascension in disgrace) should
really pursue their goals instead of stand-ins; the project's main objective becomes a
real ascension. Sightseer and treasure keep their reachable escape goals. Workflow stays
superpowers (brainstorm, spec, plan, inline execution) plus a `docs/ROADMAP.md` (not
written yet), not GSD.

Proposed ladder of sub-projects (each gets its own spec, plan and build):

0. Ascension ladder: make it the real goal and measure which stage each game reaches
1. Midgame survival, Dlvl 4-12 (most games die on Dlvl 4-8)
2. Real descent past Mines' End and the Big Room; reliably finding downstairs
3. Gearing up: wands, rings, armour, protection, reflection, magic resistance
4. Medusa's level   5. Castle and wishes   6. Quest (XL 14, Bell)
7. Gehennom: Vlad's, Wizard's Tower, invocation   8. Elemental and Astral Planes

**Start tomorrow here:** resume the brainstorm. Open question: what counts as success —
climbing the ladder (recommended: each rung is progress, a real ascension is the last
rung) or only real ascensions. Then write `docs/ROADMAP.md` and the spec for
sub-project 0.

## Yardstick: 687 real ascensions (hardfought.org, in the bench database)

Median turn of each step (131 NetHack 5.0 timelines): Mines 1173, Minetown 3538,
Sokoban 9022 (solved 12412), Mines' End luckstone 10853, Quest 22426, Medusa 29317,
Bell 30475, Gehennom 34155, Vlad 44189, invocation 49741, Astral 53518, ascended 53630.
At the end: magic resistance 100%, bag of holding 99%, reflection 83%, median XL 23,
AC -38; wands of teleportation 89%, death 83%, digging 64%.
Our bot: median game about 4900 turns, ends on Dlvl 5; best games Dlvl 10-22.

## Bench server (new, use it for every measurement)

- `uv run screens-bench serve` -> http://localhost:8765 (job, experiment verdict,
  dashboard, history, ascenders). Plays only while a job runs; 11 workers with `nice`.
- Claude: MCP tools from `.mcp.json` (reconnect MCP once: `/mcp`), or the JSON API.
  Start an experiment, then run `uv run screens-bench wait <job>` in the background.
- Experiments judge one metric (default "reached Dlvl 6+") at 192/384/576/1152 games per
  side (99% early, 95% at the end); stored games of a commit are reused. Commit first:
  only committed code can be measured.
- Database `~/.local/share/screens-bench/results.db` holds 576 games of `aa4b1cf`
  (current bot code), 1152 of `choke-points`, and the 687 reference ascensions.
- `scripts/benchmark.py` still works as a fallback.

## Done today (kept)

- Crashes 9 -> 2 per 576 games: drop spare items when Overtaxed, stop refused armour,
  parse 80-character inventory lines and worn rings, empty containers, pit-edge items,
  no kicking with wounded legs, plus a safety net (after 100 steps without game time,
  search once; `unsticks` in results). Crash reports show the bot's call chain.
- Bench server with status page, MCP tools and the ascension import.

## Tried and dropped

Earlier: resting on Elbereth, waiting for peaceful monsters, smarter hidden-passage
search, digging down, pushing boulders (git stashes / reverts). Today: fighting packs of
fast monsters (soldier ants, killer bees) from doorways and corridors — no measurable
difference (branch `choke-points`). Ants + killer bees still kill about 8% of games.

## Notes

- One change per measurement; single 576-game runs mislead (286 vs 262 was noise).
- Killers to look at: wand/ray users (~8%), ants (~8%), starvation (~13%).
- Your preference: an exciting deep run that dies beats a boring escape.
- Never push; merge finished, tested branches to `main` locally.
