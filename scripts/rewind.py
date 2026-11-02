"""Infinite lives (research only, never in play): when a seeded game dies, replay it from the start and change
NetHack's dice a little before the death, then keep going. Shows how far the bot gets with retries and which
deaths were bad luck (survived by a reseed 100 turns back) or something older (needs 1000 or 5000 turns back).

A replay is exact: same seed, same bot, same reseeds -> same game (checked 2026-11-02). Reseeds change the core
and display RNGs only (NLE screens-nh5 cb9d6572f: lgen 0), so levels not yet made come from the new dice too.

    python scripts/rewind.py --seeds 0-19 --procs 11 --out runs.jsonl
"""
import argparse
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
BACKS = (100, 1000, 5000)  # turns to rewind, tried in order
TRIES = 5  # reseeds per rewind distance
SURVIVED = 200  # a retry survives a death when it lives this many turns past it
MAX_LIVES = 60


def play_child(seed: int, history: list) -> dict:
    """Runs inside the child: one game with reseeds [(turn, new_seed), ...] applied at the first frame at/after turn."""
    from nethack_screensaver import game

    envs, pending, applied = [], sorted(history), []

    class Capture(game.NetHackChallenge):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            envs.append(self)

    game.NetHackChallenge = Capture

    def on_frame(obs):
        turn = int(obs["blstats"][game.TURN])
        while pending and turn and turn >= pending[0][0]:
            t, new = pending.pop(0)
            nh = envs[-1].nethack
            type(nh).set_current_seeds(nh, new, new, False, 0)  # lgen 0: dice only
            applied.append([t, turn])

    r = game.run_game(watchdog_seconds=120, seed=seed, on_frame=on_frame)
    end = (r.snapshots or {}).get("end") or {}
    return {"turns": r.turns, "end_reason": r.end_reason, "max_depth": r.max_depth, "rung": r.rung,
            "ladder": r.ladder, "xp_level": r.xp_level, "applied": applied, "last_messages": r.last_messages[-3:],
            "end": {k: end.get(k) for k in ("turn", "depth", "dungeon", "level", "xl", "hp", "hpmax", "ac", "gear")}}


def play(seed: int, history: list) -> dict:
    from nethack_screensaver import fixed_clock
    env = fixed_clock.preload_env({**os.environ, "PYTHONPATH": str(ROOT), "PYTHONHASHSEED": "0",
                                   "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    out = subprocess.run([sys.executable, __file__, "--child", str(seed), json.dumps(history)], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    lines = [ln for ln in out.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        return {"turns": 0, "end_reason": f"child failed: {out.stderr[-300:]}", "max_depth": 0, "rung": 0}
    return json.loads(lines[-1])


def died(r: dict) -> bool:
    return r["end_reason"].startswith("DEATH")


def new_seed(seed: int, n: int) -> int:
    return (seed * 1_000_003 + 7919 * (n + 1)) % (2 ** 63)


def run_seed(seed: int) -> dict:
    """Plays one seed with retries; returns the life story."""
    history, deaths, lives, n = [], [], 1, 0
    r = play(seed, history)
    first = {k: r.get(k) for k in ("turns", "end_reason", "max_depth", "rung")}
    while died(r) and lives < MAX_LIVES:
        d = r["turns"]
        saved = None
        tries = []
        for back in BACKS:
            t = max(1, d - back)
            for _ in range(TRIES):
                h2 = [h for h in history if h[0] < t] + [[t, new_seed(seed, n)]]
                n += 1
                r2 = play(seed, h2)
                lives += 1
                tries.append([back, r2["turns"], r2["end_reason"][:60]])
                if not died(r2) or r2["turns"] > d + SURVIVED:
                    saved = (back, h2, r2)
                    break
                if lives >= MAX_LIVES:
                    break
            if saved or lives >= MAX_LIVES:
                break
        deaths.append({"turn": d, "depth": r["max_depth"], "dlvl_at_end": (r.get("end") or {}).get("depth"),
                       "end_reason": r["end_reason"], "end": r.get("end"), "saved_by": saved[0] if saved else None,
                       "tries": tries})
        if not saved:
            break
        _, history, r = saved
    return {"seed": seed, "first_life": first, "lives": lives, "deaths": deaths,
            "final": {k: r.get(k) for k in ("turns", "end_reason", "max_depth", "rung", "ladder", "xp_level", "end")},
            "history": history}


def seeds_arg(text: str) -> list:
    out = []
    for part in text.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        result = play_child(int(sys.argv[2]), json.loads(sys.argv[3]))
        sys.stdout = sys.__stdout__
        print(json.dumps(result), flush=True)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--procs", type=int, default=11)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    todo, lock = seeds_arg(args.seeds), threading.Lock()
    out = open(args.out, "a")

    def worker():
        while True:
            with lock:
                if not todo:
                    return
                seed = todo.pop(0)
            story = run_seed(seed)
            with lock:
                out.write(json.dumps(story) + "\n")
                out.flush()
                f = story["final"]
                print(f"seed {seed}: lives {story['lives']}, Dlvl {story['first_life']['max_depth']} -> {f['max_depth']},"
                      f" rung {story['first_life']['rung']} -> {f['rung']}, {f['end_reason'][:50]}", flush=True)

    threads = [threading.Thread(target=worker) for _ in range(args.procs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
