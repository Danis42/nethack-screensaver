# Hand game: Sokoban top level (plan 01-06)

- Seed 7 (tool block), stage `soko-top` (wizard ^V to `soko1`, XL 8, no weapon), started 2026-11-12.
- Server: `.venv/bin/python scripts/handplay.py serve --seed 7 --stage soko-top --dir .planning/hand-games/soko-top`
  (keep it running: a restarted server starts the game fresh).
- Variant: soko1-1 (holes on the bottom row, x 28-45 on screen; rolling boulder trap at screen (46,19)).
- Start (T1): hero (47,16), 19 boulders, 18 holes + 1 rolling boulder trap.

## Ladder at start (T1)

    ladder: facts dungeon=4 level=1 turn=1 sokoban_seen=338 sokoban_traps=True; reached {'sokoban': 1}; log ['T1 reached sokoban']

## Finding before any push: rolling boulder traps (new in NetHack 5.0)

Every 5.0 Sokoban level places at least one rolling boulder trap among its holes or pits
(dat/soko1-1.lua:66 `des.trap("rolling boulder", 08, 01)`, also soko1-2, soko2-1/2, soko3-1/2, soko4-1/2);
NetHack 3.6.6 dat/sokoban.des has none. The bot counts every trap glyph (G.TRAPS, which includes the
rolling boulder trap) as "a trap left":

- ladder `sokoban_solved` needs `not f.sokoban_traps` (no trap glyph on the level): it cannot fire on a
  solved 5.0 level while the rolling boulder trap is on the map;
- `global_logic.sokoban_board` hands every trap glyph to the live solver as a hole to fill.

Owner decision 2026-11-12: fix the detector (holes and pits only), then play. Detector fix committed as a0a9799 (play unchanged on seeds 1000-1019). Next: play the level with handplay, record start/solved fixtures, write tests/test_sokoban_detector.py and 01-SOKOBAN-DETECTOR.md.

## Attempt 1 (seed 7): the stored 3.6 solution does not fit the 5.0 level

- The ^V arrival put the hero at screen (47,16), boxed in; wizard ^T moved the hero to the down stairs (45,5)
  at T3 (the natural arrival square, where the stored solution starts).
- The bot's stored map matches the 5.0 walls (orientation 31 of 32, offset (3, 26)), so map matching is fine.
- Pushes 0-24 of the stored solution (618 pushes) went as planned (a rust monster and a dwarf were fought off).
  Push 23 moved the boulder from (46,19), the 5.0 rolling boulder trap square, into the hole at (45,19), one
  push earlier than the 3.6 solution expects: in 3.6 every square of that row was a hole. Push 24 found no
  boulder to push, and push 25 walked the hero into the open hole at (44,19): the hero fell to Sokoban level 3
  at T52 (ladder: dungeon=4 level=3). The 3.6 stored solutions are therefore off wherever 5.0 swapped a hole
  for a rolling boulder trap.
- Log: pushes.log. Next: restart the game and plan with the live solver on the real 5.0 board (holes only).

## Attempt 2 (seed 7): live-solver plan, lost at push 190

- Live solver on the 5.0 board (18 holes, the rolling boulder trap left out, floor from the matched stored map):
  419 pushes, found in 1.2 s. The live solver's earlier failure was only the floor: squares under the kitten
  and under items are not seen bare, so `board_from_observation` left them out.
- The hero gets boxed in at (45,19) behind the rolling boulder trap at (46,19); travel never routes over a known
  trap, so wizard ^T was used to leave that corner (the bot would be stuck there the same way).
- Three Uruk-hai brought the hero to HP 0 at T71 (wizard "Die?" answered n); a wished blessed scroll of genocide
  removed orcs (class o) at T72. No boulder or trap was touched by either intervention.
- Push 190: a wizard ^T with relative cursor keys landed on a hole (the getpos cursor does not start on the hero)
  and the hero fell to level 2 at T308. Log: pushes-attempt2.log.
- Next: attempt 3 re-plans from the live board before every push and puts the cursor on the hero ('@') first.

## Attempt 3 (seed 7): running, paused at T42 (blocking checkpoint)

- T2: wizard ^T to the down stairs (45,5); wished and read a blessed scroll of genocide, class o, before any push.
- **The start board has 20 boulders, not 19:** the ^V arrival square (47,16) holds a boulder, hidden under the
  hero at T1. Attempt 2's live plan missed it, which is why that plan drifted.
- The live solver finds no plan for the true 20-boulder, 18-hole board (3,000,000 states, 484 s).
- Followed the stored 3.6 solution instead, ending each row-19 run when the boulder drops: steps 0-63 played,
  holes (44,19) and (45,19) filled. At step 64 the stored solution expects a boulder at (49,14) that is not there
  (the board has drifted from the 3.6 solution). The live solver finds no plan from T42 either (1,500,000 states).
- Board-reading gap: the hole at (34,19) lies under an item and does not show as a trap glyph (15 of 16 open holes
  visible).
- Position at the pause (T42): hero (47,19); open holes 28-43 on row 19; ladder: sokoban reached, sokoban_solved not.
  The handplay server keeps this game while it runs; a restarted server starts fresh.

## What the attempts show (for the 0/2304 cause, plan 01-16)

1. 5.0 adds a rolling boulder trap to every Sokoban level: the detector could never fire (fixed in a0a9799),
   and the bot's stored 3.6 solutions miscount where boulders drop on the hole row.
2. Travel will not cross the rolling boulder trap, so the hero can be boxed in behind it.
3. Board reading misses squares under monsters and items (a boulder under the arrival square, a hole under an
   item), so the live solver works on a wrong board.
