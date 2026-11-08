# R15 LLM advisor at rare decision points

## Summary

- NetPlay is the closest published NetHack precedent for event-triggered model intervention: the LLM chooses among predefined skills, and the controller interrupts a running skill when important game events occur. Its published results are shallow and include no ascension. [NetPlay](https://arxiv.org/abs/2403.00690).
- CodeHack (2026) is the strongest recent architectural precedent for keeping routine actions in code and using an LLM to choose reusable skills at control boundaries. The paper reports nearly 3x game progression and 86% lower estimated inference cost per episode versus primitive-only prompting. [CodeHack](https://arxiv.org/abs/2609.31076).
- Robotics work supports closed-loop feedback and replanning after unexpected outcomes, but those systems are analogies—not NetHack evaluations. [Inner Monologue](https://arxiv.org/abs/2207.05608); [DEPS](https://arxiv.org/abs/2302.01560).
- A practical design is: a deterministic Python policy owns every game turn; call the LLM only on a small set of logged, high-risk events; provide structured state plus exact screen/messages; accept only a whitelisted recommendation, never arbitrary keystrokes.
- Published latency and per-call USD costs for NetPlay and `nethack_astra` are **UNVERIFIED**. CodeHack reports estimated cost per episode, not latency or actual billing per call.
- Deterministic testing should replay cached model responses keyed by state/prompt hash, pin the model and decoding configuration where possible, validate strict JSON, and re-check game state before any action is executed.

## Facts

| claim | source | version | confidence high/medium/low |
|---|---|---|---|
| NetPlay is a zero-shot LLM agent for NetHack. It prompts a model to select from predefined skills and uses an event detector to interrupt running skills when the environment changes. | [Jeurissen et al., “Playing NetHack with LLMs”](https://arxiv.org/abs/2403.00690) | NLE-based NetHack experiment; exact engine build / NLE tag **UNVERIFIED**. | high |
| NetPlay's prompt context includes task and skill descriptions, current observations and recent interaction history. The paper's observation representation includes level structure, rooms/corridors, objects and positions, inventory, stats and context. | [NetPlay paper](https://arxiv.org/abs/2403.00690) | Same experiment; engine build **UNVERIFIED**. | high |
| NetPlay triggers interrupts on salient changes such as new messages, status/health changes, level transitions/teleportation, new structures, monsters or objects. Skills terminate or are reconsidered when the event handler signals an interruption. | [NetPlay paper](https://arxiv.org/abs/2403.00690) | Same experiment; engine build **UNVERIFIED**. | high |
| The NetPlay experiments used GPT-4 Turbo (`gpt-4-1106-preview`), temperature 0, JSON-formatted output, a short-term memory budget described as 500 tokens, and a timeout rule after repeated calls without in-game progress. | [NetPlay paper](https://arxiv.org/abs/2403.00690) | Paper's 2024 experiment; exact API endpoint behavior since then **UNVERIFIED**. | high |
| NetPlay did not demonstrate ascension. Reported scores and depths remained shallow compared with AutoAscend; the authors discuss timeout loops, stale state, combat/attitude errors and insufficient feedback. | [NetPlay paper](https://arxiv.org/abs/2403.00690) | Same NLE experiment; exact build **UNVERIFIED**. | high |
| NetPlay paper does not report a reproducible per-call wall-clock latency or a per-call USD price. | [NetPlay paper](https://arxiv.org/abs/2403.00690) | 2024 publication. | high |
| CodeHack separates semantic skill selection from low-level execution: code-based skills handle recurring local choices while the LLM picks/composes skills; primitive actions remain available when an abstraction is insufficient. | [Cupiał et al., “Up and Down the Abstraction Ladder”](https://arxiv.org/abs/2609.31076) | NLE-based NetHack tests; exact engine build **UNVERIFIED**. Published 2026-09-25. | high |
| CodeHack's reported zero-shot averages across its evaluated models are: primitive-only $4.35 ± $3.56, mixed $1.36 ± $1.04, skill-only $0.59 ± $0.45 estimated cost per episode; token usage is 6.72M, 3.54M and 1.74M per episode respectively. | [CodeHack paper, zero-shot results table](https://arxiv.org/abs/2609.31076) | NLE-based; model/provider price assumptions in the paper, not a universal retail price. | high |
| CodeHack reports skill control improves average progression from 0.69 to 1.98 and reduces estimated inference cost per episode by 86% relative to primitive-only control. | [CodeHack paper](https://arxiv.org/abs/2609.31076) | Same experiment; engine build **UNVERIFIED**. | high |
| CodeHack's reported cost figures are episode-level estimates across a model set; the paper does not establish a general per-call latency guarantee. | [CodeHack paper](https://arxiv.org/abs/2609.31076) | 2026 study. | high |
| Inner Monologue shows language-model planners can use feedback such as scene descriptions and success detection to improve closed-loop robotic instruction completion; it supports event feedback and retry logic as an architecture analogy. | [Huang et al., “Inner Monologue”](https://arxiv.org/abs/2207.05608) | Robotics experiments (2022), not NetHack. | high |
| DEPS integrates execution descriptions and explanations of failure into plan correction, and selects feasible subgoals; its benchmark focus is Minecraft/embodied environments, not NetHack. | [Wang et al., “Describe, Explain, Plan and Select”](https://arxiv.org/abs/2302.01560) | Minecraft/ALFWorld/tabletop, not NetHack. | high |
| `nethack_astra` demonstrates LLM-driven remote-terminal NetHack play with a run transcript/audit/checkpoint harness and a reported ascension, but its author reports the game as NetHack 3.6.7. | [Project repository](https://github.com/kenforthewin/nethack_astra); [ascension report](https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/) | NetHack 3.6.7, lawful dwarf Valkyrie; not 5.0.0. | high |
| The public `nethack_astra` report does not establish per-call price or latency suitable for projecting a NetHack 5.0.0 advisor budget. | [Project report](https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/) | NetHack 3.6.7 experiment. | medium |

## Bot rules

The thresholds and trigger list below are proposed engineering policy, not values validated by the cited studies. Tune them from seeded 5.0.0 rollouts; do not mistake them for NetHack mechanics.

1. **LLM call gate: emergency state**
   - **Trigger =** Parsed status has `HP <= configured_fraction * MaxHP` (initial engineering candidate: `0.35`), or deterministic damage model predicts a lethal hit before the next safe action; alternatively a fatal-condition field such as `Stone`, `Slimed`, `Strngl`, `FoodPois` or `TermIll` is present. `#attributes` (`^X`) can expose full status information in the 5.0.0 Guidebook.
   - **Action =** Do not give the model control of the terminal. Freeze the normal strategy; send one advisor request with current state and the allowed choices `HEAL_NOW`, `RETREAT_TO_STAIRS`, `ESCAPE_SPECIAL`, `USE_RESISTANCE_PLAN`, `CONTINUE_RULES`, `ABSTAIN`. Validate the JSON; execute only a locally implemented action whose preconditions are true.
   - **Done when =** HP/fatal-state danger is cleared or the local controller has selected a safe retreat/healing plan.
   - **If it fails =** Ignore invalid/unavailable output; execute the deterministic emergency policy. Do not spend multiple calls in the same unchanged emergency state.
   - **Evidence =** NetPlay event-triggered skill interruption and the 5.0.0 Guidebook status/`^X` fields. [NetPlay](https://arxiv.org/abs/2403.00690); [Guidebook](https://nethack.org/v500/Guidebook.html).

2. **LLM call gate: unknown high-threat monster**
   - **Trigger =** The map parser sees a hostile monster glyph not confidently mapped to a species, or a known species whose attack can cause an unhandled fatal condition; retain exact current message text, species-identification evidence, coordinates, attitude and distance.
   - **Action =** Send `IDENTIFY_THREAT`, `AVOID`, `ENGAGE_WITH_PLAN`, `RETREAT_TO_STAIRS` or `ABSTAIN`; include no invented species name. The local rules engine must independently enforce range, line-of-sight, reflection/resistance and safe-square checks before acting.
   - **Done when =** The monster is classified from observed evidence or the bot is out of its threat envelope.
   - **If it fails =** Treat it as unknown-dangerous; do not approach or attack solely because the model says it is safe.
   - **Evidence =** NetPlay's context-rich event reaction; BotHack's FarLook/monster disambiguation architecture. [NetPlay](https://arxiv.org/abs/2403.00690); [BotHack](https://github.com/krajj7/BotHack).

3. **LLM call gate: special-level planning**
   - **Trigger =** A confirmed special-level transition or level recognizer fires for Medusa's Island, the Quest, Castle, Valley, Gehennom/Invocation, or Astral; the recognizer must provide a confidence and map signature, not a guessed name.
   - **Action =** Send a compact map and objective question. Permit only `FOLLOW_SPECIAL_LEVEL_SOLVER`, `RETREAT_TO_ENTRY`, `REPOSITION_TO_SAFE_TILE`, `CHECK_REQUIRED_GEAR`, `ABSTAIN`. The existing deterministic level solver owns all movement, puzzle and combat actions.
   - **Done when =** The level solver reaches a validated stair/portal/objective or returns an explicit blocked result.
   - **If it fails =** Roll back to the map parser's latest known-good state and use deterministic exploration/escape; never accept blind movement sequences from the model.
   - **Evidence =** AutoAscend's special-purpose Sokoban/branch strategies and NetPlay's skill-boundary control. [AutoAscend](https://github.com/maciej-sypetkowski/autoascend); [NetPlay](https://arxiv.org/abs/2403.00690).

4. **LLM call gate: planner deadlock or repeated no-progress**
   - **Trigger =** The same high-level objective is attempted and rejected a configured number of times, or a progress counter (turn, position, floor, inventory, objective) shows no change after a configured action budget. These counts are configuration values, not game facts.
   - **Action =** Send previous actions/results, current screen/map and the failed goal; choose only among `REPLAN_OBJECTIVE`, `CHANGE_ROUTE`, `RECLASSIFY_BLOCKER`, `ABSTAIN`.
   - **Done when =** A new objective is accepted by the deterministic scheduler and its preconditions pass.
   - **If it fails =** Mark the goal blocked and switch to an independent deterministic goal; cap advisor calls per state hash.
   - **Evidence =** NetPlay reports timeout/no-progress problems; Inner Monologue and DEPS support feedback-driven replanning in robotics/Minecraft. [NetPlay](https://arxiv.org/abs/2403.00690); [Inner Monologue](https://arxiv.org/abs/2207.05608); [DEPS](https://arxiv.org/abs/2302.01560).

5. **Model output contract and execution firewall**
   - **Trigger =** Any advisor request.
   - **Action =** Request a single strict JSON object with `choice`, `confidence`, `evidence_refs`, `preconditions`, `stop_conditions`, `abstain_reason`. Require `choice` to be a member of an enumerated policy list. Reject arbitrary key sequences, raw extended commands, unobserved facts, wishes, and unbounded action plans. The local rule engine converts an accepted choice into keys using its own tested policy.
   - **Done when =** JSON schema, allowed choice, evidence references, preconditions and current-state hash all validate.
   - **If it fails =** Discard response and continue deterministic policy; log the raw response for debugging.
   - **Evidence =** NetPlay uses predefined skills and JSON output; CodeHack uses code-defined skills rather than unrestricted primitive action prediction. [NetPlay](https://arxiv.org/abs/2403.00690); [CodeHack](https://arxiv.org/abs/2609.31076).

6. **Reproducible advisor audit**
   - **Trigger =** Before and after every API call, and in every test replay.
   - **Action =** Persist JSONL with episode/seed, NetHack and NLE build IDs, bot commit, turn, state hash, previous hash, exact prompt hash/text, model identifier/revision, provider/API version, decoding parameters, tool schema, raw response, token counts, latency measurement, validator result, selected rule and resulting game action. Cache response by `(model_revision, prompt_hash, state_hash, schema_version)` and replay the exact cached response during regression tests.
   - **Done when =** The full decision can be reconstructed from the audit log and replay fixtures produce identical local actions.
   - **If it fails =** Do not compare fresh non-deterministic generations as if they were deterministic; run with recorded response cassettes. If the provider supports a seed, log and pin it, but still retain the raw response.
   - **Evidence =** `nethack_astra`'s transcript/audit/checkpoint approach and the event/action feedback loops in NetPlay. [nethack_astra](https://github.com/kenforthewin/nethack_astra); [NetPlay](https://arxiv.org/abs/2403.00690).

### Proposed NetHack advisor prompt

Use this as a starting prompt template; the `state` object should be serialized separately and its values must come from the bot's observation parser.

```text
SYSTEM
You are a tactical advisor for a deterministic NetHack 5.0.0 neutral human Valkyrie ascension bot.
You do not control the terminal. You may only recommend one policy identifier from the allow-list.
Treat the supplied state as authoritative. Do not infer unseen map tiles, unknown item identities,
monster species, resistances, charges, or prompt answers. If evidence is incomplete, abstain.
Do not output keystrokes, extended commands, wishes, free-form scripts, or a multi-turn plan.
Return exactly one JSON object matching this schema:
{
  "choice": "HEAL_NOW | RETREAT_TO_STAIRS | AVOID | ENGAGE_WITH_PLAN | CHECK_REQUIRED_GEAR | FOLLOW_SPECIAL_LEVEL_SOLVER | REPLAN_OBJECTIVE | CONTINUE_RULES | ABSTAIN",
  "confidence": 0.0,
  "evidence_refs": ["state.path.or.message_id"],
  "preconditions": ["facts that must be true before the local bot executes"],
  "stop_conditions": ["observable conditions that end the recommended policy"],
  "abstain_reason": "empty unless choice is ABSTAIN",
  "reason": "brief, evidence-grounded explanation"
}

USER
Decision question: {one specific tactical question}
Allowed policy identifiers: {the exact subset allowed for this event}
State: {JSON state object}

Rules:
- Prefer CONTINUE_RULES when the deterministic policy already has a safe action.
- Prefer ABSTAIN rather than guessing.
- Cite each recommendation with evidence_refs that point to fields in State.
- Do not recommend an action whose preconditions are false or unknown.
```

### Suggested state payload

```json
{
  "schema": "nethack-advisor-state-v1",
  "engine": {"name": "NetHack", "version": "5.0.0", "build_hash": "...", "nle_version": "..."},
  "episode": {"id": "...", "seed": "...", "turn": 0, "bot_commit": "..."},
  "character": {
    "role": "Valkyrie", "race": "human", "alignment": "neutral",
    "experience_level": 0, "dungeon_branch": "...", "dungeon_level": "...",
    "hp": 0, "max_hp": 0, "pw": 0, "max_pw": 0, "ac": 0,
    "attributes": {}, "alignment_record": null, "hunger": "...",
    "encumbrance": "...", "statuses": [], "intrinsics_confirmed": [],
    "extrinsics_confirmed": []
  },
  "terminal": {
    "geometry": [24, 80], "raw_screen_lines": [],
    "current_message": "...", "message_history": [],
    "prompt_kind": "game|more|menu|direction|yes_no|text|unknown",
    "prompt_text_exact": "..."
  },
  "map": {
    "ascii": [], "player_xy": [0, 0], "visible_cells": [],
    "known_stairs": [], "known_portals": [], "known_traps": [],
    "known_doors": [], "known_altars": [], "known_shops": [],
    "known_water": [], "unknown_frontiers": [], "map_confidence": "..."
  },
  "monsters": [
    {"glyph": "...", "species": null, "species_confidence": 0.0,
     "attitude": "hostile|peaceful|tame|unknown", "xy": [0, 0],
     "last_seen_turn": 0, "distance": null, "line_of_sight": null,
     "observed_threat_facts": []}
  ],
  "inventory": [
    {"letter": "a", "printed_name_exact": "...", "quantity": 1,
     "buc": "blessed|uncursed|cursed|unknown", "identified": false,
     "charges": null, "erosion": null, "worn_slot": null,
     "wielded": false, "known_properties": [], "evidence": []}
  ],
  "recent_actions": [{"turn": 0, "key": "...", "prompt_answer": "...", "result_message": "..."}],
  "active_rule_candidates": [],
  "advisor_event": {"kind": "...", "description": "..."}
}
```

`null` means unknown—not zero, false, or absent. Include only currently visible map cells and explicitly remembered cells with their age/confidence; do not send a fabricated complete map. Store the raw screen/message alongside normalized fields so parser mistakes can be diagnosed. NetPlay and CodeHack both use structured/text context rather than a bare screenshot or a single current message. [NetPlay](https://arxiv.org/abs/2403.00690); [CodeHack](https://arxiv.org/abs/2609.31076).

## Risks and exceptions

- Model advice is not a game mechanic oracle. It may hallucinate an item's identity, misunderstand a message, assume a line of sight, or recommend a valid action in an invalid prompt state. The local state parser and action validator must be authoritative.
- A state hash only makes a call cacheable if canonical serialization is stable. Include the exact screen, messages, inventory letters, branch/depth, turn, model version and prompt/schema version in the hash; do not include nondeterministic wall-clock timestamps.
- Temperature 0 does not guarantee bit-for-bit reproducibility across provider model revisions, backend updates or sampling implementations. Pin a revision if possible; store the raw response and replay it in tests.
- Do not send every turn to an LLM. That recreates NetPlay's inference overhead and makes the policy sensitive to model outages. Keep deterministic defaults and use a per-event cooldown/cache.
- CodeHack's per-episode dollar amounts depend on its evaluated models and provider pricing assumptions. They are not an estimate of your exact production spend. NetPlay's exact per-call latency/cost and `nethack_astra`'s exact per-call cost/latency are **UNVERIFIED**.
- A rare advisor call can still create a dangerous delay if the game clock continues while the API request is pending. Determine from the NLE wrapper whether the game is paused between actions; never assume it is. If a request requires action to proceed, use deterministic emergency rules first.
- Do not expose secrets, API credentials, server passwords, personal data or unnecessary full logs in prompts. Strip unrelated content before any external model call.

## Open questions

- What are the actual measured p50/p95 model latency and API cost for the chosen provider/model on the bot's deployment hardware/network?
- Does the target NLE 5.0.0 wrapper pause game time during an advisor call, or can monster turns advance while the bot waits?
- Which exact state fields are already exposed by the NLE observation API versus requiring reconstruction from terminal text?
- What trigger thresholds minimize ascension-risk while keeping calls rare? This needs a seeded ablation: no-advisor, all-event, threshold-only, and critical-event-only.
- Can the advisor be trained/evaluated on NLD-style offline trajectories while preserving the same strict policy allow-list and runtime validation?
