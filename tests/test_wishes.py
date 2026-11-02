from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.item import wishes as W


def item(name, category):
    return SimpleNamespace(objs=[O.from_name(name, category)], category=category, is_unambiguous=lambda: True)


def test_wishes_by_what_is_missing():
    assert W.next_wish([]) == W.WISH_MR
    kit = [item('cloak of magic resistance', nh.ARMOR_CLASS)]
    assert W.next_wish(kit) == W.WISH_REFLECTION
    kit.append(item('amulet of reflection', nh.AMULET_CLASS))
    assert W.next_wish(kit) == W.WISH_LEVITATION
    kit.append(item('levitation', nh.RING_CLASS))
    assert W.next_wish(kit) == W.WISH_DEFAULT


def test_shield_of_reflection_counts():
    kit = [item('gray dragon scale mail', nh.ARMOR_CLASS), item('shield of reflection', nh.ARMOR_CLASS)]
    assert W.next_wish(kit) == W.WISH_LEVITATION
