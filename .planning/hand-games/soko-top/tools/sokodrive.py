"""Play the validated soko1-2 push list in the running handplay server, checking the live board after every push.
Stops at the first surprise and prints why; rerun with --from N to continue."""
import argparse
import json
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCR = Path(__file__).parent
D = REPO / ".planning/hand-games/soko-top"
LOG = D / "pushes-attempt4.log"
sys.path.insert(0, str(SCR))
from sokosim import FLOOR, ROLL, B  # noqa: E402

KEY = {(-1, 0): "k", (1, 0): "j", (0, -1): "h", (0, 1): "l"}


def do(*cmds):
    r = subprocess.run([str(REPO / ".venv/bin/python"), str(REPO / "scripts/handplay.py"), "do", "--dir", str(D),
                        "--nomap", *cmds], capture_output=True, text=True)
    return r.stdout


def observed():
    tmp = SCR / "obs.json"
    do(f"record {tmp} driver")
    o = json.loads(tmp.read_text())
    return {tuple(b) for b in o["boulders"]}, {tuple(t) for t in o["traps"]}, tuple(o["player"]), o["level"], o["turn"]


def path(start, goal, boulders, holes):
    free = FLOOR - boulders - holes
    prev, todo = {start: None}, deque([start])
    while todo:
        p = todo.popleft()
        if p == goal:
            break
        for d in KEY:
            n = (p[0] + d[0], p[1] + d[1])
            if n in free and n not in prev:
                prev[n] = (p, d)
                todo.append(n)
    if goal not in prev:
        return None
    out, p = [], goal
    while prev[p] is not None:
        p, d = prev[p]
        out.append(KEY[d])
    return "".join(reversed(out))


def log(line):
    with open(LOG, "a") as f:
        f.write(line + "\n")
    print(line, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--max", type=int, default=10_000)
    a = ap.parse_args()
    plan = [((tuple(b), tuple(d))) for b, d in json.load(open(SCR / "sokosim.json"))]
    model_b, model_h = set(B["boulders"]), set(B["holes"])
    for (by, bx), (dy, dx) in plan[:a.start]:  # replay the model up to --from
        model_b.discard((by, bx))
        dest = (by + dy, bx + dx)
        if dest in model_h:
            model_h.discard(dest)
        else:
            model_b.add(dest)
    for i in range(a.start, min(len(plan), a.start + a.max)):
        (by, bx), (dy, dx) = plan[i]
        ob, ot, hero, level, turn = observed()
        if level != 1:
            return log(f"STOP push {i}: hero on Sokoban level {level} (T{turn})")
        extra = ob - model_b  # mimics look like boulders in Sokoban (makemon.c set_mimic_sym): obstacles
        if extra and extra != getattr(main, "seen_extra", set()):
            log(f"note push {i}: unexplained boulders (mimics?) at {sorted(extra)} (T{turn})")
            main.seen_extra = extra
        dest0 = (by + dy, bx + dx)
        if dest0 in extra or (by - dy, bx - dx) in extra:
            return log(f"STOP push {i}: an unexplained boulder blocks {dest0 if dest0 in extra else (by - dy, bx - dx)}")
        if (by, bx) not in model_b:
            return log(f"STOP push {i}: model has no boulder at {(by, bx)}")
        frm = (by - dy, bx - dx)
        walk = path(hero, frm, model_b | extra, model_h)
        if walk is None:
            return log(f"STOP push {i}: no path from {hero} to {frm} (T{turn})")
        keys = walk + KEY[(dy, dx)]
        out = ""
        for attempt in range(6):
            out = do(f"move {keys}")
            first = out.splitlines()[0] if out else ""
            if "FAIL" in first and "monster" in first:
                do("search 1")  # a pet or monster on the path: let it move
                _, _, hero, _, _ = observed()
                walk = path(hero, frm, model_b | extra, model_h)
                if walk is None:
                    return log(f"STOP push {i}: no path after waiting ({first})")
                keys = walk + KEY[(dy, dx)]
                continue
            break
        first = out.splitlines()[0] if out else "no output"
        msgs = next((ln for ln in out.splitlines() if ln.startswith("msgs:")), "")
        if "Really" in msgs or "?" in msgs and "rolling" in msgs:
            return log(f"STOP push {i}: prompt: {msgs}")
        if "rolling boulder" in msgs.lower() or "Click" in msgs:
            log(f"note push {i}: {msgs}")
        if not first.split(": ", 1)[-1].startswith("ok"):
            return log(f"STOP push {i}: {first} | {msgs}")
        model_b.discard((by, bx))
        dest = (by + dy, bx + dx)
        if dest in model_h:
            model_h.discard(dest)
            what = f"dropped into hole {dest}"
        else:
            model_b.add(dest)
            what = f"to {dest}"
        ob, ot, hero, level, turn = observed()
        if hero != (by, bx):
            return log(f"STOP push {i}: hero at {hero}, expected {(by, bx)} | {msgs}")
        log(f"push {i} T{turn} boulder {(by, bx)} {KEY[(dy, dx)]} {what}; open holes {len(model_h)}"
            + (f" | {msgs}" if msgs and msgs != "msgs: " else ""))
        if not model_h:
            return log(f"SOLVED after push {i} (T{turn})")


if __name__ == "__main__":
    main()
