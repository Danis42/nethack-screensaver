# The sokoban_solved detector against a played hand game (MEAS-03, first half)

## The game

- Seed 7 (tool block), stage `soko-top` (wizard ^V to Sokoban's top level, XL 8), handplay server
  `scripts/handplay.py serve --seed 7 --stage soko-top --dir .planning/hand-games/soko-top`.
- Level: NetHack 5.0 `soko1-2`, flipped in both axes. It has 20 boulders and 18 holes, plus the rolling boulder trap
  5.0 adds (3.6 had a hole there). Attempt 1 called it soko1-1; placing `dat/soko1-2.lua` onto the T1 observation
  matched all 19 traps and 19 visible boulders, and the 20th sat under the hero.
- Solved in attempt 4 (2026-11-13). The plan was the stored 3.6 solution (`autoascend/soko_solver/maps.py`) placed on
  the true 5.0 board and simulated push by push. It was played by hand in the running game, push by push, with the
  live board checked after each push. Records: `.planning/hand-games/soko-top/NOTES.md`, `pushes-attempt4.log`,
  `meta.json`, and the planning tools in `tools/`.
- Wizard-mode help, none touching a boulder or a trap: ^T to the stairs at T2, genocide of orcs, a healing potion, a
  long sword, a unicorn horn, and a prayer with "force pleased". Every one is logged with its turn.
- The last hole was filled at T882. A boulder pushed onto the rolling boulder trap was launched ("The boulder
  suddenly rolls away from you! You hear a boulder fall.") and rolled into the last open hole.

## Ladder transcript (the real Ladder observed every command's last observation)

    T1 reached sokoban
    T882 reached sokoban_solved

`sokoban_solved` fired exactly once, on the turn the last hole was filled. It was absent before.
`ladder` at T897: `facts dungeon=4 level=1 turn=897 sokoban_seen=338 sokoban_traps=False; reached {'sokoban': 1,
'sokoban_solved': 882}`.

## Builder agreement

For both fixtures (start T1, solved T897), the bot's own Facts builder (`GlobalLogic.ladder_facts` over a fake
level built from the recorded glyphs) and `staging.observation_facts` agree on dungeon, level, turn,
`sokoban_seen` and `sokoban_traps`: traps True at the start, False when solved. Fed start then solved into a
`Ladder`, the bot-path Facts fire `sokoban_solved` once at T897. Fed the solved board alone (holes never seen),
it does not fire.

## Stored-map match

The bot's stored map for this level matches the 5.0 walls. Attempt 1 found orientation 31 of 32 with offset (3, 26);
attempt 4's placement found the same map, flipped in both axes, with 181 matching boulder and floor squares. Map
matching is therefore not why the bot never solves Sokoban. The stored solution, on the other hand, assumes 3.6 hole
positions (its row runs end one square early on 5.0), and the bot's board reading takes giant mimics for boulders.
Both go to plan 01-16's written cause.

## Fixture note

`tests/data/soko_top_hand_solved.json` keeps one trap in its `traps` key: the rolling boulder trap at (18,46).
`board_from_observation` mirrors the live solver's board reader, which still counts every trap glyph (left for
Phase 2 in commit a0a97990e9a1a6902a6150923324ca455c172800). The detector counts holes and pits only. The
plan's check `not traps` was written before the rolling boulder trap was known; the test asserts
`traps == [[18, 46]]` instead.

## Test

    uv run python -m pytest -q tests/test_sokoban_detector.py tests/test_ladder.py
