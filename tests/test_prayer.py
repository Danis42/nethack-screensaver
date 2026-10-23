"""autoascend.prayer: the classifier of the lines after a prayer, from messages seen in human games."""
import pytest

from autoascend.prayer import FAILURE_MARKERS, PRAYER_START, SUCCESS_MARKERS, prayer_outcome


def test_success_with_shimmering_light_and_hopeful_feeling():
    lines = ["You are surrounded by a shimmering light.", "You finish your prayer.", "You feel a hopeful feeling."]
    assert prayer_outcome(lines) == "success"


def test_failure_displeased():
    assert prayer_outcome(["You finish your prayer.", "You feel that Tyr is displeased."]) == "failed"


def test_empty_and_unrelated_are_unknown():
    assert prayer_outcome([]) == "unknown"
    assert prayer_outcome(["Something unrelated."]) == "unknown"
    assert prayer_outcome(["You finish your prayer."]) == "unknown"


@pytest.mark.parametrize("god", ["Tyr", "Blind Io", "Shan Lai Ching", "The Lady", "Anhur"])
def test_god_name_does_not_matter(god):
    assert prayer_outcome([f"You feel that {god} is well-pleased."]) == "success"
    assert prayer_outcome([f"You feel that {god} is pleased."]) == "success"
    assert prayer_outcome([f"You feel that {god} is satisfied."]) == "success"
    assert prayer_outcome([f"You feel that {god} is displeased."]) == "failed"


@pytest.mark.parametrize("marker", SUCCESS_MARKERS)
def test_every_success_marker(marker):
    assert prayer_outcome(["You begin something.", f"  {marker}"]) == "success"


@pytest.mark.parametrize("marker", FAILURE_MARKERS)
def test_every_failure_marker(marker):
    assert prayer_outcome([marker]) == "failed"


def test_failure_wins_over_success():
    assert prayer_outcome(["You are surrounded by a shimmering light.", "Thou hast angered me."]) == "failed"
    assert prayer_outcome(["The voice of Kos booms out: \"Thou hast angered me.\""]) == "failed"


def test_displeased_is_not_mistaken_for_pleased():
    assert "is pleased." not in "You feel that Tyr is displeased."
    assert prayer_outcome(["You feel that Odin is displeased."]) == "failed"


def test_dying_while_praying_is_a_failure():
    assert prayer_outcome(["The soldier ant bites!", "You die..."]) == "failed"


def test_invulnerable_hero_attacked_is_success():
    assert prayer_outcome(["The jackal starts to attack you, but pulls back."]) == "success"


def test_accepts_any_iterable():
    assert prayer_outcome(iter(["Your stomach feels content."])) == "success"


def test_markers_hold_no_god_names():
    for marker in SUCCESS_MARKERS + FAILURE_MARKERS:
        assert PRAYER_START not in marker
        for god in ("Tyr", "Odin", "Anhur", "Thoth", "Mars", "Kos"):
            assert god not in marker
