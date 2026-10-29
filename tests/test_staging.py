from types import SimpleNamespace

from autoascend.character import Character
from nethack_screensaver.staging import STAGES, level_letter

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
    for stage in STAGES.values():
        assert stage.level and 1 <= stage.xl <= 30


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
