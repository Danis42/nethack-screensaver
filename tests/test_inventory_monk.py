from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.character import Character
from autoascend.item import Item
from autoascend.item.inventory import Inventory


def _armor(name):
    obj = O.from_name(name, nh.ARMOR_CLASS)
    glyph = O.objects.index(obj) + nh.GLYPH_OBJ_OFF
    return Item([obj], [glyph], status=Item.UNCURSED, modifier=0)


def _best(role, items):
    me = SimpleNamespace(agent=SimpleNamespace(character=SimpleNamespace(role=role)))
    return Inventory.get_best_armorset(me, items)


def test_a_monk_never_chooses_a_shield_or_body_armour():
    items = [_armor('elven shield'), _armor('leather armor'), _armor('orcish helm')]
    best = _best(Character.MONK, items)
    assert best[O.ARM_SHIELD] is None and best[O.ARM_SUIT] is None
    assert best[O.ARM_HELM] is items[2]


def test_other_roles_still_choose_a_shield():
    items = [_armor('elven shield'), _armor('leather armor')]
    best = _best(Character.VALKYRIE, items)
    assert best[O.ARM_SHIELD] is items[0] and best[O.ARM_SUIT] is items[1]
