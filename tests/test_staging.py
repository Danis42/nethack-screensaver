from types import SimpleNamespace

from autoascend.character import Character
from nethack_screensaver.staging import ITEM_TESTS, STAGES, level_letter

MENU = [" Level teleport to where:",
        " The Dungeons of Doom: levels 1 to 26",
        " a - * One way stair to The Elemental Planes: 1",
        " c -   oracle: 6",
        " h -   medusa: 22",
        " j -   castle: 26 (tune DBFFG)",
        " Gehennom: levels 27 to 46",
        " k -   valley: 27",
        " (1 of 3)"]


def test_finds_special_levels_in_the_teleport_menu():
    assert level_letter(MENU, "medusa") == "h"
    assert level_letter(MENU, "castle") == "j"
    assert level_letter(MENU, "valley") == "k"
    assert level_letter(MENU, "Val-strt") is None  # on a later page


def test_every_stage_has_a_level_and_an_experience_level():
    for name, stage in STAGES.items():
        assert (stage.level or name in ITEM_TESTS) and 1 <= stage.xl <= 30


def test_item_tests_stay_on_dlvl_1_and_stop_early():
    for stage in ITEM_TESTS.values():
        assert stage.level is None and stage.max_steps


def _enhance(popup):
    character = Character(SimpleNamespace(popup=popup))
    character.skill_levels = {}
    character._parse_enhance_view()
    return character


def test_reads_skills_in_normal_play():
    c = _enhance(['Current skills:', 'Weapon Skills', 'a - long sword [Basic]', 'dagger [Unskilled]'])
    assert c.upgradable_skills == {Character.name_to_skill_type['long sword']: 'a'}


def test_reads_skills_in_wizard_mode():
    # wizard mode (staged games) lists practice points instead of brackets
    c = _enhance(['Current skills:  (13 slots available)', 'Weapon Skills',
                  'long sword         Basic            12(  20)', 'attack spells      Unskilled        0(  20)'])
    assert c.skill_levels[Character.name_to_skill_type['long sword']] == Character.name_to_skill_level['Basic']


def test_soko_top_stage_goes_to_sokobans_top_level_without_stairs():
    from nethack_screensaver import staging
    stage = staging.STAGES["soko-top"]
    assert stage.level == "soko1" and stage.on_upstairs is False and stage.wield is None


def test_observation_facts_read_dungeon_level_seen_and_traps():
    import numpy as np
    import nle.nethack as nh
    from autoascend.glyph import G, SS
    from nethack_screensaver import staging
    glyphs = np.full((21, 79), SS.S_stone, np.int16)
    glyphs[5, 5:10] = SS.S_room
    glyphs[5, 7] = sorted(G.TRAPS)[0]
    blstats = np.zeros(30, np.int64)
    blstats[nh.NLE_BL_DNUM], blstats[nh.NLE_BL_DLEVEL], blstats[nh.NLE_BL_TIME] = 4, 1, 77
    f = staging.observation_facts({"glyphs": glyphs, "blstats": blstats})
    assert (f.dungeon, f.level, f.turn, f.sokoban_seen, f.sokoban_traps) == (4, 1, 77, 5, True)
    glyphs[5, 7] = SS.S_room
    assert not staging.observation_facts({"glyphs": glyphs, "blstats": blstats}).sokoban_traps
