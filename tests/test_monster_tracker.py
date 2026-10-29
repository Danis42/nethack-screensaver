from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np

from autoascend.glyph import C
from autoascend.monster_tracker.monster_tracker import MonsterTracker


def _tracker(popup):
    agent = SimpleNamespace(glyphs=np.zeros((C.SIZE_Y, C.SIZE_X), np.int16), message='', popup=[],
                            atom_operation=nullcontext)

    def step(action, keys):
        agent.popup = popup

    agent.step = step
    return MonsterTracker(agent)


def test_takes_monsters():
    t = _tracker(['All monsters currently shown on the map:',
                  '<74,8>   d  jackal',
                  '<8,6> G peaceful gnomish wizard, can\'t move (paralyzed)'])
    assert t.take_all_monsters() == {(8, 73): 'jackal', (6, 7): 'peaceful gnomish wizard'}


def test_skips_wrapped_lines():
    # NetHack 5 wraps long lines; the rest of the line comes without coordinates
    t = _tracker(['All monsters currently shown on the map:',
                  '<12,4> G peaceful gnome lord, can\'t move (paralyzed, or',
                  'sleeping or busy)',
                  '<13,4> v fog cloud, engulfing a cloud',
                  'of vapor'])
    assert t.take_all_monsters() == {(4, 11): 'peaceful gnome lord', (4, 12): 'fog cloud'}
