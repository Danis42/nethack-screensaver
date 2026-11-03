"""Hand-played NetHack 5 games (Claude plays by hand to refine the ascension playbook).

One seeded game runs in a background server; each client call sends commands and prints what the hero sees.
A restarted server starts the game fresh (no key log: owner, 2026-11-03).

  python scripts/handplay.py serve --seed 7 --dir .planning/hand-games/seed7      # background
  python scripts/handplay.py do --dir ... 'look'
  python scripts/handplay.py do --dir ... 'go 12 5' 'kick h' 'move hhj' 'fight y 5'

Coordinates are SCREEN coordinates: x = column, y = row of the terminal (the map is rows 1-21). The map print
has a column ruler on top and the row number at the right end of each line, so nothing shifts the columns.

Commands (one per argument; a batch stops at the first command that fails):
  look                   map, status, messages, what is around the hero
  keys <k...>            raw keys: plain chars, <esc> <ret> <sp> <tab> <bs>, ^X for control-X
  move <dirs>            single steps (yuhjklbn), stops when a step does not move the hero
  run <dir>              shift-run in one direction
  go <x> <y> | go < | go > | go _    travel; reports whether the hero arrived
  fight <dir> [n]        attack a monster there, up to n times, while it is still there
  kick <dir>             only at a closed door; kicks until it opens (max 12) or something else happens
  open <dir>             only at a closed door
  search [n]             search n turns (default 10)
--More-- is dismissed automatically and its text is listed under "msgs".
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nethack_screensaver import fixed_clock  # noqa: E402

TOKENS = {"<esc>": 27, "<ret>": 13, "<sp>": 32, "<tab>": 9, "<bs>": 8}
DIRS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1), "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1)}
NAMES = {"y": "NW", "k": "N", "u": "NE", "h": "W", "l": "E", "b": "SW", "j": "S", "n": "SE"}
OBS_KEYS = ("glyphs", "blstats", "tty_chars", "tty_cursor", "screen_descriptions", "message", "inv_strs",
            "inv_letters", "inv_oclasses")


def parse_keys(args: list[str]) -> list[int]:
    keys: list[int] = []
    for arg in args:
        i = 0
        while i < len(arg):
            m = re.match(r"<[a-z]+>", arg[i:])
            if m and m.group(0) in TOKENS:
                keys.append(TOKENS[m.group(0)])
                i += len(m.group(0))
            elif arg[i] == "^" and i + 1 < len(arg):
                keys.append(ord(arg[i + 1].upper()) & 0x1F)
                i += 2
            else:
                keys.append(ord(arg[i]))
                i += 1
    return keys


class Game:
    def __init__(self, seed: int, stage: str | None = None):
        fixed_clock.pin(seed)
        from nle.env.tasks import NetHackChallenge
        from nethack_screensaver import staging
        from nethack_screensaver.game import CHARACTER
        # a staged game (staging.py): wizard mode, kit by wishes, teleport to the stage level
        env_class = NetHackChallenge if stage is None else staging.StagedChallenge
        self.env = env_class(no_progress_timeout=10**9, fix_moon_phase=True, character=CHARACTER,
                             observation_keys=OBS_KEYS)
        type(self.env.nethack).set_initial_seeds(self.env.nethack, seed, seed, False)
        self.env.reset()
        if stage is not None:
            staging.apply_stage(self.env, staging.STAGES[stage])
        self.done = False
        self.msgs: list[str] = []

    # --- raw access -------------------------------------------------------------------------------------------
    def obs(self, name):
        return self.env.last_observation[self.env._observation_keys.index(name)]

    def key(self, k: int):
        if self.done:
            return
        self.env.last_observation, self.done = self.env.nethack.step(k)

    def lines(self) -> list[str]:
        return [bytes(r).decode("latin1").rstrip() for r in self.obs("tty_chars")]

    def stat(self, i: int) -> int:
        return int(self.obs("blstats")[i])

    def pos(self) -> tuple[int, int]:  # screen coordinates
        return self.stat(0), self.stat(1) + 1

    def turn(self) -> int:
        return self.stat(20)

    def descr(self, x: int, y: int) -> str:
        if not (0 <= x < 79 and 1 <= y <= 21):
            return "off the map"
        raw = bytes(self.obs("screen_descriptions")[y - 1][x]).split(b"\0")[0].decode("latin1")
        return raw or "unexplored/dark"

    def glyph(self, x: int, y: int) -> int:
        if not (0 <= x < 79 and 1 <= y <= 21):
            return 0
        return int(self.obs("glyphs")[y - 1][x])

    def is_monster(self, x: int, y: int) -> bool:
        import nle.nethack as nh
        if not (0 <= x < 79 and 1 <= y <= 21):
            return False
        g = self.glyph(x, y)
        return bool(nh.glyph_is_monster(g) and not nh.glyph_is_pet(g)) and (x, y) != self.pos()

    def settle(self):
        """Dismiss --More-- (collecting its text) until none is left."""
        for _ in range(30):
            ls = self.lines()
            rows = [i for i, l in enumerate(ls) if "--More--" in l]
            if not rows or self.done:
                break
            text = " ".join(l.strip() for l in ls[: rows[0] + 1] if l.strip()) if rows[0] < 3 else \
                " / ".join(l.strip() for l in ls[: rows[0] + 1] if l.strip())
            self.msgs.append(text.replace("--More--", "").strip())
            self.key(13)
        top = self.lines()[0].strip()
        if top and (not self.msgs or top not in self.msgs[-1]):
            self.msgs.append(top)

    def send(self, keys: list[int]):
        for k in keys:
            self.key(k)
        self.settle()

    # --- commands ---------------------------------------------------------------------------------------------
    def target(self, d: str) -> tuple[int, int]:
        x, y = self.pos()
        dx, dy = DIRS[d]
        return x + dx, y + dy

    def c_move(self, dirs: str) -> str:
        for d in dirs:
            if d not in DIRS:
                return f"FAIL bad direction {d!r}"
            before, t = self.pos(), self.turn()
            tgt = self.target(d)
            if self.is_monster(*tgt):
                return f"FAIL {NAMES[d]} is a monster ({self.descr(*tgt)}); use fight"
            self.send([ord(d)])
            if self.pos() == before:
                return f"FAIL step {d} blocked at {before}: {NAMES[d]} is {self.descr(*tgt)}"
            if self.adjacent_monsters():
                return f"STOPPED at {self.pos()}: monster adjacent: " + ", ".join(self.adjacent_monsters())
        return f"ok at {self.pos()}"

    def c_run(self, d: str) -> str:
        before = self.pos()
        self.send([ord(d.upper())])
        return f"ok {before} -> {self.pos()}" if self.pos() != before else \
            f"FAIL did not move: {NAMES[d]} is {self.descr(*self.target(d))}"

    def c_go(self, *args) -> str:
        if len(args) == 1 and args[0] in "<>_":
            self.send([ord("_"), ord(args[0]), ord(".")])
            return f"travel {args[0]}: now at {self.pos()} on {self.descr(*self.pos())!r}"
        tx, ty = int(args[0]), int(args[1])
        for _ in range(4):  # travel stops when something comes into view; resume
            x, y = self.pos()
            if (x, y) == (tx, ty):
                break
            keys = [ord("_"), ord("@")]
            dx, dy = tx - x, ty - y
            while dx or dy:
                sx, sy = (dx > 0) - (dx < 0), (dy > 0) - (dy < 0)
                d = next(k for k, v in DIRS.items() if v == (sx, sy))
                big = min(abs(dx) if sx else 99, abs(dy) if sy else 99) >= 8
                keys.append(ord(d.upper() if big else d))
                step = 8 if big else 1
                dx -= sx * step
                dy -= sy * step
            keys.append(ord("."))
            t, hp = self.turn(), self.stat(10)
            self.send(keys)
            if self.turn() == t:
                break
            if self.stat(10) < hp or self.adjacent_monsters():  # never walk on while something attacks
                return (f"STOPPED at {self.pos()}: " + (f"HP {hp}->{self.stat(10)} " if self.stat(10) < hp else "")
                        + "monster adjacent: " + ", ".join(self.adjacent_monsters()))
        ok = self.pos() == (tx, ty)
        return f"{'ok' if ok else 'FAIL'} now at {self.pos()}" + ("" if ok else f", target is {self.descr(tx, ty)!r}")

    PASSIVE = ("floating eye", "peaceful")  # never attack on their own: no reason to stop next to them

    def adjacent_monsters(self, threats_only: bool = True) -> list[str]:
        x, y = self.pos()
        out = [f"{NAMES[d]} {self.descr(x + dx, y + dy)}" for d, (dx, dy) in DIRS.items()
               if self.is_monster(x + dx, y + dy)]
        return [m for m in out if not any(p in m for p in self.PASSIVE)] if threats_only else out

    def c_fight(self, d: str, n: str = "1") -> str:
        out = []
        for _ in range(int(n)):
            tgt = self.target(d)
            if not self.is_monster(*tgt):
                return "; ".join(out) + f"; now no monster {NAMES[d]}" if out else \
                    f"FAIL no monster {NAMES[d]}: it is {self.descr(*tgt)}"
            n_msgs = len(self.msgs)
            self.send([ord("F"), ord(d)])
            out.append(f"[{' '.join(self.msgs[n_msgs:])}] HP{self.stat(10)}")
            if self.stat(10) * 3 < self.stat(11):
                return "; ".join(out) + " STOP: HP below 1/3"
        return "; ".join(out)

    def door_check(self, d: str) -> str | None:
        desc = self.descr(*self.target(d))
        if "door" not in desc or any(w in desc for w in ("open", "broken", "doorway", "no door")):
            return f"FAIL {NAMES[d]} is {desc!r}, not a closed door"
        return None

    def c_kick(self, d: str) -> str:
        if (err := self.door_check(d)):
            return err
        for i in range(12):
            self.send([4, ord(d)])
            last = self.msgs[-1] if self.msgs else ""
            if not any(w in last.upper() for w in ("WHAMM", "THWACK")):
                return f"kick {i + 1}: {last}"
        return "FAIL still closed after 12 kicks"

    def c_open(self, d: str) -> str:
        if (err := self.door_check(d)):
            return err
        self.send([ord("o"), ord(d)])
        last = self.msgs[-1] if self.msgs else "?"
        return ("FAIL " + last + " (use kick)") if "locked" in last else last

    def c_search(self, n: str = "10") -> str:
        t, hp = self.turn(), self.stat(10)
        self.send(parse_keys([f"{int(n)}s"]))
        if self.stat(10) < hp or self.adjacent_monsters():
            return (f"STOPPED after {self.turn() - t} turns: HP {hp}->{self.stat(10)}; adjacent: "
                    + (", ".join(self.adjacent_monsters()) or "none"))
        return f"ok ({self.turn() - t} turns)"

    def c_keys(self, *ks) -> str:
        self.send(parse_keys(list(ks)))
        return "ok"

    def c_look(self) -> str:
        return "ok"

    # --- view -------------------------------------------------------------------------------------------------
    def view(self, show_map: bool = True) -> str:
        ls = self.lines()
        x, y = self.pos()
        out = [f"T{self.turn()} pos ({x},{y}) on {self.descr(x, y)!r}" + ("  GAME OVER" if self.done else "")]
        out += [ls[22], ls[23]]
        if self.msgs:
            out.append("msgs: " + " | ".join(self.msgs))
        around = [f"{NAMES[d]}: {self.descr(x + dx, y + dy)}" for d, (dx, dy) in DIRS.items()]
        out.append("around: " + ", ".join(around))
        if self.adjacent_monsters(False):
            out.append("ADJACENT: " + ", ".join(self.adjacent_monsters(False)))
        mons = [f"{self.descr(cx, cy)} at ({cx},{cy})" for cy in range(1, 22) for cx in range(79)
                if self.is_monster(cx, cy)]
        if mons:
            out.append("monsters: " + "; ".join(mons))
        import nle.nethack as nh
        objs, feats = [], []
        for cy in range(1, 22):
            for cx in range(79):
                g = self.glyph(cx, cy)
                if (cx, cy) == (x, y):
                    continue
                if nh.glyph_is_object(g) or nh.glyph_is_body(g) or nh.glyph_is_statue(g):
                    objs.append(f"{self.descr(cx, cy)} ({cx},{cy})")
                elif nh.glyph_is_cmap(g):
                    dsc = self.descr(cx, cy)
                    if any(w in dsc for w in ("stair", "ladder", "altar", "fountain", "sink", "throne", "grave",
                                              "tree", "trap", "hole", "web", "portal")) or "door" in dsc \
                            and not any(w in dsc for w in ("open", "broken", "doorway", "no door")):
                        feats.append(f"{dsc} ({cx},{cy})")
                elif nh.glyph_is_trap(g):
                    feats.append(f"{self.descr(cx, cy)} ({cx},{cy})")
        if objs:
            out.append("objects: " + "; ".join(objs))
        if feats:
            out.append("features: " + "; ".join(feats))
        if any(l.strip() for l in ls[1:22]) and show_map:
            used = [i for i in range(1, 22) if ls[i].strip()]
            width = max(len(ls[i]) for i in used)
            left = min(len(ls[i]) - len(ls[i].lstrip()) for i in used)
            left -= left % 10
            out.append("     " + "".join(str(c // 10 % 10) if c % 10 == 0 else " " for c in range(left, width)))
            out.append("     " + "".join(str(c % 10) for c in range(left, width)))
            for i in used:
                out.append(f"r{i:02d}  " + ls[i][left:].ljust(width - left) + f"  r{i:02d}")
            out.append(f"(columns start at {left})")
        elif any(l.strip() for l in ls[1:22]):
            pass
        # menus and text windows are not map: show raw lines when the screen holds one
        if any(m in "".join(ls) for m in ("(end)", "(1 of", "(2 of", "(3 of")):
            out.append("screen:\n" + "\n".join(l for l in ls[:22] if l.strip()))
        return "\n".join(out)

    def run(self, cmds: list[str], show_map: bool) -> str:
        self.msgs = []
        results = []
        for c in cmds:
            parts = c.split()
            fn = getattr(self, "c_" + parts[0], None) if parts else None
            if fn is None:
                results.append(f"{c}: FAIL unknown command")
                break
            try:
                r = fn(*parts[1:])
            except (TypeError, ValueError, KeyError) as e:
                r = f"FAIL {e}"
            results.append(f"{c}: {r}")
            if r.startswith(("FAIL", "STOPPED")) or "STOP:" in r or self.done:
                break
        return "\n".join(results) + "\n" + self.view(show_map)


def serve(seed: int, d: Path, stage: str | None = None):
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({"seed": seed, "stage": stage}))
    game = Game(seed, stage)
    sock_path = d / "sock"
    sock_path.unlink(missing_ok=True)
    srv = socket.socket(socket.AF_UNIX)
    srv.bind(str(sock_path))
    srv.listen(1)
    print("ready", flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            req = json.loads(conn.makefile().readline())
            if req.get("quit"):
                conn.sendall(b"bye\n")
                break
            try:
                reply = game.run(req["cmds"], req.get("map", True))
            except Exception as e:  # keep the game alive on a tool bug
                reply = f"TOOL ERROR {type(e).__name__}: {e}"
            conn.sendall((reply + "\n").encode("latin1", "replace"))
    sock_path.unlink(missing_ok=True)


def client(d: Path, req: dict) -> str:
    s = socket.socket(socket.AF_UNIX)
    s.connect(str(d / "sock"))
    s.sendall((json.dumps(req) + "\n").encode())
    return s.makefile(encoding="latin1").read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["serve", "do", "quit"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--nomap", action="store_true")
    ap.add_argument("--stage", help="staged start (nethack_screensaver/staging.py STAGES), wizard mode")
    a = ap.parse_args()
    if a.cmd == "serve":
        fixed_clock.ensure_preloaded()
        serve(a.seed, a.dir, a.stage)
    elif a.cmd == "quit":
        print(client(a.dir, {"quit": True}), end="")
    else:
        print(client(a.dir, {"cmds": a.args or ["look"], "map": not a.nomap}), end="")


if __name__ == "__main__":
    main()
