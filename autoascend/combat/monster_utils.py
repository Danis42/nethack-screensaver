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
    _, y, x, mon, _ = monster
    return mon.mmove > our_speed(agent)


def imminent_death_on_melee(agent, monster):
    _, y, x, mon, glyph = monster
    damage = threat.damage_per_turn(monster_index(glyph), getattr(mon, 'mlevel', 0), mon.mmove,
                                    agent.blstats.armor_class, our_speed(agent))
    return agent.blstats.hitpoints <= max(8, 2 * damage)


def is_dangerous_monster(monster):
    _, y, x, mon, glyph = monster
    if any(name in mon.mname for name in PET_NAMES):
        return True
    index = monster_index(glyph)
    return threat.has_special_attack(index) or \
        threat.damage_per_turn(index, getattr(mon, 'mlevel', 0), mon.mmove, 10) >= threat.DANGER_HP_PER_TURN


def consider_melee_only_ranged_if_hp_full(agent, monster):
    return monster[3].mname in ('brown mold', 'blue jelly') and agent.blstats.hitpoints == agent.blstats.max_hitpoints
