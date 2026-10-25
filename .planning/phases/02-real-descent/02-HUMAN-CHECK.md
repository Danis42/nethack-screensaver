# Phase 2 fixes checked against NetHack knowledge (2026-10-25)

Sources: NetHack 3.6.6 source (`dat/mines.des`, `src/hack.c`, tag NetHack-3.6.6_Released) and the NetHack wiki
(Spotted jelly, Water nymph, Gnomish Mines, Trap). Human ttyrecs (NLD-NAO) not scanned yet: decoding needs an
idle bench (job 37 ran during this check).

| Fix | What the bot did | What the game / humans say | Verdict |
|---|---|---|---|
| exp 13 standoff | waits at distance 2 for a monster that never comes | jellies have speed 0 and never move; the wiki advises sneaking past sleeping nymphs, not waiting | supported |
| Mines searching (candidate) | searches dead ends on Mines filler levels for hidden passages | `minefill` is `INIT_MAP: mines`, a generated cave map with no secret doors; only Grotto Town (1 `S`) and the three Mines' End maps have secret doors | supported: search is wasted on fillers |
| exp 12 clear-way | crossed every known trap the same way | the wiki rates squeaky boards and rust traps harmless and magic traps deadly; trap doors and holes drop you a level, which helps a dive | half right: crossing should depend on the trap type |
| exp 12 peacefuls | waits beside a peaceful monster | 3.6.6 swaps places only with pets (`hack.c` `is_safepet`), so waiting or going around is the only option | supported |
| (none) digging | uses a pick-axe only on Sokoban boulders | humans dig down with a pick-axe when a level blocks them | missing tactic |

## Candidates from this check
1. No searching on Mines filler levels (keep it for Grotto Town and Mines' End). Source-backed.
2. Use trap doors and holes on purpose when the bot wants to go down (not in Sokoban, not when it needs the up
   stairs).
3. Dig down with a pick-axe when stuck on a level that allows digging (not Sokoban, and never inside a shop).
4. Never melee spotted or blue jellies (their passive damage hurts the attacker); walk past.

Still to do on an idle bench: count in NLD-NAO ttyrecs how often humans fall through trap doors on purpose, dig
down, and search in the Mines.
