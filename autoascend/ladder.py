"""The ascension ladder: 18 rungs from the Gnomish Mines to an ascension.

"Quest portal" (MEAS-02, D-21) is its own stage: reached when the magic portal is found
(its trap glyph is on the level map) or entered. "Quest" is Home 1.

Standard library only, so the bench server can import the rung list. The bot hands over
plain Facts once per step; no glyph or agent code lives here. Level numbers are NetHack's
level numbers inside each dungeon (Sokoban 1 is its top level, Astral is Planes level 1)."""
from dataclasses import dataclass

DOOM, GEHENNOM, MINES, QUEST, SOKOBAN, LUDIOS, VLAD, PLANES = range(8)  # dungeon.def order
MINES_END_WAIT = 1000  # proxy, when the layout is unknown: turns on Mines level 8 without a down staircase
SOKOBAN_DRAWN = 100  # squares seen before "no trap left" means anything (Sokoban levels are lit)
VIBRATION = "You feel a strange vibration"


@dataclass(frozen=True)
class Rung:
    number: int
    key: str
    title: str
    yardstick_event: str | None  # first-time event in real ascensions' dumplogs, if there is one


RUNGS = tuple(Rung(i + 1, *r) for i, r in enumerate([
    ("mines", "Gnomish Mines", "entered the Gnomish Mines"),
    ("minetown", "Minetown", "reached Mine Town"),
    ("oracle", "Oracle", None),
    ("sokoban", "Sokoban", "entered Sokoban"),
    ("sokoban_solved", "Sokoban solved", "completed 4th Sokoban level"),
    ("mines_end", "Mines' End", "acquired the Mines' End luckstone"),
    ("dlvl15", "Dlvl 15+", None),
    ("quest_portal", "Quest portal", None),
    ("quest", "Quest", "entered Home 1, the Quest"),
    ("medusa", "Medusa", "killed Medusa"),
    ("castle", "Castle", None),
    ("gehennom", "Gehennom", "entered Gehennom"),
    ("vlad", "Vlad's Tower", "destroyed Vlad the Impaler"),
    ("wizard_tower", "Wizard's Tower", "acquired the Book of the Dead"),
    ("invocation", "Invocation", "performed the invocation"),
    ("planes", "Elemental Planes", "entered the Elemental Planes"),
    ("astral", "Astral Plane", "entered the Astral Plane"),
    ("ascended", "Ascended", "ascended"),
]))
BY_KEY = {r.key: r for r in RUNGS}


@dataclass(frozen=True)
class Facts:
    turn: int
    dungeon: int
    level: int
    oracle_seen: bool = False
    minetown_seen: bool = False
    sokoban_seen: int = 0  # squares seen on the current level
    sokoban_traps: bool = True  # a trap glyph is left on the current level
    medusa_seen: bool = False
    water_share: float = 0.0  # share of the seen squares that are water
    drawbridge_seen: bool = False
    down_stairs_seen: bool = False
    inventory: tuple[str, ...] = ()
    message: str = ""
    mines_end_level: int | None = None  # the game's real last Mines level, when the measuring side knows it
    quest_portal_found: bool = False  # magic portal glyph on this level, or the activation message


@dataclass
class _Memory:
    here: tuple[int, int] | None = None
    arrived: int = 0  # turn the bot arrived on `here`
    vibration_level: int | None = None  # Gehennom level of the vibrating square
    sokoban_traps_seen: bool = False  # saw a hole on Sokoban level 1, so "none left" means solved


def _mines_end(f, m):
    if f.dungeon != MINES:
        return False
    if f.mines_end_level is not None:
        return f.level == f.mines_end_level
    return f.level >= 9 or (f.level == 8 and not f.down_stairs_seen and f.turn - m.arrived >= MINES_END_WAIT)


DETECTORS = {
    "mines": lambda f, m: f.dungeon == MINES,
    "minetown": lambda f, m: f.minetown_seen,
    "oracle": lambda f, m: f.oracle_seen,
    "sokoban": lambda f, m: f.dungeon == SOKOBAN,
    "sokoban_solved": lambda f, m: (f.dungeon, f.level) == (SOKOBAN, 1) and f.sokoban_seen >= SOKOBAN_DRAWN
                                   and m.sokoban_traps_seen and not f.sokoban_traps,  # fact:sokoban-entry-is-bottom-level
    "mines_end": _mines_end,
    "dlvl15": lambda f, m: f.dungeon == DOOM and f.level >= 15,
    # fact:quest-portal-entered-message, quest-portal-level-call
    "quest_portal": lambda f, m: f.quest_portal_found or f.dungeon == QUEST,  # in the Quest: it was entered
    "quest": lambda f, m: f.dungeon == QUEST,
    "medusa": lambda f, m: f.dungeon == DOOM and f.level >= 21 and (f.medusa_seen or f.water_share > 1 / 3),
    "castle": lambda f, m: f.dungeon == DOOM and f.drawbridge_seen,
    "gehennom": lambda f, m: f.dungeon == GEHENNOM,
    "vlad": lambda f, m: f.dungeon == VLAD,
    "wizard_tower": lambda f, m: any("Book of the Dead" in name or "papyrus spellbook" in name for name in f.inventory),
    "invocation": lambda f, m: f.dungeon == GEHENNOM and m.vibration_level is not None
                               and f.level > m.vibration_level,
    "planes": lambda f, m: f.dungeon == PLANES,
    "astral": lambda f, m: (f.dungeon, f.level) == (PLANES, 1),
    "ascended": lambda f, m: False,  # only the end of the game tells, see Ladder.finish
}


class Ladder:
    def __init__(self):
        self.reached = {}  # rung key -> turn first reached
        self._memory = _Memory()

    def observe(self, facts: Facts) -> None:
        m = self._memory
        here = (facts.dungeon, facts.level)
        if here != m.here:
            m.here, m.arrived = here, facts.turn
        if here == (SOKOBAN, 1) and facts.sokoban_traps:
            m.sokoban_traps_seen = True
        if facts.dungeon == GEHENNOM and VIBRATION in facts.message:
            m.vibration_level = facts.level
        for rung in RUNGS:
            if rung.key not in self.reached and DETECTORS[rung.key](facts, m):
                self.reached[rung.key] = facts.turn

    def finish(self, end_reason: str, turn: int) -> None:
        if "ascended" in end_reason.lower():
            self.reached.setdefault("ascended", turn)

    def highest(self) -> int:
        return max((BY_KEY[k].number for k in self.reached), default=0)
