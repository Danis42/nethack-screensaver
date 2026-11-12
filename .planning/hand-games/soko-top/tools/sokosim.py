"""Translate the stored 3.6 soko1-2 solution onto the true 5.0 board and simulate it push by push.
Planning aid only: prints a validated push list (fixture (row, col) coordinates) for the hand game."""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, str(Path(__file__).parent))
from autoascend.soko_solver import orientations  # noqa: E402
from sokoplan import placed  # noqa: E402

start = json.load(open("tests/data/soko_top_hand_start.json"))
B = placed(start)
FLOOR = set(B["floor"]) | set(B["rolling"])
ROLL = set(B["rolling"])


def stored():
    """(orientation text, moves, offset) of the stored map whose walls/boulders fit the true board."""
    best = None
    for text, moves in orientations():
        if "|.....|--|" not in text and "|--|.....|" not in text:
            continue
        rows = text.split("\n")
        bl = {(y, x) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "0"}
        fl = {(y, x) for y, r in enumerate(rows) for x, c in enumerate(r) if c in ".0^<>?+"}
        for (by, bx) in bl:
            for (ty, tx) in B["boulders"]:
                oy, ox = ty - by, tx - bx
                s = len({(y + oy, x + ox) for y, x in bl} & B["boulders"]) + \
                    len({(y + oy, x + ox) for y, x in fl} & FLOOR)
                if best is None or s > best[0]:
                    tgt = [(y + oy, x + ox) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "^"][0]
                    hero = [(y + oy, x + ox) for y, r in enumerate(rows) for x, c in enumerate(r) if c == ">"][0]
                    best = (s, [((y + oy, x + ox), d) for (y, x), d in moves], tgt, hero, len(bl))
    return best


def reach(pos, boulders, holes):
    free = FLOOR - boulders - holes
    seen, todo = {pos}, [pos]
    while todo:
        y, x = todo.pop()
        for n in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):  # orthogonal only: the strict case
            if n in free and n not in seen:
                if n[0] != y and n[1] != x:  # diagonal: Sokoban forbids squeezing between boulders/walls? allow
                    pass
                seen.add(n)
                todo.append(n)
    return seen


def simulate(hero):
    score, moves, tgt, shero, nb = stored()
    print("stored fit", score, "target", tgt, "stored start", shero, "moves", len(moves), "stored boulders", nb)
    boulders, holes = set(B["boulders"]), set(B["holes"])
    out, i, roll_steps = [], 0, 0
    while i < len(moves):
        (by, bx), (dy, dx) = moves[i]
        if (by, bx) not in boulders:
            return out, f"stored push {i}: no boulder at {(by, bx)}", boulders, holes
        run_dir = (dy, dx)
        # one push
        frm, dest = (by - dy, bx - dx), (by + dy, bx + dx)
        if frm not in reach(hero, boulders, holes):
            return out, f"stored push {i}: hero {hero} cannot reach {frm}", boulders, holes
        if frm in ROLL:
            roll_steps += 1
        if dest not in FLOOR or dest in boulders:
            return out, f"stored push {i}: {dest} blocked", boulders, holes
        boulders.remove((by, bx))
        out.append(((by, bx), (dy, dx)))
        hero = (by, bx)
        i += 1
        if dest in holes:
            holes.remove(dest)
            if not holes:
                return out, f"solved after {len(out)} pushes, hero on rolling trap {roll_steps}x", boulders, holes
            # the stored run may continue toward the target: drop pushes of this boulder
            while i < len(moves) and moves[i][0] == dest:
                d2 = moves[i][1]
                i += 1
                dest = (dest[0] + d2[0], dest[1] + d2[1])
            continue
        boulders.add(dest)
        if dest == tgt:
            # stored run ends here; on 5.0 keep pushing along the row until the boulder drops
            cur, (ddy, ddx) = dest, run_dir
            while cur not in holes:
                nxt = (cur[0] + ddy, cur[1] + ddx)
                frm = (cur[0] - ddy, cur[1] - ddx)
                if nxt not in FLOOR or nxt in boulders or frm not in reach(hero, boulders, holes):
                    # try the other row direction is not possible: report
                    return out, f"after stored push {i - 1}: row run from {cur} dir {(ddy, ddx)} blocked", \
                        boulders, holes
                if frm in ROLL:
                    roll_steps += 1
                boulders.remove(cur)
                out.append((cur, (ddy, ddx)))
                hero = cur
                cur = nxt
                if cur in holes:
                    holes.remove(cur)
                    if not holes:
                        return out, f"solved after {len(out)} pushes, hero on rolling trap {roll_steps}x", \
                            boulders, holes
                    break
                boulders.add(cur)
    return out, f"done: {len(holes)} holes open, {len(boulders)} boulders left, hero on rolling trap {roll_steps}x", \
        boulders, holes


if __name__ == "__main__":
    hero = tuple(map(int, sys.argv[1].split(","))) if len(sys.argv) > 1 else None
    s = stored()
    plan, msg, bs, hs = simulate(hero or s[3])
    print(msg)
    print("pushes", len(plan), "open holes", sorted(hs))
    json.dump(plan, open(Path(__file__).with_name("sokosim.json"), "w"))
