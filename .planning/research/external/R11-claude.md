# R11 Valkyrie Quest (Claude, local 5.0.0 source: quest.c, quest.h, dat/Val-*.lua, dat/quest.lua)

## Summary
- Portal level: Dlvl 11-16 (quest branch = Oracle level + 6..7; Oracle Dlvl 5-9; dungeon.lua). Message on first
  arrival: "You receive a faint telepathic message from Norn: Your help is urgently needed at the Shrine of
  Destiny! Look for a ...ic transporter. You couldn't quite make out that last message." (quest.lua:184-187).
- Entry: XL >= 14 (quest.h:45), alignment record >= 20 = "pious" (quest.h:43), never converted (quest.c:171).
  Too low: "badlevel" text and sent back, no penalty, retry later. 5.0 never seals the portal for this
  (expulsion(FALSE) everywhere, quest.c:336-353); a converted hero is banished once.
- Home "the Shrine of Destiny" (ice, 13 random lava squares, 8 warriors, fire ants, fire traps), leader Norn;
  locate "the cave of Surtur" (17 fire ants, fire traps); 2 filler levels; goal: lava cave.
- Lord Surtur (monsters.h:3749): level 15, speed 12, AC 2, MR 50; two weapon hits 2d10 and a claw 2d6 that steals
  the Orb; resists fire and stoning; throws boulders; follows the hero (M2_STALK); carries the Bell of Opening
  (makemon.c:1379). No poison cloud on death (his death text has no "noxious").
- Goal level: 12 hostile fire giants (several in two columns at x 10 and 24), fire ants, fire traps; the Orb
  (blessed crystal ball +5) lies on Surtur's square (17,8). Most of the level is lava.
- Orb of Fate (artilist.h:297): carried = warning, half spell damage, half physical damage, luck; invoke = level
  teleport. NOT magic resistance.

## 5.0 changes vs 3.6
- Valkyries now START WITH A +1 SPEAR, not a long sword (u_init.c:161, fixes5-0-0.txt:971).
- Stealth now comes at XL 3, not XL 1 (attrib.c:82).
- Bad-alignment visits no longer use up tries and seal the quest; killing the leader opens the quest
  (fixes5-0-0.txt:551). Valkyrie/warrior guardians became lawful (fixes:555).
- On returning the Orb without the Bell, the leader says to go back for it (quest.c:267).

## Bot rules
1. Do not take the portal before XL 14 and fire resistance (the Norn: "you will need to be immune to fire").
   Fire resistance or levitation is required: the goal level is mostly lava.
2. Alignment record is not on screen: the bot must count it (kills of hostiles +, peaceful kills -) or #pray /
   enlightenment. Plan for a failed first chat; it costs nothing in 5.0.
3. Fight the fire giants one at a time; kill Surtur with cold (he does not resist it) and melee; pick up the
   Bell from his drop, then the Orb.

## Open questions
- The bot's weapon: does it still use the starting spear, or wield a long sword when found? (bench data)
- Exact goal-level map and where the up stairs is relative to the lava (Val-goal.lua map not read in full).

## Compared with ChatGPT R11 (2026-11-08)
- Agrees: portal Dlvl 11-16, XL 14 / alignment 20 / no conversion, Surtur stats, Orb powers, Bell from the
  nemesis, 5.0 non-sealing, spear start, lawful guardians.
- WRONG in ChatGPT: home is "the Shrine of Destiny", not "Temple of Light"; it called the portal message
  unverified (it is in quest.lua:184).
- Missed by ChatGPT: stealth moved to XL 3; 12 fire giants on the goal level; Surtur follows across levels.
