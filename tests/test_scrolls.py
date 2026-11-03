from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.item import scrolls as S
from autoascend.item.item import Item

STATE = dict(impaired=False, worn_armor_mods=[0, 1], weapon_mod=0, cursed_equipped=False, unidentified=True)


def scroll(*names, status=Item.UNCURSED, shop=Item.NOT_SHOP):
    return SimpleNamespace(objs=[O.from_name(n, nh.SCROLL_CLASS) for n in names], category=nh.SCROLL_CLASS,
                           status=status, shop_status=shop)


def test_known_scrolls_by_need():
    assert S.should_read(scroll('enchant armor'), **STATE)
    assert not S.should_read(scroll('enchant armor'), **{**STATE, 'worn_armor_mods': [0, 4]})
    assert not S.should_read(scroll('enchant armor'), **{**STATE, 'worn_armor_mods': []})
    assert S.should_read(scroll('enchant weapon'), **STATE)
    assert not S.should_read(scroll('enchant weapon'), **{**STATE, 'weapon_mod': None})
    assert not S.should_read(scroll('remove curse'), **STATE)
    assert S.should_read(scroll('remove curse'), **{**STATE, 'cursed_equipped': True})
    assert not S.should_read(scroll('fire'), **STATE)


def test_never_confused_cursed_or_unpaid():
    assert not S.should_read(scroll('enchant armor'), **{**STATE, 'impaired': True})
    assert not S.should_read(scroll('enchant armor', status=Item.CURSED), **STATE)
    assert not S.should_read(scroll('enchant armor', shop=Item.UNPAID), **STATE)


def test_unknown_scrolls_only_in_safe_price_groups():
    assert S.should_read(scroll('enchant armor', 'remove curse'), **STATE)  # 80 zm
    assert not S.should_read(scroll('enchant armor', 'remove curse'), **{**STATE, 'worn_armor_mods': []})
    assert not S.should_read(scroll('teleportation', 'destroy armor', 'fire'), **STATE)  # 100 zm


def test_identify_menu_picks_rings_and_amulets_first():
    popup = ['What would you like to identify first?', 'Weapons', 'a - a +1 spear (weapon in right hand)',
             'Potions', 'f - a murky potion', 'Rings', 'g - an agate ring', '(end)']
    assert S.identify_choice(popup) == 'g'
    assert S.identify_choice(['What would you like to identify first?', '(end)']) is None
