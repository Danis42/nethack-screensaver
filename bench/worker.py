"""Plays one NetHack game per 'play [seed]' line on stdin and prints its result as one JSON line.

The bench server starts this script with PYTHONPATH pointing at a commit's worktree, so the
game code comes from that commit. It must not import the bench package: old commits do not
have it. Anything the game prints goes to stderr so stdout carries only results."""
import inspect
import json
import os
import sys
from dataclasses import asdict


def parse(line):
    """'play' -> (True, None); 'play 17' -> (True, 17); anything else -> (False, None)."""
    words = line.split()
    if not words or words[0] != "play" or len(words) > 2:
        return False, None
    return True, int(words[1]) if len(words) == 2 else None


def main():
    results = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # C code printing to fd 1 lands in the log
    sys.stdout = sys.stderr
    from nethack_screensaver.game import run_game
    can_seed = "seed" in inspect.signature(run_game).parameters  # older commits cannot

    for line in sys.stdin:
        ok, seed = parse(line)
        if not ok:
            continue
        if seed is not None and can_seed:
            result = asdict(run_game(watchdog_seconds=120, seed=seed))
        else:
            result = asdict(run_game(watchdog_seconds=120))
            result.pop("seed", None)  # unseeded: the scheduler refuses it for seeded jobs
        results.write(json.dumps(result) + "\n")
        results.flush()


if __name__ == "__main__":
    main()
