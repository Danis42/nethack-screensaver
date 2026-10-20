"""Plays one NetHack game per 'play' line on stdin and prints its result as one JSON line.

The bench server starts this script with PYTHONPATH pointing at a commit's worktree, so the
game code comes from that commit. It must not import the bench package: old commits do not
have it. Anything the game prints goes to stderr so stdout carries only results."""
import json
import os
import sys
from dataclasses import asdict


def main():
    results = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # C code printing to fd 1 lands in the log
    sys.stdout = sys.stderr
    from nethack_screensaver.game import run_game

    for line in sys.stdin:
        if line.strip() != "play":
            continue
        result = run_game(watchdog_seconds=120)
        results.write(json.dumps(asdict(result)) + "\n")
        results.flush()


if __name__ == "__main__":
    main()
