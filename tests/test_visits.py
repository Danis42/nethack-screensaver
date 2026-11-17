import numpy as np

from nethack_screensaver import visits
from test_snapshots import obs


def test_visit_log_keeps_first_turn_and_milestones_in_order():
    rec = visits.Recorder()
    rec.observe(obs(turn=1, dnum=0, dlevel=1), milestone="BE_ON_FIRST_LEVEL")
    rec.observe(obs(turn=50, dnum=0, dlevel=1), milestone="FIND_SOKOBAN")
    rec.observe(obs(turn=60, dnum=2, dlevel=3, depth=3), milestone="FIND_SOKOBAN")
    rec.observe(obs(turn=70, dnum=0, dlevel=1), milestone="BE_ON_FIRST_LEVEL")
    v = rec.result()["visits"]
    assert v == {"0:1": {"turn": 1, "milestones": ["BE_ON_FIRST_LEVEL", "FIND_SOKOBAN"]},
                 "2:3": {"turn": 60, "milestones": ["FIND_SOKOBAN"]}}


def test_visit_log_ignores_the_game_over_observation_and_keeps_snapshots():
    rec = visits.Recorder()
    rec.observe(obs(turn=5), milestone="X")
    o = obs()
    o["blstats"] = np.zeros(27, dtype=np.int64)
    rec.observe(o, milestone="Y")
    r = rec.result()
    assert r["visits"] == {"0:1": {"turn": 5, "milestones": ["X"]}}
    assert set(r) >= {"depth", "rung", "end", "before_end", "visits"}


def test_visit_log_without_a_milestone_records_the_place_only():
    rec = visits.Recorder()
    rec.observe(obs(turn=3))
    assert rec.result()["visits"] == {"0:1": {"turn": 3, "milestones": []}}
