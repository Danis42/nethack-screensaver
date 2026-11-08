# R10 The Castle (Claude, local 5.0.0 dat/castle.lua, src/music.c, src/pray.c)

## Summary
- No-teleport, all walls undiggable, floor cannot be dug (bottom level of the Dungeons). There are NO down
  stairs: the way on is one of 5 trap doors in the east corridor (40,8) (44,8) (48,8) (52,8) (55,8) to the Valley.
- "noflipy" only: the level can still be mirrored left-right, so the drawbridge can be on the east side.
- Arrival from above: west strip x 1-10 (teleport_region down). Drawbridge (5,8), facing east; the hero plays
  from (4,8) next to it. Giant eels sit at (5,7) and (5,9): right beside that square.
- Wand chest: one of 4 corner towers (4,2) (58,2) (4,14) (58,14); 5.0: chest is LOCKED and holds wand of wishing
  + potion of gain level (3.6: unlocked, wand only). The square also has a burned Elbereth and a CURSED scroll
  of scare monster (picking it up turns it to dust: leave it).
- Towers are reached only from the long halls (rows 3 and 13), and those only through the throne room doors
  (32,4) / (32,12) (locked). So the wand means passing the throne room (27 court monsters, random classes
  L N E H M O R T X Z; no arch-lich in 5.0).

## Facts
| claim | source |
|---|---|
| 16 soldiers + 1 lieutenant placed (8 + lt. in the entry hall, 8 in towers) plus 2 filled barracks | castle.lua:132-148, 204-205 |
| 4 random dragons in storeroom alcoves (47,5) (47,6) (47,10) (47,11) | castle.lua |
| moat: 4 giant eels, 4 sharks | castle.lua:153-160 |
| storerooms: armour, weapons, gems, food (shuffled) | castle.lua:17, 79-125 |
| passtune: 5 notes A-G; "N gears turn" = right note right place; "N tumblers click" = right note wrong place; only within 1 square of the drawbridge or its wall; not when deaf | music.c:844-880 |
| correct tune next to the bridge opens it (or closes it if open) | music.c:813-830 |
| prayer boon "Hark, mortal! To enter the castle, thou must play the right tune!", then a second boon gives the tune itself | pray.c:1218-1240 |
| eels drown a levitating hero too (only Swimming / Amphibious / Breathless protect) | uhitm.c:3389 |
| soldiers are @ (human): Elbereth does not scare them | monmove.c onscary |
| door states: (56,8) east door locked; (38,8) corridor-to-throne locked; tower doors (7,3) (55,3) (7,13) (55,13) closed | castle.lua:62-79 |

## Safe plan, Valkyrie XL 14 with reflection and levitation
1. Arrive west. Do not stand at (4,8) beside the eels unless needed.
2. To go on (Valley): levitate over the moat around the castle to the east courtyard (58-62, 6-10), open/kick the
   locked east door (56,8), remove levitation in the corridor and step on a trap door. This skips soldiers and
   the throne room.
3. For the wand (worth it on the pilgrim route): from the corridor, open (38,8) into the throne room, fight the
   court one by one in the doorway, then door (32,4) or (32,12) to a hall, then each tower door until the chest.
   Open the chest with a key / lock pick / wand of opening, else #force while wielding a SPARE dagger or other
   blade (a blade can break: ~1/3 over a full attempt, lock.c:229-234; never force with the main long sword).
   Never force with a blunt weapon: 1 in 3 smashes the chest, every potion and 1/3 of other items (the wand!)
   break (lock.c:181-186, 252).
4. Soldiers: corridors and doorways, reflection covers their ray wands; Elbereth does not help.
5. Drawbridge only if no levitation: tune from prayer (2 boons) or Mastermind; never stand ON the bridge square
   when it opens/closes; force bolt / striking destroys it.

## Open questions
- Whether the west and east mazes connect around the castle without crossing water (map rows 0 and 16 are moat
  at both ends: looks like no).

## Compared with ChatGPT R10 (2026-11-08)
- Agrees: layout, door list (checked, exact), soldier/dragon/eel/shark counts, 27 court monsters, trap doors,
  locked chest + potion of gain level new in 5.0, gears/tumblers meaning, striking destroys the bridge.
- Missed by ChatGPT: there are no down stairs (trap doors are the only way on); left-right mirroring; eels drown a
  levitating hero; Elbereth useless against soldiers; the prayer boon that tells the tune; the cursed scare
  monster scroll must be left on the floor; the throne room cannot be bypassed to reach the towers.
- ChatGPT's "avoid the trap doors" is right only while getting the wand; afterwards they are the exit.
