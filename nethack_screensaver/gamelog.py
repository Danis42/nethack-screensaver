import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from nethack_screensaver.game import GameResult


@dataclass(frozen=True)
class LogStats:
    games: int
    best_depth: int


def append_result(path: Path, result: GameResult, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    record = {"timestamp": now.isoformat(timespec="seconds"), **asdict(result)}
    with Path(path).open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_stats(path: Path) -> LogStats:
    games = best = 0
    try:
        lines = Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return LogStats(0, 0)
    for line in lines:
        try:
            depth = json.loads(line)["max_depth"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if not isinstance(depth, int):
            continue
        games += 1
        best = max(best, depth)
    return LogStats(games, best)
