# R02 Unicorns: fight or avoid

## Summary
- **Hostile unicorns do not intentionally charge into melee.** They actively avoid being lined up orthogonally or diagonally and will stay a knight’s move away; they attack only when you close in, when cornered, or when invisibility/terrain forces an accidental approach. They may teleport away if no safe square exists. 
- **Killing a co-aligned unicorn costs −5 Luck; killing a cross-aligned one carries no documented Luck penalty.** For a neutral Valkyrie, **gray unicorns are co-aligned** (peaceful) and **white/black are cross-aligned** (hostile). 
- **Gems are the main Luck tool.** Throwing a valuable gem to a **co-aligned** unicorn gives **+5 Luck if formally identified, +2 if type-named, +1 if completely unknown**. Throwing any gem to a **hostile** unicorn pacifies it, but cross-aligned gem Luck is unreliable and can go **down**. 
- **The safe early-game answer is not to melee.** Let a pet kill the unicorn, use projectiles/rays bounced off walls, or trap it; a weak Valkyrie should avoid direct combat entirely. 
- **Unicorn horns are still essential, but 5.0 removed attribute restoration.** In 5.0.0 the horn no longer restores drained attributes; it still cures blindness, hallucination, confusion, and stunning. 
- **Sokoban is the best place to manipulate unicorns.** On non-teleport levels they cannot teleport away, so cornering and gem-throwing are far more reliable. 

---

## Facts

| Claim | Source | Version | Confidence |
|---|---|---|---|
| White unicorn = lawful, gray = neutral, black = chaotic. | NetHackWiki, *Unicorn* (rev. 2025-09-09), opening; Fandom *Unicorn*. | 3.6/3.7 page; 5.0 **UNVERIFIED** but likely unchanged. | high |
| Normally generated co-aligned unicorns are peaceful; all others are hostile. | NetHackWiki, *Unicorn*, §Generation. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| Directly killing a co-aligned unicorn always carries a **−5 Luck** penalty. | NetHackWiki, *Unicorn*, opening. | 3.6/3.7; 5.0 **UNVERIFIED** whether penalty value changed. | high |
| Unicorns have **speed 24** and can outpace even “very fast” players. | Fandom *Unicorn* infobox; NetHackWiki, *Unicorn*, §Strategy. | 3.6/3.7; 5.0 **UNVERIFIED** but likely unchanged. | medium |
| A unicorn that can see the hero avoids being “lined up” even when hostile; it will not intentionally move into melee range. | NetHackWiki, *Unicorn*, §Strategy. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| If no neighbouring square avoids lining up, a unicorn has a **50% chance to teleport away** each move. | NetHackWiki, *Unicorn*, §Strategy. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| **NOTONL** is set for unicorns on teleportable levels so they avoid the hero’s line; on non-teleport levels they may not be able to avoid the hero. | NetHackWiki refs to `src/monmove.c` (3.6.6 lines 1089, 1125); code comment: “unicorn may not be able to avoid hero on a noteleport level” then `flag |= NOTONL` if `!noteleport`. | 3.6.6 source behaviour; 5.0 **UNVERIFIED** line numbers. | medium |
| Throwing **any gem** to a hostile unicorn makes it peaceful. | NetHackWiki, *Unicorn*, §Unicorns and gems; Fandom *Unicorn*. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| Co-aligned valuable gem: **+5 Luck** formally identified, **+2** type-named, **+1** completely unknown. | NetHackWiki, *Unicorn*, §Unicorns and gems (citing `dothrow.c` `gem_accept`); NetHackWiki, *Luckstone*. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| Cross-aligned valuable gem: Luck may go **up or down by 1** if unidentified and **up to 3** if identified. | NetHackWiki, *Unicorn*, §Unicorns and gems. | 3.6/3.7; 5.0 **UNVERIFIED**. | medium |
| “**Graciously** accepts” = worthless glass; “**gratefully** accepts” = valuable gem. | NetHackWiki, *Unicorn*, §Unicorns and gems; Fandom *Unicorn*. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| A unicorn normally leaves a corpse and a **unicorn horn**; revived or polymorph-trap unicorns leave a horn only **50%** of the time. | NetHackWiki, *Unicorn*, §Generation. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| A pet killing a co-aligned unicorn avoids the Luck penalty. | NetHackWiki, *Unicorn*, §Combat; *Unicorn horn*. | 3.6/3.7; 5.0 **UNVERIFIED**. | high for 3.6/3.7 |
| In **5.0.0**, unicorn horns **no longer restore lost attributes**. | Alternativeto summary of 5.0.0; GameBrief 5.0.0 guide; NetHackWiki *Unicorn horn* (3.7 upcoming note). | 5.0.0 confirmed by secondary release summaries; **UNVERIFIED** in primary source text. | medium |
| Unicorn horn still cures blindness, hallucination, confusion, and stunning. | NetHackWiki, *Unicorn*, §Unicorn horns. | 3.6/3.7; 5.0 **UNVERIFIED** whether this list is unchanged. | medium |
| Unicorn attacks: **headbutt 1d12**, **kick 1d6**, multiple attacks per turn. | Fandom *Unicorn* infobox. | 3.6/3.7; 5.0 **UNVERIFIED**. | medium |

---

## Bot rules

### Rule 1 — Classify the unicorn by colour before acting
**Trigger:** Map shows a `u`; the bot can read its colour from the terminal or monster description.
**Action:**
- White `u` → **lawful / cross-aligned** for a neutral Valkyrie → treat as hostile.
- Gray `u` → **neutral / co-aligned** → peaceful.
- Black `u` → **chaotic / cross-aligned** → hostile.

Record the classification. Do not assume hostility from the `u` symbol alone.
**Done when:** colour recorded.
**If it fails:** if colour cannot be read, default to “unknown” and do not melee.
**Evidence:** white/gray/black correspond to lawful/neutral/chaotic; co-aligned generated peaceful. 

---

### Rule 2 — Do not melee a hostile unicorn unless it is already adjacent and you are cornered
**Trigger:** Hostile `u` is adjacent, or the bot is considering pressing `F` toward a `u`.
**Action:**
- **Default: do not press `F`.** Unicorns do not intentionally enter melee; they attack when you close in or when cornered. 
- If the unicorn is adjacent and the bot has a ranged option (dagger, attack wand), use it. If not, retreat toward a corridor or upstairs.
- On a **non-teleport level** (Sokoban), a cornered unicorn cannot teleport away; only there may the bot consider melee if HP is high and the unicorn is likely to die quickly. **Exact HP threshold UNVERIFIED**; use a conservative rule such as “only if HP > 4 × (XL + 1) and AC ≥ 10”.
- On a **teleportable level**, do not chase a cornered unicorn into melee; it has a 50% chance to teleport away each move. 

**Done when:** hostile unicorn is dead, pacified, or no longer adjacent.
**If it fails:** if the unicorn lands multiple hits, retreat immediately; do not trade blows. Use stairs or teleport.
**Evidence:** unicorn speed 24, headbutt 1d12 + kick 1d6, multiple attacks per turn; they avoid melee unless forced. 

---

### Rule 3 — Throw a gem at a co-aligned unicorn to raise Luck
**Trigger:** Peaceful gray `u` is visible; inventory contains at least one gem; hero Luck is below maximum (or Luck is unknown).
**Action:**
1. If the gem is **not yet type-named**, type-name it first if the bot can safely do so (the game checks name/type, not actual identity). 
2. Press `t` → select the gem → direction toward the gray unicorn.
3. Read the message:
   - “**gratefully** accepts” → valuable gem; Luck increases by **+5 / +2 / +1** depending on identification status.
   - “**graciously** accepts” → worthless glass; no Luck change.
   - “**not interested in your junk**” → glass; no Luck change.
4. Repeat with other gems if Luck still below max.

**Done when:** Luck increases, or all candidate gems have been thrown.
**If it fails:** if the unicorn is peaceful but the bot accidentally attacks it, stop immediately; co-aligned kill is −5 Luck.
**Evidence:** co-aligned valuable gem Luck values; message meanings. 

---

### Rule 4 — Throw any gem at a hostile unicorn to pacify it
**Trigger:** Hostile white or black `u` is adjacent or blocking a corridor; the bot wants to avoid combat; inventory contains a gem (even worthless glass).
**Action:**
- Press `t` → select any gem → direction toward the hostile unicorn.
- Throwing **any gem** makes a hostile unicorn peaceful.
- Do **not** expect reliable Luck gain from a cross-aligned unicorn; Luck may go **down**. Use this rule only for pacification, not for Luck farming.

**Done when:** message indicates the unicorn calms or becomes peaceful.
**If it fails:** retreat or use ranged attacks; do not melee.
**Evidence:** any gem pacifies a hostile unicorn; cross-aligned Luck is unreliable. 

---

### Rule 5 — Do not throw unidentified valuable gems at cross-aligned unicorns
**Trigger:** Hostile `u`; the bot is considering throwing a gem that is **not known to be worthless glass**.
**Action:** Do **not** throw unidentified gems at hostile unicorns. The Luck change for a cross-aligned unicorn can be **negative** (down 1 if unidentified, down up to 3 if identified). Throw only gems the bot knows are glass, or throw only to pacify when survival matters more than Luck.
**Done when:** decision made not to throw, or a known-glass gem is thrown.
**If it fails:** if Luck drops, stop throwing gems at that unicorn.
**Evidence:** cross-aligned Luck may increase or decrease. 

---

### Rule 6 — Acquire a unicorn horn with minimal Luck damage
**Trigger:** Inventory contains no unicorn horn; a unicorn is present or the bot is on a level where unicorns can spawn.
**Action, in order of preference:**
1. **Let a pet kill the unicorn.** A pet kill avoids the −5 Luck penalty even for a co-aligned unicorn. 
2. **Kill a cross-aligned (white or black) unicorn.** No Luck penalty is documented for killing a cross-aligned unicorn.
3. **If only a co-aligned unicorn is available and the bot must kill it:** throw valuable gems to the co-aligned unicorn first to raise Luck, then kill it; the −5 Luck penalty will apply, but the gem Luck partially offsets it. 
4. **Use a trap or polearm** if available: pit/beartrap can hold the unicorn; polearm/lance at Skilled can hit it at a knight’s move. 

**Done when:** a `unicorn horn` appears in inventory.
**If it fails:** a revived or polymorph-trap unicorn may not drop a horn (only 50%); do not waste resources on revived unicorns if another horn source exists. 
**Evidence:** horn drop rules; pet kill avoids Luck penalty; gem-offset strategy. 

---

### Rule 7 — Use the horn for status cures, not attribute restoration
**Trigger:** Hero is blind, hallucinating, confused, or stunned, and inventory contains an uncursed unicorn horn.
**Action:** Press `a` → select `unicorn horn`. Do **not** expect drained attributes to be restored in 5.0.0; that function was removed. If the horn is cursed, do not apply it (cursed horns can induce nausea in 3.7/5.0). 
**Done when:** status cure message appears or the status ends.
**If it fails:** use potions, prayer, or other cures; do not rely on the horn for attribute drain.
**Evidence:** 5.0 removal of attribute restoration; horn still cures blindness/hallucination/confusion/stunning. 

---

### Rule 8 — Prefer Sokoban for unicorn manipulation
**Trigger:** Bot is in Sokoban (non-teleport level) and a unicorn is present.
**Action:** Because unicorns cannot teleport away on non-teleport levels, the bot may corner them or line them up more reliably. Use Sokoban for gem-throwing and horn acquisition when possible. On teleportable levels, assume a cornered unicorn will teleport.
**Done when:** unicorn is pacified, killed, or the bot leaves Sokoban.
**If it fails:** on teleportable levels, disengage rather than chase.
**Evidence:** NOTONL is not applied on non-teleport levels, so unicorns “may not be able to avoid hero”; wiki recommends non-teleport zones for gem-throwing. 

---

## Risks and exceptions
- **Pet kill is not risk-free.** The pet may die to the unicorn’s multiple attacks. Do not rely on a low-HP pet. 
- **Invisibility can backfire.** A hostile unicorn that cannot see the hero will not know to stay a knight’s move away and may accidentally close to melee. Do not use invisibility as a “safe” unicorn tool at low XL. 
- **Displacement bug.** In 3.6, unicorns are not fooled by displacement while avoiding the hero; the 3.7/5.0 fix is **UNVERIFIED** in live play. Do not rely on displacement to mislead unicorns. 
- **5.0 horn nerf.** Any bot logic that assumes “apply horn to restore drained Strength” is obsolete in 5.0.0. Use potions of restore ability, the restore ability spell, or prayer instead. 
- **Exact 5.0 monmove.c behaviour is UNVERIFIED.** The NOTONL logic is documented for 3.6.6; 5.0 line numbers and any changes are not confirmed from source text.
- **Cross-aligned kill Luck.** I found no documented Luck penalty for killing a cross-aligned unicorn, but a possible alignment penalty is **UNVERIFIED**. The bot should not assume a cross-aligned kill is completely free in every respect.

---

## Open questions
1. **Exact 5.0 monmove.c NOTONL implementation and line numbers** — is the teleportable/non-teleportable unicorn behaviour unchanged from 3.6.6? **UNVERIFIED.**
2. **Does killing a cross-aligned unicorn carry an alignment penalty in 5.0.0**, even if there is no Luck penalty? **UNVERIFIED.**
3. **Exact 5.0 unicorn horn cure list** after the attribute-restoration removal — does it still cure sickness, nausea, and all the 3.6 statuses? **UNVERIFIED.**
4. **Exact Luck values for 5.0 gem throwing** — the +5/+2/+1 and cross-aligned ±1/±3 values are 3.6/3.7 wiki values; 5.0 source confirmation was not obtained. **UNVERIFIED.**
5. **Best NLE key sequence for throwing a gem at a specific adjacent unicorn** — whether the direction prompt accepts the unicorn’s map direction or `.`/`>` in all cases. **UNVERIFIED.**
