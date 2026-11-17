import pytest

from bench.filters import parse_where
from bench.metrics import METRICS, evaluate, killer
from bench.report import compare, summary


def _g(depth=5, reason="DEATH: killed by a soldier ant, while fainted from lack of food",
       outcome="died on Dlvl 5", **extra):
    return {"max_depth": depth, "end_reason": reason, "outcome": outcome, "turns": 1000,
            "score": 500, "strategy": "pilgrim", "role": "val", **extra}


def test_killer_strips_the_article_and_the_circumstances():
    assert killer(_g()) == "soldier ant"
    assert killer(_g(reason="DEATH: killed by an Uruk-hai")) == "Uruk-hai"
    assert killer(_g(reason="ESCAPED: escaped the dungeon")) == ""


def test_rate_metrics():
    games = [_g(6), _g(10, reason="DEATH: killed by a wand"), _g(2, reason="exception: RuntimeError: x"),
             _g(3, reason="ESCAPED: escaped the dungeon", outcome="escaped")]
    assert evaluate(METRICS["dlvl6"], games)["hits"] == 2
    assert evaluate(METRICS["dlvl10"], games)["hits"] == 1
    assert evaluate(METRICS["ants"], games)["hits"] == 1
    assert evaluate(METRICS["rays"], games)["hits"] == 1
    assert evaluate(METRICS["crashed"], games)["hits"] == 1
    assert evaluate(METRICS["escaped"], games)["hits"] == 1
    assert evaluate(METRICS["starved"], games)["hits"] == 1
    assert evaluate(METRICS["dlvl6"], games)["rate"] == 0.5


def test_games_from_older_commits_without_a_field_are_skipped_not_counted():
    games = [_g(unsticks=2), _g(unsticks=0), _g()]  # the last game predates the field
    result = evaluate(METRICS["unstuck"], games)
    assert result == {"n": 2, "skipped": 1, "hits": 1, "rate": 0.5}


def test_median_metrics_and_empty_input():
    assert evaluate(METRICS["depth"], [_g(1), _g(5), _g(9)])["median"] == 5
    assert evaluate(METRICS["depth"], [])["median"] is None
    assert evaluate(METRICS["dlvl6"], [])["rate"] is None


def test_filters():
    games = [_g(3), _g(12, role="sam"), _g(7, reason="DEATH: killed by a giant bat")]
    pick = lambda where: [g["max_depth"] for g in games if parse_where(where)(g)]
    assert pick("max_depth>5") == [12, 7]
    assert pick("max_depth<5") == [3]
    assert pick("role=sam") == [12]
    assert pick("end_reason~BAT") == [7]
    assert pick("max_depth>5,end_reason~soldier") == [12]  # "giant bat" also contains "ant"
    assert pick("nosuchfield=1") == []
    assert pick("") == [3, 12, 7]
    with pytest.raises(ValueError):
        parse_where("max_depth>>5;drop")


def test_summary_and_compare():
    games = [_g(6), _g(2, reason="exception: RuntimeError: Cyclic Panic"), _g(6, unsticks=3)]
    s = summary(games)
    assert s["games"] == 3
    assert s["killers"][0] == ("soldier ant", 2)
    assert s["depths"] == {2: 1, 6: 2}
    assert s["outcomes"] == {"pilgrim": {"died": 3}}
    assert s["crashes"] == ["exception: RuntimeError: Cyclic Panic"]
    assert s["unstuck"][0]["unsticks"] == 3
    rows = {r["metric"]: r for r in compare(games, [_g(1), _g(1), _g(1)])}
    assert rows["dlvl6"]["diff"] > 0 and "lo" in rows["dlvl6"]
    assert "diff" not in rows["depth"]


from bench.report import ladder_rows
from bench.stats import Z95, wilson


def test_stage_metrics_skip_games_without_a_ladder():
    games = [_g(ladder={"mines": 900, "minetown": 3000}), _g(ladder={}), _g(), _g(ladder={"minetown": 50})]
    assert evaluate(METRICS["stage_minetown"], games) == {"n": 3, "skipped": 1, "hits": 2, "rate": 2 / 3}
    assert evaluate(METRICS["stage_mines"], games)["hits"] == 1  # marginal reach: minetown alone is not mines
    assert evaluate(METRICS["stage_oracle"], games)["hits"] == 0
    assert METRICS["stage_minetown"].description == "reached Minetown"
    assert METRICS["stage_minetown"].kind == "rate"
    stages = [n for n in METRICS if n.startswith("stage_")]
    assert len(stages) == 18 and "stage_quest_portal" in stages and "stage_ascended" in stages
    assert not [n for n in METRICS if n.startswith("rung")]


def test_ladder_rows_compare_with_the_yardstick():
    games = [_g(ladder={"mines": 1000, "sokoban": 8000}), _g(ladder={"mines": 2000}), _g()]
    rows = {r["key"]: r for r in ladder_rows(games, {"entered the Gnomish Mines": 1173})}
    assert len(rows) == 18
    lo, hi = wilson(2, 2, Z95)
    assert rows["mines"] == {"order": 1, "key": "mines", "title": "Gnomish Mines", "hits": 2, "n": 2, "rate": 1.0,
                             "lo": lo, "hi": hi, "median_turn": 1500, "yardstick_turn": 1173}
    assert rows["oracle"]["hits"] == 0 and rows["oracle"]["median_turn"] is None  # marginal: sokoban is not oracle
    assert rows["sokoban"]["hits"] == 1 and rows["sokoban"]["median_turn"] == 8000
    assert rows["ascended"]["hits"] == 0 and rows["ascended"]["yardstick_turn"] is None
    assert summary(games)["ladder"][0]["n"] == 2
    assert summary([])["ladder"][0]["n"] == 0 and summary([])["ladder"][0]["rate"] is None


def test_summary_carries_the_funnel():
    games = [_g(ladder={"mines": 1, "quest_portal": 9}), _g()]
    f = summary(games)["funnel"]
    assert len(f["rows"]) == 18 and f["n"] == 1 and f["excluded"] == {"no_ladder": 1}
    assert {r["key"]: r["hits"] for r in f["rows"]}["quest_portal"] == 1


def test_unicorn_deaths_lower_is_better():
    games = [_g(reason="DEATH: killed by a white unicorn"), _g(reason="DEATH: killed by a black unicorn, while helpless"),
             _g(reason="DEATH: killed by a jackal")]
    assert evaluate(METRICS["unicorns"], games)["hits"] == 2
    assert METRICS["unicorns"].lower_is_better
