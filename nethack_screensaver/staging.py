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
CTRL_I, CTRL_V, CTRL_W = 9, 22, 23
MORE = ("--More--", "(end)")
# wizard-only prompts: a death stays a death; skills advance only with practice
WIZARD_PROMPTS = {"Die?": "y", "Advance skills without practice?": "n",
                  "Where do you want to be teleported?": "\x1b"}  # wizard has teleport control


@dataclass(frozen=True)
class Stage:
    level: str | None  # special level name as the ^V menu lists it ("medusa", "castle", "Val-strt"); None stays put
    xl: int = 1
    wishes: tuple[str, ...] = field(default_factory=tuple)
    wield: str | None = "long sword"  # wielded before the teleport (part of the item's name)
    strategy: str = "daredevil"  # plan for the bot (autoascend/plans.py): a deep start dives, not back to the Mines
    identify: bool = True  # False keeps the kit unidentified (price groups, read-testing)
    max_steps: int | None = None  # item tests stop early: the check is the inventory, not survival


# A kit that a bot reaching the level could plausibly have (ASCENSION-PLAN-NH5.md); grows with the phases.
MIDGAME_KIT = ("blessed +2 dwarvish mithril coat", "blessed +2 dwarvish iron helm", "blessed +2 iron shoes",
               "pick-axe", "blessed fixed +2 long sword", "4 blessed potions of extra healing",
               "uncursed unicorn horn", "2 lizard corpses", "blindfold")
STAGES = {
    "medusa": Stage("medusa", xl=14, wishes=MIDGAME_KIT + ("blessed amulet of reflection",)),
    "castle": Stage("castle", xl=14, wishes=MIDGAME_KIT + ("blessed amulet of reflection",
                                                          "blessed ring of levitation", "wooden flute")),
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
    "kit-unihorn": Stage(None, xl=8, wield=None, max_steps=1500, wishes=(
        "uncursed unicorn horn", "3 uncursed potions of confusion", "2 uncursed potions of hallucination")),
    "kit-scrolls": Stage(None, xl=8, wield=None, max_steps=1500, wishes=(
        "uncursed +0 plate mail", "2 uncursed scrolls of enchant armor", "uncursed scroll of remove curse",
        "cursed -1 leather gloves", "uncursed scroll of enchant weapon", "uncursed scroll of fire")),
    "kit-scroll-prices": Stage(None, xl=8, wield=None, max_steps=1500, identify=False, wishes=(
        "uncursed +0 plate mail", "2 uncursed scrolls of enchant armor", "uncursed scroll of identify",
        "uncursed scroll of destroy armor")),
    "kit-levitation": Stage(None, xl=8, wield=None, max_steps=600, wishes=(
        "uncursed ring of levitation", "wooden flute")),
}
STAGES.update(ITEM_TESTS)


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
        if not letter or "(being worn)" in text or "(weapon in" in text or "(on " in text:
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
        send(env, [CTRL_I, CTRL_I])  # wizard identify menu, then ^I again: identify all of it
        settle(env)
        send(env, [ESC])
    if stage.level is None:  # item tests: the bot itself puts the kit on
        settle(env)
        return env._get_observation(env.last_observation)
    equip(env, stage.wield)
    if not teleport_to(env, stage.level):
        raise RuntimeError(f"stage level not found in the ^V menu: {stage.level}")
    settle(env)
    return env._get_observation(env.last_observation)
