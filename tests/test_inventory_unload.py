from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.item import Item
from autoascend.item.inventory import items_to_unload, prying_blade


def _item(name, weight, category=nh.TOOL_CLASS, equipped=False, droppable=True):
    return SimpleNamespace(name=name, category=category, equipped=equipped,
                           weight=lambda: weight, can_be_dropped_from_inventory=lambda: droppable)


def test_unload_drops_heaviest_spare_items_first_and_food_last():
    food = _item("food ration", 20, category=nh.FOOD_CLASS)
    apple = _item("apple", 2, category=nh.FOOD_CLASS)
    box = _item("pick-axe", 100)
    rock = _item("rocks", 300, category=nh.ROCK_CLASS)
    wand = _item("wand", 7, category=nh.WAND_CLASS)
    sword = _item("long sword", 40, category=nh.WEAPON_CLASS, equipped=True)
    stone = _item("loadstone", 500, category=nh.ROCK_CLASS, droppable=False)

    order = items_to_unload([food, apple, box, rock, wand, sword, stone], keep=[food])

    assert [i.name for i in order] == ["rocks", "pick-axe", "wand", "apple"]


def _weapon(name, status=Item.UNCURSED):
    return SimpleNamespace(object=O.from_name(name), status=status, is_weapon=lambda: True,
                           is_unambiguous=lambda: True)


def test_prying_blade_prefers_the_dagger():
    dagger = _weapon('dagger')
    assert prying_blade([_weapon('long sword'), dagger, _weapon('spear')]) is dagger


def test_prying_blade_skips_cursed_and_non_blades():
    assert prying_blade([_weapon('dagger', Item.CURSED), _weapon('spear'), _weapon('dwarvish mattock')]) is None
