# Phase 1 human study: prayer and food in recorded NetHack 3.6 games

Source: NLD-NAO (`/ssd2/nethackFiles/db/nld.db`, dataset `nld-nao-aa`), read-only, decoded with
`nle.dataset.TtyrecDataset` by `scripts/nld_study.py`. Only 3.6.x games are used (the bot plays 3.6.6).
Only aggregate numbers and anonymised message lines are written here: god names are replaced by `<god>`,
and no per-game or per-player identifier is copied (plan 01-04, threat T-01-08).

How the numbers are read: every frame of a ttyrec is a terminal screen. Row 0 is the message line, rows
22-23 the status lines. A message shown on row 0 can be redrawn piece by piece and is cut at 80 columns, so
the script reports a message only once it is replaced or cleared, joins growth of the same text into one
message, splits a line into its messages (NetHack joins them with two spaces) and drops a last message that
the 80-column line cut short.

## Prayer messages (NetHack 3.6, NLD-NAO)

What the message line shows after "You begin praying to ...": the next distinct messages, at most 6, within
the 3 moves a prayer takes and until the first interface prompt. The list also holds what the hero did next
in the same move (menus, "Unknown command", pets and monsters), because a ttyrec cannot tell them apart;
those rows are noise, not prayer answers.

Command: `uv run python scripts/nld_study.py prayers --games 400 --top 40` (3.6.x games with maxlvl >= 4,
random sample, sampling seed 0). 400 games scanned, 315 prayers seen.

| # | count | line after "You begin praying" |
|---|---|---|
| 1 | 269 | You are surrounded by a shimmering light. |
| 2 | 156 | You feel that <god> is well-pleased. |
| 3 | 154 | You finish your prayer. |
| 4 | 63 | You feel much better. |
| 5 | 51 | Your stomach feels content. |
| 6 | 39 | The potions on the altar glow light blue for a moment. |
| 7 | 20 | Unknown command ' '. |
| 8 | 19 | You feel that <god> is pleased. |
| 9 | 17 | Coins |
| 10 | 11 | You feel purified. |
| 11 | 9 | # name |
| 12 | 9 | A spellbook appears at your feet! |
| 13 | 8 | You feel better. |
| 14 | 7 | You are surrounded by a golden glow. |
| 15 | 6 | Some of the potions on the altar glow light blue for a moment. |
| 16 | 6 | You are surrounded by a light blue aura. |
| 17 | 6 | The potion on the altar glows light blue for a moment. |
| 18 | 6 | You feel something move nearby. |
| 19 | 6 | Pick |
| 20 | 5 | You feel in good health again. |
| 21 | 5 | You can hear again. |
| 22 | 5 | You die... |
| 23 | 5 | Unknown command '^J'. |
| 24 | 4 | You feel that <god> is satisfied. |
| 25 | 4 | The rabid rat starts to attack you, but pulls back. |
| 26 | 4 | The killer bee starts to attack you, but pulls back. |
| 27 | 4 | The giant spider starts to attack you, but pulls back. |
| 28 | 4 | The coyote starts to attack you, but pulls back. |
| 29 | 4 | The giant ant starts to attack you, but pulls back. |
| 30 | 4 | / |
| 31 | 3 | The jackal starts to attack you, but pulls back. |
| 32 | 3 | The werejackal starts to attack you, but pulls back. |
| 33 | 3 | The giant bat starts to attack you, but pulls back. |
| 34 | 3 | "Hark, mortal!" |
| 35 | 3 | Choose which spell t |
| 36 | 3 | Message History |
| 37 | 3 | Choose wh |
| 38 | 3 | Your movements are now unencumbered. |
| 39 | 3 | You return to human form! |
| 40 | 2 | The door resists! |

`autoascend.prayer.prayer_outcome` over these 315 prayers: success 293, failed 7, unknown 15.

### Where the failure strings come from

Humans rarely fail a prayer (7 of 315 above), so two extra cohorts were scanned to see how a bad prayer
reads. Commands: `uv run python scripts/nld_study.py prayers --cohort died-praying --games 150 --top 25`
(all 141 games that ended "while praying", 348 prayers, classifier: success 198, failed 139, unknown 11) and
`uv run python scripts/nld_study.py prayers --cohort wrath --games 100 --top 25` (all 27 games killed by an
angry god, 86 prayers, classifier: success 7, failed 46, unknown 33). Lines that matter, with counts:

| cohort | count | line |
|---|---|---|
| died while praying | 134 | You die... (right after monsters hit: no shimmering light, so no invulnerability) |
| died while praying | 8 / 7 / 7 / 7 | "It hits!", "It bites!", "The giant ant bites!", "The soldier ant bites!" before dying |
| killed by an angry god | 15 | You fry to a crisp! |
| killed by an angry god | 14 | "Thou must relearn thy lessons!" |
| killed by an angry god | 14 | You feel foolish! |
| killed by an angry god | 12 | Suddenly, a bolt of lightning strikes you! |
| killed by an angry god | 4 | You feel that <god> is displeased. |
| killed by an angry god | 4 + 2 + 2 + 1 | The voice of <god> booms/thunders/rings out: "Thou hast angered me." |
| killed by an angry god | 4 | You are being punished for your misbehavior! |
| killed by an angry god | 3 | "Thou art arrogant, mortal." |
| killed by an angry god | 1 + 1 | "Thou durst call upon me?", "Then die, mortal!" |
| killed by an angry god | 1 | A black glow surrounds you. |

### What went into `autoascend/prayer.py`

- Success markers: the shimmering light (a prayer that will work makes the hero invulnerable for its 3 moves, so
  "starts to attack you, but pulls back." is as certain), "is well-pleased." / "is pleased." / "is satisfied.",
  the fixes (stomach content, much better, better, purified, good health again, hear again), golden glow, light
  blue aura, a spellbook gift, a softly glowing item, and potions on an altar blessed ("glow light blue").
- Failure markers: "is displeased." and the angry god's lines above, plus "You die..." inside the prayer window.
- Not in the census, so not in the tuples: "You feel a hopeful feeling." (the plan's example text; the example
  still classifies as success through the shimmering light), the hallucination wordings of the pleased and
  displeased lines, "Goodbye level N." (the level-loss line in the recorded games read "Farvel level N."),
  "Thou hast strayed from the path." and the minion-summon text.
- A non-lethal failed prayer that prints nothing god-like (monsters hit, the hero survives, no answer line) is
  `unknown`, not `failed`: no human string shows it, and `unknown` is the honest answer.

Findings:

- Humans fail about 2% of prayers (7 failed of 315 prayers by this classifier, probably a few more among the
  15 unknown); the bot's own record is 77 failures in 643 prayers (12%), so the bot's prayers are not as safe.
- 85% of all prayers (269 of 315) start with the shimmering light, i.e. the humans prayed when it was safe.
- A death "while praying" is almost never the god's doing: 134 of 141 such games show monsters hitting a hero who
  never got the shimmering light, then "You die...". The god's anger (lightning, lost wisdom and level) is a
  separate, rarer ending (27 games).
- The census counts are a method check, not a rate: the 400 games were sampled by Dlvl 4+, not by prayer.

## Food and prayer on Dlvl 4-12

<!-- food-table:start -->
Cohorts (NetHack 3.6.x): **got through** = 300 games sampled from those with maxlvl >= 13 (sampling seed 0); **starved** = 153 games with maxlvl 4-12 whose death line names starvation or fainting from lack of food (all of them); **starved, died there** = the 125 of those whose death level is also on Dlvl 4-12. Band = status line shows Dlvl 4..12 (Mines and Sokoban levels count by their Dlvl). Rates pool all games of a cohort.

| | got through (maxlvl >= 13) | starved or fainted to death (maxlvl 4-12) | same, and died on Dlvl 4-12 |
|---|---|---|---|
| games used / excluded (no T: counter, or status unreadable for over 20% of the game) | 292 / 8 | 143 / 10 | 117 / 8 |
| turns observed on Dlvl 4-12 (median per game) | 10,349 | 722 | 929 |
| turns observed on Dlvl 4-12 (all games) | 3,718,182 | 217,030 | 202,681 |
| prayers on Dlvl 4-12 (games with at least one) | 542 (200) | 74 (46) | 64 (37) |
| prayers per 1000 band turns | 0.15 | 0.34 | 0.32 |
| median gap between prayers (turns; gaps counted) | 2,715 (342) | 946 (28) | 941 (27) |
| 25th percentile of the gap between prayers | 927 | 611 | 591 |
| share of gaps under 500 turns | 14.3% | 17.9% | 18.5% |
| failed prayers after a gap under 1000 turns (failed / prayers) | 6 / 90 | 6 / 15 | 5 / 14 |
| failed prayers after a gap of 1000+ turns (failed / prayers) | 5 / 252 | 2 / 13 | 2 / 13 |
| share of prayers while Weak or worse | 13.3% | 54.1% | 51.6% |
| share of prayers that failed | 2.8% | 14.9% | 14.1% |
| eating events per 1000 band turns (meals: 10443 / 627 / 591) | 2.81 | 2.89 | 2.92 |
| share of band turns Hungry or worse | 3.9% | 20.9% | 21.2% |
| share of band turns Weak or worse | 0.4% | 8.9% | 9.2% |
<!-- food-table:end -->

Command: `uv run python scripts/nld_study.py food --games 300 --jobs 8 --write .planning/phases/01-midgame-survival/01-HUMAN-STUDY.md`
(sampling seed 0 for the "got through" sample; the starved cohorts are all matching games, so the seed does not
touch them). The table between the markers above is written by that command; the text below is by hand.

How each row is measured (all from the screen of each recorded game, `scripts/nld_study.py`):

- Band turns: the turn counter `T:` is read from the status line; each step in `T:` counts for the Dlvl and the
  hunger word of the earlier reading. A reading is ignored when `T:` goes backwards, exceeds the game's real
  length (`turns` in the games table), jumps ahead by more than 500 and the next reading does not confirm it, or
  sits in a row that also shows attribute-line pieces (`St:`, `Wi:`, ...): a window drawn over the status lines
  leaves such garbage (13 of the first 300 games showed turn counters up to about 100 times the real game length before
  these rules).
- Games without `T:` on the status line (the player did not enable it) and games whose status line could be
  followed for under 80% of their real length are excluded and counted in the first row.
- Prayers: "You begin praying to" while the status line shows Dlvl 4..12. Hunger is the word on the status line
  just before the prayer takes effect; the outcome is `autoascend.prayer.prayer_outcome` over the messages
  that followed (a prayer with no recognised answer counts as not failed).
- Eating events: one per meal, not per message. The taste line ("This newt corpse tastes terrible!"), the finish
  line ("You finish eating ...") and an interruption ("You stop eating ...") of one meal count once;
  a meal that shows only one of them counts once; the "hard time getting all of it down" and "hit the spot"
  lines are part of a meal. A meal left open is forgotten after 60 turns.
- Dlvl 4-12 is the number on the status line, so Mines levels (Dlvl 3-13) and Sokoban (Dlvl 5-9) count as well,
  for both cohorts alike.
- Only aggregates are printed or stored: the script never writes any per-game or per-player column.

Findings (plain language; the starved cohorts are small, so read the third and fourth as indications):

1. Humans who got through Dlvl 4-12 were Hungry or worse for 3.9% of their turns there and Weak or worse for 0.4%;
   humans who starved there were Hungry or worse for about 21% and Weak or worse for about 9%. Hunger was a
   short episode for the survivors, a long state for the others.
2. The humans who starved there did not eat less often: 2.8 to 2.9 eating events per 1000 turns in all three
   columns. They also died early: the median of the 153 starved games ended at game turn 2,206 (quartiles 1,505 and
   3,717; games table), after a median of 722 to 929 turns on Dlvl 4-12 (survivors: 10,349 turns there). That is
   a different picture from the bot, whose median starvation turn is 7,828 (RESEARCH, Pattern 3): the human
   starvers are early-game deaths, the bot's are late. Eating frequency alone does not separate the groups; what
   each meal was worth (corpse versus ration) does not show in this measurement.
3. Humans pray rarely when they get through: 0.15 prayers per 1000 band turns (one per 6,700 turns), median gap
   2,715 turns, 25th percentile 927 turns; only 14% of the gaps are under 500 turns. The bot's limits are 400
   (hunger) and 500 (low HP) turns (`autoascend/agent.py`), i.e. it is ready to pray again after roughly the
   shortest 15% of human gaps. Only 13% of the survivors' prayers were made while Weak or worse, so most of
   their prayers were for low HP, not for hunger.
4. Humans fail 2.8% of their prayers on Dlvl 4-12 (15 of 542) against the bot's 12% (77 failures in 643 prayers,
   PORTING.md). After a gap under 1000 turns 6 of 90 prayers failed (6.7%), after 1000 or more turns 5 of 252
   (2.0%): the direction matches RESEARCH's computed safety (about 77% at a gap of 400 turns, 95% at 1000), with
   small numbers. The humans who starved prayed mostly while Weak or worse (54%) and 14.9% of their prayers failed
   (6 of 15 after a gap under 1000 turns).
5. Method limits: the cohorts are not matched by role or by Dlvl at death; "got through" includes the deepest
   players only (maxlvl >= 13), so it is the best case, not an average human; only 3.6.x games with `T:` shown and a
   readable status line are used; a prayer or meal message hidden by a window or cut by the 80-column line is missed.
