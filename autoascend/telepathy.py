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
