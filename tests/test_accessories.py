from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.item import accessories as acc
from autoascend.item.item import Item


def _item(name, category, *, equipped=False, status=Item.UNCURSED, modifier=None, known=True):
    obj = O.from_name(name, category=category)
    objs = [obj] if known else [obj, O.from_name('teleportation', nh.RING_CLASS)]
    return SimpleNamespace(objs=objs, category=category, equipped=equipped,
                           status=status, modifier=modifier, is_unambiguous=lambda: known)


def ring(name, **kw):
    return _item(name, acc.RING_CLASS, **kw)


def amulet(name, **kw):
    return _item(name, acc.AMULET_CLASS, **kw)


def test_ranks_rings_and_skips_harmful_ones():
    items = [ring('teleportation'), ring('free action'), ring('slow digestion'), ring('hunger')]
    amu, rings = acc.best_accessories(items)
    assert amu is None
    assert [r.objs[0].name for r in rings] == ['slow digestion', 'free action']


def test_unknown_rings_are_never_worn():
    assert acc.ring_value(ring('slow digestion', known=False)) is None


def test_charged_rings_need_a_known_positive_enchantment():
    assert acc.ring_value(ring('protection', modifier=None)) is None
    assert acc.ring_value(ring('protection', modifier=-1)) is None
    assert acc.ring_value(ring('protection', modifier=2)) == 2


def test_keeps_a_hand_free_for_levitation():
    items = [ring('free action'), ring('slow digestion')]
    _, rings = acc.best_accessories(items, keep_hand_free=True)
    assert [r.objs[0].name for r in rings] == ['slow digestion']


def test_cursed_worn_ring_stays_and_counts():
    stuck = ring('poison resistance', equipped=True, status=Item.CURSED)
    _, rings = acc.best_accessories([stuck, ring('free action'), ring('slow digestion')])
    assert rings[0] is stuck and len(rings) == 2


def test_amulets():
    ls, refl, strang = amulet('amulet of life saving'), amulet('amulet of reflection'), \
        amulet('amulet of strangulation')
    assert acc.best_accessories([refl, strang])[0] is refl
    assert acc.best_accessories([refl, ls])[0] is ls
    assert acc.best_accessories([refl], reflection_elsewhere=True)[0] is None
    assert acc.best_accessories([strang])[0] is None


def test_armour_by_property():
    assert acc.armor_bonus(O.from_name('cloak of magic resistance')) == 10
    assert acc.armor_bonus(O.from_name('shield of reflection')) == 8
    assert acc.armor_bonus(O.from_name('speed boots')) == 5
    assert acc.armor_bonus(O.from_name('leather cloak')) == 0
    assert acc.never_wear(O.from_name('levitation boots')) and acc.never_wear(O.from_name('fumble boots'))
