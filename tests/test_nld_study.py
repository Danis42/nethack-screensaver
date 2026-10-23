"""Helpers of scripts/nld_study.py on synthetic 24x80 tty frames (no NLD-NAO data needed)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import nld_study  # noqa: E402


def make_frame(message="", status1="", status2=""):
    frame = np.full((24, 80), ord(" "), dtype=np.uint8)
    for row, text in ((0, message), (22, status1), (23, status2)):
        data = np.frombuffer(text.encode("ascii"), dtype=np.uint8)
        frame[row, :len(data)] = data
    return frame


def test_message_line_decodes_and_strips():
    assert nld_study.message_line(make_frame("  You begin praying to Tyr.   ")) == "You begin praying to Tyr."


def test_message_line_blank_frame_is_empty():
    assert nld_study.message_line(make_frame()) == ""
    assert nld_study.message_line(np.zeros((24, 80), dtype=np.uint8)) == ""


def test_status_parses_dlvl_turn_and_hunger():
    frame = make_frame(status1="[Name the Aspirant] St:12 Dx:11 Co:13 In:10 Wi:18 Ch:11 Neutral",
                       status2="Dlvl:7 $:0 HP:14(14) Pw:9(9) AC:7 Xp:3 T:1234 Weak")
    assert nld_study.status(frame) == (7, 1234, "Weak")


def test_status_without_turn_counter_or_hunger():
    frame = make_frame(status2="Dlvl:2 $:5 HP:14(14) Pw:9(9) AC:7 Xp:1")
    assert nld_study.status(frame) == (2, None, "")


def test_status_blank_frame_is_all_unknown():
    assert nld_study.status(make_frame()) == (None, None, "")


def test_status_hunger_words():
    for word in ("Hungry", "Weak", "Fainting", "Fainted"):
        frame = make_frame(status2=f"Dlvl:4 $:0 HP:1(14) Pw:9(9) AC:7 Xp:1 T:900 {word}")
        assert nld_study.status(frame)[2] == word


def test_normalise_replaces_god_names():
    assert nld_study.normalise("You feel that Tyr is displeased.") == "You feel that <god> is displeased."
    assert nld_study.normalise("You feel that Blind Io is well-pleased.") == "You feel that <god> is well-pleased."
    assert nld_study.normalise("Thou hast angered me.") == "Thou hast angered me."


def test_sentences_split_joined_messages_and_drop_more():
    assert nld_study.sentences("You finish your prayer.  You feel a hopeful feeling.--More--") == [
        "You finish your prayer.", "You feel a hopeful feeling."]
    assert nld_study.sentences("") == []


STATUS = "Dlvl:{d} $:0 HP:14(14) Pw:9(9) AC:7 Xp:1 T:{t} {h}"


def play(messages_and_turns, hunger="Weak", dlvl=5):
    """Feed one message per frame into a GameScanner (a message that extends the previous one is a redraw)."""
    scanner = nld_study.GameScanner()
    for message, turn in messages_and_turns:
        scanner.feed(make_frame(message, status2=STATUS.format(d=dlvl, t=turn, h=hunger)))
    return scanner.finish()


def test_scanner_collects_the_lines_after_a_prayer():
    scan = play([
        ("You begin praying to Tyr.", 100),
        ("You begin praying to Tyr.  You are surrounded by a shimmering light.", 100),
        ("You finish your prayer.  You feel that Tyr is well-pleased.--More--", 103),
        ("Your stomach feels content.", 103),
        ("You hit the newt!", 104),
    ])
    assert len(scan.prayers) == 1
    prayer = scan.prayers[0]
    assert (prayer["dlvl"], prayer["turn"], prayer["hunger"]) == (5, 100, "Weak")
    assert prayer["lines"] == ["You are surrounded by a shimmering light.", "You finish your prayer.",
                               "You feel that <god> is well-pleased.", "Your stomach feels content."]


def test_scanner_reads_hunger_before_the_prayer_fixes_it():
    scanner = nld_study.GameScanner()
    for message, hunger in (("You begin praying to Tyr.", "Weak"), ("Your stomach feels content.", "")):
        scanner.feed(make_frame(message, status2=STATUS.format(d=5, t=100, h=hunger)))
    prayer = scanner.finish().prayers[0]
    assert prayer["hunger"] == "Weak"


def test_scanner_ignores_partial_redraws():
    scan = play([
        ("You begin praying to Tyr.", 10),
        ("You begin praying to Tyr.  You fini", 10),
        ("You begin praying to Tyr.  You finish your prayer.", 10),
    ])
    assert scan.prayers[0]["lines"] == ["You finish your prayer."]


def test_scanner_drops_a_message_cut_by_the_80_column_line():
    cut = "You begin praying to Tyr.  You are surrounded by a shimmering light.  You finish"
    assert len(cut) >= 78
    scan = play([(cut, 10)])
    assert scan.prayers[0]["lines"] == ["You are surrounded by a shimmering light."]


def test_scanner_stops_at_the_next_move_and_at_prompts():
    scan = play([
        ("You begin praying to Tyr.", 100),
        ("You finish your prayer.", 103),
        ("Pick up what?", 103),
        ("You hit the newt!", 110),
    ])
    assert scan.prayers[0]["lines"] == ["You finish your prayer."]
    scan = play([("You begin praying to Tyr.", 100), ("You finish your prayer.", 103), ("You hit the newt!", 110)])
    assert scan.prayers[0]["lines"] == ["You finish your prayer."]


def test_scanner_keeps_the_angry_gods_question():
    scan = play([("You begin praying to Tyr.", 100), ('"Thou durst call upon me?"', 103)])
    assert scan.prayers[0]["lines"] == ['"Thou durst call upon me?"']


def test_scanner_two_prayers_in_one_game():
    scan = play([("You begin praying to Tyr.", 100), ("You finish your prayer.", 103),
                 ("You begin praying to Tyr.", 400), ("You finish your prayer.", 403)])
    assert [p["turn"] for p in scan.prayers] == [100, 400]


def test_census_table_counts_lines():
    prayers = [{"lines": ["A.", "B."]}, {"lines": ["A."]}]
    table = nld_study.census(prayers, 10)
    assert "| 1 | 2 | A. |" in table and "| 2 | 1 | B. |" in table


# ---- food study (task 2) ----

@pytest.mark.parametrize("line", [
    "You finish eating the food ration.",
    "This newt corpse tastes terrible!",
    "This lump of royal jelly is delicious!",
    "You're having a hard time getting all of it down.",
    "You stop eating the gnome corpse.",
    "That food really hit the spot!",
])
def test_eat_event_true(line):
    assert nld_study.eat_event(line)


@pytest.mark.parametrize("line", [
    "You see here a food ration.",
    "With great effort you move the boulder.",
    "There is a gnome corpse here; eat it? [ynq] (n)",
    "This door is locked.",
    "",
])
def test_eat_event_false(line):
    assert not nld_study.eat_event(line)


def readings(*items):
    return [make_frame(status2=STATUS.format(d=d, t=t, h=h)) for d, t, h in items]


def test_band_turns_counts_turn_deltas_while_dlvl_in_band():
    result = nld_study.band_turns(readings((3, 100, ""), (4, 110, ""), (4, 130, "Hungry"), (5, 140, "Weak"),
                                           (13, 150, ""), (13, 400, "")))
    # each delta belongs to the earlier reading: 100->110 on dlvl 3 (outside), 110->130 on dlvl 4 (20),
    # 130->140 on dlvl 4 Hungry (10), 140->150 on dlvl 5 Weak (10), 150->400 on dlvl 13 (outside)
    assert result.total == 40
    assert result.hungry == 20  # Hungry for 10 turns, then Weak for 10 more
    assert result.weak == 10
    assert result.excluded == 0


def test_band_turns_excludes_frames_without_turn_counter():
    frames = readings((5, 100, ""), (5, 120, "")) + [make_frame(status2="Dlvl:5 $:0 HP:14(14) Pw:9(9) AC:7 Xp:1")]
    result = nld_study.band_turns(frames)
    assert result.total == 20
    assert result.excluded == 1


def test_band_turns_ignores_a_turn_counter_that_goes_backwards():
    # a status line caught half-drawn reads T:1 instead of T:120; it must not erase or double count time
    result = nld_study.band_turns(readings((5, 100, ""), (5, 1, ""), (5, 120, "")))
    assert result.total == 20


def test_band_turns_edges_of_the_band_are_included():
    assert nld_study.band_turns(readings((4, 0, ""), (4, 10, ""))).total == 10
    assert nld_study.band_turns(readings((12, 0, ""), (12, 10, ""))).total == 10
    assert nld_study.band_turns(readings((3, 0, ""), (3, 10, ""))).total == 0
    assert nld_study.band_turns(readings((13, 0, ""), (13, 10, ""))).total == 0


def test_scanner_counts_meals_once_when_opener_and_closer_both_show():
    scan = play([("This gnome corpse tastes terrible!", 100), ("You finish eating the gnome corpse.", 112),
                 ("You finish eating the food ration.", 300), ("That food really hit the spot!", 300),
                 ("This carrot is delicious!", 500)])
    assert [m["turn"] for m in scan.meals] == [100, 300, 500]


def test_scanner_an_interrupted_meal_is_one_meal():
    scan = play([("You stop eating the gnome corpse.", 100), ("You finish eating the gnome corpse.", 120)])
    assert len(scan.meals) == 1


def test_scanner_records_band_and_hunger_time_and_prayers():
    scanner = nld_study.GameScanner()
    for d, t, h, msg in [(3, 10, "", ""), (4, 20, "", ""), (4, 120, "Weak", "You begin praying to Tyr."),
                         (4, 123, "", "You are surrounded by a shimmering light."), (4, 200, "", "")]:
        scanner.feed(make_frame(msg, status2=STATUS.format(d=d, t=t, h=h)))
    record = scanner.finish().record()
    assert record["has_turn"] is True
    assert record["band_turns"] == 180
    assert record["weak_turns"] == 3 and record["hungry_turns"] == 3  # the Weak reading at 120 covers 120->123
    assert record["prayers"] == [{"turn": 120, "hunger": "Weak", "outcome": "success"}]


def test_scanner_without_turn_counter_is_excluded_in_the_record():
    scanner = nld_study.GameScanner()
    scanner.feed(make_frame("You hit it.", status2="Dlvl:5 $:0 HP:14(14) Pw:9(9) AC:7 Xp:1"))
    assert scanner.finish().record()["has_turn"] is False


def game(band=1000, hungry=0, weak=0, prayers=(), meals=0, has_turn=True, coverage=1.0):
    return {"has_turn": has_turn, "coverage": coverage, "band_turns": band, "hungry_turns": hungry, "weak_turns": weak,
            "prayers": [{"turn": t, "hunger": h, "outcome": o} for t, h, o in prayers], "meals": meals}


def test_summarize_cohort_medians_and_shares():
    records = [
        game(band=2000, hungry=200, weak=100, meals=4, prayers=[(500, "Weak", "success"), (1200, "", "failed")]),
        game(band=1000, hungry=0, weak=0, meals=2, prayers=[(300, "Weak", "success")]),
        game(band=3000, hungry=300, weak=0, meals=6),
        game(has_turn=False),
    ]
    s = nld_study.summarize(records)
    assert (s["games_used"], s["games_excluded"]) == (3, 1)
    assert s["median_band_turns"] == 2000
    assert s["prayers"] == 3
    assert s["prayers_per_1000"] == pytest.approx(3 / 6000 * 1000)
    assert s["gaps"] == [700]
    assert s["median_gap"] == 700
    assert s["share_prayers_weak"] == pytest.approx(2 / 3)
    assert s["share_prayers_failed"] == pytest.approx(1 / 3)
    assert s["meals_per_1000"] == pytest.approx(12 / 6000 * 1000)
    assert s["share_hungry"] == pytest.approx(500 / 6000)
    assert s["share_weak"] == pytest.approx(100 / 6000)


def test_summarize_empty_cohort_has_no_numbers():
    s = nld_study.summarize([])
    assert s["games_used"] == 0 and s["median_band_turns"] is None and s["median_gap"] is None
    assert s["prayers_per_1000"] is None and s["share_prayers_weak"] is None


def test_food_table_has_the_rows_plan_01_08_compares_against():
    table = nld_study.food_table({"through": nld_study.summarize([game(prayers=[(1, "", "success")])]),
                                  "starved": nld_study.summarize([game()])})
    for row in ("prayers per 1000 band turns", "median gap between prayers", "share of prayers while Weak or worse",
                "share of prayers that failed", "eating events per 1000 band turns",
                "share of band turns Hungry or worse", "share of band turns Weak or worse", "games used / excluded"):
        assert row in table


def test_status_ignores_a_row_with_pieces_of_the_attribute_line():
    frame = make_frame(status2="Dlvl:2  $:536  HP:12(12)  Pw:3(3)  AC:7  Xp:1/0  T:5498 Wi:17 Ch:9")
    assert nld_study.status(frame) == (None, None, "")


def test_status_reads_the_long_layout_with_double_spaces():
    frame = make_frame(status2="Dlvl:5  $:6778  HP:60(60)  Pw:111(111)  AC:-2  Xp:10  T:1472  Hungry")
    assert nld_study.status(frame) == (5, 1472, "Hungry")


def test_band_turns_drops_a_jump_the_next_reading_does_not_confirm():
    # T:5498 for a moment, then the real counter again: the 5000-turn jump must not count
    result = nld_study.band_turns(readings((5, 100, ""), (5, 5498, ""), (5, 110, ""), (5, 130, "")))
    assert result.total == 30


def test_band_turns_keeps_a_long_jump_that_the_next_reading_confirms():
    result = nld_study.band_turns(readings((5, 100, ""), (5, 900, ""), (5, 905, "")))
    assert result.total == 805


def test_band_clock_ignores_turns_beyond_the_real_game_length():
    clock = nld_study.BandClock(max_turn=500)
    for reading in ((5, 100, ""), (5, 90000, ""), (5, 300, "")):
        clock.update(reading)
    assert clock.total == 200


def test_summarize_excludes_games_whose_status_line_was_mostly_unreadable():
    s = nld_study.summarize([game(band=1000), game(band=5000, coverage=0.5), game(band=3000, coverage=0.8),
                             game(band=9000, coverage=None)])
    assert (s["games_used"], s["games_excluded"]) == (3, 1)
    assert s["band_turns"] == 1000 + 3000 + 9000


def test_scanner_record_reports_coverage_of_the_real_game_length():
    scanner = nld_study.GameScanner(max_turn=400)
    for t in (1, 100, 200):
        scanner.feed(make_frame(status2=STATUS.format(d=5, t=t, h="")))
    assert scanner.finish().record()["coverage"] == pytest.approx(0.5)
    assert nld_study.GameScanner().finish().record()["coverage"] is None


def test_summarize_gap_rows():
    records = [game(prayers=[(100, "Weak", "success"), (400, "Weak", "failed"), (2000, "", "success"),
                             (2300, "", "failed")])]
    s = nld_study.summarize(records)
    assert s["gaps"] == [300, 1600, 300]
    assert s["share_gaps_under_500"] == pytest.approx(2 / 3)
    assert s["failed_after_short_gap"] == (2, 2)  # the prayers at 400 and 2300 both failed after a short gap
    assert s["failed_after_long_gap"] == (0, 1)
    assert s["gap_p25"] == 300
