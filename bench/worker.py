"""Plays one NetHack game per 'play [seed [lgen]]' line on stdin and prints its result as one JSON line.

Lines: 'play' (unseeded), 'play <seed>', 'play <seed> <lgen>' (lgen = NLE level-generation seed).
A commit whose run_game cannot take lgen plays the seed alone and leaves lgen out of its result,
so the scheduler refuses it for an lgen job instead of storing a wrong-mode game.

The bench server starts this script with PYTHONPATH pointing at a commit's worktree, so the
game code comes from that commit. It must not import the bench package: old commits do not
have it. Anything the game prints goes to stderr so stdout carries only results."""
import inspect
import json
import os
import sys
from dataclasses import asdict


def parse(line):
    """'play' -> (True, None, None); 'play 17' -> (True, 17, None); 'play 17 9' -> (True, 17, 9);
    anything else -> (False, None, None)."""
    words = line.split()
    if not words or words[0] != "play" or len(words) > 3:
        return False, None, None
    numbers = [int(w) for w in words[1:]] + [None, None]
    return True, numbers[0], numbers[1]


def main():
    results = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # C code printing to fd 1 lands in the log
    sys.stdout = sys.stderr
    from nethack_screensaver.game import run_game
    can_seed = "seed" in inspect.signature(run_game).parameters  # older commits cannot
    can_lgen = "lgen" in inspect.signature(run_game).parameters

    for line in sys.stdin:
        ok, seed, lgen = parse(line)
        if not ok:
            continue
        if seed is not None and can_seed and lgen is not None and can_lgen:
            result = asdict(run_game(watchdog_seconds=120, seed=seed, lgen=lgen))
        elif seed is not None and can_seed:
            result = asdict(run_game(watchdog_seconds=120, seed=seed))
            result.pop("lgen", None)  # lgen asked for but not applied: the scheduler refuses it
        else:
            result = asdict(run_game(watchdog_seconds=120))
            result.pop("seed", None)  # unseeded: the scheduler refuses it for seeded jobs
        results.write(json.dumps(result) + "\n")
        results.flush()


if __name__ == "__main__":
    main()
