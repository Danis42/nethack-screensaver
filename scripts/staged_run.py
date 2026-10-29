"""Play seeded staged games (nethack_screensaver/staging.py) in parallel and summarise them.

    .venv/bin/python scripts/staged_run.py medusa --seeds 1-24 --jobs 4 [--out staged.jsonl]

Staged games start in wizard mode at a late-game level; their results never go into the bench store
(natural-play rates). Each game runs in its own process with PYTHONHASHSEED=0, like the bench workers.
"""
import argparse
import collections
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ONE_GAME = """
import json, sys
from dataclasses import asdict
from nethack_screensaver.game import run_game
r = run_game(watchdog_seconds=120, seed=int(sys.argv[2]), stage=sys.argv[1])
print(json.dumps(asdict(r)))
"""


def seeds(text):
    out = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out.extend(range(int(lo), int(hi or lo) + 1))
    return out


def play(stage, seed):
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(REPO)}
    proc = subprocess.run([sys.executable, "-c", ONE_GAME, stage, str(seed)], cwd=REPO, env=env,
                          capture_output=True, text=True)
    lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
    if not lines:
        return {"seed": seed, "stage": stage, "end_reason": f"no result (exit {proc.returncode})", "turns": 0}
    return json.loads(lines[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage")
    ap.add_argument("--seeds", default="1-12")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args()
    with ThreadPoolExecutor(args.jobs) as pool:
        results = list(pool.map(lambda s: play(args.stage, s), seeds(args.seeds)))
    if args.out:
        Path(args.out).write_text("".join(json.dumps(r) + "\n" for r in results))
    for r in results:
        print(f"{r['seed']:5d} T{r['turns']:6d} Dlvl{r.get('max_depth', 0):3d}  {r['end_reason'][:90]}")
    ends = collections.Counter(r["end_reason"].split(":")[0] for r in results)
    print(f"{args.stage}: {len(results)} games, median turns "
          f"{sorted(r['turns'] for r in results)[len(results) // 2]}, ends {dict(ends)}")


if __name__ == "__main__":
    main()
