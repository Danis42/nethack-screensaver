# Hand game seed 1 (val-hum-fem-neu, NetHack 5.0, natural play)

Tool: scripts/handplay.py (keys.log + seed rebuild the game). Findings feed ASCENSION-PLAYBOOK-NH5.md.

## Findings
- F1 (T1): NetHack 5 Valkyrie starts with a +1 spear and +0 dagger, NOT a long sword (src/u_init.c:160).
  Excalibur (fountain.c:404) needs a LONG_SWORD found or bought, XL >= 5. Playbook rule missing: pick up / buy
  a long sword; dip at a fountain at XL 5+. Staged kits assume a long sword.
- F2 (T44-160, Dlvl 2): arrival room sealed: one locked door + one hidden door (found after ~10 searches next
  to the wall) leading to a dead end. Kicking the locked door opened it in 3 kicks. Rule: in a closed start room,
  search along walls 10-30 turns, else kick a locked door (check the hero is ADJACENT first: my first kick hit
  air and strained a leg = "Dumb move! You strain a muscle", legs heal ~15 turns).
- F3 (Dlvl 2): NetHack 5 draws statues with the monster letter ('o' = statue of a goblin). Only the glyph /
  farlook tells. Bot must not fight or flee statues.
- F4 (Dlvl 2): an item ')' in a room was 8 arrows on an arrow trap; stepping there fired the trap.
- F5 (T246, XL1): HP 5/16 after two zombies in a row while resting in the open. Prayer at T246 worked
  (prayer timeout starts at 300, so T>=100 is enough for major trouble: needs timeout <= 200).
  SOURCE (pray.c:116 critically_low_hp): low HP = HP <= 5 or HP*div <= maxHP, div 5 at XL1-5, 6 at XL6-13,
  7 at XL14-21, 8 at XL22-29. Playbook said a flat 1/7: WRONG at low XL. Also: rest in a corridor/doorway, not
  in the middle of a room with several entrances.
- F6 (T360-382): locked chest. Pry with +0 dagger: 6%/turn success, 0.8%/turn break -> ~12% chance the dagger
  breaks (lock.c:229). It broke here. Bash with a non-blade (spear): 16%/turn (d8*2), weapon never breaks, but
  1/3 of successes destroy the box: all potions and 1/3 of the rest lost (lock.c:252). Cursed blades never
  break but weld to the hand. Rule: pry only with a spare blade, else bash; no potions expected -> bash.
  Chest had: egg, scroll.
- F7: altar BUC test works for any altar alignment (dropping on a lawful altar). Orcish dagger cursed, orcish
  helm and scroll uncursed. Eggs of unknown kind: do not eat (cockatrice egg stones).
- F8 (T630-880, Dlvl 3): a floating eye blocked the only corridor east. I threw the dagger, rock, spear and
  food at it; it survived (2 dagger hits + 1 spear hit) and I spent ~250 turns, ended up weaponless for ~200
  turns while exploring. Rules: (a) never throw the ONLY weapon at a blocker; (b) a floating eye in a corridor
  is a wall: route around or wait - it follows the hero slowly (speed 1) and moved off the corridor within
  ~150 turns; (c) telepathy needs several projectiles (>= 4 daggers) - not worth it with 1;
  (d) pickup_thrown is on: walking over thrown items picks them up; (e) danger: one raw step into the eye =
  paralysis; the bot's own move code must refuse a melee step into a floating eye (exp 21 covers fight, check
  it covers travel/explore steps too).
- F9: travel (_) does not autopickup gold; travel never attacks ("X blocks your path").
- F10 (Dlvl 3): two hobbits (sling + thrown daggers), a coyote, geckos, iguana: all trivial at XL 2-3, AC 3.
  Hobbit corpse eaten at once: "Blecch! Rotten food!" (no effect) - corpses are not always safe even fresh.
- F11: locked large box opened by kicking (8 kicks, "You break open the lock"), contents intact
  (polearm, scroll, spellbook). Kicking = no weapon risk. Tin whistle: "high whistling sound".
- State at T880: XL3 HP28 AC3, Dlvl 3, spear, 2 rations, towel, 3 unknown scrolls (2 TEMOV that do not
  stack = different BUC), no Mines branch seen on Dlvl 2 (partly explored) or Dlvl 3 (west half explored).
- F12 (T1128, Dlvl 4): wielded an UNTESTED dagger (picked up on Dlvl 3, thrown by a hobbit) to pry a box:
  it was cursed and welded. Pry worked (cursed blades never break), but the spear is now unusable.
  Rule: only wield known-uncursed items, also for prying (the spare-blade rule needs a BUC-tested blade).
  CORRECTED: a welded ONE-handed weapon with an UNCURSED shield is NOT major trouble: freehand()
  (engrave.c:473) says the hand is free because the shield could come off. It is only minor trouble
  (TROUBLE_CURSED_ITEMS, needs prayer timeout < 100). Prayed at T1246 (HP 10/28 vs a giant bat): "well-pleased",
  nothing fixed, timeout reset. Too-soon prayer cost (pray.c:2316): Luck -3, god anger +1, timeout +rnz(250).
  P(timeout still > 200 after ~1000 turns from rnz(350)) is about 5% (my calculation).
- F13 (Dlvl 3): the floating eye came back into the corridor later and blocked again; luring works: wait in a
  room off the corridor ~60 turns, it follows, then take the other exit. Hunger: Hungry at T805 and again T986
  (lichen = 200 nutrition only); ate a ration at T992.
- F14 (Dlvl 4 arrival room): food ration, potion, gold, locked large box (scroll + blue gem) all next to '<'.
- F15 (T1230-1320, Dlvl 4): giant bat took HP 28 -> 10 in 4 turns while my welded dagger missed 5 of 6.
  Fast erratic bats: fight them in a corridor, not in a room. Two gnomes (one with a bow) on Dlvl 4 =
  Mines branch is likely on this level or the gnomes came up from it.
- F16 (T1321): second large box was TRAPPED: "A tower of flame bursts from the large box!" max HP 28 -> 25,
  leather armor burnt (AC 3 -> 4). Rule: #untrap boxes before opening (or accept it); human players check
  with #untrap first. Contents: scroll, potion, wand. Engrave-test: "The floor is riddled by bullet holes!"
  = wand of magic missile.
- F17 NEAR-DEATH (T1329, Dlvl 4): HP 14/25 -> 2/25 in ONE turn: zapped magic missile west at an adjacent
  giant bat standing 1 square from a wall; the ray bounced off the wall and hit me too (magic missile is a
  ray: it bounces), plus a bat bite. Rules: (a) never zap a ray toward a near wall in line with yourself;
  zap only along long open lines; (b) prayer was used 83 turns earlier (F12 misjudgement) -> no emergency
  prayer: a wasted prayer is the cost of a wrong trouble rule; (c) SAVED by Elbereth in the dust
  (E - n Elbereth): "The giant bat turns to flee"; rested on it from HP 3 to 13 in 60 turns undisturbed,
  even with a bow gnome on the level. Unknown potions at HP 3: NOT quaffed (acid / sickness can kill).
