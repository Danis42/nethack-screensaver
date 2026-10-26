# 02 Knowledge sweep: NetHack 3.6.6 source + wiki against the bot

Date: 2026-10-26. Sources: `reference/nethack-3.6.6/src` (file:line given), `reference/nethackwiki/text/pages`,
current baseline games (`99b0a2b` = exp/standoff, 2304 seeded games; main `c429830` is its merge).
Purpose (owner request): list what the game's own rules say the bot gets wrong or leaves unused, ranked by
expected gain per bench hour. Each candidate is one experiment under 02-EXPERIMENT-PROTOCOL.

## Where the games end (baseline 99b0a2b, 2304 games)

- starved (or killed while fainted): 24.4%; died: 95.3%; crashed: 2.6%
- rung7 (Dlvl 15+) 9.9%, rung8 (Quest) 2.0%, rung9 (Medusa) 1.0%, nothing beyond
- top killers: soldier ant 97, killer bee 63, wand 48, gray unicorn 41, mumak 41, rothe 41, Woodland-elf 37,
  hill orc 35, leocrotta 34, giant ant 33, fire ant 32, giant bat 30, bolt of lightning 28, spotted jelly 25

## Facts from the source that matter

### Prayer cannot be the food supply (pray.c, rnd.c, allmain.c)
- The timeout falls by 1 per turn (`allmain.c:184`). A successful prayer sets it to `rnz(350)` (`pray.c:1220`).
  Weak hunger is major trouble, so praying is safe while the timeout is at most 200 (`pray.c:1819`).
- Simulated `rnz(350)` (200k draws, rne capped at 5 below XL 15): median 348, p90 884, p99 1900.
  Chance that a prayer made N turns after the previous one comes "too soon":
  300: 34%, 500: 12%, 700: 10%, **870 (the bot's median gap): 7.4%**, 1000: 5.4%, 1200: 2.3%, 1500: 1.5%.
  This matches the bench's measured 8.9% failure rate.
- A too-soon prayer sets god anger +1, Luck -3, timeout + rnz(250), and smites the hero (`pray.c:1914`,
  `gods_upset` `pray.c:1287`). **While the god is angry, every later prayer fails** ("too naughty",
  `pray.c:1823`). Only a sacrifice lowers anger ("<god> seems slightly mollified", `pray.c:1688`). Luck
  drifts back by 1 every 300 turns while the god is angry.
  So after the first failure, prayer never works again unless the bot sacrifices. 59% of failed-prayer
  starvers had 2+ failures. That fits, and so do some of the 28 "bolt of lightning" deaths.
- Over 10 hunger prayers (about 9000 turns at the bot's pace) the chance of no failure is 0.926^10 = 46%.
  A hero who lives on prayer for food fails at it in a long game. The fix has to be a food supply, and the
  starvers lack one because they are stuck (PORTING experiment 2: 5.3 kills per 1000 turns vs 14 in survivors).

### Where hidden ways on come from (mklev.c, sp_lev.c)
- Room doors are secret (SDOOR) 1 time in 8 (`mklev.c:1256`). Niches use them more often (`mklev.c:522-526`).
- Corridor squares are secret (SCORR) 1 time in 100 (`sp_lev.c:2259-2264`).
- The extra random corridors (`nxcor`) stop at random, 1 step in 35 (`sp_lev.c:2248`). **Those are real dead
  ends with nothing behind them.** A corridor dead end is therefore often not a hidden passage. The way on
  usually sits in a room wall (secret door) on the side toward unseen map.
- Mines filler levels have no secret doors (02-HUMAN-CHECK: `minefill`, `mkmap.c`).

### Trap doors and holes (trap.c)
- They fall at least 1 level, plus 1 more level with chance 1/4 each time, down to the dungeon's bottom
  (`trap.c:471-474`). In the Quest they stop at the locate level.
- They are never generated on levels with undiggable floors (wiki "Trap door"). Messages: "A trap door opens
  up under you!", "There's a gaping hole under you!", and "You fall down a (deep|very deep) shaft!" for 2-4+
  levels.

### Elbereth in 3.6.6 (monmove.c:135-180)
- Elbereth only works while the hero stands on the square. It is ignored by: humans and elves (every `@`,
  `S_HUMAN`), minotaurs, shopkeepers, guards, priests in their temple, peaceful monsters, and blinded
  monsters. It does nothing in Gehennom.
- Attacking from the square erases it, and the hero loses 5 alignment (wiki "Elbereth").
- Bot: `fight_heur.elbereth_action` counts every adjacent monster, so it can spend a turn engraving while an
  elf or soldier keeps hitting. Woodland-elf (37), Green-elf, Grey-elf, sergeant and soldier deaths are all
  `@`.

### Passive monsters (monst.c)
- Passive damage written "0dN" is (monster level + 1)dN (`uhitm.c:2755-2758`). Acid splashes on half of
  the hits that land, even on the killing blow (`uhitm.c:2776`).
- Spotted jelly: speed 0, passive acid (level 5 + 1)d6 = 6d6, about 21 per splash. It never attacks or moves
  (`monst.c:515`). Ochre jelly: speed 3, engulf 3d6 plus passive 3d6 (`monst.c:522`). Green mold (acid 2d4),
  yellow mold (stun) and red mold (fire): speed 0, passive damage only (`monst.c:1311-1327`).
- Bot: `ONLY_RANGED_SLOW_MONSTERS` = floating eye, blue jelly, brown mold, gas spore, acid blob. **No spotted
  jelly, ochre jelly, green, yellow or red mold.** The baseline has 32 jelly deaths. Example: seed 170, Dlvl
  15, XL 9, "You hit the spotted jelly! ... You are splashed by the spotted jelly's acid!" until death.
- Blue jelly and brown mold do cold damage, and Valkyries resist cold, so they are harmless to her (safe
  experience points). Low priority.

### Slow heavy hitters (monst.c)
- mumak: speed 9, butt 4d12 + bite 2d6 (`monst.c:695`). rothe: speed 9, three attacks (`monst.c:689`). The
  hero walks at 12 (Valkyries are intrinsically fast from XL 7), so both can always be outrun.
  Leocrotta (speed 18) and gray unicorn (speed 24) cannot.
- Bot: `is_dangerous_monster` has mumak/rothe/unicorn/leocrotta commented out; only pets and insects count.

### Digging tools (makemon.c:367-386, mon.c:2462-2512)
- A dwarf carries a mattock 1 time in 8 and a pick-axe 1 time in 4 (37.5% together). For a dwarvish hero
  every dwarf and gnome is peaceful by race (`peace_minded`, `makemon.c:2015`).
- Killing a peaceful dwarf is not "murder" (that applies to humans only). It costs 5 alignment and a 1/2
  chance of 1 Luck. Negative Luck makes prayers fail until it recovers (600 turns per point).
- Bot: uses a pick-axe only to break boulders (`global_logic.py:440`). An earlier "dig down" try (2026-10-20,
  unforced games) used a known wand of digging only. Nobody has measured how often the bot carries a pick-axe.

### Excalibur (wiki "Excalibur", fountain.c)
- A lawful hero at XL 5+ who dips a long sword into a fountain gets Excalibur 1 time in 6: +1d5 to-hit and
  +1d10 damage against everything.
- Bot: dips only from XL 7 (`global_logic.py:842,856`; the wiki advises waiting for intrinsic speed against
  water demons) and never in the Mines before Minetown is known. When the bot gets Excalibur is not recorded.
  Deaths cluster at Dlvl 5-8, around XL 5-7.

### Quest portal (dungeon.def, quest.txt)
- In progress: exp/quest-portal is job 38. Smoke on 22 deep seeds: message seen in 20, Quest entered in 10,
  hunt given up in 8.

## Ranked candidates

| # | Candidate | Evidence | Games touched | Cost | Primary metric |
|---|---|---|---|---|---|
| 1 | Never melee passive-only monsters: add spotted jelly, ochre jelly, green/yellow/red mold to `ONLY_RANGED_SLOW_MONSTERS`, and let the path go around them | monst.c:515; 32 jelly deaths, deep (rung7 games) | 1.4% die | tiny | `died` (mechanism `rung7`) |
| 2 | Elbereth only against monsters that respect it: leave out `@`, minotaurs, peaceful and blind monsters from `elbereth_action`'s count | monmove.c:163-180 | `@` deaths about 3% | small | `free5` |
| 3 | Never pray while the god is angry: after a too-soon prayer, mark anger; pray again only after a sacrifice message ("mollified"/"reconciliation"); go to a known coaligned altar to sacrifice | pray.c:1287,1688,1823 | failed-prayer starvers (most starvers) | small-medium | `starved` |
| 4 | Outwalk slow heavy hitters: mumak and rothe (speed 9) count as dangerous; retreat instead of melee when HP < 50% | monst.c:689,695; 82 deaths | 3.6% | medium (combat) | `died` |
| 5 | Trap doors and holes on purpose while diving (not Sokoban, not on the Quest portal level before entry) | trap.c:471 | rung7 needs speed; count first | medium | `rung7` |
| 6 | Dig down with a carried pick-axe/mattock when the stuck watch fires; first measure how often one is carried (counter) | makemon.c:385; earlier wand-only try | stuck starvers | medium | `starved` / `free5` |
| 7 | Excalibur from XL 5 (Oracle fountains first); first record the turn of Excalibur | wiki Excalibur | most games past Dlvl 5 | tiny | `rung2` |
| 8 | Search room walls toward unseen map instead of corridor dead ends when stuck (dead ends from extra corridors hide nothing) | sp_lev.c:2248 | stuck games | medium | `free5` |
| 9 | Gold, then food from shops and protection from the Minetown priest (400 x XL gold per AC point) | wiki Priest/Shop | everyone | large (shopping is not built) | `starved` |

Parked from earlier checks: no searching on Mines fillers (02-HUMAN-CHECK 1), food stock (owner idea). Both
feed into #6/#8 and #9.

## Order for the next experiments

1. #1 passive monsters: cheap, source-certain, and its deaths are deep ones.
2. #2 Elbereth filter.
3. #3 angry god.
4. Counters for #5-#7 (trap doors seen, digging tool carried, Excalibur turn) in one instrumentation commit;
   pick among #5-#7 from the numbers.

## Full wiki pass (local model, 2026-10-26)
- qwen2.5:14b (Ollama, local GPU) summarised all 2058 pages kept by the ledger into `sweep/wiki-facts.jsonl`:
  8095 facts, danger 5: 530, of which 332 come from pages the bot code never names. Read inline.
- Quality: much of it is noise (variant monsters such as tannin/ancients, Astral/Gehennom bosses, some invented
  key commands). Nothing new for the current bottleneck except prayer: a prayer also fails with Luck < 0 or a
  negative alignment record (pray.c can_pray p_type 1), e.g. after killing peacefuls.
- Checked on the 6a840f2 bench games: the gap before each game's first failed prayer is 500-999 turns in 388
  of 564 games, under 500 in 44, 1000+ in 101, first prayer ever in 31. So timing (rnz(350) timeout) explains
  most first failures; Luck/alignment at most ~1 in 4. Games where the bot attacked everything in reach
  (`allow_attack_all`, 370) fail a prayer slightly more often (26.2% vs 24.1%): not a lever.
- Consequence: exp/prayer-timing (job 42) targets the main cause. Later, cheap follow-ups: Minetown watch
  (attacking peacefuls in sight angers them), pyrolisk eggs / wererat corpses in the food filter (verify).
