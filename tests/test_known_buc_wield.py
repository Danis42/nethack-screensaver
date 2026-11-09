"""Weapons are only switched to when their curse status is really known.

item_manager stores an unknown B/U/C as UNCURSED (it scores better elsewhere); a wielded cursed weapon welds.
Baseline 87e0af5: 46 of 2304 games end wielding a cursed weapon, mostly unidentified elven daggers and daggers.
"""
from types import SimpleNamespace

from autoascend.item import Item
from autoascend.item.inventory import Inventory


def _weapon(dps, buc_known=True, equipped=False):
    return SimpleNamespace(status=Item.UNCURSED, buc_known=buc_known, equipped=equipped, dps=dps,
                           is_weapon=lambda: True, is_container=lambda: False)


def _inventory():
    character = SimpleNamespace(role=None,
                                get_melee_bonus=lambda item, large_monster: (0, 0 if item is None else item.dps))
    inv = Inventory.__new__(Inventory)
    inv.agent = SimpleNamespace(character=character)
    return inv


def test_unknown_status_weapon_is_not_chosen(monkeypatch):
    import autoascend.item.inventory as module
    monkeypatch.setattr(module.utils, "calc_dps", lambda to_hit, dmg: dmg)
    spear = _weapon(5, equipped=True)
    dagger = _weapon(9, buc_known=False)
    assert _inventory().get_best_melee_weapon([spear, dagger]) is spear


def test_known_status_weapon_and_the_wielded_one_stay_allowed(monkeypatch):
    import autoascend.item.inventory as module
    monkeypatch.setattr(module.utils, "calc_dps", lambda to_hit, dmg: dmg)
    known = _weapon(9)
    wielded_unknown = _weapon(5, buc_known=False, equipped=True)
    assert _inventory().get_best_melee_weapon([wielded_unknown, known]) is known
    assert _inventory().get_best_melee_weapon([wielded_unknown]) is wielded_unknown


def test_artifact_of_unknown_status_is_chosen(monkeypatch):
    # altar gifts are always uncursed (5.0 pray.c bestow_artifact); dec417a: 41 Mjollnir carried, none wielded
    import autoascend.item.inventory as module
    monkeypatch.setattr(module.utils, "calc_dps", lambda to_hit, dmg: dmg)
    spear = _weapon(5, equipped=True)
    mjollnir = _weapon(17, buc_known=False)
    mjollnir.dmg_bonus = 12.5
    assert _inventory().get_best_melee_weapon([spear, mjollnir]) is mjollnir


def test_artifact_names_parse_to_their_base_weapon():
    from autoascend.item.item_manager import ItemManager
    for text, base in [('a war hammer named Mjollnir', 'war hammer'), ('a long sword named Frost Brand', 'long sword'),
                       ('a long sword named Giantslayer', 'long sword'), ('a silver saber named Grayswandir', 'silver saber'),
                       ('a silver mace named Demonbane', 'silver mace')]:
        parsed = ItemManager.parse_text(text)
        objs, dmg_bonus = parsed[0], parsed[10]
        assert [o.name for o in objs] == [base], text
        assert dmg_bonus is not None, text
