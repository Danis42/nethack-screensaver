from types import SimpleNamespace

import nle.nethack as nh

from autoascend import objects as O
from autoascend.agent import dig_down_tool


def _item(obj, known=True):
    return SimpleNamespace(object=obj, is_unambiguous=lambda: known)


WAND = O.from_name('digging', nh.WAND_CLASS)
PICK = O.from_name('pick-axe')


def test_a_known_wand_of_digging_is_preferred():
    items = [_item(PICK), _item(WAND)]
    assert dig_down_tool(items, slow_ok=True).object is WAND


def test_a_pick_axe_only_when_there_is_time():
    assert dig_down_tool([_item(PICK)], slow_ok=True).object is PICK
    assert dig_down_tool([_item(PICK)], slow_ok=False) is None


def test_unidentified_wands_are_not_trusted():
    assert dig_down_tool([_item(WAND, known=False)], slow_ok=True) is None
