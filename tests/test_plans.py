import pytest

from autoascend.plans import DEFAULT_PLAN, STRATEGIES, Milestone as M, Plan


def test_plan_walks_milestones_in_order():
    p = Plan([M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.GO_DOWN])
    seen = [p.current]
    for _ in range(2):
        p.advance()
        seen.append(p.current)
    assert seen == [M.BE_ON_FIRST_LEVEL, M.FIND_GNOMISH_MINES, M.GO_DOWN]


def test_last_milestone_never_advances():
    p = Plan([M.BE_ON_FIRST_LEVEL, M.LEAVE_DUNGEON])
    for _ in range(5):
        p.advance()
    assert p.current == M.LEAVE_DUNGEON


def test_dropped_sokoban_skips_the_loot():
    p = Plan(STRATEGIES["treasure"].milestones)
    while p.current != M.SOLVE_SOKOBAN:
        p.advance()
    p.drop_sokoban()
    assert p.current == M.RETURN_TO_SURFACE


def test_dropped_sokoban_in_pilgrim_just_advances():
    p = Plan(STRATEGIES["pilgrim"].milestones)
    while p.current != M.SOLVE_SOKOBAN:
        p.advance()
    p.drop_sokoban()
    assert p.current == M.FIND_MINES_END


@pytest.mark.parametrize("name", ["pilgrim", "daredevil", "sightseer", "treasure"])
def test_every_strategy_starts_on_first_level(name):
    s = STRATEGIES[name]
    assert s.name == name and s.title and s.ending
    assert s.milestones[0] == M.BE_ON_FIRST_LEVEL


def test_endings_and_routes_match_spec():
    assert {n: s.ending for n, s in STRATEGIES.items()} == {
        "pilgrim": "ascension",
        "daredevil": "escape in celestial disgrace",
        "sightseer": "escape the dungeon",
        "treasure": "escape with loot",
    }
    assert STRATEGIES["daredevil"].milestones == (M.BE_ON_FIRST_LEVEL, M.GO_DOWN)
    assert STRATEGIES["sightseer"].milestones[-2:] == (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)
    assert DEFAULT_PLAN == STRATEGIES["pilgrim"].milestones


def test_global_logic_still_exports_milestone():
    from autoascend.global_logic import Milestone
    assert Milestone is M


class _Item:
    def __init__(self, text, *names):
        from autoascend import objects as O
        self.text, self.objs = text, [O.from_name(n) for n in names]

    def __str__(self):
        return self.text

    def is_container(self):
        return False


def _logic(level, items):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    logic = GlobalLogic.__new__(GlobalLogic)  # no agent needed for the prize check
    logic.agent = SimpleNamespace(current_level=lambda: SimpleNamespace(key=lambda: level),
                                  inventory=SimpleNamespace(items=items))
    logic._prize_baseline, logic._prize_found = None, False
    return logic


def test_amulet_carried_into_sokoban_is_not_the_prize():
    held = [_Item("a circular amulet", "amulet of reflection", "amulet of strangulation")]
    logic = _logic((4, 1), held)
    assert logic._loot_check() is False and logic.has_prize() is False


def test_amulet_picked_up_on_top_sokoban_level_is_the_prize():
    items = []
    logic = _logic((4, 1), items)
    assert logic._loot_check() is False
    items.append(_Item("an oval amulet", "amulet of reflection", "amulet of strangulation"))
    assert logic._loot_check() is True and logic.has_prize() is True


def test_loot_check_ignores_other_levels():
    items = [_Item("a bag", "bag of holding", "sack")]
    assert _logic((0, 5), items)._loot_check() is False
