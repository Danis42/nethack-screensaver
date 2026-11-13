# Why the bot never solves Sokoban (MEAS-03, cause half)

All numbers below come from baseline job 7: commit e5b5a7f525bc51b8008f665173600aba80de466d, dev seeds 1,000-10,999, lgen off, replicate 0 (10,000 games). Each number carries the read-only query that produced it. Dungeon 4 is Sokoban; its entry level is dunlev 4, the bottom, and dunlev 1 is the top (fact `sokoban-entry-is-bottom-level`, 5.0 source).

## Numbers from the fresh baseline (job 7)

- Games that reached Sokoban: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.ladder.sokoban') IS NOT NULL => 2544]
- Games where `sokoban_solved` fired: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.ladder.sokoban_solved') IS NOT NULL => 0]
- Games that dropped Sokoban: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.events.sokoban_dropped') IS NOT NULL => 2256]
- Of those, through the "unsolvable" branch (stored solution and live solver both failed): [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.events.sokoban_unsolvable') IS NOT NULL => 2256]
- Drops because no stored map matched: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.events.sokoban_map_not_found') IS NOT NULL => 0]
- Games where the live solver succeeded: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.events.sokoban_live_solved') IS NOT NULL => 0]
- Drops on dunlev 4, the entry level: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.events.sokoban_drop_level_4') IS NOT NULL => 2256]
- Drops on dunlev 1, 2 or 3: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND (json_extract(json, '$.events.sokoban_drop_level_1') IS NOT NULL OR json_extract(json, '$.events.sokoban_drop_level_2') IS NOT NULL OR json_extract(json, '$.events.sokoban_drop_level_3') IS NOT NULL) => 0]
- Games that ended inside Sokoban: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.dungeon_at_end') = 4 => 262], all of them on dunlev 4: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.dungeon_at_end') = 4 AND json_extract(json, '$.level_at_end') = 4 => 262]
- Games that reached Sokoban without dropping it: [query: SELECT COUNT(*) FROM games WHERE sha = 'e5b5a7f525bc51b8008f665173600aba80de466d' AND rep = 0 AND seed BETWEEN 1000 AND 10999 AND lgen IS NULL AND json_extract(json, '$.ladder.sokoban') IS NOT NULL AND json_extract(json, '$.events.sokoban_dropped') IS NULL => 288]. These games ended some other way before the solver gave up. The stored fields cannot show whether any of them climbed above dunlev 4 and later left Sokoban; they do show that no game ended above dunlev 4 and no drop happened above it.

## Detector check (plan 01-06)

`sokoban_solved` fired exactly once, on the turn the last hole was filled, in a hand-played top-level game (seed 7, `soko-top` stage) and in the bot-path Facts replay of its observations. Test: `uv run python -m pytest -q tests/test_sokoban_detector.py tests/test_ladder.py`. Details in 01-SOKOBAN-DETECTOR.md.

## Cause

The zero is a bot failure, not a detector failure. Every drop goes through one code path (`autoascend/global_logic.py`, the `sokoban_unsolvable` branch before `drop_sokoban()`) on the entry level. The stored map is always found, since no drop has `sokoban_map_not_found`. But the stored moves stop fitting the board, the mimic search and the last-resort push do not recover, and the live solver never succeeds. The bot then drops Sokoban and never climbs to dunlev 1, where the detector sits.

## Open question for Phase 2

The numbers say where the bot gives up, not which push first fails on the entry level. The plan 01-06 hand game showed two 3.6/5.0 differences on the top level: the stored solution assumes 3.6 hole positions, and the board reader takes giant mimics for boulders. Whether the same differences break the entry levels (5.0 `soko4-*`) is not measured. A staged entry-level run that logs the first push where the board and the stored solution disagree would answer it.

## Archive history (commit 72ca0b63de44c38af34650ab6c7141b44f868425, not current results)

In the archive bench of 2,304 seeded games (archive/screens-v0-final.tar.gz, read-only, 01-RESEARCH.md Pattern 14), the archive showed the same picture: the `sokoban` key in 570 archive games, `sokoban_dropped` in 515 archive games, `sokoban_solved` in 0, and the 52 archive games that ended inside Sokoban all ended on dunlev 4. These archive numbers are history only; the fresh numbers above replace them.
