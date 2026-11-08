# R09 Medusa's Island (Claude, local 5.0.0 dat/medusa-1..4.lua, src/mhitu.c, src/uhitm.c)

## Summary
- Medusa's level is 1-4 levels above the Castle (dungeon.lua base -5, range 4); 4 maps; all no-teleport; maps
  can be flipped (no noflip flag), so match by shape, not by fixed coordinates.
- Medusa (monsters.h:2836): level 20, speed 12, AC 2, MR 50, flies and swims; weapon 2d4, claw 1d8, stoning gaze,
  poison bite 1d6; resists poison and stoning, so a cockatrice corpse does nothing to her.
- Reflection kills her with her own gaze, but only if she can see the hero: an invisible hero gets
  "doesn't seem to notice" and no kill (mhitu.c:1731). Stoning resistance also blocks the gaze (mhitu.c:1746).
- Biggest hidden danger: an eel's wrap drowns the hero unless Swimming/Amphibious/Breathless. LEVITATION AND
  WATER WALKING DO NOT PROTECT (uhitm.c:3389). The wrap is avoided only by a greased or oilskin item (u_slip_free).
- Digging down works on Medusa's level (not hardfloor, not bottom level: dungeon.c:1649) and skips her entirely.

## Facts: the four maps
| map | up stairs / arrival | down stairs + Medusa + Perseus | monsters | notes |
|---|---|---|---|---|
| 1 | up (5,14), west | (36,10) inside walled building, locked doors (38,8) (38,11) | 3 giant eels, 3 jellyfish, 2 water trolls, 2 random S at the doors | building walls undiggable |
| 2 | up (4,9), west island | (68,10) east island, locked door (71,7) | titan (2,5) ON THE ARRIVAL ISLAND, 6 electric eels (10-11,13-15), gremlin, 4 stone golems + 2 cobras asleep beside Medusa, an A | wand under boulder at (52,9); magic trap (3,12) |
| 3 | stair-up region (32-39,1-7) | one random room of (8,6) (66,5) (46,15) | 2 giant eels, 2 jellyfish, 4 nymphs, 30 hostile ravens | "shortsighted" level |
| 4 | stair-up region east (67-74) | one random room of (4,8) (10,4) (10,8) (10,12) in the west palace (7 locked doors) | kraken (7,7), yellow dragon + babies, 2 giant eels, black nagas | |

Perseus statue: shield of reflection (cursed +0) 75 %, levitation boots 25 % (map 2: 25 % / 75 %), blessed +2
scimitar 50 %, sack 50 %. Same odds as 3.6.

## 5.0 changes vs 3.6.6 (diffed against reference/nethack-3.6.6/dat/medusa.des)
- Maps 3 and 4: Perseus' statue now stands on the down stairs with Medusa (3.6: a different random room). So on
  maps 3/4 the statue marks the stairs.
- Maps can be mirrored (5.0 level flipping).
- Monster lists and statue odds unchanged.

## Ways across, ranked for the bot
1. Levitation boots/ring (permanent, controllable). Stay 2+ squares from eels when possible.
2. Water walking boots (same eel risk).
3. Dig down with a pick-axe from the arrival side: skips Medusa and the water entirely. Costs: no Medusa kill,
   no Perseus loot; the bot lands on the Castle level outside the moat (castle.lua teleport_region down = west).
4. Wand of cold / frost horn: freezes a line; many charges for wide water; ice melts? (not checked).
5. Boulders / scroll of earth: too few squares for these maps.

## Ways to kill Medusa
1. Reflection, visible to her, not blind: she dies on her first gaze.
2. Blindfold/towel on, then melee: safe from the gaze; her 4 attacks are ordinary (~13 avg/round + poison bite).
3. Cockatrice corpse: useless (MR_STONE).

## Bot rules
1. Before the level: have levitation or a pick-axe. Without either, do not go down.
2. On map 2: the titan is next to the arrival point; leave or fight at once, do not explore the island first.
3. Never stand next to water with an eel around unless the hero is amphibious or wearing a greased/oilskin item.
4. With reflection: walk up to Medusa visible (not invisible). Without: blindfold on before the room opens.

## Open questions
- Does ice from a cold ray melt back in 5.0 (melt_ice timer)? Not checked.
- How often the bot already has levitation or a pick-axe at Medusa's depth (bench data).

## Compared with ChatGPT R09 (2026-11-08)
- Agrees: four maps, flipping, coordinates, Perseus odds (incl. map 2 swap), maps 3/4 statue on the stairs,
  reflection best, cockatrice useless.
- WRONG in ChatGPT: "levitation protects against drowning" — not against eels: drowning by an eel checks only
  Swimming, Amphibious and Breathless.
- Missed by ChatGPT: titan beside the map-2 arrival, 30 ravens on map 3, invisible hero spoils the reflection
  kill, stoning resistance blocks the gaze, digging down lands outside the Castle moat.
- ChatGPT ranks digging down last; for this bot it is the most reliable crossing that needs only a pick-axe.
