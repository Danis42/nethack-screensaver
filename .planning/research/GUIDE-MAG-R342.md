# Maniac's Ascension Guide (3.4.2) vs our playbook (read 2026-11-03)

Source: Mark Johnson, "Maniac's Ascension Guide" r342 (2003), alt.org mirror; local copy reference/guides/mag-r342.txt
(owner pointed to it). Written for 3.4.2: anything below marked [check 5.0] needs the 5.0 source before it becomes a rule.

## Checkpoints the guide sets (stage requirements we can measure against)
| Point | Guide's target |
|---|---|
| Below Minetown in the Mines | AC <= 0, better -4; else Sokoban first or come back |
| Quest entry (XL 14) | MC2-3, reflection, poison/fire/cold/shock/sleep res., AC -15..-25, HP 100-200, telepathy + towel/blindfold, unicorn horn, identified attack wands, a good weapon; Mines, Sokoban done |
| Before Gehennom / Vlad | AC -25..-35, HP 200-300, Medusa and Castle done, reliable water crossing (levitation before the Valley), speed boots, engulf escape, illness cure, essentials blessed |
| Medusa | a sure way across water BEFORE going (ring/boots of levitation, water walking); otherwise turn back and look, or dig down |
Our bot today: AC stops at -3/-4 (AC-GAP-NH5.md), HP and XL match humans to Dlvl 10-12 (STRENGTH-PER-DEPTH.md).
These targets are candidates for the stage requirements (owner plan item 3); thresholds still come from our data.

## Rules in the guide that our playbook lacks or contradicts
1. Telepathy from a floating eye + blindfold/towel is part of the standard kit (also MEDUSA-NH5.md: 95% / 96% of 5.0
   ascenders). MISSING in the bot.
2. Valkyrie: do the Quest early (artifact helps) - our ASCENSION-PLAN does Castle first (XL 14 by wraiths/Castle,
   XL14-NH5.md). Keep ours unless data says otherwise; note the disagreement.
3. Excalibur: guide says lawful only; 5.0 source agrees (fountain.c:404, 1/30 for non-Knights). Our Valkyrie is
   neutral: no Excalibur; never dip a long sword (playbook corrected).
4. Moving: when the down stairs are found, go down and back up at once (learn the arrival, spawn the level's
   monsters at lower XL). Dig a hole near the up stairs for fast descents later. MISSING.
5. Open Mines levels: fight next to the up stairs and go up to heal. MISSING (bot fights where it stands).
6. Elbereth: write it several times on the same square; blind writing can misspell it (5.0 wiki agrees). Elbereth
   rules changed in 3.6 [check 5.0]: attacking from the square erases it.
7. Identification: altar for non-stackables; armour only when known non-cursed; helmets only with a way to uncurse;
   kick gray stones before picking up (loadstone "Thump!"). Partly HAVE (loadstone?), check.
8. Drowning (Medusa, Castle): when an eel wraps you there is one turn: zap teleport or cold at it, or engrave
   Elbereth with a wand (one turn). MISSING.
9. Medusa: blind + telepathy to enter her room; apply (not wield) a mirror, or reflection. Perseus' statue: shield of
   reflection 25-75%. Titans on map 2: kill fast. HAVE partly (reflection), rest MISSING.
10. Castle: stand a knight's move from the drawbridge, play the passtune (Mastermind if unknown; BUILT solver),
    fight the outflow there; never stand on the bridge (striking destroys it). Wand of wishing in a corner tower.
11. Protection racket: #chat to the Minetown priest, 400*XL gold per point [check 5.0 price]; AC-GAP says the bot
    has ~121 gold at XL 8.
12. Pets: guide leans on the pet (displace it ahead, let it kill). AutoAscend mostly ignores the pet. Not pursued.
13. Wishes (guide's list): charging, magic marker, cloak of magic resistance, GDSM/SDSM, bag of holding, artifact
    weapon, speed boots, gauntlets of power. Compare WISHES-NH5.md.

## Next uses
- Item 1 (telepathy) and the Medusa crossing are the strongest gaps: both agree with the 199-dumplog data.
- Items 4, 5 and 8 are cheap bot rules; each needs our own data first (deaths near stairs, drowning deaths).
