"""Helpers of scripts/nld_study.py on synthetic 24x80 tty frames (no NLD-NAO data needed)."""
import sys
from pathlib import Path

import numpy as np

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
                 ("You begin praying to Tyr.", 900), ("You finish your prayer.", 903)])
    assert [p["turn"] for p in scan.prayers] == [100, 900]


def test_census_table_counts_lines():
    prayers = [{"lines": ["A.", "B."]}, {"lines": ["A."]}]
    table = nld_study.census(prayers, 10)
    assert "| 1 | 2 | A. |" in table and "| 2 | 1 | B. |" in table
