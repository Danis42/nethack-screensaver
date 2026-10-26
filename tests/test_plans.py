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
    assert dive_stairs(2, objects, {}, bfs) == []  # not in a branch once its dive is over
    assert dive_stairs(2, objects, {}, bfs, mines=True) == [(3, 4), (10, 10)]  # down the Mines
    assert dive_stairs(1, objects, {}, bfs, mines=True) == []  # other branches never


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



def _bl(hp=20, maxhp=20, xl=3, hunger=1):
    from types import SimpleNamespace
    return SimpleNamespace(hitpoints=hp, max_hitpoints=maxhp, experience_level=xl, hunger_state=hunger)


def test_pray_when_weak_from_hunger_not_only_when_fainting():
    from autoascend.agent import prayer_trouble
    assert prayer_trouble(_bl(hunger=3), safe_hp=True, safe_hunger=True)  # Weak is major trouble
    assert prayer_trouble(_bl(hunger=4), safe_hp=True, safe_hunger=True)
    assert not prayer_trouble(_bl(hunger=2), safe_hp=True, safe_hunger=True)  # merely Hungry
    assert not prayer_trouble(_bl(hunger=3), safe_hp=True, safe_hunger=False)  # cooldown


def test_eat_carried_food_instead_of_praying_for_hunger():
    from autoascend.agent import prayer_trouble
    assert not prayer_trouble(_bl(hunger=3), safe_hp=True, safe_hunger=True, has_food=True)
    assert not prayer_trouble(_bl(hunger=4), safe_hp=True, safe_hunger=True, has_food=True)
    assert prayer_trouble(_bl(hp=3, maxhp=20, hunger=3), safe_hp=True, safe_hunger=True, has_food=True)  # HP first


def test_pray_at_low_hp_keeps_upstream_thresholds():
    from autoascend.agent import prayer_trouble
    assert prayer_trouble(_bl(hp=3, maxhp=20), safe_hp=True, safe_hunger=False)
    assert not prayer_trouble(_bl(hp=10, maxhp=20), safe_hp=True, safe_hunger=False)
    assert not prayer_trouble(_bl(hp=3, maxhp=20), safe_hp=False, safe_hunger=True)


def test_dive_instead_replaces_the_rest_of_the_route():
    p = Plan(STRATEGIES["sightseer"].milestones)
    while p.current != M.RETURN_TO_SURFACE:
        p.advance()
    p.dive_instead()
    assert p.current == M.DIVE
    assert not p.can_bail_out()
    p.advance()
    assert p.current == M.DIVE


def test_progress_watch_counts_new_levels_and_milestones():
    from autoascend.plans import ProgressWatch
    w = ProgressWatch(limit=100)
    assert not w.stuck((0, 1), M.FIND_SOKOBAN, 0)
    assert not w.stuck((0, 1), M.FIND_SOKOBAN, 100)
    assert w.stuck((0, 1), M.FIND_SOKOBAN, 101)
    assert not w.stuck((0, 2), M.FIND_SOKOBAN, 150)  # new level is progress
    assert not w.stuck((0, 1), M.FIND_SOKOBAN, 240)  # an old level is not, but the clock restarted at 150
    assert w.stuck((0, 1), M.FIND_SOKOBAN, 251)
    assert not w.stuck((0, 1), M.SOLVE_SOKOBAN, 300)  # next milestone is progress


def test_progress_watch_ignores_the_first_level_phase_and_restarts():
    from autoascend.plans import ProgressWatch
    w = ProgressWatch(limit=10)
    assert not w.stuck((0, 1), M.BE_ON_FIRST_LEVEL, 500)
    assert not w.stuck((0, 3), M.DIVE, 1000)
    assert w.stuck((0, 3), M.DIVE, 1011)  # a diver can be stuck too (e.g. at Mines' End)
    w.restart(1011)
    assert not w.stuck((0, 3), M.DIVE, 1020)


@pytest.mark.parametrize("text,race", [
    ("Hello Agent, welcome to NetHack!  You are a lawful dwarven Cavewoman.", "dwa"),
    ("Hello Agent, welcome to NetHack!  You are a neutral female gnomish\nHealer.", "gno"),
    ("Aloha Agent, welcome to NetHack!  You are a neutral male human Tourist.", "hum"),
    ("Hello Agent, welcome to NetHack!  You are a chaotic elven Priest.", "elf"),
    ("Hello Agent, welcome to NetHack!  You are a chaotic male orcish Rogue.", "orc"),
    ("$ - 3 gold pieces.", None),
])
def test_race_from_welcome(text, race):
    from autoascend.plans import race_from_welcome
    assert race_from_welcome(text) == race


def test_pilgrim_does_sokoban_first_unless_the_mines_are_peaceful():
    from autoascend.plans import plan_for
    for race in ("hum", "elf", "orc"):
        assert plan_for("pilgrim", race)[:3] == (M.BE_ON_FIRST_LEVEL, M.FIND_SOKOBAN, M.SOLVE_SOKOBAN)
    for race in ("dwa", "gno", None):  # gnomes and dwarves are left alone in the Mines
        assert plan_for("pilgrim", race) == STRATEGIES["pilgrim"].milestones
    assert set(plan_for("pilgrim", "hum")) == set(STRATEGIES["pilgrim"].milestones)
    assert plan_for("sightseer", "hum") == STRATEGIES["sightseer"].milestones


# --- stuck reports (measuring only) -----------------------------------------------------------

def _stuck_map():
    import numpy as np
    from autoascend.glyph import C
    objects = np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16)
    seen = np.zeros((C.SIZE_Y, C.SIZE_X), bool)
    walkable = np.zeros((C.SIZE_Y, C.SIZE_X), bool)
    seen[5, 5:12] = walkable[5, 5:12] = True  # a corridor, all seen
    dis = np.full((C.SIZE_Y, C.SIZE_X), -1, np.int32)
    dis[5, 5:12] = range(7)
    glyphs = np.zeros((C.SIZE_Y, C.SIZE_X), np.int16)
    return objects, seen, walkable, dis, glyphs


def _report(objects, seen, walkable, dis, glyphs):
    from autoascend.stuck import stuck_report
    return stuck_report(turn=900, dungeon=0, level=7, dlvl=7, milestone="DIVE", target=(0, 100), objects=objects,
                        seen=seen, walkable=walkable, dis=dis, glyphs=glyphs)


def test_stuck_report_sees_a_reachable_down_staircase():
    from autoascend.glyph import SS
    objects, seen, walkable, dis, glyphs = _stuck_map()
    objects[5, 11] = SS.S_dnstair
    row = _report(objects, seen, walkable, dis, glyphs)
    assert row["down_seen"] and row["down_reachable"]
    assert {k: row[k] for k in ("turn", "dungeon", "level", "dlvl", "milestone")} == \
        {"turn": 900, "dungeon": 0, "level": 7, "dlvl": 7, "milestone": "DIVE"}
    assert all(type(row[k]) in (int, bool, str) for k in row if k != "target")
    assert all(type(v) is int for v in row["target"])


def test_stuck_report_sees_a_down_staircase_behind_a_wall():
    from autoascend.glyph import SS
    objects, seen, walkable, dis, glyphs = _stuck_map()
    objects[9, 20] = SS.S_dnstair
    seen[9, 20] = True
    row = _report(objects, seen, walkable, dis, glyphs)
    assert row["down_seen"] and not row["down_reachable"]


def test_stuck_report_counts_the_frontier():
    objects, seen, walkable, dis, glyphs = _stuck_map()
    row = _report(objects, seen, walkable, dis, glyphs)
    assert row["frontier"] == 7  # every corridor square has unseen squares above and below
    seen[4, 4:13] = seen[6, 4:13] = True
    seen[5, 4] = seen[5, 12] = True
    assert _report(objects, seen, walkable, dis, glyphs)["frontier"] == 0
    seen[4, 6] = seen[6, 7] = False
    seen[5, 12] = False
    assert _report(objects, seen, walkable, dis, glyphs)["frontier"] == 3


def _stuck_logic():
    from types import SimpleNamespace

    import numpy as np

    from autoascend.global_logic import GlobalLogic
    from autoascend.plans import Plan
    objects, seen, walkable, dis, glyphs = _stuck_map()
    level = SimpleNamespace(dungeon_number=0, level_number=7, objects=objects, seen=seen, walkable=walkable)
    logic = GlobalLogic.__new__(GlobalLogic)
    logic.plan = Plan(DEFAULT_PLAN)
    logic.stuck_reports = []
    events = []
    logic.agent = SimpleNamespace(current_level=lambda: level, blstats=SimpleNamespace(time=np.int64(5), depth=7),
                                  bfs=lambda: dis, glyphs=glyphs,
                                  stats_logger=SimpleNamespace(log_event=events.append))
    return logic, events


def test_stuck_reports_keep_the_newest_fifty():
    from autoascend.stuck import KEEP
    logic, events = _stuck_logic()
    for t in range(KEEP + 5):
        logic.agent.blstats.time = t
        logic._report_stuck((0, 100))
    assert len(logic.stuck_reports) == KEEP and logic.stuck_reports[0]["turn"] == 5 and events == []


def test_a_failing_stuck_report_is_counted_not_raised():
    logic, events = _stuck_logic()
    logic.agent.bfs = lambda: 1 / 0
    logic._report_stuck((0, 100))
    assert logic.stuck_reports == [] and events == ["stuck_report_error"]


def test_stuck_report_knows_when_the_way_starts_upwards():
    from autoascend.stuck import wants_up
    assert wants_up(2, 5, (0, 100))          # Mines -> main dungeon: up
    assert not wants_up(2, 3, (2, 9))        # deeper in the Mines
    assert wants_up(0, 7, (0, 1))            # back to Dlvl 1
    assert wants_up(4, 3, (4, 1))            # Sokoban: level 1 is the top
    assert not wants_up(4, 2, (0, 100))      # leaving Sokoban goes down
    assert not wants_up(0, 5, (2, 9))        # main dungeon -> Mines: not clear from the keys


def test_stuck_report_sees_the_up_staircase():
    from autoascend.glyph import SS
    objects, seen, walkable, dis, glyphs = _stuck_map()
    objects[5, 5] = SS.S_upstair
    row = _report(objects, seen, walkable, dis, glyphs)
    assert row["up_seen"] and row["up_reachable"] and not row["down_seen"]
    assert row["target"] == [0, 100] and not row["wants_up"]


def test_hunger_prayer_gap_eases_while_weak():
    from autoascend.agent import hunger_prayer_gap
    assert hunger_prayer_gap(0) == 1000  # just turned Weak: wait for a safe timeout
    assert hunger_prayer_gap(100) == 700
    assert hunger_prayer_gap(200) == 400  # near starvation: the old gap
    assert hunger_prayer_gap(5000) == 400
