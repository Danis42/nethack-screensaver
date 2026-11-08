# R06 Buying protection from temple priests (A)

## Summary

- Protection is bought in chunks, not at a fixed price per AC point. In 5.0, the priest's baseline is `peak XL × random(150..250)`, adjusted upwards by the priest's cheapskate count. The first protection offer is twice that baseline (scaled for the money carried). [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L527-L681)
- The priest need not be co-aligned with the neutral Valkyrie. The protection branch is available when the peaceful priest is in their own undesecrated temple. Co-alignment affects other benefits and alignment consequences, not the protection purchase itself. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L545-L575) [5.0 `src/priest.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L634-L666)
- At XL8, the first protection threshold is 2,400–4,000 gold before any cheapskate penalty, assuming the purse is small enough that the scaling factor remains 1. With 120 gold, the bot cannot buy protection.
- The first successful purchase gives 2–4 protection points. Further purchases give +1 point per 2-baseline chunk up to 9; above 9, each additional point becomes less likely, and protection is capped at 20. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L666)
- The best early gold sources for a Valkyrie bot are generally selling surplus equipment and collecting accessible gold, with Mines digging and gold detection as opportunistic extras. Vaults contain gold but introduce a guard interaction. Leprechauns are not a reliable gold-farming plan.
- Buying protection is a strong long-term AC investment once the required cash is available. At 120 gold in Minetown, however, preserve the money; do not make a token offer.

## Facts

### 1. Exact priest donation formula

The 5.0 calculation in `priest_talk()` is:

\\[ B = L\_{\mathrm{peak}}\times \operatorname{rn1}(101,\ 150+40C) \\]

Where:

- \\(B\\) = priest's donation baseline.
- \\(L\_{\mathrm{peak}}\\) = hero's peak experience level (`u.ulevelpeak`).
- \\(C\\) = that priest's cheapskate count.
- `rn1(101, n)` produces an integer from \\(n\\) through \\(n+100\\).

The game then calculates:

\\[ Q=\max\left(1,\left\lfloor \frac{G}{3B}\right\rfloor\right) \\]

Where \\(G\\) is the gold counted in the hero's accessible inventory.

The prompt displays:

\\[ \text{First suggestion}=BQ \\]

\\[ \text{Second suggestion}=2BQ \\]

| Claim                                                                                                                                                                              | Source                                                                                                                                        | Version | Confidence |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| Baseline uses peak XL multiplied by a random amount from 150 through 250, plus 40 for every cheapskate mark.                                                                       | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L617) | 5.0.0   | high       |
| `u.ulevelpeak` is used, not necessarily current XL. Level-drain does not reduce the donation baseline once the peak has been reached.                                              | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L617) | 5.0.0   | high       |
| The scaling quantity is at least 1 and is derived from gold divided by three times the baseline.                                                                                   | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L617) | 5.0.0   | high       |
| The prompt shows the first and second suggested contributions.                                                                                                                     | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L617) | 5.0.0   | high       |
| The gold-counting function operates on the hero's inventory list; gold inside a carried container is not part of the amount counted for the prompt.                                | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L617) | 5.0.0   | high       |
| Protection purchase is made in increments of twice the unscaled baseline \\(B\\), not twice the displayed scaled suggestion \\(BQ\\).                                              | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L666) | 5.0.0   | high       |
| The first protection grant is a random 2–4 points. Subsequent increments below 9 grant +1 point; above 9, the chance of another point decreases with the current protection value. | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L666) | 5.0.0   | high       |
| Intrinsic protection contributes directly to AC through `u.ublessed`.                                                                                                              | [`src/do_wear.c::find_ac()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/do_wear.c?utm_source=chatgpt.com#L2370-L2373) | 5.0.0   | high       |
| Protection is capped at 20.                                                                                                                                                        | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L666) | 5.0.0   | high       |

### 2. Messages and donation bands

The priest uses the following important message branches.

| Donation result                                                   | Message                                                                                         | Game effect                                                                                        | Source                                                                                                                                    | Version | Confidence |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| No money, eligible co-aligned priest                              | `I will accept a small contribution...` / ale-related line, if the priest has change            | Small payment may be accepted; no protection purchase.                                             | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L577-L593) | 5.0.0   | high       |
| No money, cross-aligned priest                                    | `I am not interested.`                                                                          | No useful purchase.                                                                                | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L577-L593) | 5.0.0   | high       |
| Offer zero                                                        | `Thou shalt regret thine action!`                                                               | Penalty to co-aligned alignment record; priest's cheapskate counter increases.                     | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L617-L622) | 5.0.0   | high       |
| Offer below \\(BQ\\), with sufficient money left over             | `Cheapskate.`                                                                                   | Cheapskate count increases, increasing future donation baselines at this priest.                   | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L623-L633) | 5.0.0   | high       |
| Offer below \\(BQ\\), but not satisfying the remaining-money test | `I thank thee for thy contribution.`                                                            | Small donation; no protection, generally a Wisdom exercise.                                        | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L623-L633) | 5.0.0   | high       |
| At least \\(BQ\\), but below \\(2BQ\\)                            | `Thou art indeed a pious individual.` / `I bestow upon thee a blessing.`                        | Temporary clairvoyance, not protection.                                                            | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L634-L643) | 5.0.0   | high       |
| At least \\(2BQ\\), but below \\(3BQ\\)                           | `Thou hast been rewarded for thy devotion.` or `Thy selfless generosity is deeply appreciated.` | Permanent intrinsic protection, subject to cap and diminishing returns.                            | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L666) | 5.0.0   | high       |
| At least \\(3BQ\\)                                                | `Thy selfless generosity is deeply appreciated.`                                                | The protection-purchase branch is skipped; excessive donation is not a better protection purchase. | [`priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L667-L681) | 5.0.0   | high       |

Cheapskate test: the low-offer penalty is conditional. If the contribution is below \\(BQ\\), and the remaining gold is greater than twice the contribution, the priest says `Cheapskate.` and increases \\(C\\). A zero offer is a separate penalty branch and also increases the counter. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L617-L633)

For the XL8 bot carrying 120 gold:

- \\(B\\) is between 1,200 and 2,000 when \\(C=0\\).
- Since \\(G < 3B\\), \\(Q=1\\).
- First suggestion: 1,200–2,000 gold.
- Second suggestion: 2,400–4,000 gold.
- A 120-gold purse cannot reach either protection threshold.

Do not chat just to test the priest's price. A token offer may increase the cheapskate count.

### 3. Cost per protection point by experience level

For an unpenalized priest (\\(C=0\\)) and \\(Q=1\\):

\\[ 2B = L\_{\mathrm{peak}}\times[300,\ 500] \\]

This is the price threshold for the first protection purchase, which grants 2–4 points. The figures below are gold amounts, not expected costs.

| Peak XL | Baseline \\(B\\) | First protection threshold \\(2B\\) | Average cost per first point, assuming 3 points |
| ------- | ---------------- | ----------------------------------- | ----------------------------------------------- |
| 1       | 150–250          | 300–500                             | 100–167                                         |
| 5       | 750–1,250        | 1,500–2,500                         | 500–833                                         |
| 8       | 1,200–2,000      | 2,400–4,000                         | 800–1,333                                       |
| 10      | 1,500–2,500      | 3,000–5,000                         | 1,000–1,667                                     |
| 15      | 2,250–3,750      | 4,500–7,500                         | 1,500–2,500                                     |
| 20      | 3,000–5,000      | 6,000–10,000                        | 2,000–3,333                                     |
| 25      | 3,750–6,250      | 7,500–12,500                        | 2,500–4,167                                     |
| 30      | 4,500–7,500      | 9,000–15,000                        | 3,000–5,000                                     |

After the initial purchase:

- Protection below 9: another \\(2B\\) contribution grants one additional point.
- Protection 9–19: another \\(2B\\) contribution has a probability of \\(1/P\\) of granting +1, where \\(P\\) is the current protection value.
- At 20: no further protection is granted.

Source: 5.0 `src/priest.c::priest_talk()`. The averages in the last column are derived from the source's initial random 2–4 points, not a measured player statistic.

Effect of the scaling quantity \\(Q\\): the second displayed suggestion is \\(2BQ\\), but the internal loop processes increments of \\(2B\\). Thus an exact second-suggestion donation can fund \\(Q\\) protection increments, not merely one.

### Additional combat and movement facts

| Claim                                                                                                              | Source                                                                                                                                                                                                                                            | Version                     | Confidence |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- | ---------- |
| Intrinsic fast gives the hero an additional movement on one-third of turns, averaging 16 movement points per turn. | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                                                                                                                   | Current Wiki; 5.0 mechanics | high       |
| Burdened fast movement is 12; stressed fast movement is 8; strained fast movement is 4.                            | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                                                                                                                   | Current Wiki; 5.0 mechanics | high       |
| A speed-18 monster receives one move each turn plus a 50% chance of another.                                       | [NetHackWiki: Speed](https://nethackwiki.com/wiki/Speed?utm_source=chatgpt.com)                                                                                                                                                                   | Current Wiki; 5.0 mechanics | high       |
| Valkyries gain permanent intrinsic speed at XL7.                                                                   | [NetHackWiki: Valkyrie](https://nethackwiki.com/wiki/Valkyrie?utm_source=chatgpt.com)                                                                                                                                                             | Current Wiki; 5.0 mechanics | high       |
| A scared monster that cannot find a legal move can attack despite being scared (`panicattk`).                      | [`src/monmove.c::dochug()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/monmove.c?utm_source=chatgpt.com#L847-L900)                                                                                                        | 5.0.0                       | high       |
| Written Elbereth is disabled in Gehennom and the Endgame, and does not scare every species.                        | [`src/monmove.c::onscary()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/monmove.c?utm_source=chatgpt.com#L2617-L2687)                                                                                                     | 5.0.0                       | high       |
| The four target species do not have the stalking property required to follow the hero between levels.              | [`src/mondata.c::levl_follower()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mondata.c?utm_source=chatgpt.com#L1136-L1152); species definitions in `monsters.h`                                                          | 5.0.0                       | high       |
| The XL6–13 critical-HP test for prayer is `HP <= 5` or `6 × current HP <= maximum HP`.                             | [`src/pray.c::critically_low_hp()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c?utm_source=chatgpt.com#L102-L143)                                                                                                   | 5.0.0                       | high       |
| Prayer eligibility depends on cooldown and other deity/temple conditions; `#pray` is `M-p` in the standard keymap. | [`src/pray.c::can_pray()` and `dopray()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/pray.c?utm_source=chatgpt.com#L2041-L2154); [5.0 Guidebook](https://nethack.org/v500/Guidebook.html?utm_source=chatgpt.com#Commands) | 5.0.0                       | high       |

### What the AC and HP numbers mean

At AC -3, the hero is better protected than a character in ordinary starting armour, but AC is not immunity. The hit probability still depends on the monster's to-hit calculation and other combat circumstances. No source-backed AC value makes any of these four monsters harmless.

The one-attack-set maximums are:

- Mumak: `4d12 + 2d6` = 60.
- Soldier ant: `2d4 + 3d4` = 20 dice damage, with an additional poison hazard.
- Owlbear: `1d6 + 1d6 + 2d8` = 28.
- Leocrotta: `2d6 + 2d6 + 2d6` = 36.

These are upper bounds for one completed attack sequence, not guaranteed damage or a bound on all damage received before the hero acts again. In particular, speed-18 monsters can obtain a second action on some hero turns. [5.0 `include/monsters.h`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/include/monsters.h?utm_source=chatgpt.com#L98-L105) [5.0 `src/monmove.c::dochug()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/monmove.c?utm_source=chatgpt.com#L847-L900)

For maximum HP 60–85, the prayer critical-health threshold corresponds to approximately 10–14 current HP. That is an emergency threshold, not a sensible HP target for starting a fight.

## Bot rules

### Rule 1 — Retreat based on actual speed and encumbrance

- Trigger = Monster name is `mumak`, `soldier ant`, `owlbear`, or `leocrotta`; status line supplies XL, speed condition and encumbrance.
- Action =
  1. If mumak: move away, provided the hero has at least normal movement advantage and a clear path.
  2. If owlbear: move away when XL7+ and unburdened, or when otherwise demonstrably faster.
  3. If soldier ant or leocrotta: do not rely on walking away, even at XL7 and unburdened.
  4. Use the direction opposite the monster (`h`, `j`, `k`, `l`, `y`, `u`, `b`, `n` for vi movement).
  5. Check distance and encumbrance again after each action.
- Done when = The target is no longer an immediate threat or the hero reaches a known exit/stair.
- If it fails = Use stairs, a known wand or emergency prayer. Do not repeatedly walk away from a speed-18 monster while it remains adjacent.
- Evidence = 5.0 monster speed definitions; NetHackWiki Speed and Valkyrie.

### Rule 2 — Make Elbereth usable rather than assuming it is a force field

- Trigger = A target monster is approaching on a level where written Elbereth works; hero is not swallowed.
- Action =
  1. Prefer an open room with multiple legal escape directions.
  2. Press `E`.
  3. Select `-` for finger engraving if asked.
  4. Enter `Elbereth`, then Enter.
  5. Stay on the tile only while the monster is visibly fleeing.
  6. Keep an open retreat route.
- Done when = The monster has retreated enough for the hero to reach stairs, another room or a safe position.
- If it fails = If the monster does not flee, or it is scared but cannot move, leave immediately. Do not wait for a panic attack.
- Evidence = 5.0 `src/monmove.c::onscary()` and `dochug()`.

### Rule 3 — Use stairs instead of fighting a faster monster

- Trigger = Soldier ant or leocrotta is approaching, or the hero's retreat distance is not increasing; known stairs are accessible.
- Action =
  1. Move to the stair tile.
  2. Press `<` or `>` to use the appropriate staircase.
  3. Verify the new level.
- Done when = The hero has changed levels.
- If it fails = Use a known wand or Elbereth to create the space needed to reach the stairs.
- Evidence = 5.0 `src/mondata.c::levl_follower()`; none of the four species follows the hero across levels.

### Rule 4 — Use a known wand for a dangerous adjacent threat

- Trigger = Monster is visible and a known wand of sleep, slow monster, striking or teleportation is in inventory.
- Action =
  1. Press `z`.
  2. Select the known wand's inventory letter.
  3. Enter the direction towards the target.
  4. Parse the result message.
  5. If sleep or slowing succeeded, retreat or reassess before attacking.
- Done when = The monster is asleep, controlled, removed, killed or no longer threatening.
- If it fails = If it resists or continues moving, do not spend repeated turns on an unverified effect. Go to stairs or use another escape method.
- Evidence = 5.0 `src/zap.c` wand-hit handling and the target monster definitions.

### Rule 5 — Gate melee by monster type and current HP

- Trigger = Bot proposes a long-sword attack against one of the four species.
- Action =
  1. Read current HP, not maximum HP.
  2. Check whether poison resistance is present for soldier ant.
  3. Use the maximum attack-set table as a warning threshold.
  4. Avoid mumak melee unless there is a strong immediate kill opportunity.
  5. Avoid soldier-ant melee without poison resistance or an excellent immediate kill opportunity.
  6. Owlbear melee is the least unattractive of the four if HP is comfortably above 28 and there is an escape route.
  7. Leocrotta melee should be treated as high risk while it is healthy.
- Done when = Monster dies or the hero safely breaks contact.
- If it fails = If current HP drops sharply, poison is applied, or the hero is grabbed, abandon routine melee and switch to escape.
- Evidence = 5.0 `include/monsters.h` attack data and `src/monmove.c::dochug()`.

### Rule 6 — Pray only when critically endangered

- Trigger = At XL6–9, `current_HP <= 5` or `current_HP * 6 <= max_HP`; prayer cooldown and other conditions appear eligible.
- Action =
  1. Press `M-p` (`#pray`).
  2. Read the result message.
  3. Do not repeat if rejected.
- Done when = The hero survives the emergency and HP is no longer critical.
- If it fails = Use a known escape item or stairs. Do not assume that the deity will intervene on demand.
- Evidence = 5.0 `src/pray.c::critically_low_hp()`, `can_pray()` and `dopray()`.

## Risks and exceptions

1\. Mumak damage is deceptive. Its speed makes retreat practical, but its 4d12 butt attack has a high maximum. Do not stand adjacent while deciding whether to fight.

2\. The soldier ant's sting is a special risk. Poison can be fatal independently of the immediate HP damage. A nominally survivable 20-damage attack set can still end the run.

3\. The owlbear is a grabbing monster. It should not be treated as a harmless, slow melee opponent. Its hug attack is part of the attack sequence.

4\. A leocrotta's speed makes it much more dangerous than its AC suggests. At speed 18 it can obtain a second action on some turns. The hero's fast intrinsic at XL7 is not enough to guarantee escape.

5\. Elbereth may fail tactically even when the species is susceptible. A scared monster with no legal fleeing square can panic-attack. An open room is preferable to a blocked corridor.

6\. Monster HP and exact attack hit probability are randomized. The theoretical damage maxima are not a reliable damage prediction. The bot should not encode them as deterministic safe-melee thresholds.

## Open questions

- Exact wand success probabilities against each species under the NLE 5.0 configuration: UNVERIFIED.
- Whether the NLE's visible map and monster-identification observation expose species names rather than only glyphs: UNVERIFIED.
- A named 5.0 dumplog sample validating the user's 1152-game kill counts: not supplied; the counts are treated as the bot's own observations.

## Facts

### Donation eligibility and alignment

| Claim                                                                                                                                                                                           | Source                                                                                                                                                                                                                                                                       | Version | Confidence |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- |
| `priest_talk()` requires the priest to be peaceful and in their own temple.                                                                                                                     | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L545-L567)                                                                                                                                | 5.0.0   | high       |
| A sleeping, paralyzed or otherwise helpless priest can become hostile when chatted to.                                                                                                          | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L550-L565)                                                                                                                                | 5.0.0   | high       |
| A desecrated temple makes its peaceful priest hostile if the hero tries to chat.                                                                                                                | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L568-L575)                                                                                                                                | 5.0.0   | high       |
| Co-alignment is not a requirement for buying protection. The protection branch does not test `coaligned`; co-alignment is used for separate alignment adjustments and the no-money handout.     | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L577-L593) [`src/priest.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L634-L679) | 5.0.0   | high       |
| A priest without any gold in the hero's open inventory may give a small amount for ale if co-aligned and the hero has not strayed; a cross-aligned priest instead says they are not interested. | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L577-L593)                                                                                                                                | 5.0.0   | high       |
| Each priest has their own cheapskate counter; the penalty is not shared across all temples.                                                                                                     | [`src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L527-L532)                                                                                                                                | 5.0.0   | high       |

### Gold sources

| Source                         | What the bot can realistically get                                                                                                                                                                             | Source                                                                                                                                                                                                                                                                               | Version                                      | Confidence |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | ---------- |
| Selling unwanted items         | Cash from saleable spare equipment, weapons, armour, tools and other stock accepted by the shop. The usual quote for a known item is half its effective shop value.                                            | [`src/shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2981); [`src/shknam.c::saleable()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shknam.c?utm_source=chatgpt.com#L3441-L3478) | 5.0.0                                        | high       |
| Selling unidentified items     | Some shopkeepers pay 3/8 rather than 1/2 of the effective value; the affected keeper is selected by `m_id % 4`.                                                                                                | [`src/shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2968-L2981)                                                                                                                                               | 5.0.0                                        | high       |
| Ordinary vault                 | A substantial concentrated gold cache. The current Wiki describes four gold squares, each containing `50 + d(100 × dungeon level)` gold. Exact 5.0 generation amount is UNVERIFIED against the release source. | [NetHackWiki: Vault](https://nethackwiki.com/wiki/Vault?utm_source=chatgpt.com)                                                                                                                                                                                                      | Current Wiki; exact 5.0 amount unverified    | medium     |
| Vault frequency                | The Wiki describes a 1/2 chance of a vault on a level with at least six rooms, subject to space and level exclusions.                                                                                          | [NetHackWiki: Vault](https://nethackwiki.com/wiki/Vault?utm_source=chatgpt.com)                                                                                                                                                                                                      | Current Wiki; exact 5.0 frequency unverified | medium     |
| Mines digging                  | The game seeds eligible rock tiles with gold. Gold placement probability is increased in the Mines.                                                                                                            | [`src/mklev.c::mineralize()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1348-L1443)                                                                                                                                         | 5.0.0                                        | high       |
| Mines gold probability         | `goldprob = 20 + depth/3`, doubled in the Mines. Each eligible tile has a `goldprob/1000` chance of receiving a deposit.                                                                                       | [`src/mklev.c::mineralize()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1382-L1397) [`src/mklev.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1403-L1425)          | 5.0.0                                        | high       |
| Mines deposit quantity         | A deposit has `1 + rnd(3 × goldprob)` pieces; one-third of deposits are placed in the buried-object list.                                                                                                      | [`src/mklev.c::mineralize()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1417-L1425)                                                                                                                                         | 5.0.0                                        | high       |
| Gold-detection scroll          | A non-cursed scroll reveals gold on the level, including buried gold. Blessed detection additionally detects certain gold objects.                                                                             | [`src/read.c`, gold detection effect](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1925-L1942); [NetHackWiki: Scroll of gold detection](https://nethackwiki.com/wiki/Scroll_of_gold_detection?utm_source=chatgpt.com)           | 5.0.0; Wiki                                  | high       |
| Cursed/confused gold detection | Detects traps rather than gold.                                                                                                                                                                                | [`src/read.c`, gold detection effect](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1925-L1942); [NetHackWiki: Scroll of gold detection](https://nethackwiki.com/wiki/Scroll_of_gold_detection?utm_source=chatgpt.com)           | 5.0.0; Wiki                                  | high       |
| Leprechaun theft               | The leprechaun's attack steals gold from open inventory. Gold in containers is protected from this attack.                                                                                                     | [NetHackWiki: AD_SGLD](https://nethackwiki.com/wiki/AD_SGLD?utm_source=chatgpt.com)                                                                                                                                                                                                  | Current Wiki; 5.0-related mechanics          | high       |
| Leprechaun escape              | A leprechaun can teleport after successfully stealing gold. In 5.0, fleeing leprechauns may bury stolen gold after teleporting out of sight into a non-shop room.                                              | [`doc/fixes5-0-0.txt`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/doc/fixes5-0-0.txt?utm_source=chatgpt.com#L743-L746); [NetHackWiki: Leprechaun](https://nethackwiki.com/wiki/Leprechauns?utm_source=chatgpt.com)                                               | 5.0.0                                        | high       |
| Vault guard demands            | A guard may demand that the hero drop all visible and hidden gold and follow them out.                                                                                                                         | [`src/vault.c::gd_move()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L889-L925)                                                                                                                                              | 5.0.0                                        | high       |
| Vault guard identity trick     | The guard accepts `Croesus`, `Kroisos` or `Creosote` as the player's name and leaves peacefully if Croesus has not already died.                                                                               | [`src/vault.c`, guard name dialogue](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L469-L510)                                                                                                                                    | 5.0.0                                        | high       |

### Realistic gold policy for this Valkyrie

At Minetown, the bot's 120 gold is only 3–5% of the first protection threshold at XL8. There is no reason to sacrifice useful equipment or take a dangerous fight solely to raise that amount a little.

I would rank the income methods as follows:

| Rank | Method                                     | Bot practicality                                                     | Recommendation                                                                                              |
| ---- | ------------------------------------------ | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1    | Sell surplus equipment and duplicate items | Good when suitable shops are encountered                             | Make this the routine source. Sell items with low future utility, not essential equipment.                  |
| 2    | Collect accessible vault gold              | Potentially very high yield                                          | Worth exploiting when the bot can identify the vault and handle the guard safely.                           |
| 3    | Mine gold in the Mines                     | Opportunistic; requires a pick-axe or another digging source         | Mine accessible rock when the bot is already exploring the Mines, not as an exhaustive wall-mining project. |
| 4    | Use gold detection                         | Excellent for locating buried gold and vaults, but consumes a scroll | Save known non-cursed scrolls for levels where detecting gold can produce a worthwhile collection route.    |
| 5    | Leprechauns                                | Unreliable and potentially counterproductive                         | Do not farm them. Protect carried gold against their theft.                                                 |

Vaults deserve a special note. The guard is not necessarily an obstacle that has to be fought. When asked:

`"Hello stranger, who are you?"`

the 5.0 source accepts the name `Croesus` (also `Kroisos` or `Creosote`) and dismisses the guard if Croesus has not already died. The response is:

`Oh, yes, of course. Sorry to have disturbed you.`

The guard instead becomes hostile if Croesus has already been killed. This is a source-verified vault interaction, not an assumed general-purpose guard bypass. [5.0 `src/vault.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L469-L510)

For a Valkyrie bot, the practical sequence is to notice vault clues, locate the vault, recover the gold, and use the guard's dialogue correctly if encountered. The Wiki's vault article lists footsteps and the messages about someone counting money as clues to a vault. [NetHackWiki: Vault](https://nethackwiki.com/wiki/Vault?utm_source=chatgpt.com)

Mining is real but stochastic. `mineralize()` does not place gold in every rock tile. It checks only eligible diggable rock positions with the surrounding-stone conditions satisfied. In the Mines, the base probability is doubled, and one-third of generated deposits are buried. This supports opportunistic mining but not a predictable income estimate. [5.0 `src/mklev.c::mineralize()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1382-L1425)

Leprechauns are principally a gold-loss threat. If the bot has a large open-inventory purse, a successful leprechaun theft can remove some or all of it; if the leprechaun teleports out of sight, the 5.0 burial change can make recovery difficult. Keep gold in a container when travelling through areas where leprechauns are a realistic threat, then take it out when needed for a shop or priest. [5.0 `doc/fixes5-0-0.txt`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/doc/fixes5-0-0.txt?utm_source=chatgpt.com#L743-L746) [NetHackWiki: AD_SGLD](https://nethackwiki.com/wiki/AD_SGLD?utm_source=chatgpt.com)

Gold detection is especially useful when there is a specific target. The non-cursed scroll can reveal buried gold as well as gold in monster inventories and vaults. A cursed scroll, or any scroll read while confused, detects traps instead. Thus the bot should not consume an unknown scroll merely because it hopes to find a vault. [5.0 `src/read.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/read.c?utm_source=chatgpt.com#L1925-L1942) [NetHackWiki: Scroll of gold detection](https://nethackwiki.com/wiki/Scroll_of_gold_detection?utm_source=chatgpt.com)

How many protection points do human players usually buy? The community strategy reference recommends aiming for 9: below 9, later qualifying donations produce guaranteed additional points, whereas above 9 they have diminishing probability. However, a reliable percentage of human ascenders who buy a particular number of points is UNVERIFIED without a named game or dumplog sample. [NetHackWiki: Protection run](https://nethackwiki.com/wiki/Protection_run?utm_source=chatgpt.com) [NetHackWiki: Aligned cleric](https://nethackwiki.com/wiki/Aligned_priestess?utm_source=chatgpt.com)

For this bot, 9 protection points is a sensible routine stopping target, not a proven human average. The first 2–4 points are particularly attractive because they are obtained in one successful donation. Further points up to 9 are guaranteed per qualifying donation increment; after that, the cost-benefit becomes much worse.

## Bot rules

### Rule 1 — Decide whether to approach the priest

- Trigger = A known priest is visible in a known temple; the bot has at least one gold piece in its open inventory.
- Action =
  1. Confirm that the priest is peaceful.
  2. Confirm that the priest is in their own temple and that its shrine has not been desecrated.
  3. Confirm that the priest is not fleeing, sleeping or helpless.
  4. Read the open-inventory gold quantity and peak XL.
  5. Do not chat if the bot cannot afford a meaningful protection donation or has no budget to spare.
- Done when = The bot has established eligibility and budget.
- If it fails = Do not issue `M-c`. A priest who is outside their temple or in an ineligible state can become hostile when chatted to.
- Evidence = 5.0 `src/priest.c::priest_talk()`.

### Rule 2 — Obtain the actual donation quotation

- Trigger = A peaceful eligible temple priest is adjacent and the bot's open-inventory gold is sufficient to consider a donation.
- Action =
  1. Press `M-c` (`#chat`).
  2. If the interface asks `Talk to whom? (in what direction)`, enter the direction towards the priest.
  3. Read the message.
  4. At `How much will you offer (suggested: N or M)?`, record both amounts.
  5. Calculate whether the second suggestion is affordable and worthwhile before entering an amount.
- Done when = The bot has recorded the two suggestions and knows the exact protection purchase amount.
- If it fails = If the priest says `is not interested`, `doesn't want anything to do with you`, or gives a hostility warning, do not make another attempt with that priest.
- Evidence = 5.0 `src/priest.c::priest_talk()`; 5.0 Guidebook, `#chat` command.

### Rule 3 — Buy the intended protection amount

- Trigger = Donation prompt shows two suggestions, and the bot has enough open-inventory gold to pay the second suggestion without compromising essential supplies.
- Action =
  1. Calculate `offer = second_suggestion`.
  2. Type that integer at the donation prompt.
  3. Press Enter.
  4. Read the response.
  5. Update the protection value by comparing the actual AC/status change.
- Done when = The priest reports the devotion reward or the status shows increased intrinsic protection.
- If it fails = If the message indicates clairvoyance rather than protection, record that the first donation band was reached, not the protection band. If the message is `Thy selfless generosity is deeply appreciated.` without a protection increase, do not assume that the donation bought additional protection; it may have entered the excessive-offer band or hit diminishing returns.
- Evidence = 5.0 `src/priest.c::priest_talk()`.

### Rule 4 — Avoid cheapskate donations

- Trigger = The bot is at a donation prompt but cannot afford the first suggestion.
- Action = Do not enter zero or an arbitrary low amount. Prefer to leave the conversation unused and preserve the gold.
- Done when = No low donation was made and the priest's cheapskate counter was not increased.
- If it fails = If an offer has already been made and the priest says `Cheapskate.`, record one cheapskate penalty for that priest. Recalculate future donation thresholds rather than reusing the earlier baseline.
- Evidence = 5.0 `src/priest.c::priest_talk()`.

### Rule 5 — Sell surplus gear for gold

- Trigger = The bot is inside an appropriate shop and the inventory contains an item that is saleable and no longer strategically useful.
- Action =
  1. Press `d`.
  2. Select the inventory letter for the item.
  3. If the item is part of a stack, specify the number to sell.
  4. At the shopkeeper's `Sell it?` prompt, press `y`.
  5. Confirm that the gold amount in inventory has increased.
- Done when = The item is sold, and the open-inventory gold amount is updated.
- If it fails = If the keeper is uninterested or the offer is capped by the keeper's available money, mark the transaction as non-standard. Do not sell a strategically important object just because it receives a high quote.
- Evidence = 5.0 `src/shk.c::set_cost()`, `sellobj()` and `src/shknam.c::saleable()`.

### Rule 6 — Collect Mines gold only when it is worthwhile

- Trigger = The hero has a known pick-axe or another known digging source, and accessible diggable stone is present.
- Action =
  1. Press `a`.
  2. Select the pick-axe.
  3. Enter the direction of the diggable wall when prompted.
  4. Repeat only when the gold yield and terrain justify the actions.
  5. Collect the resulting gold with `,` if it is on the floor.
- Done when = Gold has been collected or the accessible mining opportunity is exhausted.
- If it fails = If the wall is non-diggable, or the area has dangerous monsters, stop mining rather than spend turns or resources unnecessarily.
- Evidence = 5.0 `src/mklev.c::mineralize()` and the pick-axe application path.

### Rule 7 — Use gold detection on a promising level

- Trigger = Inventory contains a known non-cursed scroll of gold detection; hero is not confused; level contains a plausible vault or buried treasure area.
- Action =
  1. Press `r`.
  2. Select the known gold-detection scroll.
  3. Read the visual messages and map markings.
  4. Route towards detected gold only if the path is safe.
  5. Collect gold and verify the open-inventory count.
- Done when = Detected gold has been collected or the accessible targets have been evaluated.
- If it fails = If the message indicates trap detection, record that the scroll was cursed or the hero was confused; do not follow `$` markings as though they were gold.
- Evidence = 5.0 `src/read.c`, gold-detection effect; NetHackWiki: Scroll of gold detection.

### Rule 8 — Handle a vault guard without losing the gold

- Trigger = The screen shows `Hello stranger, who are you?` from a vault guard, and the bot has already confirmed that Croesus has not been killed.
- Action =
  1. Type `Croesus`.
  2. Press Enter.
  3. Check for `Oh, yes, of course. Sorry to have disturbed you.`
  4. Confirm the guard has disappeared and the gold is still in inventory.
- Done when = The vault guard has left peacefully.
- If it fails = If Croesus is dead, or the guard reacts angrily, do not repeat the name trick. Follow the normal safe guard-escape policy instead; do not fight the vault guard simply to retain the gold.
- Evidence = 5.0 `src/vault.c`, vault guard name dialogue.

## Risks and exceptions

1\. Gold in a container is protected from leprechaun theft, but it is not necessarily hidden from a vault guard. The vault guard uses `hidden_gold(TRUE)` in addition to open gold when determining whether the hero carries gold. [5.0 `src/vault.c::gd_move()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L889-L905)

2\. A priest donation only uses gold counted from the hero's inventory. Do not assume that the same gold amount that appears in a container-inclusive display is necessarily counted by `money_cnt(gi.invent)` in the donation code. Keep the actual donation money accessible to the priest. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L601-L610)

3\. The second suggested amount is the protection threshold; a much larger payment is not better. The code only awards protection within its second-to-third suggestion band. At or above three times the first suggestion, the protection-increment loop is skipped. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L679)

4\. Protection is permanent but can be stolen or lost through game effects. The priest's protection is recorded as the hero's intrinsic protection; the priest code itself notes that gremlin theft clears the intrinsic protection flag but retains the former magnitude for recovery. [5.0 `src/priest.c::priest_talk()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/priest.c?utm_source=chatgpt.com#L644-L653)

5\. A vault's value is high, but its guard interaction is not optional. The source checks for both open and hidden gold, and repeated refusal can make the guard hostile. The name trick only works before Croesus has been killed. [5.0 `src/vault.c`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L469-L510) [5.0 `src/vault.c::gd_move()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/vault.c?utm_source=chatgpt.com#L889-L925)

6\. Selling has opportunity cost. A high-value item might be worth much more as an emergency tool, a resistance source, or an ascension resource than its shopkeeper offer. The bot should use an item-retention whitelist before accepting sales. [5.0 `src/shk.c::set_cost()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/shk.c?utm_source=chatgpt.com#L2954-L2981)

7\. Mining is not a guaranteed income strategy. The game only tests eligible rock positions; the per-position probability is low even in the Mines. One-third of deposits are buried, which can require additional digging. [5.0 `src/mklev.c::mineralize()`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/src/mklev.c?utm_source=chatgpt.com#L1382-L1425)

8\. Do not chase leprechauns with a full purse. A leprechaun can steal gold, teleport and bury it out of sight. Carrying a large open purse is a liability in leprechaun territory. [5.0 `doc/fixes5-0-0.txt`](https://github.com/NetHack/NetHack/blob/NetHack-5.0.0_Released/doc/fixes5-0-0.txt?utm_source=chatgpt.com#L743-L746)

## Open questions

- Human protection-point distribution: UNVERIFIED. The Wiki supports a practical target of 9, but no representative dataset of human ascender donations has been established here.
- Expected gold by Minetown: UNVERIFIED. No named human dump or 5.0 NLE batch results establish the median gold carried by a Valkyrie at XL8.
- Vault yield in the 5.0 release: the Wiki's per-square quantity and generation chance are cited, but exact confirmation against the 5.0 release's vault-generation implementation is UNVERIFIED.
- NLE-specific command prompts: standard commands are `M-c`, `d`, `a` and `r`; exact prompt rendering for the configured NLE build should be tested rather than assumed.
