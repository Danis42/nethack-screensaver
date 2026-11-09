# Research prompts for other agents (ChatGPT, Gemini, ...)

## How to use
1. Open a new chat per prompt (a web-search or "deep research" mode works best).
2. Copy the COMMON BLOCK below, then the prompt you want (R01-R16), into the chat.
3. Save the whole answer as a Markdown file in this folder: `<ID>-<agent>.md`, e.g. `R04-chatgpt.md`.
   Two agents on the same prompt are welcome (`R04-chatgpt.md`, `R04-gemini.md`).
4. Tell Claude "external results ready" (or name the files). Claude checks every claim against the local
   NetHack 5.0.0 source and wiki before using it; unverified claims are never built on.

Priority: A = needed for current work, B = next phases, C = late game, D = method.

---

## COMMON BLOCK (paste before every prompt)

```
Context: I am building an automated bot that plays NetHack 5.0.0 (released 2026-05-02). NetHack 5.0 descends
from the NetHack 3.7 development line, so 3.7 changes apply and NetHack 3.6 facts may be outdated. The bot
always plays a neutral human Valkyrie, aims for a real ascension, and runs in the NetHack Learning Environment
(terminal screen, status lines, inventory text). Research is turned into rules a Python program can follow.

Rules for your answer:
- Cite every fact: NetHack source (github.com/NetHack/NetHack, file + function or line; say 3.6, 3.7 or 5.0),
  a NetHackWiki page, or a named human game / dumplog. Say which version each fact is from.
- If you are not sure, or a fact may have changed in 3.7/5.0, write UNVERIFIED instead of guessing.
  Never invent numbers.
- Answer in this Markdown format:
  # <ID> <title>
  ## Summary            (at most 6 bullets)
  ## Facts              (table: claim | source | version | confidence high/medium/low)
  ## Bot rules          (each rule: Trigger = what a program can see: exact message text, status line,
                         map symbols, inventory text; Action = exact keys and prompt answers in order;
                         Done when; If it fails; Evidence)
  ## Risks and exceptions
  ## Open questions
```

---

## A. Needed now

### R01 Energy vortex and other fast passive monsters (A)
```
R01. Our bot dies to energy vortices (speed 20, passive shock when hit in melee, engulfs) and fire
elementals/fire vortices (passive fire). The hero is a neutral human Valkyrie, XL 6-14, usually without shock
resistance, carrying a long sword and a few daggers. How should a bot deal with these monsters: kill at range
(throwing daggers: how many hits needed), Elbereth (do vortices respect it in 5.0?), retreat, escape items,
what to do once engulfed (attack from inside? passive damage then?), and when melee is acceptable (HP thresholds,
passive damage formula). Also list every other NetHack 5.0 monster with a damaging passive and whether it is fast.
```

### R02 Unicorns: fight or avoid (A)
```
R02. Our bot (neutral human Valkyrie, XL 5-9, Dlvl 5-9) dies to white and black unicorns. In NetHack 5.0:
(1) do hostile unicorns come into melee range by themselves, or only when the hero closes in (monmove.c,
NOTONL, teleport-level differences such as Sokoban)? (2) Luck effects of killing co-aligned vs cross-aligned
unicorns; (3) throwing gems at unicorns (which gems, Luck changes, identification); (4) how experienced players
handle unicorns before the hero is strong; (5) the value of the unicorn horn and the safest way to get one.
Give concrete rules: when to fight, when to ignore, when to throw gems.
```

### R03 Mumak, leocrotta, owlbear, soldier ants (A)
```
R03. These are our bot's top killers at XL 6-9 on Dlvl 7-9 (counts in 1152 games: mumak 40, soldier ant 31,
owlbear 25, leocrotta 22). The hero is a neutral human Valkyrie with long sword, AC about -3, max HP 60-85,
intrinsically fast from XL 7. For each monster give speed, attacks, AC, and the safest tactic: walk away (speed
comparison with the "fast" intrinsic in 5.0 movement rules), fight on stairs and leave, Elbereth (and the "panic
attack" when a scared monster cannot flee), corridors, wands, prayer. When is melee acceptable? Exact HP
thresholds are welcome if sourced.
```

### R04 Sell-price identification in 5.0 shops (A)
```
R04. We want the bot to price-identify unknown scrolls by offering to sell them and declining. For NetHack 5.0:
(1) the exact dialog when dropping an item in a shop ("<shk> offers N gold pieces for your ... Sell it? [ynaq]")
and every variant (no gold: credit; not interested; "a sucker"); (2) the sell price formula and the 1/4 of
shopkeepers who pay less for unidentified items, any 3.7/5.0 changes in shk.c; (3) which shop types buy scrolls
(general store, bookstores) and which buy other classes; (4) dangers (angering the shopkeeper, items left on the
floor, pets stealing); (5) the shops in each Minetown variant of 5.0; (6) the same method for potions, rings,
wands, amulets: offer tables per base price. Output a step-by-step protocol a bot can follow.
```

### R05 Enchant armour and early armour sources (A)
```
R05. Our bot's AC stops at -3/-4 while human ascenders have about -6 at Dlvl 10, -10 at Dlvl 15 and -14 when
they reach Medusa; 79% of human ascenders read enchant armour about 3 times before Medusa. For NetHack 5.0:
(1) enchant armour rules: which worn piece gets it (some_armor), evaporation limits (+3 for most, +5 elven),
blessed vs uncursed vs cursed, confused reading; (2) which pieces to wear before reading; (3) where a Valkyrie
gets armour by Dlvl 10 (dwarvish mithril coats and iron helms from Mines dwarves, elven mithril, shops, other
monsters' drops), with rough chances; (4) other AC sources by Dlvl 15 (rings of protection, cloaks, shields).
Give a ranked list of the cheapest AC gains for a bot.
```

### R06 Priest protection and gold (A)
```
R06. Buying protection from temple priests in NetHack 5.0: exact donation formula and messages (priest.c),
cost per point by experience level, whether the priest must be co-aligned, the "cheapskate" effect, and how
many points humans usually buy. Our bot carries about 120 gold at Minetown (XL 8). Where do players get gold
early and mid game (selling, vaults, digging, leprechauns, gold detection), and what is realistic for a bot?
Is buying protection worth it for a bot compared with other uses of gold?
```

### R07 Read-testing scrolls and every scroll prompt (A)
```
R07. Our bot carries about 8 unknown scrolls by Dlvl 10 and never reads them. For NetHack 5.0: (1) community
best practice for read-testing unknown scrolls (when, where, what to take off first, BUC requirements);
(2) for EVERY scroll type: the message that identifies it when read, any prompt it asks (identify menu,
genocide, stinking cloud position, charging, blessed destroy armor's new "destroy which armor" prompt in 5.0,
teleport control, earth), and the best answer for a bot; (3) the effect of cursed and confused reading for each;
(4) how to live with or remove punishment (ball and chain); (5) frequency identification (identify is 18% of
scrolls). Output a decision table: scroll -> read now? -> prompt answers.
```

---

## B. Next phases

### R08 Avoiding starvation (B)
```
R08. Starvation ends 15.7% of our bot's games (many in the Gnomish Mines). For NetHack 5.0: how do players
keep enough food early (safe corpses list, corpse age limits, tins, lichen and lizard, buying food, praying when
Weak and the prayer timeout), what changed about food or hunger in 3.7/5.0, and simple rules for a bot that is
often far from food. Include which corpses are dangerous (poisonous, acidic, cannibalism, petrification) for a
human Valkyrie.
```

### R09 Medusa's Island in 5.0 (B)
```
R09. Medusa's level in NetHack 5.0 has four maps. For each map: layout, where the hero arrives, dry squares,
the down stairs, the doors (locked or not), Perseus' statue and its items, the special monsters (titan, kraken,
ravens, eels). Rank the ways to cross the water (levitation, water walking, freezing with a wand of cold,
boulders/scroll of earth, digging down) by reliability, and the ways to kill Medusa (reflection, blindfold,
cockatrice corpse). Note every 5.0 change compared with 3.6.
```

### R10 The Castle in 5.0 (B)
```
R10. The Castle (stronghold) in NetHack 5.0: crossing the moat, opening the drawbridge (passtune Mastermind
game: messages and how to solve it; force bolt / wand of striking; opening from the other side), the soldiers
and how to survive them, the chest with the wand of wishing, the trap doors to the Valley, sea monsters. Give
a safe step-by-step plan for a Valkyrie at XL 14 with reflection and levitation.
```

### R11 Valkyrie Quest in 5.0 (B)
```
R11. The Valkyrie Quest in NetHack 5.0: how the portal level is found (messages), entry requirements (XL 14,
alignment), the home level and leader, the locate and goal levels, Lord Surtur (attacks, resistances needed),
the artifact (Orb of Fate), and the Bell of Opening. What do players bring, and what changed from 3.6?
```

---

## C. Late game

### R12 Gehennom and the invocation (C)
```
R12. Gehennom in NetHack 5.0 for an automated player: navigating mazes, the special levels (Valley, Asmodeus,
Juiblex, Baalzebub, Orcus Town, the fake Wizard's towers, Vlad's Tower), getting the Candelabrum (Vlad) and the
Book of the Dead (Wizard), finding the vibrating square, the exact invocation ritual (items, order, candle
lighting, messages), and Moloch's Sanctum. Note every 3.7/5.0 change. Which dangers kill well-equipped players
most often there?
```

### R13 Elemental Planes and Astral (C)
```
R13. The Elemental Planes and the Astral Plane in NetHack 5.0: how each plane works (Earth, Air, Fire, Water;
the 3.7 changes to Water), finding the portal on each, what kills players there, and on Astral: finding the
co-aligned high altar, the Riders, the mysterious force on the way up. Give a bot-oriented checklist.
```

---

## D. Method

### R14 Survey of NetHack bots and agents (D)
```
R14. Survey every automated NetHack player you can find: BotHack (2015 ascension), AutoAscend (NetHack
Challenge 2021 winner), TAEB, Saiph, nethack_astra (2026 LLM ascension), BALROG/NetPlay and other LLM agents,
imitation-learning work on NLD (Dungeons and Data, later papers). For each: version played, best result,
the techniques that mattered most, and links. Which ideas could a rule-based Python bot copy?
```

### R15 LLM advisor at rare decision points (D)
```
R15. Design question: a rule-based NetHack bot plays every turn itself, and asks a large language model only at
rare critical moments (low HP deep in the dungeon, unknown dangerous monster, Medusa, the Castle). Find
published work or projects with this hybrid design (games or robotics), how they choose when to call the model,
what state they send (screen text, inventory, map), cost and latency per call, and how they keep results
reproducible for testing. Suggest a concrete prompt and state format for NetHack.
```

### R16 Valkyrie intrinsics and key-item timeline (D)
```
R16. For a human Valkyrie in NetHack 5.0: intrinsics by experience level (cold resistance, stealth, speed),
where and when players usually get poison resistance, telepathy, magic resistance, reflection, free action,
speed boots, levitation, and a pick-axe. Give a typical timeline by dungeon level for an ascending player, with
sources (dumplogs, wiki), and which items are must-haves before the Quest, Medusa and the Castle.
```
