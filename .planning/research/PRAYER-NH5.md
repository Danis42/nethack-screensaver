# Prayer after a failure (research, 2026-10-29)

Source: p5-baseline (579c4d5, 2304 games), NetHack 5.0.0 src/pray.c, autoascend/agent.py.

## Data

- 33 games (1.4%) die to "wrath of Tyr": in all 33 the bot prayed into an angry god.
- All baseline prayers: 11,414 ok, 589 "displeased", 370 "Thou must relearn thy lessons!"
  (level drain), 163 "Thou hast angered me", 76 "pleased".
- Typical sequence: ok every ~890 turns, then one failure, then a new prayer every ~410
  turns, each failing, until the god kills the hero.

## Rules (pray.c 5.0.0)

- Too soon (p_type 0: timeout > 200 with major trouble): timeout += rnz(250), Luck -3, gods_upset
  (anger +1, then angrygods).
- Luck < 0 or anger > 0 (p_type 1): every prayer fails and calls angrygods. Its punishment roll
  is rn2(3 * anger - Luck ...) capped at 15: displeased, level drain (relearn), black glow
  (curses items), punishment ball, minion, and from 9 up lightning/disintegration (death).
- Anger only drops by sacrificing at a co-aligned altar ("You have a feeling of reconciliation"
  at 0); Luck recovers by 1 per 600 turns without a luck item.

## Bot

- agent.py keeps only last_prayer_turn; hunger prayers wait 1000 turns easing to 400 while Weak,
  HP prayers 500. Nothing records a failed prayer, so after the first failure it keeps praying.
- prayer.py already classifies outcomes ("is displeased.", "Thou hast angered me.", "Thou must
  relearn thy lessons!") but only for statistics.

## Candidate experiment

After a failed prayer, never pray again until a sacrifice brings "reconciliation" (or, simpler,
for the rest of the game). Expected effect is modest: most of these games lived on prayer for
food and die anyway (starvation instead of wrath), but it removes level drains, cursed items
and minions in ~10% of games that see a failure. The root cause is the food supply
(FOOD-NH5.md): ~6% of 890-turn gaps are too soon, and a starving bot prays 7 times per game.
