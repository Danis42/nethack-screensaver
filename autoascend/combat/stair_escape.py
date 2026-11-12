"""Stair escape on deep levels: standing on the up stairs and losing a fight, go up, rest, come back.

Sources (NetHack 5.0.0):
- only adjacent monsters that are levl_follower() come along (dog.c keepdogs): pets and M2_STALK types that are not
  fleeing (mondata.c:1211). Most Medusa-level killers in staged runs are not stalkers (minotaur, dragons, ettin,
  xorn, titan, giants, displacer beast, mind flayers), so the stairs shed them; trolls, gremlins, devils and the
  Aleax do follow.
- humans arrive on Medusa's level by these stairs (dat/medusa-*.lua des.stair("up")) and use them to retreat.
Staged Medusa runs (2026-11-11, .planning/staged/): the hero went from full HP to dead in 2-3 turns against a summoned
minotaur + black dragon; the escape fires at half HP so there is still a turn to climb.
"""
M2_STALK = 0x01000000  # include/monflag.h:146  # fact:m2-stalk-flag-value
# fact:medusa-level-depth
MIN_DEPTH = 21  # Medusa's level and below (dungeon.lua: Medusa 21-24); natural play above stays unchanged
# fact:minotaur-not-a-stalker
HP_FRACTION = 0.5  # climb below half HP: two rounds of a minotaur (3d10, 3d10, 2d8) can take 50-76 HP each
REST_TO = 0.9  # rest on the level above until this share of max HP
REST_TURNS = 1500  # never rest longer than this in one go (hunger)


def is_stalker(permonst) -> bool:  # fact:stalkers-follow-on-stairs
    return bool(getattr(permonst, 'mflags2', 0) & M2_STALK)


REACH = 8  # walk back to up stairs at most this many steps away (staged seed 12: a displacer beast swapped the hero
# off the stairs on turn 2 of the fight; the hero is Fast, speed 15, most killers 9-15)


def should_escape(depth: int, stairs_distance, hp: int, max_hp: int, near_permonsts) -> bool:
    """True when the up stairs are within REACH (0 = standing on them), HP is low and climbing would leave at least
    one nearby hostile (adjacent when on the stairs) behind."""
    if depth < MIN_DEPTH or stairs_distance is None or stairs_distance > REACH or hp >= HP_FRACTION * max_hp:
        return False
    return any(not is_stalker(p) for p in near_permonsts)


def rest_done(hp: int, max_hp: int, rested: int, hostiles_seen: bool, weak: bool) -> bool:
    return hp >= REST_TO * max_hp or rested >= REST_TURNS or hostiles_seen or weak
