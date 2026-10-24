import nle.nethack as nh

from . import threat

# heuristic monster types lists
ONLY_RANGED_SLOW_MONSTERS = ['floating eye', 'blue jelly', 'brown mold', 'gas spore', 'acid blob']
EXPLODING_MONSTERS = ['yellow light', 'gas spore', 'flaming sphere', 'freezing sphere', 'shocking sphere']
INSECTS = ['giant ant', 'killer bee', 'soldier ant', 'fire ant', 'giant beetle', 'queen bee']
WEAK_MONSTERS = ['lichen', 'newt', 'shrieker', 'grid bug']
WEIRD_MONSTERS = ['leprechaun', 'nymph']


FAST_ROLES = (0, 5, 9)  # Character.ARCHEOLOGIST, MONK, SAMURAI: intrinsically Fast from turn 1
PET_NAMES = ('dog', 'cat', 'kitten', 'pony', 'horse')


def monster_index(glyph):
    """NLE monster index of a monster or pet glyph, -1 otherwise."""
    if nh.glyph_is_monster(glyph):
        return nh.glyph_to_mon(glyph)
    if nh.glyph_is_pet(glyph):
        return nh.glyph_to_pet(glyph)
    return -1


def our_speed(agent):
    return threat.FAST_SPEED if agent.character.role in FAST_ROLES else threat.BASE_SPEED


def is_monster_faster(agent, monster):
    # Upstream name list. Tried mmove > our speed (2026-10-21): soldier ants then counted
    # as faster, doubling their Elbereth weight, and ant deaths rose (35 -> 49 per 1152).
    _, y, x, mon, _ = monster
    return 'bat' in mon.mname or 'dog' in mon.mname or 'cat' in mon.mname \
           or 'kitten' in mon.mname or 'pony' in mon.mname or 'horse' in mon.mname \
           or 'bee' in mon.mname or 'fox' in mon.mname


def imminent_death_on_melee(agent, monster):
    # Upstream limits, now with the real danger test. Tried HP <= 2 x damage per turn
    # (2026-10-21): it broke off fights against fast monsters, rung2 -3.7 points at 1152.
    if is_dangerous_monster(monster):
        return agent.blstats.hitpoints <= 16
    return agent.blstats.hitpoints <= 8


def is_dangerous_monster(monster):
    _, y, x, mon, glyph = monster
    if any(name in mon.mname for name in PET_NAMES):
        return True
    index = monster_index(glyph)
    return threat.has_special_attack(index) or \
        threat.damage_per_turn(index, getattr(mon, 'mlevel', 0), mon.mmove, 10) >= threat.DANGER_HP_PER_TURN


def consider_melee_only_ranged_if_hp_full(agent, monster):
    return monster[3].mname in ('brown mold', 'blue jelly') and agent.blstats.hitpoints == agent.blstats.max_hitpoints
