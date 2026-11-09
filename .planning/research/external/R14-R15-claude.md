# R14 bot survey and R15 LLM advisor (Claude review of the ChatGPT answers)

These are web topics; nothing in them can be checked against the game source.

## R14 (survey)
- Matches what we already know (memory 'Bot ascension references'): BotHack 2015 ascension (pudding farming, dead
  in 3.6), nethack_astra 2026-09 LLM ascension (lawful dwarvish Valkyrie, NetHack 3.6.7), AutoAscend won the
  2021 challenge without ascending (NetHack 3.6.6).
- New to us: TAEB bot index (Saiph reached the Castle, killed Medusa, finished the Quest: best pure-rules bot
  after BotHack); CodeHack 2026 paper (arxiv 2609.31076: LLM picks code skills; claims ~3x progress and -86 %
  cost). Not opened yet: read before relying on it.
- Ideas worth copying are already in our bot (AutoAscend base) except: Saiph's and BotHack's special-level
  solvers for Medusa/Castle, and BotHack's corpse-age tracking (see R08 rule 2).

## R15 (LLM advisor)
- Design advice is sound and fits our rules: bot plays every turn; model only at rare logged events; send structured
  state + screen text; accept only a whitelisted answer; cache answers by state hash so bench runs stay
  reproducible.
- Costs and latency: ChatGPT found no published numbers (marked UNVERIFIED). Nothing to build on yet.
- Parked: the owner's priority is the pilgrim route with a rule bot; an advisor needs its own decision.

## Links (from ChatGPT, not opened)
- github.com/krajj7/BotHack, github.com/canidae/saiph, taeb.github.io/bots.html,
  github.com/maciej-sypetkowski/autoascend, github.com/kenforthewin/nethack_astra,
  arxiv.org/abs/2403.00690 (NetPlay), arxiv.org/abs/2609.31076 (CodeHack), balrogai.com
