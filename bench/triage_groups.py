"""Failure groups for triage (SURV-01, D-10, D-11): one system-level group per game ending, first match wins.

Each rule reads only the stored game (GameResult JSON): no replays, no LLM. Groups name the bot system that
failed (food, prayer, getting stuck, fights it should avoid), not single monsters. The order matters: specific
causes come first, so a game that starved while stuck counts as starvation.
"""
from functools import lru_cache

from .metrics import ended_stuck, killer

ANGERED = ("watch captain", "watchman", ", the shopkeeper", "priest of", "priestess of", "vault guard", "wrath of",
           " of Odin", " of Tyr", " of Loki")  # in end_reason
RANGED = ("wand", "magic missile", "bolt of", "death ray", "blast of", "arrow", "dagger", "spear", "dart",
          "crossbow bolt", "boomerang", "explosion", "spell", "knife", "shuriken", "aklys", "ranseur",
          "falling rock", "potion of", "poisoned blast")
RANGED_EXACT = ("rock", "boulder")
PASSIVE = ("jelly", "blob", "mold", "vortex", "gelatinous cube", "lichen")
HELPLESS = ("while sleeping", "while frozen", "while paralyzed", "paralyzed by", "while unconscious",
            "floating eye's gaze", "while helpless", "sleeping off")
BAD_FOOD = ("rotted", "tasting", "rotten food", "corpse", "acidic", "poisonous")
DEEP_GAP = 4  # dungeon level minus experience level at which a death counts as "too deep for its level"
STRONG_GAP = 3  # monster difficulty minus experience level at which a fight counts as one to avoid
NORMAL_SPEED = 12  # fact:normal-speed-is-12
GROUPS_MASK = 0x0080 | 0x0040  # G_SGROUP | G_LGROUP, fact:group-generation-flags


@lru_cache(maxsize=1)
def _monsters():
    """{name: (speed, difficulty, generated in groups)} for every monster name (5.0 gendered names included)."""
    import nle.nethack as nh
    out = {}
    for i in range(nh.NUMMONS):
        m = nh.permonst(i)
        for name in (m.mname, *(getattr(m, "pmnames", None) or ())):
            if name:
                out[name] = (m.mmove, m.difficulty, bool(m.geno & GROUPS_MASK))
    return out


def monster(name):
    """(speed, difficulty, in groups) of a killer name, or None when it is not a monster."""
    return _monsters().get(name)


PREFIXES = ("invisible ", "hallucinogen-distorted ")  # how NetHack names a killer it did not see clearly
FAINTING = 4  # hunger_at_end: autoascend.glyph.Hunger.FAINTING; 5 is fainted, 6 starved


def monster_killer(game):
    """killer() without the 'invisible' / 'hallucinogen-distorted' prefixes."""
    k = killer(game)
    for prefix in PREFIXES:
        k = k.removeprefix(prefix)
    if " imitating " in k:  # a chameleon fights as the monster it imitates
        k = k.split(" imitating ", 1)[1].removeprefix("an ").removeprefix("a ")
    return k


def _has(text, words):
    return any(w in text for w in words)


# (name, plain description, rule) in match order
GROUPS = [
    ("bot_crash", "the bot crashed (Cyclic Panic or another exception)",
     lambda g, r, k: r.startswith("exception")),
    ("watchdog", "the game stopped changing the screen for 120 s (watchdog)",
     lambda g, r, k: r == "watchdog"),
    ("aborted", "NetHack ended the game for lack of progress (ABORTED)",
     lambda g, r, k: r.startswith("ABORTED")),
    ("starvation", "starved, or killed while fainted from hunger: food supply and eating",
     lambda g, r, k: "starved" in r or "fainted from lack of food" in r or g.get("hunger_at_end", 0) >= FAINTING),
    ("bad_food", "ate something harmful: rotten or poisonous corpses, cockatrice meat",
     lambda g, r, k: r.startswith("DEATH") and ("poisoned by" in r or "tasting" in r or "rotten food" in r)
     and _has(r, BAD_FOOD)),
    ("prayer", "killed while praying: prayed when it could not help (timeout, wrong trouble)",
     lambda g, r, k: "while praying" in r),
    ("stoning", "turned to stone by touching or fighting a cockatrice/chickatrice",
     lambda g, r, k: "petrified" in r),
    ("helpless", "killed while asleep, frozen or paralysed: walked into a disabling attack",
     lambda g, r, k: _has(r, HELPLESS)),
    ("angered", "killed by the watch, a shopkeeper, a priest or its god: angered someone it should not",
     lambda g, r, k: _has(r, ANGERED)),
    ("stuck", "ended on a Dlvl 5+ level it could not leave (stuck explorer)",
     lambda g, r, k: ended_stuck(g)),
    ("ranged", "killed by wands, rays, missiles or explosions: no answer to ranged attacks",
     lambda g, r, k: r.startswith("DEATH") and (_has(k or r, RANGED) or k in RANGED_EXACT)),
    ("unicorns", "killed by a unicorn: fights unicorns it should leave alone",
     lambda g, r, k: k.endswith("unicorn")),
    ("passive", "killed by passive or engulfing monsters (jellies, molds, blobs, vortices)",
     lambda g, r, k: _has(k, PASSIVE)),
    ("too_deep", f"killed in melee {DEEP_GAP}+ levels deeper than its experience level: descends too fast",
     lambda g, r, k: r.startswith("DEATH") and k != "" and g["depth_at_end"] - g["xp_level"] >= DEEP_GAP),
    ("strong", f"killed by a monster {STRONG_GAP}+ difficulty above its experience level: fights it should avoid",
     lambda g, r, k: monster(k) is not None and monster(k)[1] - g["xp_level"] >= STRONG_GAP),
    ("groups", "killed by a monster that comes in groups (ants, bees, elves, soldiers, Mines natives)",
     lambda g, r, k: monster(k) is not None and monster(k)[2]),
    ("fast", "killed by a monster faster than an unhasted hero: cannot run away from it",
     lambda g, r, k: monster(k) is not None and monster(k)[0] > NORMAL_SPEED),
    ("melee", "killed in melee by a monster its level should handle: fights it lost anyway",
     lambda g, r, k: r.startswith("DEATH") and monster(k) is not None),
    ("other", "anything else", lambda g, r, k: True),
]
NAMES = [name for name, _, _ in GROUPS]
DESCRIPTIONS = {name: text for name, text, _ in GROUPS}


def classify(game):
    reason, k = game["end_reason"], monster_killer(game)
    for name, _, rule in GROUPS:
        if rule(game, reason, k):
            return name
    raise AssertionError("'other' matches everything")
