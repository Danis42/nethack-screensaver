"""Rich per-game stats for the bench: snapshots of the hero at first arrival on each depth, at each
ladder rung, at the end, and about 200 turns before the end.

Recording only. The recorder reads observations (and the ladder's reached-rung keys) and nothing
else, so a seeded game plays the same with or without it. Fields per snapshot: turn, place, XL, HP,
AC, attributes, gold, hunger, encumbrance, kills and damage taken so far, worn/wielded gear, item
counts per class and the full inventory text."""
import re
from collections import deque

STR125, DEX, CON, INT, WIS, CHA = 3, 4, 5, 6, 7, 8
HP, HPMAX, DEPTH, GOLD, ENE, ENEMAX, AC = 10, 11, 12, 13, 14, 15, 16
XL, EXP, TIME, HUNGER, CAP, DNUM, DLEVEL, CONDITION = 18, 19, 20, 21, 22, 23, 24, 25

BEFORE_END = 200  # turns before the end for the "before_end" snapshot
SAMPLE_EVERY = 20  # turns between candidate before_end samples
SAMPLES_KEPT = 40  # covers 800 turns, enough for big turn jumps (sleeping, praying, fainting)

CLASSES = {1: "illobj", 2: "weapon", 3: "armor", 4: "ring", 5: "amulet", 6: "tool", 7: "food", 8: "potion",
           9: "scroll", 10: "spellbook", 11: "wand", 12: "coin", 13: "gem", 14: "rock", 15: "ball", 16: "chain",
           17: "venom"}
GEAR = ("(being worn", "(weapon in", "(wielded", "(alternate weapon", "(on left", "(on right", "(in use")
_KILL = re.compile(r"\bYou (kill|destroy) ")
_QUANTITY = re.compile(r"^(\d+) ")


def _text(row) -> str:
    return bytes(row).decode("latin1").rstrip("\x00 ")


def _inventory(obs) -> list[tuple[str, int, str]]:
    out = []
    for letter, oclass, row in zip(obs["inv_letters"], obs["inv_oclasses"], obs["inv_strs"]):
        if letter:
            out.append((chr(int(letter)), int(oclass), _text(row)))
    return out


def _quantity(text: str) -> int:
    m = _QUANTITY.match(text)
    return int(m.group(1)) if m else 1


class Recorder:
    def __init__(self):
        self._depth: dict[str, dict] = {}
        self._rung: dict[str, dict] = {}
        self._samples: deque = deque(maxlen=SAMPLES_KEPT)
        self._last_obs = None  # copies of the last observation with real blstats
        self._kills = 0
        self._damage = 0
        self._hp = None
        self._message = ""

    def observe(self, obs, rungs=()) -> None:
        bl = obs["blstats"]
        if not bl.any():  # the game-over observation is all zero
            return
        hp, turn = int(bl[HP]), int(bl[TIME])
        if self._hp is not None and hp < self._hp:
            self._damage += self._hp - hp
        self._hp = hp
        message = _text(obs["message"])
        if message != self._message:
            self._message = message
            self._kills += len(_KILL.findall(message))
        self._last_obs = {k: obs[k].copy() for k in ("blstats", "inv_strs", "inv_letters", "inv_oclasses")}
        depth = str(int(bl[DEPTH]))
        if depth not in self._depth:
            self._depth[depth] = self._snapshot(obs)
        for key in rungs:
            if key not in self._rung:
                self._rung[key] = self._snapshot(obs)
        if not self._samples or turn // SAMPLE_EVERY != self._samples[-1]["turn"] // SAMPLE_EVERY:
            self._samples.append(self._snapshot(obs))

    def _snapshot(self, obs) -> dict:
        bl = obs["blstats"]
        inv = _inventory(obs)
        counts: dict[str, int] = {}
        for _letter, oclass, text in inv:
            name = CLASSES.get(oclass, str(oclass))
            counts[name] = counts.get(name, 0) + _quantity(text)
        return {
            "turn": int(bl[TIME]), "depth": int(bl[DEPTH]), "dungeon": int(bl[DNUM]), "level": int(bl[DLEVEL]),
            "xl": int(bl[XL]), "exp": int(bl[EXP]), "hp": int(bl[HP]), "hpmax": int(bl[HPMAX]),
            "ene": int(bl[ENE]), "enemax": int(bl[ENEMAX]), "ac": int(bl[AC]),
            "str": int(bl[STR125]), "dex": int(bl[DEX]), "con": int(bl[CON]), "int": int(bl[INT]),
            "wis": int(bl[WIS]), "cha": int(bl[CHA]), "gold": int(bl[GOLD]), "hunger": int(bl[HUNGER]),
            "cap": int(bl[CAP]), "condition": int(bl[CONDITION]),
            "kills": self._kills, "damage_taken": self._damage,
            "gear": [text for _l, _c, text in inv if any(g in text for g in GEAR)],
            "counts": counts,
            "inventory": [f"{letter} - {text}" for letter, _c, text in inv],
        }

    def result(self) -> dict:
        end = before = None
        if self._last_obs is not None:
            end = self._snapshot(self._last_obs)
            cutoff = end["turn"] - BEFORE_END
            before = next((s for s in reversed(self._samples) if s["turn"] <= cutoff), None)
        return {"depth": self._depth, "rung": self._rung, "end": end, "before_end": before}
