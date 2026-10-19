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
