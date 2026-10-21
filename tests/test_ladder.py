import pytest

from autoascend.ladder import BY_KEY, RUNGS, Facts, Ladder, MINES_END_WAIT

DOOM, GEHENNOM, MINES, QUEST, SOKOBAN, LUDIOS, VLAD, PLANES = range(8)


def reached(*steps):
    ladder = Ladder()
    for facts in steps:
        ladder.observe(facts)
    return ladder


def test_rungs_are_numbered_in_order_with_unique_keys():
    assert [r.number for r in RUNGS] == list(range(1, 18))
    assert len(BY_KEY) == 17
    assert RUNGS[0].key == "mines" and RUNGS[-1].key == "ascended"


@pytest.mark.parametrize("dungeon, level, key", [
    (MINES, 1, "mines"), (SOKOBAN, 4, "sokoban"), (QUEST, 1, "quest"), (GEHENNOM, 1, "gehennom"),
    (VLAD, 1, "vlad"), (PLANES, 5, "planes"), (DOOM, 15, "dlvl15"),
])
def test_rungs_from_the_dungeon_number(dungeon, level, key):
    assert key in reached(Facts(turn=7, dungeon=dungeon, level=level)).reached


def test_astral_is_planes_level_one_and_dlvl15_only_counts_in_the_main_dungeon():
    ladder = reached(Facts(turn=1, dungeon=PLANES, level=1), Facts(turn=2, dungeon=GEHENNOM, level=20))
    assert {"planes", "astral"} <= set(ladder.reached)
    assert "dlvl15" not in ladder.reached
    assert "dlvl15" not in reached(Facts(turn=1, dungeon=DOOM, level=14)).reached


def test_rungs_the_bot_notices():
    ladder = reached(Facts(turn=5, dungeon=MINES, level=3, minetown_seen=True),
                     Facts(turn=9, dungeon=DOOM, level=6, oracle_seen=True))
    assert ladder.reached["minetown"] == 5 and ladder.reached["oracle"] == 9


def test_sokoban_solved_needs_the_top_level_drawn_and_no_trap_left():
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=40, sokoban_traps=False)).reached
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=300, sokoban_traps=True)).reached
    assert "sokoban_solved" not in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=2, sokoban_seen=300, sokoban_traps=False)).reached
    assert "sokoban_solved" in reached(
        Facts(turn=1, dungeon=SOKOBAN, level=1, sokoban_seen=300, sokoban_traps=False)).reached


def test_mines_end_is_level_nine_or_a_level_eight_without_down_stairs():
    assert "mines_end" in reached(Facts(turn=1, dungeon=MINES, level=9)).reached
    stay = [Facts(turn=t, dungeon=MINES, level=8) for t in (100, 100 + MINES_END_WAIT)]
    assert reached(*stay).reached["mines_end"] == 100 + MINES_END_WAIT
    early = [Facts(turn=t, dungeon=MINES, level=8) for t in (100, 99 + MINES_END_WAIT)]
    assert "mines_end" not in reached(*early).reached
    stairs = [Facts(turn=t, dungeon=MINES, level=8, down_stairs_seen=True) for t in (100, 5000)]
    assert "mines_end" not in reached(*stairs).reached


def test_leaving_mines_level_eight_restarts_the_wait():
    visits = [Facts(turn=100, dungeon=MINES, level=8), Facts(turn=900, dungeon=MINES, level=7),
              Facts(turn=1000, dungeon=MINES, level=8), Facts(turn=1500, dungeon=MINES, level=8)]
    assert "mines_end" not in reached(*visits).reached


def test_medusa_and_castle_proxies():
    assert "medusa" in reached(Facts(turn=1, dungeon=DOOM, level=22, medusa_seen=True)).reached
    assert "medusa" in reached(Facts(turn=1, dungeon=DOOM, level=23, water_share=0.5)).reached
    assert "medusa" not in reached(Facts(turn=1, dungeon=DOOM, level=12, water_share=0.5)).reached
    assert "medusa" not in reached(Facts(turn=1, dungeon=DOOM, level=23, water_share=0.2)).reached
    assert "castle" in reached(Facts(turn=1, dungeon=DOOM, level=27, drawbridge_seen=True)).reached
    assert "castle" not in reached(Facts(turn=1, dungeon=GEHENNOM, level=3, drawbridge_seen=True)).reached


def test_wizard_tower_and_invocation_proxies():
    book = Facts(turn=1, dungeon=GEHENNOM, level=12, inventory=("a papyrus spellbook", "the Book of the Dead"))
    assert "wizard_tower" in reached(book).reached
    vibration = Facts(turn=2, dungeon=GEHENNOM, level=20, message="You feel a strange vibration under your feet.")
    assert "invocation" not in reached(vibration).reached
    assert "invocation" in reached(vibration, Facts(turn=3, dungeon=GEHENNOM, level=21)).reached
    assert "invocation" not in reached(Facts(turn=3, dungeon=GEHENNOM, level=21)).reached


def test_first_turn_is_kept_and_highest_rung_is_reported():
    ladder = reached(Facts(turn=10, dungeon=MINES, level=1), Facts(turn=20, dungeon=MINES, level=2),
                     Facts(turn=30, dungeon=SOKOBAN, level=4))
    assert ladder.reached == {"mines": 10, "sokoban": 30}
    assert ladder.highest() == 4
    assert Ladder().highest() == 0


def test_finish_adds_ascended_only_for_an_ascension():
    ladder = Ladder()
    ladder.finish("DEATH: killed by a newt", 500)
    assert ladder.reached == {}
    ladder.finish("ASCENDED: ascended to demigod-hood", 53000)
    assert ladder.reached == {"ascended": 53000} and ladder.highest() == 17


import numpy as np


def _fake_logic(hallu=False, objects=None, seen=None, glyphs=None, key=(0, 22)):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    from autoascend.glyph import C
    logic = GlobalLogic.__new__(GlobalLogic)
    level = SimpleNamespace(dungeon_number=key[0], level_number=key[1], key=lambda: key,
                            objects=objects if objects is not None else np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16),
                            seen=seen if seen is not None else np.ones((C.SIZE_Y, C.SIZE_X), bool))
    logic.agent = SimpleNamespace(
        current_level=lambda: level, blstats=SimpleNamespace(time=123),
        character=SimpleNamespace(prop=SimpleNamespace(hallu=hallu)),
        glyphs=glyphs if glyphs is not None else np.zeros((C.SIZE_Y, C.SIZE_X), np.int16),
        inventory=SimpleNamespace(items=[]), message="")
    logic.oracle_level = logic.minetown_level = None
    return logic


def test_facts_see_water_and_medusa_but_not_while_hallucinating():
    from autoascend.glyph import C, MON, SS
    objects = np.full((C.SIZE_Y, C.SIZE_X), SS.S_pool, np.int16)
    glyphs = np.zeros((C.SIZE_Y, C.SIZE_X), np.int16)
    glyphs[3, 3] = MON.fn('Medusa')
    facts = _fake_logic(objects=objects, glyphs=glyphs).ladder_facts()
    assert facts.turn == 123 and (facts.dungeon, facts.level) == (0, 22)
    assert facts.water_share == 1.0 and facts.medusa_seen
    tripping = _fake_logic(hallu=True, objects=objects, glyphs=glyphs).ladder_facts()
    assert tripping.water_share == 0.0 and not tripping.medusa_seen and not tripping.drawbridge_seen


def test_facts_on_an_undrawn_sokoban_top_level_are_not_solved():
    from autoascend.glyph import C
    facts = _fake_logic(key=(4, 1), seen=np.zeros((C.SIZE_Y, C.SIZE_X), bool)).ladder_facts()
    assert facts.sokoban_seen == 0
    assert "sokoban_solved" not in reached(facts).reached
