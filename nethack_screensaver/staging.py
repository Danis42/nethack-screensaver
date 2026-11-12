"""Staged games: start a late-game situation (level, experience level, kit) in NetHack's wizard mode.

Never used for natural play. The stage is set up with wizard commands before the bot takes over:
^V with the "?" menu teleports to a named special level (works for branches such as the Quest or Vlad's
Tower), #levelchange sets the experience level, ^W wishes for the kit and ^I identifies the inventory.
NLE's wizkit option does not reach our NetHack 5 build ("NetHack asked for env variable WIZKIT"), so the
kit comes from wishes. Dying in wizard mode asks "Die?"; StagedChallenge answers yes so a death stays one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import nle.env.base as nle_base
import nle.nethack as nethack
from nle.env.tasks import NetHackChallenge

ENTER, ESC = 13, 27
CTRL_I, CTRL_T, CTRL_V, CTRL_W, CTRL_X = 9, 20, 22, 23, 24
MORE = ("--More--", "(end)")
# wizard-only prompts: a death stays a death; skills advance only with practice
WIZARD_PROMPTS = {"Die?": "y", "Advance skills without practice?": "n",
                  "Where do you want to be teleported?": "\x1b",  # wizard has teleport control
                  # no wizard luck: pray.c:2233 forced success, pray.c:1790 sure gift, teleport.c:869, steed.c:185
                  "Force the gods to be pleased?": "n", "Gift an artifact?": "n", "Override?": "n",
                  "Force the mount to succeed?": "n"}


@dataclass(frozen=True)
class Stage:
    level: str | None  # special level name as the ^V menu lists it ("medusa", "castle", "Val-strt"); None stays put
    xl: int = 1
    wishes: tuple[str, ...] = field(default_factory=tuple)
    wield: str | None = "long sword"  # wielded before the teleport (part of the item's name)
    strategy: str = "daredevil"  # plan for the bot (autoascend/plans.py): a deep start dives, not back to the Mines
    identify: bool = True  # False keeps the kit unidentified (price groups, read-testing)
    max_steps: int | None = None  # item tests stop early: the check is the inventory, not survival
    quaff: tuple[str, ...] = field(default_factory=tuple)  # potions drunk before the bot starts (inventory text)
    drop: tuple[str, ...] = field(default_factory=tuple)  # items put on the floor before the bot starts
    eat: tuple[str, ...] = field(default_factory=tuple)  # eaten before the teleport (inventory text), e.g. an eye
    # a natural arrival comes down the stairs: stand on the up stairs (the hero's way back), not a random spot
    on_upstairs: bool = True


# A kit that a bot reaching the level could plausibly have (ASCENSION-PLAN-NH5.md); grows with the phases.
MIDGAME_KIT = ("blessed +2 dwarvish mithril coat", "blessed +2 dwarvish iron helm", "blessed +2 iron shoes",
               "pick-axe", "blessed fixed +2 long sword", "4 blessed potions of extra healing",
               "uncursed unicorn horn", "2 lizard corpses", "blindfold")
# Human 3.6 ascensions at arrival on Medusa's level (72 NLD-NAO games, 59 with a Medusa kill, 2026-11-05):
# AC median -14 (p75 -11, p90 -9), XL 13, max HP 110. MIDGAME_KIT alone gives about AC -10; these two make -14.
MEDUSA_ARMOUR = ("blessed +0 cloak of protection", "blessed +0 leather gloves")
STAGES = {
    # human 5.0 ascenders (MEDUSA-NH5.md, 199 dumplogs): levitation item 85 %, telepathic 95 %, reflection 83 %
    "medusa": Stage("medusa", xl=14, wishes=MIDGAME_KIT + MEDUSA_ARMOUR + (
        "blessed amulet of reflection", "blessed ring of levitation", "floating eye corpse"),
        eat=("floating eye corpse",)),
    # the Castle comes after Medusa: at least the Medusa stage's kit (armour, telepathy)
    "castle": Stage("castle", xl=14, wishes=MIDGAME_KIT + MEDUSA_ARMOUR + (
        "blessed amulet of reflection", "blessed ring of levitation", "wooden flute", "floating eye corpse"),
        eat=("floating eye corpse",)),
    "quest": Stage("Val-strt", xl=14, wishes=MIDGAME_KIT),
    "valley": Stage("valley", xl=16, wishes=MIDGAME_KIT + ("blessed +2 gray dragon scale mail",
                                                          "blessed amulet of reflection",
                                                          "blessed ring of levitation")),
}
# Item-skill tests (Phase 02.2 Part 1a): Dlvl 1, the kit in the pack (not worn), a short game; the check is
# the end-of-game inventory and the bot's event counters (scripts/staged_run.py prints both).
ITEM_TESTS = {
    "kit-accessories": Stage(None, xl=8, wield=None, max_steps=1500, wishes=(
        "uncursed ring of slow digestion", "uncursed ring of free action", "uncursed ring of teleportation",
        "uncursed amulet of life saving", "uncursed amulet of strangulation")),
    "kit-armour": Stage(None, xl=8, wield=None, max_steps=1500, wishes=(
        "uncursed +0 cloak of magic resistance", "uncursed +3 elven cloak", "uncursed +0 speed boots",
        "uncursed +2 fumble boots", "uncursed +0 levitation boots")),
    "kit-unihorn": Stage(None, xl=8, wield=None, max_steps=300, quaff=("hallucination", "confusion"), wishes=(
        "uncursed unicorn horn", "uncursed potion of confusion", "uncursed potion of hallucination")),
    "kit-scrolls": Stage(None, xl=8, wield=None, max_steps=1500, wishes=(
        "uncursed +0 plate mail", "2 uncursed scrolls of enchant armor", "uncursed scroll of remove curse",
        "cursed -1 leather gloves", "uncursed scroll of enchant weapon", "uncursed scroll of fire")),
    "kit-scroll-prices": Stage(None, xl=8, wield=None, max_steps=1500, identify=False, wishes=(
        "uncursed +0 plate mail", "2 uncursed scrolls of enchant armor", "uncursed scroll of identify",
        "uncursed scroll of destroy armor")),
    "kit-chest": Stage(None, xl=8, wield=None, max_steps=400, wishes=("locked chest",), drop=("chest",)),
    "kit-wish": Stage(None, xl=8, wield=None, max_steps=600, identify=False, wishes=("wand of wishing",)),
    "kit-levitation": Stage(None, xl=8, wield=None, max_steps=600, wishes=(
        "uncursed ring of levitation", "wooden flute", "uncursed ring of free action",
        "uncursed ring of slow digestion")),
    "kit-levitation-boots": Stage(None, xl=8, wield=None, max_steps=600, wishes=(
        "uncursed +0 levitation boots", "uncursed +0 iron shoes")),
}
STAGES.update(ITEM_TESTS)
# Sokoban's top level (dunlev 1, ^V name soko1) for a hand game that checks the sokoban_solved detector
# (plan 01-06); soko1 is the top, so there are no up stairs to stand on.
STAGES["soko-top"] = Stage("soko1", xl=8, wield=None, max_steps=8000, on_upstairs=False)
# primitive self-tests at a real level (scripts/item_selftest.py)
STAGES["kit-rise"] = Stage("medusa", xl=14, max_steps=60, wishes=MIDGAME_KIT + ("2 cursed potions of gain level",))


class StagedChallenge(NetHackChallenge):
    """NetHackChallenge in wizard mode. NetHackChallenge forces wizard=False and NLE reads the options only
    when it builds the game, so the Nethack class is swapped for one that sets wizard=True while building."""

    def __init__(self, character=None, **kwargs):
        # wizard mode renames the hero "wizard", which drops NLE's name-suffix character choice: pass options
        if character is not None and character != "@":
            role, race, gender, align = character.split("-")
            kwargs["options"] = tuple(nethack.NETHACKOPTIONS) + (
                f"role:{role}", f"race:{race}", f"gender:{gender}", f"align:{align}")
        real = nle_base.nethack.Nethack
        nle_base.nethack.Nethack = lambda *a, **k: real(*a, **{**k, "wizard": True})
        try:
            super().__init__(**kwargs)
        finally:
            nle_base.nethack.Nethack = real

    def step(self, action):
        result = super().step(action)
        for _ in range(3):  # prompts that only wizard mode asks get the answer normal play implies
            top = screen_top(self)
            key = next((k for prompt, k in WIZARD_PROMPTS.items() if prompt in top), None)
            if key is None:
                break
            self.last_observation, done = self.nethack.step(ord(key))
            result = (self._get_observation(self.last_observation), 0.0, done, False,
                      self._get_information(self._get_end_status(self.last_observation, done)))
        return result


def screen_lines(env) -> list[str]:
    chars = env.last_observation[env._observation_keys.index("tty_chars")]
    return [bytes(row).decode("latin1").rstrip() for row in chars]


def screen_top(env) -> str:
    return screen_lines(env)[0]


def send(env, keys) -> None:
    """Raw keys to NetHack, below NLE's action set (wizard commands are not in it)."""
    for key in keys:
        env.last_observation, _ = env.nethack.step(key if isinstance(key, int) else ord(key))


def settle(env, limit=20) -> None:
    """Dismiss --More-- and end-of-text prompts."""
    for _ in range(limit):
        if not any(m in line for line in screen_lines(env) for m in MORE):
            return
        send(env, [ENTER])


def level_letter(lines: list[str], name: str) -> str | None:
    """The menu letter of `name` in one page of the ^V "?" level menu ("h -   medusa: 22")."""
    pattern = re.compile(rf"^\s*([a-zA-Z]) - .{{2}}{re.escape(name)}: -?\d+")
    for line in lines:
        m = pattern.match(line)
        if m:
            return m.group(1)
    return None


def teleport_to(env, name: str, pages: int = 5) -> bool:
    send(env, [CTRL_V, "?", ENTER])
    for _ in range(pages):
        letter = level_letter(screen_lines(env), name)
        if letter is not None:
            send(env, [letter])
            settle(env)
            return True
        if not any(re.search(r"\(\d+ of \d+\)", line) for line in screen_lines(env)):
            break
        send(env, [">"])
    send(env, [ESC])
    settle(env)
    return False


def equip(env, wield: str | None) -> None:
    """Wear all armour, put on amulets and rings, wield `wield`: the kit is ready before the teleport."""
    obs = env._get_observation(env.last_observation)
    hands = iter("rl")
    for letter, oclass, text in zip(obs["inv_letters"], obs["inv_oclasses"], obs["inv_strs"]):
        text = bytes(text).decode("latin1").rstrip("\x00 ")
        if not letter or "(being worn)" in text or "(weapon in" in text or "(on " in text or "levitation" in text:
            continue
        if oclass == nethack.ARMOR_CLASS:
            keys = ["W", int(letter)]
        elif oclass in (nethack.AMULET_CLASS, nethack.RING_CLASS):
            keys = ["P", int(letter)]
        elif wield is not None and wield in text:
            keys = ["w", int(letter)]
        else:
            continue
        send(env, keys)
        if "ring-finger" in screen_top(env):
            send(env, [next(hands, "l")])
        settle(env)


def to_upstairs(env) -> None:
    """Wizard ^T (ignores no-teleport levels, teleport.c scrolltele) to the up stairs: getpos '<' jumps the cursor
    to a seen staircase. The ^V arrival region lies around the up stairs, so they are usually in view."""
    send(env, [CTRL_T])
    if "Where do you want to be teleported?" not in screen_top(env):
        settle(env)
        return
    send(env, ["<", "."])
    settle(env)


# Each wish adds 50-149 turns to the prayer timeout (zap.c:6421 "the gods take notice"): a staged kit of ~14 wishes
# left it at ~1700 (^X, castle seed 6), so every low-HP prayer failed. A hero who gathered the kit in play has
# usually not prayed for a long time; a forced prayer sets the timeout to rnz(350) (pray.c:1356, draws of 366-662
# seen on seed 1), repeated until it is at most a fresh game's 300 (u_init.c:1005), which is also what the bot's
# prayer rule assumes (agent.is_safe_to_pray: never prayed -> safe after turn 300).
PRAYER_TIMEOUT_MAX = 300
_PRAY_TIMEOUT = re.compile(r"can't safely pray \((\d+)\)")


def prayer_timeout(env) -> int | None:
    """The prayer timeout from wizard ^X, 0 when it says prayer is safe, None if not shown."""
    send(env, [CTRL_X])
    found = None
    for _ in range(6):
        text = "\n".join(screen_lines(env))
        m = _PRAY_TIMEOUT.search(text)
        if m:
            found = int(m.group(1))
        elif "can safely pray" in text:
            found = 0
        if found is not None or not re.search(r"\(\d+ of \d+\)|--More--", text):  # ^X is paged "(1 of 2)"
            break
        send(env, [" "])
    send(env, [ESC])
    settle(env)
    return found


def reset_prayer_timeout(env, tries: int = 20) -> int | None:
    timeout = prayer_timeout(env)
    for _ in range(tries):
        if timeout is None or timeout <= PRAYER_TIMEOUT_MAX:
            break
        send(env, "#pray\r")
        for _ in range(40):  # the pet's fight can fill many --More-- screens
            top = screen_top(env)
            if "Are you sure you want to pray?" in top or "Force the gods to be pleased?" in top:
                send(env, ["y"])
            elif any(m in line for line in screen_lines(env) for m in MORE):
                send(env, [ENTER])
            else:
                break
        timeout = prayer_timeout(env)
    return timeout


def inventory_letter(env, text: str) -> str | None:
    obs = env._get_observation(env.last_observation)
    for letter, row in zip(obs["inv_letters"], obs["inv_strs"]):
        if letter and text in bytes(row).decode("latin1"):
            return chr(int(letter))
    return None


def apply_stage(env, stage: Stage) -> dict:
    """Set the stage up and return the fresh observation for the bot."""
    settle(env)
    if stage.xl > 1:
        send(env, "#levelchange\r" + f"{stage.xl}\r")
        settle(env)
    for wish in stage.wishes:
        send(env, [CTRL_W])
        send(env, wish + "\r")
        settle(env)
    if stage.identify:
        # wizard identify menu, ^I again selects all of it, Enter confirms (ESC cancelled it: the Medusa and Castle
        # stages ran with unknown potions, amulet and ring until 2026-11-11)
        send(env, [CTRL_I, CTRL_I, "\r"])
        settle(env)
    if stage.wishes:
        reset_prayer_timeout(env)
    for potion in stage.quaff:
        letter = inventory_letter(env, potion)
        if letter is not None:
            send(env, ["q", letter])
            settle(env)
    for name in stage.drop:
        letter = inventory_letter(env, name)
        if letter is not None:
            send(env, ["d", letter])
            settle(env)
    for food in stage.eat:  # before the teleport: on the target level monsters interrupt the meal
        letter = inventory_letter(env, food)
        if letter is not None:
            send(env, ["e", letter])
            settle(env)
    if stage.level is None:  # item tests: the bot itself puts the kit on
        settle(env)
        return env._get_observation(env.last_observation)
    equip(env, stage.wield)
    if not teleport_to(env, stage.level):
        raise RuntimeError(f"stage level not found in the ^V menu: {stage.level}")
    settle(env)
    if stage.on_upstairs:
        to_upstairs(env)
    return env._get_observation(env.last_observation)


# --- observations read without the bot (hand games, detector checks) ------------------------------------------



def unexplored_glyph():
    """Glyph NLE shows for a never-seen map square: the S_stone cmap glyph (seen on staged soko1, seed 7)."""
    from autoascend.glyph import SS
    return SS.S_stone


def observation_facts(obs):
    """Ladder Facts from a raw observation, the way the bot's ladder_facts builds them, without an agent:
    dungeon, level and turn from blstats; squares seen = map glyphs other than the unexplored glyph; traps =
    any trap glyph on the map. Other Facts fields keep their defaults."""
    import numpy as np
    from autoascend.glyph import G
    from autoascend.ladder import Facts
    glyphs, bl = obs["glyphs"], obs["blstats"]
    return Facts(turn=int(bl[nethack.NLE_BL_TIME]), dungeon=int(bl[nethack.NLE_BL_DNUM]),
                 level=int(bl[nethack.NLE_BL_DLEVEL]), sokoban_seen=int((glyphs != unexplored_glyph()).sum()),
                 sokoban_traps=bool(np.isin(glyphs, list(G.TRAPS)).any()))


def board_from_observation(obs):
    """{'floor', 'boulders', 'traps', 'player'} of a Sokoban level from one observation, in the format of
    tests/data/soko_real_*.json, classified like global_logic.sokoban_board (seen-bare squares only)."""
    import numpy as np
    from autoascend.glyph import G
    glyphs, bl = obs["glyphs"], obs["blstats"]
    boulders = np.isin(glyphs, list(G.BOULDER))
    traps = np.isin(glyphs, list(G.TRAPS))
    player = (int(bl[nethack.NLE_BL_Y]), int(bl[nethack.NLE_BL_X]))
    floor = (np.isin(glyphs, list(G.FLOOR | G.STAIR_UP | G.STAIR_DOWN)) & ~np.isin(glyphs, list(G.DOORS | G.WALL)))
    floor |= traps | boulders
    floor[player] = True
    cells = lambda mask: sorted([int(y), int(x)] for y, x in zip(*mask.nonzero()))
    return {"floor": cells(floor), "boulders": cells(boulders), "traps": cells(traps), "player": list(player)}
