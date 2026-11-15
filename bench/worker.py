"""Plays one NetHack game per stdin line ('play', 'play <seed>', 'play <seed> <lgen>', 'trace <seed> <path>') and
prints its result as one JSON line. lgen is NLE's level-generation seed; 'trace' writes the frame-hash trace of
bench/frame_trace.py to path and adds trace_digest and trace_steps. A seed or lgen the commit's run_game cannot take
is left out of the result, so the scheduler refuses it. The server starts this script with PYTHONPATH at a commit's
worktree; it must not import the bench package (old commits lack it; frame_trace is loaded by path). Anything the
game prints goes to stderr so stdout carries only results."""
import importlib.util
import inspect
import json
import os
import sys
from dataclasses import asdict


def parse(line):
    """'play' -> (True, None, None); 'play 17 9' -> (True, 17, 9); 'trace 17 /p' -> (True, 17, '/p'); else (False, ...)."""
    words = line.split()
    if len(words) == 3 and words[0] == "trace":
        return True, int(words[1]), words[2]
    if not words or words[0] != "play" or len(words) > 3:
        return False, None, None
    return (True, *([int(w) for w in words[1:]] + [None, None])[:2])


def main():
    results = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # C code printing to fd 1 lands in the log
    sys.stdout = sys.stderr
    from nethack_screensaver.game import run_game
    params = inspect.signature(run_game).parameters  # older commits cannot take seed or lgen
    spec = importlib.util.spec_from_file_location("frame_trace", os.path.join(os.path.dirname(__file__), "frame_trace.py"))
    spec.loader.exec_module(frame_trace := importlib.util.module_from_spec(spec))
    for line in sys.stdin:
        ok, seed, extra = parse(line)
        if not ok:
            continue
        trace = frame_trace.Trace(extra) if line.split()[0] == "trace" else None
        kwargs = {"seed": seed} if seed is not None and "seed" in params else {}
        if trace is None and extra is not None and "lgen" in params:
            kwargs["lgen"] = extra
        result = asdict(run_game(watchdog_seconds=120, **kwargs, **({"on_frame": trace.frame} if trace else {})))
        if trace:
            result.update(trace_digest=trace.close(), trace_steps=trace.steps)
        for key in ("seed", "lgen"):  # not applied (old commit or unseeded): the scheduler refuses such results
            if key not in kwargs:
                result.pop(key, None)
        results.write(json.dumps(result) + "\n")
        results.flush()


if __name__ == "__main__":
    main()
