"""The sokoban_solved detector against a played hand game (MEAS-03, plan 01-06).

The fixtures are observations recorded from a hand game on seed 7, stage soko-top (NetHack 5.0 soko1-2, the top
Sokoban level, flipped): the start board at T1 and the solved board at T897, after the last hole was filled at T882.
Facts come from the bot's own path (GlobalLogic.ladder_facts over a fake level built from the recorded glyphs)."""
import json
from pathlib import Path

import numpy as np
import pytest
from nle import nethack

from autoascend.ladder import SOKOBAN, Ladder
from fake_logic import fake_logic
from nethack_screensaver import staging

DATA = Path(__file__).parent / "data"


def _fixture(name):
    return json.loads((DATA / f"soko_top_hand_{name}.json").read_text())


def _bot_facts(fx):
    glyphs = np.array(fx["glyphs"], np.int16)
    logic = fake_logic(objects=glyphs, seen=glyphs != staging.unexplored_glyph(), glyphs=glyphs,
                       key=(fx["dungeon"], fx["level"]))
    logic.agent.blstats.time = np.int64(fx["turn"])
    return logic.ladder_facts()


def _observation(fx):
    blstats = np.zeros(nethack.NLE_BLSTATS_SIZE, np.int64)
    blstats[nethack.NLE_BL_TIME] = fx["turn"]
    blstats[nethack.NLE_BL_DNUM] = fx["dungeon"]
    blstats[nethack.NLE_BL_DLEVEL] = fx["level"]
    blstats[nethack.NLE_BL_Y], blstats[nethack.NLE_BL_X] = fx["player"]
    return {"glyphs": np.array(fx["glyphs"], np.int16), "blstats": blstats}


def test_fixtures_are_played_observations_of_the_sokoban_top_level():
    start, solved = _fixture("start"), _fixture("solved")
    for fx in (start, solved):
        assert "played" in fx["note"] and "computed" not in fx["note"] and "simulated" not in fx["note"]
        assert (fx["dungeon"], fx["level"]) == (SOKOBAN, 1) and len(fx["glyphs"]) == 21
    assert len(start["traps"]) == 19  # 18 holes and the rolling boulder trap NetHack 5.0 adds
    assert solved["traps"] == [[18, 46]]  # only the rolling boulder trap, which no boulder fills


@pytest.mark.parametrize("name", ["start", "solved"])
def test_bot_facts_agree_with_the_observation_builder(name):
    fx = _fixture(name)
    bot, obs = _bot_facts(fx), staging.observation_facts(_observation(fx))
    assert (bot.dungeon, bot.level, bot.turn) == (obs.dungeon, obs.level, obs.turn) == (SOKOBAN, 1, fx["turn"])
    assert bot.sokoban_seen == obs.sokoban_seen
    assert bot.sokoban_traps == obs.sokoban_traps == (name == "start")


def test_solved_fires_once_after_the_start_board_showed_its_holes():
    ladder = Ladder()
    ladder.observe(_bot_facts(_fixture("start")))
    assert "sokoban" in ladder.reached and "sokoban_solved" not in ladder.reached
    ladder.observe(_bot_facts(_fixture("solved")))
    assert ladder.reached["sokoban_solved"] == 897
    first = dict(ladder.reached)
    ladder.observe(_bot_facts(_fixture("solved")))
    assert ladder.reached == first  # it does not fire again


def test_no_solved_without_having_seen_the_holes_first():
    ladder = Ladder()
    ladder.observe(_bot_facts(_fixture("solved")))
    assert "sokoban_solved" not in ladder.reached
