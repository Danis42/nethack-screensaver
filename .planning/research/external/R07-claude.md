# R07 Read-testing scrolls and every scroll prompt (Claude, from local 5.0.0 source + NLD data)

Sources: reference/nethack-5.0.0 (tag NetHack-5.0.0_Released), file:line below; human data = 72 NLD-NAO 3.6
ascensions (scratch scroll_reads.py); bot data = bench e1d8086 (1152 games).

## Summary
- Humans read about 29 scrolls before Medusa but almost never a harmful one (destroy armour 3 of 2512 reads,
  amnesia 6, punishment 1): they identify first (price, identify scrolls), then read freely. Blind reading would
  hit destroy armour ~4.5%, amnesia ~3.5%, punishment ~1.5% of reads.
- 5.0 amnesia is mild: it no longer forgets the map or object identities; it forgets spells (not if blessed),
  drains 1-5 weapon-skill advances (blessed: 1-3 and spells kept) and forgets seen monsters (read.c:1020-1040).
- Three scrolls ask for a map position: blessed fire, stinking cloud, and (with teleport control) teleport.
  A cancelled or invalid answer to blessed fire centres a 5x explosion ON THE HERO (read.c:1893-1905).
- Genocide asks by class when blessed, by species otherwise; a cursed one CREATES the named monster.
- Blessed destroy armour asks which worn piece to destroy (5.0, read.c:1366-1380).
- Cursed or confused teleportation level-teleports (read.c:2021); uncursed teleports within the level.

## Facts (all 5.0.0 source unless noted)
| claim | source | confidence |
|---|---|---|
| Scroll table: identify 180/1000 at 20 zm; enchant armour 63 + remove curse 65 at 80; enchant weapon 80 + blank 28 at 60; light 90 at 50; 100 zm: destroy armour 45, confuse 53, scare 35, teleport 55, gold det 33, food det 25, magic mapping 45, fire 30; 200: create monster 45, taming 15, amnesia 35, earth 18; 300: genocide 15, punishment 15, charging 15, stinking cloud 15 | include/objects.h:1187-1265 | high |
| Enchant armour target: cloak, else body armour, else shirt; helm, gloves, boots, shield each take over with 1/4 | do_wear.c:2630 some_armor | high |
| Enchant armour amount: s=(4-spe)/2, +1 elven/cornuthaum, +1 non-magical armour, +1 blessed; s<=0 -> 0 (1 with chance 1/spe); else rnd(s). Uncursed on +0 plain armour: +1..+3 | read.c:1178-1220 | high |
| Enchant armour evaporates when spe > 3 (> 5 elven) and rn2(spe) | read.c:1179-1186 | high |
| Destroy armour: uncursed destroys some_armor(); blessed with 2+ worn pieces asks "destroy" (getobj); cursed disintegrates, or -1 and stun if that piece is cursed; confused only changes erodeproofing | read.c:1324-1398 | high |
| Fire: uncursed/cursed explode on the hero (damage (2*(rn1(3,3)+2*bcsign)+1)/3); blessed x5 and asks "Where do you want to center the explosion?"; invalid/cancel -> on the hero; confused: 1 HP burn only | read.c:1850-1917 | high |
| Stinking cloud: "Where do you want to center the cloud?"; cancel -> "Never mind"; invalid square -> "Ugh... someone cut the cheese." (wasted) | read.c:3086-3100 | high |
| Genocide prompts: blessed "What class of monsters do you want to genocide?", else "What type of monster do you want to genocide?"; 'none' allowed; after 5 bad tries "That's enough tries!"; cursed (reverse) creates the named monster | read.c:2640-2870 | high |
| Identify: confused or cursed-unknown just identifies itself; uncursed identifies 1 item, 1/5 chance rn2(5) items (0 = all); blessed always rn2(5) (+1 if 1 and Luck>0) | read.c:2055-2101 | high |
| Teleportation: confused or cursed -> level_tele(); else scrolltele() on the level | read.c:2015-2034 | high |
| Amnesia: unblessed forget(ALL_SPELLS): all spells + rnd(5) weapon-skill advances; blessed forget(0): rnd(3) advances, spells kept; forgets seen monsters; no map/object forgetting | read.c:1020-1040, 1836 | high |
| Create monster: 1 monster, 13 if cursed or confused | read.c:1608 | high |
| Charging: getobj "charge"; confused restores energy ("You feel charged up!") | read.c:1788-1829 | high |
| Punishment: "You are being punished for your misbehavior!" ball and chain; blessed/confused: "You feel guilty." only | read.c:1976, 3030 | high |

## Bot rules
1. Never read an unknown scroll whose identity set contains a harmful scroll (have it: scrolls.py SAFE_UNKNOWN).
   Feed the identity set from prices: 5.0 option price_quotes + sell offers (SCROLL-ID-NH5.md).
2. Prompt answers when a scroll asks (Trigger = the top-line prompt text):
   - "What would you like to identify first?" -> scrolls.identify_choice (have it).
   - "Where do you want to center the explosion?" -> a visible square 2+ away inside the highlighted range,
     preferably on a hostile; NEVER escape (explodes on the hero x5).
   - "Where do you want to center the cloud?" -> a visible square with a hostile, 2+ away; escape is safe
     ("Never mind", scroll used).
   - "What type of monster do you want to genocide?" -> known uncursed: "soldier ant" early (31 of 1152 bot
     deaths), later "master mind flayer"; BUC unknown: do not read genocide (cursed creates the named monster).
   - "What class of monsters do you want to genocide?" (blessed) -> ";" (sea monsters: eel drowning) or "L" late.
   - "What do you want to destroy?" (blessed destroy armour) -> the cheapest worn piece (never body armour).
   - "What do you want to charge?" -> a wand with few charges, else escape.
3. Never read while confused, stunned, hallucinating or blind (have it).
4. Prefer reading scrolls in a quiet room: fire, create monster and stinking cloud need space.

## Risks and exceptions
- Blessed destroy armour's prompt and the blessed fire position prompt are new handlers the bot does not have.
- The scroll of amnesia's skill drain hurts a Valkyrie's long sword skill; still much milder than 3.6.
- Punishment: the bot has a known crash with the heavy iron ball prompt (bench crashes).

## Open questions
- none open from the source side; NLE prompt rendering to confirm in a staged game.
