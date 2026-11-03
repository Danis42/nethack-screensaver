"""Run scenarios (scripts/scenario_lib.py) against a bot tree and report pass rates per check.

    .venv/bin/python scripts/scenario_run.py pry-cursed-dagger [--tree .worktrees/x] [--seeds 1-12] [--jobs 2]
    .venv/bin/python scripts/scenario_run.py all --jobs 10

The setup (staging.py, scenario_lib.py) always comes from THIS checkout, the bot (autoascend, game.py) from --tree,
so an older commit or a branch worktree can be tested without switching branches. Each game is its own process with
PYTHONHASHSEED=0 and the fixed clock, like the bench. Exit code 0 when every check passed on every seed.
"""
import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "scripts"))
from scenario_lib import SCENARIOS  # noqa: E402

CHILD = r"""
import importlib.util, json, sys
from dataclasses import asdict
here, name, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])

def load(modname, path):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod  # dataclasses look their module up here
    spec.loader.exec_module(mod)
    return mod

lib = load("scenario_lib", here + "/scripts/scenario_lib.py")
setup = load("setup_staging", here + "/nethack_screensaver/staging.py")  # this checkout's setup code
sc = lib.SCENARIOS[name]
stage = setup.Stage(**sc.stage)

import nethack_screensaver.staging as target   # the tested tree's module, used by its run_game
from nethack_screensaver.game import run_game

state = {"start_depth": 0}

def prepare(env, _stage):
    obs = setup.apply_stage(env, stage)
    for item in sc.eat:
        letter = setup.inventory_letter(env, item)
        if letter:
            setup.send(env, "e" + letter)
            setup.settle(env)
    for keys in sc.keys:
        setup.send(env, keys)
        setup.settle(env)
    for item, potion in sc.dips:
        a, b = setup.inventory_letter(env, item), setup.inventory_letter(env, potion)
        if a and b:
            setup.send(env, "#dip\r" + a)
            setup.settle(env)
            setup.send(env, b)
            setup.settle(env)
    for mon in sc.monsters:
        setup.send(env, [7])                    # ^G: create monster (wizard mode)
        setup.send(env, mon + "\r")
        setup.settle(env)
    obs = env._get_observation(env.last_observation)
    state["start_depth"] = int(obs["blstats"][12])
    return obs

target.STAGES[name] = stage
target.apply_stage = prepare
import os
if os.environ.get("SCENARIO_HOOK"):              # debug: a file run in this process (wrap functions, print HOOK lines)
    exec(open(os.environ["SCENARIO_HOOK"]).read())
messages, seen = [], set()

def frame(obs):
    m = bytes(obs["message"]).split(b"\0")[0].decode("latin1").strip()
    if m and m not in seen:
        seen.add(m)
        messages.append(m)

r = run_game(watchdog_seconds=120, seed=seed, stage=name, strategy=sc.strategy, on_frame=frame,
             max_steps=stage.max_steps)  # older trees do not read the stage's limit
res = asdict(r)
snaps = res.get("snapshots") or {}
inv = (snaps.get("end") or snaps.get("before_end") or {}).get("inventory", [])
print("RECORD " + json.dumps({"seed": seed, "result": res, "messages": messages, "inventory": inv,
                              "start_depth": state["start_depth"]}))
"""


def seeds(text):
    out = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out.extend(range(int(lo), int(hi or lo) + 1))
    return out


SHOW_N = int(os.environ.get("SHOW_N", "12"))
PYTHON = os.environ.get("SCREENS_BENCH_PYTHON") or str(Path.home() / ".cache/screens-nh5/venv/bin/python")


def play(tree, name, seed):
    sys.path.insert(0, str(HERE))
    from nethack_screensaver import fixed_clock  # the time() shim, as the bench workers load it
    env = fixed_clock.preload_env({**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(tree)})
    proc = subprocess.run([PYTHON, "-c", CHILD, str(HERE), name, str(seed)], cwd=tree, env=env,
                          capture_output=True, text=True, timeout=1800)
    lines = [line[7:] for line in proc.stdout.splitlines() if line.startswith("RECORD ")]
    hook = [line for line in proc.stdout.splitlines() if line.startswith("HOOK")]
    if not lines:
        tail = (proc.stderr.strip().splitlines() or ["?"])[-1]
        return {"seed": seed, "error": f"exit {proc.returncode}: {tail[:150]}"}
    rec = json.loads(lines[-1])
    rec["hook"] = hook
    return rec


def run(name, tree, seed_text, jobs, verbose, show=False):
    sc = SCENARIOS[name]
    with ThreadPoolExecutor(jobs) as pool:
        records = list(pool.map(lambda s: play(tree, name, s), seeds(seed_text or sc.seeds)))
    passed = {check: 0 for check in sc.checks}
    ok_all = True
    for rec in records:
        if "error" in rec:
            ok_all = False
            print(f"  seed {rec['seed']:4d} ERROR {rec['error']}")
            continue
        marks = {check: bool(fn(rec)) for check, fn in sc.checks.items()}
        for check, ok in marks.items():
            passed[check] += ok
        ok_all &= all(marks.values())
        res = rec["result"]
        if verbose or not all(marks.values()):
            fails = ", ".join(c for c, ok in marks.items() if not ok) or "all pass"
            print(f"  seed {rec['seed']:4d} T{res['turns']:5d} Dlvl{res.get('max_depth', 0):3d} "
                  f"{res['end_reason'][:45]:45s} | {fails}")
        if show:
            for line in rec.get("hook", []):
                print("      " + line)
            print("      inventory: " + " ; ".join(rec["inventory"]))
            print("      first messages: " + " | ".join(rec["messages"][:SHOW_N]))
    n = len(records)
    summary = "  ".join(f"{check} {count}/{n}" for check, count in passed.items())
    print(f"{name}: {summary}   ({sc.note})")
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", help="scenario name or 'all'")
    ap.add_argument("--tree", default=str(HERE), help="bot code to test (repo checkout or worktree)")
    ap.add_argument("--seeds")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--show", action="store_true", help="print each game's end inventory and first messages")
    args = ap.parse_args()
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    ok = all([run(n, Path(args.tree).resolve(), args.seeds, args.jobs, args.verbose, args.show) for n in names])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
