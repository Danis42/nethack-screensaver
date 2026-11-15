"""Failure triage (SURV-01): one group per ending, first match wins, gains add up, stable output."""
from bench import triage
from bench.triage_groups import NAMES, classify


def g(reason, depth=5, xl=5, ladder=(), seed=1, **kw):
    return {"end_reason": reason, "max_depth": depth, "depth_at_end": depth, "xp_level": xl, "seed": seed,
            "ladder": {k: 1 for k in ladder}, "dungeon_at_end": 0, "level_at_end": depth, "stuck_reports": [],
            "unsticks": 0, **kw}


def test_each_group_has_a_matching_ending():
    cases = {
        "bot_crash": g("exception: RuntimeError: Cyclic Panic"),
        "watchdog": g("watchdog"),
        "aborted": g("ABORTED: the Fighter St:18"),
        "starvation": g("DEATH: killed by a jackal, while fainted from lack of food"),
        "bad_food": g("DEATH: poisoned by a rotted gnome corpse"),
        "prayer": g("DEATH: killed by a gargoyle, while praying"),
        "stoning": g("DEATH: petrified by a cockatrice"),
        "helpless": g("DEATH: killed by a jackal, while sleeping"),
        "angered": g("DEATH: killed by Asidonhopo, the shopkeeper"),
        "stuck": g("DEATH: killed by a jackal", depth=7, unsticks=1),
        "ranged": g("DEATH: killed by a wand"),
        "unicorns": g("DEATH: killed by a white unicorn"),
        "passive": g("DEATH: killed by a spotted jelly"),
        "too_deep": g("DEATH: killed by a jackal", depth=12, xl=4),
        "strong": g("DEATH: killed by a troll", xl=5),
        "groups": g("DEATH: killed by a hill orc", xl=8),
        "fast": g("DEATH: killed by a pony", xl=8),
        "melee": g("DEATH: killed by a newt", xl=8),
        "other": g("DEATH: fell into a pit"),
    }
    assert set(cases) == set(NAMES)
    for name, game in cases.items():
        assert classify(game) == name, (name, game["end_reason"])


def test_first_match_wins():
    assert classify(g("DEATH: killed by a soldier ant, while fainted from lack of food", depth=7, unsticks=1)) == \
        "starvation"


def test_gains_use_conditional_odds_and_add_up():
    games = [g("DEATH: killed by a newt", xl=8, ladder=("mines",), seed=s) for s in range(3)] + \
            [g("DEATH: killed by a newt", xl=8, ladder=("mines", "minetown"), seed=3, depth=12)]
    out = triage.rank(games)
    assert out["n"] == 4 and sum(r["count"] for r in out["groups"]) == 4
    melee = next(r for r in out["groups"] if r["group"] == "melee")
    # 3 games stop at 'mines', where 1 of 4 went on: 0.75; 1 game at 'minetown': P(oracle | minetown) = 0
    assert melee["stage_gain"] == 0.8  # 0.75 rounded to one decimal
    # games ending at depth 5: 1 of 4 that reached Dlvl 5 reached Dlvl 10
    assert melee["dlvl10_gain"] == 0.8


def test_rank_is_stable():
    games = [g("DEATH: killed by a newt", xl=8, seed=s) for s in range(5)] + [g("watchdog", seed=9)]
    assert triage.rank(games) == triage.rank(list(reversed(games)))


def test_replay_check_fixes():
    """Rules refined after the replay check of 2026-11-15 (02-TRIAGE.md)."""
    assert classify(g("DEATH: killed by a hallucinogen-distorted soldier ant", xl=8)) == "groups"
    assert classify(g("DEATH: killed by an invisible soldier ant", xl=8)) == "groups"
    assert classify(g("DEATH: killed by a chameleon imitating a minotaur", xl=8)) == "strong"
    assert classify(g("DEATH: killed by a grid bug", xl=8, hunger_at_end=4)) == "starvation"
    assert classify(g("DEATH: killed by brainlessness", xl=8)) == "other"
    assert classify(g("DEATH: killed by an air elemental of Odin", xl=8)) == "angered"
