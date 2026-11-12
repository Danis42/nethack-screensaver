"""Plan soko1-2 (NetHack 5.0) pushes on the true board from dat/soko1-2.lua, placed onto screen coordinates
by matching the recorded T1 observation. Planning aid only; the game itself is played by hand."""
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(".")
sys.path.insert(0, str(REPO))
from autoascend.soko_solver.search import solve  # noqa: E402

LUA = (REPO / "reference/nethack-5.0.0/dat/soko1-2.lua").read_text()


def lua_board():
    rows = re.search(r"des\.map\(\[\[\n(.*?)\]\]\)", LUA, re.S)[1].split("\n")
    floor = {(y, x) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "."}
    doors = {(y, x) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "+"}
    boulders = {(int(y), int(x)) for x, y in re.findall(r'des\.object\("boulder",\s*(\d+),\s*(\d+)\)', LUA)}
    holes = {(int(y), int(x)) for x, y in re.findall(r'des\.trap\("hole",\s*(\d+),\s*(\d+)\)', LUA)}
    rolling = {(int(y), int(x)) for x, y in re.findall(r'des\.trap\("rolling boulder",\s*(\d+),\s*(\d+)\)', LUA)}
    h, w = len(rows), max(len(r) for r in rows)
    return floor, doors, boulders, holes, rolling, h, w


def placed(start):
    """The lua board in fixture (row, col) coordinates: the flip and offset that fit the T1 observation."""
    floor, doors, boulders, holes, rolling, h, w = lua_board()
    seen_b = {tuple(b) for b in start["boulders"]}
    seen_t = {tuple(t) for t in start["traps"]}
    best = None
    for fy in (False, True):
        for fx in (False, True):
            f = lambda p: ((h - 1 - p[0]) if fy else p[0], (w - 1 - p[1]) if fx else p[1])
            traps = {f(p) for p in holes | rolling}
            # offset from any trap pairing
            for ty, tx in seen_t:
                for ly, lx in traps:
                    oy, ox = ty - ly, tx - lx
                    mv = lambda s: {(y + oy, x + ox) for y, x in s}
                    score = len(mv(traps) & seen_t) + len(mv({f(p) for p in boulders}) & seen_b)
                    if best is None or score > best[0]:
                        best = (score, fy, fx, oy, ox)
    score, fy, fx, oy, ox = best
    f = lambda p: (((h - 1 - p[0]) if fy else p[0]) + oy, ((w - 1 - p[1]) if fx else p[1]) + ox)
    return {"flip_y": fy, "flip_x": fx, "offset": (oy, ox), "score": score,
            "floor": {f(p) for p in floor}, "doors": {f(p) for p in doors}, "boulders": {f(p) for p in boulders},
            "holes": {f(p) for p in holes}, "rolling": {f(p) for p in rolling}}


if __name__ == "__main__":
    start = json.load(open(REPO / "tests/data/soko_top_hand_start.json"))
    b = placed(start)
    seen_b = {tuple(x) for x in start["boulders"]}
    print("flip_y", b["flip_y"], "flip_x", b["flip_x"], "offset", b["offset"], "match score", b["score"])
    print("boulders lua", len(b["boulders"]), "seen", len(seen_b), "seen-not-lua", seen_b - b["boulders"],
          "lua-not-seen", b["boulders"] - seen_b)
    print("traps seen-not-lua", {tuple(x) for x in start["traps"]} - b["holes"] - b["rolling"],
          "lua-not-seen", (b["holes"] | b["rolling"]) - {tuple(x) for x in start["traps"]})
    print("rolling", b["rolling"], "player", start["player"])
    player = tuple(map(int, sys.argv[1].split(","))) if len(sys.argv) > 1 else tuple(start["player"])
    t = time.time()
    plan = solve(b["floor"] | b["rolling"], b["boulders"] - {player} if False else b["boulders"], b["holes"], player,
                 max_states=3_000_000, max_seconds=None)
    print("plan", None if plan is None else len(plan), "pushes in", round(time.time() - t, 1), "s")
    if plan:
        json.dump({"board": {k: sorted(v) if isinstance(v, set) else v for k, v in b.items()}, "plan": plan},
                  open(Path(__file__).with_name("sokoplan.json"), "w"))
