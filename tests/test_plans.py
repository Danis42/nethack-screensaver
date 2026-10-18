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


def _clock_logic(milestones):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    logic = GlobalLogic.__new__(GlobalLogic)
    logic.agent = SimpleNamespace(blstats=SimpleNamespace(time=100),
                                  current_level=lambda: SimpleNamespace(key=lambda: (2, 3)))
    logic.plan, logic._started, logic._arrived = Plan(milestones), {}, {}
    logic.minetown_level = None
    return logic


def test_minetown_search_gives_up_after_budget():
    from autoascend.global_logic import MINETOWN_SEARCH_TURNS
    logic = _clock_logic([M.FIND_MINETOWN, M.EXPLORE_MINETOWN])
    assert logic._minetown_found() is False
    logic.agent.blstats.time += MINETOWN_SEARCH_TURNS
    assert logic._minetown_found() is True


def test_no_minetown_means_nothing_to_explore():
    logic = _clock_logic([M.EXPLORE_MINETOWN])
    assert logic._minetown_explored() is True
    logic.minetown_level = (2, 3)
    assert logic._minetown_explored() is False


def test_too_heavy_to_climb_drops_heaviest_non_prize_item():
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic

    class Thing(_Item):
        def __init__(self, text, weight, *names):
            super().__init__(text, *names)
            self._w = weight

        def weight(self):
            return self._w

        def can_be_dropped_from_inventory(self):
            return True

    boulder_ish = Thing("a heavy iron ball", 480, "heavy iron ball")
    prize = Thing("a bag", 600, "bag of holding", "sack")
    dropped = []
    logic = GlobalLogic.__new__(GlobalLogic)
    logic.agent = SimpleNamespace(
        message="You have a little trouble lifting. Your load is too heavy to climb the stairs.",
        inventory=SimpleNamespace(items=[prize, boulder_ish], drop=dropped.append))
    logic._prize_baseline, logic._prize_found = set(), True
    logic._after_failed_climb()
    assert dropped == [boulder_ish]


def test_failed_climb_for_other_reasons_drops_nothing():
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    dropped = []
    logic = GlobalLogic.__new__(GlobalLogic)
    logic.agent = SimpleNamespace(message="You are held back by the giant eel.",
                                  inventory=SimpleNamespace(items=[], drop=dropped.append))
    logic._after_failed_climb()
    assert dropped == []


def test_prize_pickups_only_while_looting_top_sokoban():
    bag = _Item("a bag", "bag of holding", "sack")
    junk = _Item("a rock", "rock")
    logic = _logic((4, 1), [])
    logic.plan = Plan([M.LOOT_SOKOBAN_PRIZE])
    assert logic.prize_pickups([bag, junk]) == [bag]
    logic.plan = Plan([M.GO_DOWN])
    assert logic.prize_pickups([bag, junk]) == []
    elsewhere = _logic((0, 5), [])
    elsewhere.plan = Plan([M.LOOT_SOKOBAN_PRIZE])
    assert elsewhere.prize_pickups([bag]) == []


def test_dive_stairs_are_known_reachable_main_dungeon_downstairs():
    import numpy as np

    from autoascend.glyph import G
    from autoascend.global_logic import dive_stairs
    down = next(iter(G.STAIR_DOWN))
    objects = np.zeros((21, 79), dtype=np.int16)
    objects[3, 4] = objects[10, 10] = objects[15, 20] = down
    bfs = np.full((21, 79), -1)
    bfs[3, 4] = bfs[10, 10] = 5  # (15, 20) is unreachable
    to_mines = {(10, 10): ((2, 1), (7, 7))}  # this one is known to lead into the Mines
    assert dive_stairs(0, objects, to_mines, bfs) == [(3, 4)]
    assert dive_stairs(2, objects, {}, bfs) == []  # never dive inside a branch


def test_daredevil_dives():
    assert STRATEGIES["daredevil"].milestones == (M.BE_ON_FIRST_LEVEL, M.DIVE)


def test_path_following_can_skip_waiting_for_the_pet():
    from types import SimpleNamespace

    import numpy as np

    from autoascend.exploration_logic import ExplorationLogic
    moves = []
    agent = SimpleNamespace(has_pet=True, glyphs=np.zeros((21, 79), dtype=np.int16),
                            blstats=SimpleNamespace(y=5, x=5), move=moves.append)
    ex = ExplorationLogic.__new__(ExplorationLogic)
    ex.agent = agent
    ran = []
    go_to = lambda y, x: SimpleNamespace(run=lambda: ran.append((y, x)))
    ex.follow_level_path_strategy([((5, 5), None, '<')], go_to, wait_for_pet=False).run()
    assert ran == [(5, 5)] and moves == ['<']  # no '.' waits for the pet


def test_bail_out_jumps_to_return_to_surface():
    p = Plan(STRATEGIES["sightseer"].milestones)
    p.advance()  # FIND_GNOMISH_MINES
    assert p.can_bail_out()
    p.bail_out()
    assert p.current == M.RETURN_TO_SURFACE
    assert not p.can_bail_out()  # already heading home


def test_plans_without_a_way_home_never_bail_out():
    for name in ("pilgrim", "daredevil"):
        p = Plan(STRATEGIES[name].milestones)
        assert not p.can_bail_out()
        p.bail_out()
        assert p.current == M.BE_ON_FIRST_LEVEL


def _bail_logic(milestones, hunger=1, food=(), elapsed=0, can_pray=False):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic

    class Food(_Item):
        def is_food(self):
            return True

    logic = GlobalLogic.__new__(GlobalLogic)
    logic.agent = SimpleNamespace(blstats=SimpleNamespace(time=100 + elapsed, hunger_state=hunger),
                                  inventory=SimpleNamespace(items=[Food(f) for f in food]),
                                  is_safe_to_pray=lambda: can_pray)
    logic.plan, logic._started = Plan(milestones), {logic_m: 100 for logic_m in milestones}
    return logic


def test_weak_with_no_food_heads_home():
    route = STRATEGIES["sightseer"].milestones[1:]
    assert _bail_logic(route, hunger=3)._should_bail()
    assert not _bail_logic(route, hunger=3, food=["a food ration"])._should_bail()
    assert not _bail_logic(route, hunger=2)._should_bail()


def test_weak_but_prayer_available_keeps_going():
    route = STRATEGIES["sightseer"].milestones[1:]
    assert not _bail_logic(route, hunger=3, can_pray=True)._should_bail()


def test_treasure_gives_up_on_sokoban_after_budget():
    from autoascend.global_logic import SOKOBAN_SEARCH_TURNS
    route = STRATEGIES["treasure"].milestones[1:]  # FIND_SOKOBAN first
    assert not _bail_logic(route, elapsed=SOKOBAN_SEARCH_TURNS - 1)._should_bail()
    assert _bail_logic(route, elapsed=SOKOBAN_SEARCH_TURNS)._should_bail()


def test_no_bail_without_a_way_home():
    assert not _bail_logic(STRATEGIES["daredevil"].milestones, hunger=3)._should_bail()


@pytest.mark.parametrize("role,favoured,share", [("val", {"pilgrim", "treasure"}, 0.7),
                                                 ("tou", {"sightseer", "daredevil"}, 0.8)])
def test_role_tilts_but_never_excludes(role, favoured, share):
    import random
    from collections import Counter

    from autoascend.plans import choose_strategy
    rng = random.Random(1)
    picks = Counter(choose_strategy(role, rng) for _ in range(4000))
    assert set(picks) == set(STRATEGIES)  # every strategy still possible
    assert sum(picks[s] for s in favoured) / 4000 == pytest.approx(share, abs=0.04)


def test_unknown_role_gets_equal_odds():
    import random
    from collections import Counter

    from autoascend.plans import choose_strategy
    rng = random.Random(2)
    picks = Counter(choose_strategy("???", rng) for _ in range(4000))
    assert all(abs(n / 4000 - 0.25) < 0.04 for n in picks.values())


def _explorer(oracle_level):
    from types import SimpleNamespace

    from autoascend.exploration_logic import ExplorationLogic
    ex = ExplorationLogic.__new__(ExplorationLogic)
    ex.agent = SimpleNamespace(global_logic=SimpleNamespace(oracle_level=oracle_level))
    return ex


def test_sokoban_is_searched_only_below_a_known_oracle():
    reached = {(0, i) for i in range(1, 10)}
    assert _explorer((0, 7)).levels_to_explore_to_get_to(4, 4, reached) == {(0, 8)}


def test_sokoban_search_without_oracle_covers_dlvl_6_to_10():
    reached = {(0, i) for i in range(1, 10)}
    assert _explorer(None).levels_to_explore_to_get_to(4, 4, reached) == {(0, i) for i in range(6, 10)}

