"""What to wish for (Phase 02.2 Part 1a, plan decision D-07; WISHES-NH5.md).

By what the hero is missing: magic resistance, reflection, levitation, then blessed potions of gain level
(levels to XL 14 for the Quest). The Castle-specific order (gain level first) is Part 1c."""

_ANTIMAGIC, _REFLECTING, _LEVITATION = 12, 65, 48  # prop numbers in autoascend/objects/data.py

WISH_MR = 'blessed greased fixed +2 gray dragon scale mail'
WISH_REFLECTION = 'blessed fixed amulet of reflection'
WISH_LEVITATION = 'blessed ring of levitation'
WISH_DEFAULT = '2 blessed potions of gain level'


def _powers(items):
    out = set()
    for item in items:
        if not item.is_unambiguous():
            continue
        obj = item.objs[0]
        power = getattr(obj, 'power', None)
        if power is not None:
            out.add(power)
        if obj.name == 'amulet of reflection':
            out.add(_REFLECTING)
        if obj.name in ('levitation',) and item.category == 4:
            out.add(_LEVITATION)
    return out


def next_wish(items):
    have = _powers(items)
    if _ANTIMAGIC not in have:
        return WISH_MR
    if _REFLECTING not in have:
        return WISH_REFLECTION
    if _LEVITATION not in have:
        return WISH_LEVITATION
    return WISH_DEFAULT
