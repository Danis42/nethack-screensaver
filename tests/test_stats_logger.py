import re
from pathlib import Path

from autoascend.stats_logger import StatsLogger

AUTOASCEND = Path(__file__).parent.parent / "autoascend"


def test_stats_logger_knows_every_logged_event():
    src = "".join(p.read_text() for p in AUTOASCEND.rglob("*.py"))
    names = set(re.findall(r"log_event\('([a-z_]+)'\)", src))
    assert names
    logger = StatsLogger()
    for name in sorted(names):
        logger.log_event(name)  # KeyError for an unknown name crashes the game


def test_sokoban_drop_level_events_are_known_for_every_sokoban_level():
    logger = StatsLogger()
    for level in range(1, 5):  # global_logic logs f'sokoban_drop_level_{level_number}'; the regex above misses it
        logger.log_event(f"sokoban_drop_level_{level}")


def test_counters_and_add():
    import pytest
    logger = StatsLogger()
    assert logger.counters() == {}
    logger.add("unstick", 3)
    logger.log_event("agent_panic")
    assert logger.counters() == {"unstick": 3, "agent_panic": 1}
    with pytest.raises(KeyError):
        logger.add("no_such_counter")
