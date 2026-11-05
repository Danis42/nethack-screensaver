"""Telepathy from a floating eye (.planning/research/TELEPATHY-NH5.md).

Eating a floating eye corpse always grants intrinsic telepathy (eat.c:980, message eat.c:1075 "You feel a strange
mental acuity."). 95% of 199 human 5.0 ascensions end telepathic. Hitting a SEEN floating eye can paralyse the hero
for a long time; a blind hero is safe (uhitm.c passive gaze needs the hero to see). So: blindfold or towel on, attack
the eye, blindfold off, eat the corpse.
"""
TELEPATHY_MESSAGES = ("strange mental acuity", "in touch with the cosmos")
EYE = 'floating eye'


def eye_target(monsters, telepathic, has_blindfold):
    """(y, x) of the floating eye to kill for telepathy, or None.

    monsters: Agent.get_visible_monsters() tuples (distance, y, x, permonst, glyph). Only when nothing else hostile
    is in view: the hero is blind while it fights."""
    if telepathic or not has_blindfold:
        return None
    eyes = [m for m in monsters if m[3].mname == EYE]
    if not eyes or any(m[3].mname != EYE for m in monsters):
        return None
    _, y, x, _, _ = min(eyes, key=lambda m: m[0])
    return int(y), int(x)

# A corpse up to 50 turns old is never rotten: eat.c rottenfood rotted = age / (10 + rn2(20)), rotten above 5.
EYE_CORPSE_MAX_AGE = 50
OVERFULL_MESSAGE = "hard time getting all of it down"  # eat.c:3315, nutrition >= 1500


def may_eat_eye(hunger_state, overfull):
    """Eat a floating eye corpse now? Yes, even Satiated, unless the hero may be near 2000 nutrition.

    Choking needs nutrition >= 2000 and a meal started while Satiated (eat.c:3138/3297). The eye gives 10. The game
    warns at >= 1500 (OVERFULL_MESSAGE); `overfull` = that warning was seen since the hero was last below Satiated."""
    from .glyph import Hunger
    return not (hunger_state == Hunger.SATIATED and overfull)


def eye_corpse_squares(corpses_to_eat, eye_id, now):
    """Squares of the level's corpses_to_eat ({(y, x): {monster_id: kill turn}}) holding a fresh floating eye."""
    return [pos for pos, mapping in corpses_to_eat.items()
            if eye_id in mapping and now - mapping[eye_id] <= EYE_CORPSE_MAX_AGE]
