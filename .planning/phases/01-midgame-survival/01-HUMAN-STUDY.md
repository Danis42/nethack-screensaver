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
