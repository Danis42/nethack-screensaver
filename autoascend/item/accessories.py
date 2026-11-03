"""Which rings and amulet to wear (Phase 02.2 Part 1a, plan decisions D-02 and D-03).

Only identified types are ever put on, and only types that do no harm when cursed: a cursed ring of slow
digestion still works, it just stays on. Unknown rings and amulets are never tried (teleportitis,
strangulation, levitation are among them). One ring hand stays free while a levitation item is carried, so the
levitation skill (Part 1b) can put it on."""

from autoascend.item.item import Item

# Best first. Value: what the route needs most (WIKI ring/amulet pages, ASCENSION-PLAN-NH5.md).
RING_RANK = (
    'slow digestion',  # starvation is the top killer; the ring stops hunger nearly completely
    'free action',  # paralysis is death deep down
    'poison resistance',
    'fire resistance',
    'cold resistance',
    'shock resistance',
    'see invisible',
    'sustain ability',
)
CHARGED_RINGS = ('protection', 'increase damage', 'increase accuracy')  # only with a known enchantment >= +1
AMULET_RANK = (
    'amulet of life saving',
    'amulet of reflection',
    'amulet of ESP',
    'amulet versus poison',
    'amulet of guarding',
    'amulet of magical breathing',
)


def _name(item):
    return item.objs[0].name if item.is_unambiguous() else None


def ring_value(item):
    """Higher is better; None means never put this ring on."""
    name = _name(item)
    if name is None:
        return None
    if name in RING_RANK:
        return len(RING_RANK) - RING_RANK.index(name) + 10
    if name in CHARGED_RINGS and item.modifier is not None and item.modifier >= 1 and item.status != Item.CURSED:
        return item.modifier
    return None


def amulet_value(item, reflection_elsewhere=False):
    name = _name(item)
    if name is None or name not in AMULET_RANK:
        return None
    if name == 'amulet of reflection' and reflection_elsewhere:
        return 0
    return len(AMULET_RANK) - AMULET_RANK.index(name)


def best_accessories(items, *, reflection_elsewhere=False, keep_hand_free=False):
    """(amulet or None, list of up to two rings) to wear. Worn cursed ones stay: they cannot come off."""
    rings = [i for i in items if i.category == RING_CLASS]
    amulets = [i for i in items if i.category == AMULET_CLASS]

    stuck_rings = [r for r in rings if r.equipped and r.status == Item.CURSED]
    candidates = [(ring_value(r), r) for r in rings if r not in stuck_rings and ring_value(r) is not None]
    candidates.sort(key=lambda vr: -vr[0])
    hands = 2 - (1 if keep_hand_free else 0)
    chosen = stuck_rings + [r for _, r in candidates]
    chosen = chosen[:max(hands, len(stuck_rings))]

    stuck_amulet = next((a for a in amulets if a.equipped and a.status == Item.CURSED), None)
    if stuck_amulet is not None:
        return stuck_amulet, chosen
    scored = [(amulet_value(a, reflection_elsewhere), a) for a in amulets]
    scored = [(v, a) for v, a in scored if v is not None and v > 0]
    amulet = max(scored, key=lambda va: va[0])[1] if scored else None
    return amulet, chosen


RING_CLASS = 4  # nh.RING_CLASS / nh.AMULET_CLASS (kept literal so the ranking imports without NLE)
AMULET_CLASS = 5


# Armour by property (D-04): worth this many points of AC on top of its own AC.
_ANTIMAGIC, _REFLECTING, _FAST = 12, 65, 64  # prop numbers in autoascend/objects/data.py
ARMOR_BONUS_BY_POWER = {_ANTIMAGIC: 10, _REFLECTING: 8, _FAST: 5}
ARMOR_BONUS_BY_NAME = {'gauntlets of power': 3, 'oilskin cloak': 2, 'helm of telepathy': 1,
                       'cloak of displacement': 1, 'elven cloak': 1, 'water walking boots': 1}
NEVER_WEAR = frozenset({'levitation boots', 'fumble boots', 'gauntlets of fumbling', 'helm of opposite alignment',
                        'dunce cap'})


def armor_bonus(obj):
    return ARMOR_BONUS_BY_POWER.get(obj.power, 0) + ARMOR_BONUS_BY_NAME.get(obj.name, 0)


def never_wear(obj):
    return obj.name in NEVER_WEAR
