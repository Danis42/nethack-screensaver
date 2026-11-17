"""Hostile unicorns below XL 10: never walk up to one (plan 04-02).

A unicorn that sees the hero never steps onto a square in line with the hero, and adjacent squares are in line
(# fact:unicorn-avoids-hero-line), so melee with one only starts when the hero walks up to it. In job 23 the Monk
died to unicorns at XL 5-9 by doing exactly that. A co-aligned unicorn is peaceful (# fact:unicorn-coaligned-peaceful)
and never reaches this module: Agent.get_visible_monsters drops peaceful monsters. From XL 10 the bot engages as
before, as every human Monk winner kills cross-aligned unicorns for the horn (04-MONK-HUMAN-STUDY.md).

Once adjacent (a unicorn unseen in a dark corridor), the bot fights as before: the unicorn attacks twice a turn anyway,
and in replays of job 23 deaths a step away only led the bot's route straight back into it (seed 7432)."""

ENGAGE_XL = 10


def avoided(agent, mon):
    """A hostile unicorn the bot keeps away from (callers pass only hostile monsters)."""
    return 'unicorn' in getattr(mon, 'mname', '') and agent.blstats.experience_level < ENGAGE_XL
