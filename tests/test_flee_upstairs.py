from types import SimpleNamespace

import numpy as np

from autoascend.combat import fight_heur
from autoascend.combat.utils import action_str
from autoascend.glyph import C, MON, SS
from autoascend.level import Level


def fake_agent(pos=(10, 10), stairs=((10, 12),), key=(Level.DUNGEONS_OF_DOOM, 5), time=1000,
               fled_from=None, occupied=(), unreachable=False):
    objects = np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16)
    for y, x in stairs:
        objects[y, x] = SS.S_upstair
    yy, xx = np.mgrid[0:C.SIZE_Y, 0:C.SIZE_X]
    dis = np.maximum(abs(yy - pos[0]), abs(xx - pos[1]))
    if unreachable:
        for y, x in stairs:
            dis[y, x] = -1
    mask = np.zeros((C.SIZE_Y, C.SIZE_X), bool)
    for y, x in occupied:
        mask[y, x] = True
    level = SimpleNamespace(dungeon_number=key[0], level_number=key[1], key=lambda: key, objects=objects)

    def path(y1, x1, y2, x2):
        out = [(y1, x1)]
        while (y1, x1) != (y2, x2):
            y1 += int(np.sign(y2 - y1))
            x1 += int(np.sign(x2 - x1))
            out.append((y1, x1))
        return out

    return SimpleNamespace(blstats=SimpleNamespace(y=pos[0], x=pos[1], time=time),
                           current_level=lambda: level, bfs=lambda: dis, path=path,
                           monster_tracker=SimpleNamespace(monster_mask=mask),
                           fled_from=fled_from if fled_from is not None else {})


def monster(name, dist=2, y=10, x=8):
    glyph = MON.fn(name)
    return (dist, y, x, MON.permonst(glyph), glyph)


def test_climbs_when_standing_on_the_up_stairs():
    agent = fake_agent(pos=(10, 12))
    assert fight_heur.flee_upstairs_action(agent, [monster("soldier ant")]) == [(50, ('flee_up',))]


def test_steps_toward_near_stairs():
    agent = fake_agent(pos=(10, 10), stairs=((10, 12),))
    assert fight_heur.flee_upstairs_action(agent, [monster("killer bee")]) == [(40, ('flee_to', 10, 11))]


def test_no_flee_without_a_fast_insect_in_sight():
    agent = fake_agent(pos=(10, 12))
    assert fight_heur.flee_upstairs_action(agent, [monster("soldier ant", dist=7)]) == []
    assert fight_heur.flee_upstairs_action(agent, [monster("newt")]) == []
    assert fight_heur.flee_upstairs_action(agent, []) == []


def test_no_flee_where_going_up_is_wrong():
    ant = [monster("fire ant")]
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.DUNGEONS_OF_DOOM, 1)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.SOKOBAN, 2)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.QUEST, 1)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 12), key=(Level.GNOMISH_MINES, 1)), ant) \
        == [(50, ('flee_up',))]


def test_far_unreachable_or_blocked_stairs_are_ignored():
    ant = [monster("giant ant")]
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), stairs=((10, 19),)), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), unreachable=True), ant) == []
    assert fight_heur.flee_upstairs_action(fake_agent(pos=(10, 10), occupied=((10, 11),)), ant) == []


def test_cooldown_is_per_level():
    ant = [monster("soldier ant")]
    key = (Level.GNOMISH_MINES, 3)
    recent = fake_agent(pos=(10, 12), key=key, time=1000, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(recent, ant) == []
    later = fake_agent(pos=(10, 12), key=key, time=1050, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(later, ant) == [(50, ('flee_up',))]
    other = fake_agent(pos=(10, 12), key=(Level.GNOMISH_MINES, 4), time=1000, fled_from={key: 900})
    assert fight_heur.flee_upstairs_action(other, ant) == [(50, ('flee_up',))]


def test_action_str_prints_flee_actions():
    assert action_str(None, (50, ('flee_up',))) == '50<'
    assert action_str(None, (40, ('flee_to', 3, 4))) == '40flee:3,4'
