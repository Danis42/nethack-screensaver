"""Replay sampled baseline games of one triage group to 50 turns before their end, for a by-hand label check.

    uv run python scripts/triage_replay.py --sha <full sha> --group starvation [--n 5] [--before 50]

Seeds are sampled deterministically (sorted seeds of the group, evenly spaced). Each replay runs in its own process
from a worktree of the sha with the bench environment (fixed_clock shim, PYTHONHASHSEED=0, one BLAS thread), so it
plays exactly like the stored game, and stops at turn `turns - before`. It writes the screen, the status numbers and
the last 20 messages to .planning/phases/02-proven-change-loop/triage-replays/<group>/<seed>.txt. It writes no
database rows: these are not new games (SURV-01, D-10).
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

from bench import gitrefs, seeds as seedlib  # noqa: E402
from bench.cli import CACHE, DATA, WORKER_PYTHON  # noqa: E402
from bench.store import Store  # noqa: E402
from bench.triage_groups import classify  # noqa: E402
from nethack_screensaver import fixed_clock  # noqa: E402

OUT = REPO / ".planning" / "phases" / "02-proven-change-loop" / "triage-replays"
CHILD = """
import json, sys
from nethack_screensaver.game import run_game
seed, stop, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
messages = []

class Stop(Exception):
    pass

def frame(obs):
    msg = bytes(obs["message"]).decode(errors="replace").strip("\\x00 ")
    if msg and (not messages or messages[-1] != msg):
        messages.append(msg)
    if int(obs["blstats"][20]) >= stop:
        screen = "\\n".join(bytes(row).decode(errors="replace").rstrip() for row in obs["tty_chars"])
        with open(out, "w") as f:
            f.write(f"seed {seed}, stopped at turn {int(obs['blstats'][20])} (target {stop})\\n\\n{screen}\\n\\n")
            f.write("blstats: " + json.dumps([int(v) for v in obs["blstats"]]) + "\\n\\nlast messages:\\n")
            f.write("\\n".join(messages[-20:]) + "\\n")
        raise Stop

run_game(seed=seed, on_frame=frame, watchdog_seconds=300)
"""


def sample(seeds, n):
    seeds = sorted(seeds)
    if len(seeds) <= n:
        return seeds
    return [seeds[i * len(seeds) // n] for i in range(n)]


def replay(worktree, seed, stop, out):
    env = fixed_clock.preload_env({**os.environ, "PYTHONPATH": str(worktree), "PYTHONHASHSEED": "0",
                                   "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    subprocess.run([str(WORKER_PYTHON), "-c", CHILD, str(seed), str(stop), str(out)], env=env, cwd=worktree,
                   capture_output=True, text=True, timeout=1800)
    return out.exists()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sha", required=True)
    p.add_argument("--group", required=True)
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--before", type=int, default=50)
    p.add_argument("--lo", type=int, default=seedlib.BASELINE_WINDOW[0])
    p.add_argument("--hi", type=int, default=seedlib.BASELINE_WINDOW[1])
    p.add_argument("--jobs", type=int, default=5)
    args = p.parse_args(argv)
    sha, _ = gitrefs.resolve(REPO, args.sha)
    games = {g["seed"]: g for g in Store(DATA / "results.db").games(sha, rep=0, lo=args.lo, hi=args.hi,
                                                                       lgen_mode="off") if classify(g) == args.group}
    chosen = sample(games, args.n)
    worktree = gitrefs.ensure_worktree(REPO, sha, CACHE / "worktrees")
    out_dir = OUT / args.group
    out_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(args.jobs) as pool:
        done = list(pool.map(lambda s: replay(worktree, s, max(1, games[s]["turns"] - args.before),
                                              out_dir / f"{s}.txt"), chosen))
    for seed, ok in zip(chosen, done):
        print(json.dumps({"group": args.group, "seed": seed, "end_reason": games[seed]["end_reason"],
                          "turns": games[seed]["turns"], "replayed": ok, "file": str(out_dir / f"{seed}.txt")}))
    return 0 if all(done) else 1


if __name__ == "__main__":
    sys.exit(main())
