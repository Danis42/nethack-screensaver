# Flee upstairs from fast insects (sub-project 1, step 2) — design

Date: 2026-10-21. The user delegated the details; the bench decides.

## Evidence

Human NetHack 3.6 games on nethack.alt.org (NetHack Learning Dataset, part `aa`, 7,726
games that reached Dlvl 4+; spike script, not kept): in 827 games a soldier ant came within
3 squares. Of the 145 players it killed, 6% went upstairs in the 400 frames after first
seeing it; of the 682 who survived it, 31% did. Elbereth made no difference (15% vs 16%).
In our baseline (1152 games of `2653410`) soldier, fire and giant ants and killer bees kill
about 9% of all games.

## Rule

During a fight (`Agent.fight2`), when a **fast insect** — soldier ant, fire ant, giant ant,
killer bee — is visible within 6 squares (bot distance as in `get_visible_monsters`):

- standing on an up staircase: climb it (action `flee_up`), priority 50 — above melee
  (≈16), Elbereth and every move;
- else, an up staircase on this level reachable within 8 steps: take one step along the
  path to it (action `flee_to`), priority 40, but only when the next square holds no
  monster (otherwise no flee action this turn).

Never on Dlvl 1 of the Dungeons of Doom (going up there leaves the dungeon and ends the
game), never in Sokoban (its up stairs lead on into the puzzle) and never outside the
Dungeons of Doom and the Gnomish Mines. After fleeing from a level, no new flee from that
same level for 150 turns, so the bot does not bounce between two levels.

Each climb is counted (`flee_upstairs` stat, `GameResult.flee_upstairs`).

## Measurement

One experiment, candidate vs `2653410`, metric `rung2`; also watch the ant + bee death
counts. Merge only on a measured gain.

## Testing

Unit tests of the decision function with a fake agent: on stairs with a soldier ant near →
`flee_up`; two steps away → `flee_to` with the first step; ant 8 squares away → nothing;
Dlvl 1, Sokoban, cooldown → nothing; next square occupied → nothing; a newt → nothing.
`action_str` prints both new actions. Whole suite before and after.
