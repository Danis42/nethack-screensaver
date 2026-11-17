"""Leaving an unwanted Mines level (SURV-04, D-06, D-07): pure rules plus the climb-out step on a fake agent."""
from types import SimpleNamespace

import numpy as np

from autoascend import stairs
from autoascend.global_logic import GlobalLogic
from autoascend.glyph import SS
from autoascend.level import Level
from autoascend.plans import Milestone


def test_mines_milestones_want_the_mines_others_do_not():
    for m in (Milestone.FIND_GNOMISH_MINES, Milestone.FIND_MINETOWN, Milestone.EXPLORE_MINETOWN,
              Milestone.FIND_MINES_END, Milestone.DIVE):
        assert stairs.wants_mines(m)
    for m in (Milestone.BE_ON_FIRST_LEVEL, Milestone.FIND_SOKOBAN, Milestone.SOLVE_SOKOBAN,
              Milestone.LOOT_SOKOBAN_PRIZE, Milestone.GO_DOWN, Milestone.RETURN_TO_SURFACE):
        assert not stairs.wants_mines(m)


def _mines_level(ups=((5, 5), (9, 40))):
    objects = np.full((21, 79), -1, dtype=np.int16)  # like Level.objects
    for y, x in ups:
        objects[y, x] = SS.S_upstair
    return SimpleNamespace(objects=objects, dungeon_number=Level.GNOMISH_MINES)


def test_mines_exit_is_the_nearest_reachable_upstairs():
    bfs = np.full((21, 79), -1)
    bfs[5, 5], bfs[9, 40] = 30, 4
    assert stairs.mines_exit(_mines_level(), bfs) == (9, 40)
    bfs[9, 40] = -1
    assert stairs.mines_exit(_mines_level(), bfs) == (5, 5)
    bfs[5, 5] = -1
    assert stairs.mines_exit(_mines_level(), bfs) is None


def _logic(milestone, dungeon=Level.GNOMISH_MINES):
    moves, events = [], []
    level = _mines_level()
    level.dungeon_number = dungeon
    bfs = np.full((21, 79), -1)
    bfs[5, 5] = 3
    agent = SimpleNamespace(current_level=lambda: level, bfs=lambda: bfs,
                            go_to=lambda y, x: moves.append(("go", y, x)), move=lambda d: moves.append(d),
                            stats_logger=SimpleNamespace(log_event=events.append))
    logic = SimpleNamespace(agent=agent, milestone=milestone)
    logic._on_wrong_branch = lambda: GlobalLogic._on_wrong_branch(logic)
    return logic, moves, events


def test_unwanted_mines_level_is_left_by_the_nearest_upstairs():
    for milestone in (Milestone.FIND_SOKOBAN, Milestone.GO_DOWN):
        logic, moves, events = _logic(milestone)
        assert GlobalLogic._leave_mines(logic) is True
        assert moves == [("go", 5, 5), "<"] and events == ["mines_left_unwanted"]


def test_wanted_mines_and_other_dungeons_are_not_left():
    for logic, moves, _ in (_logic(Milestone.FIND_MINETOWN), _logic(Milestone.FIND_SOKOBAN, Level.DUNGEONS_OF_DOOM)):
        assert GlobalLogic._leave_mines(logic) is False and moves == []


def test_the_bench_trigger_knows_the_same_wanted_mines_milestones():
    # 02-MINES-PREREG.md: the trigger mines_unwanted must fire exactly where wants_mines is false
    from bench.triggers import MINES_WANTED
    assert {m.name for m in stairs.MINES_MILESTONES} == MINES_WANTED
