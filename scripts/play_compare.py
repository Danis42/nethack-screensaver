"""Play the same seeds under two interpreter/tree configurations and compare the results seed by seed.

Usage: uv run python scripts/play_compare.py --python-a PY --python-b PY [--tree-a DIR] [--tree-b DIR]
                                             [--seeds 1000-1009] [--jobs 10] [--max-steps N] [--ignore FIELD]...

Used to show that a rebuilt NLE of the same commit plays exactly like the earlier build. Each game runs in
its own process with the environment of bench/runner.py (fixed hash seed, one BLAS thread, the fixed_clock
shim). Prints one JSON line per seed {"seed", "same", "diffs"} and a final line
{"compared", "identical", "watchdog_skipped", "differing_seeds"}.
Exit 0: every compared seed is identical. Exit 1: some seed differs. Exit 2: a game produced no result.
A seed whose end_reason is "watchdog" on either side is skipped (that ending depends on machine load).
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from nethack_screensaver import fixed_clock  # noqa: E402

# Must stay the same list as FIELDS in scripts/replay_check.py.
COMPARED_FIELDS = ("role", "race", "gender", "alignment", "max_depth", "turns", "score", "end_reason", "rung",
                   "ladder", "xp_level", "last_messages", "prayers", "zaps_seen", "hp_at_end", "max_hp_at_end",
                   "hunger_at_end", "depth_at_end", "food_at_end", "events")
ONE_GAME = """
import json, sys
from dataclasses import asdict
from nethack_screensaver.game import run_game
max_steps = int(sys.argv[2]) if sys.argv[2] else None
r = run_game(watchdog_seconds=120, seed=int(sys.argv[1]), max_steps=max_steps)
print(json.dumps(asdict(r)))
"""


def seeds(text):
    out = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out.extend(range(int(lo), int(hi or lo) + 1))
    return out


def play(python, tree, seed, max_steps):
    env = fixed_clock.preload_env({**os.environ, "PYTHONPATH": str(tree), "PYTHONHASHSEED": "0",
                                   "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    proc = subprocess.run([str(python), "-c", ONE_GAME, str(seed), str(max_steps or "")], cwd=tree, env=env,
                          capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
    if not lines:
        return None
    return json.loads(lines[-1])


def compare(a, b, ignore):
    """Names of the compared fields on which two results differ."""
    return [f for f in COMPARED_FIELDS if f not in ignore and a.get(f) != b.get(f)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--python-a", required=True)
    ap.add_argument("--tree-a", default=str(REPO))
    ap.add_argument("--python-b", required=True)
    ap.add_argument("--tree-b", default=str(REPO))
    ap.add_argument("--seeds", default="1000-1009", help='"LO-HI" (inclusive) or a comma list')
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--ignore", action="append", default=[], metavar="FIELD",
                    help="field left out of the comparison (repeatable)")
    args = ap.parse_args(argv)

    wanted = seeds(args.seeds)
    with ThreadPoolExecutor(max_workers=max(args.jobs, 1)) as pool:
        futures = {seed: (pool.submit(play, args.python_a, args.tree_a, seed, args.max_steps),
                          pool.submit(play, args.python_b, args.tree_b, seed, args.max_steps)) for seed in wanted}
        results = {seed: (fa.result(), fb.result()) for seed, (fa, fb) in futures.items()}

    missing = [seed for seed, (a, b) in results.items() if a is None or b is None]
    if missing:
        print(json.dumps({"error": "no result", "seeds": missing}))
        return 2
    compared = identical = 0
    watchdog, differing = [], []
    for seed in wanted:
        a, b = results[seed]
        if "watchdog" in (a.get("end_reason"), b.get("end_reason")):
            watchdog.append(seed)
            continue
        diffs = compare(a, b, set(args.ignore))
        compared += 1
        identical += not diffs
        if diffs:
            differing.append(seed)
        print(json.dumps({"seed": seed, "same": not diffs, "diffs": diffs}), flush=True)
    print(json.dumps({"compared": compared, "identical": identical, "watchdog_skipped": watchdog,
                      "differing_seeds": differing}))
    return 1 if differing else 0


if __name__ == "__main__":
    sys.exit(main())
