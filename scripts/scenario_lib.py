"""Scenario library: one situation the bot must handle, set up in wizard mode, with pass/fail checks.

A scenario = a staging.Stage (level, XL, wishes, drops, ...) + monsters created next to the hero + checks over the
game record. Run them with scripts/scenario_run.py; they never go into the bench store.

Check functions get a record dict:
  result    GameResult as a dict (events, snapshots, end_reason, max_depth, ...)
  messages  every distinct message line of the game, in order
  inventory the hero's inventory lines at the end (snapshots)
and return True (pass) or False.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Scenario:
    stage: dict  # keyword arguments for staging.Stage
    checks: dict[str, Callable[[dict], bool]]
    monsters: tuple[str, ...] = ()  # created next to the hero after the setup (wizard ^G)
    dips: tuple[tuple[str, str], ...] = ()  # (item text, potion text): #dip the item into the potion after setup
    eat: tuple[str, ...] = ()  # inventory texts eaten after the setup (e.g. a floating eye corpse: telepathy)
    keys: tuple[str, ...] = ()  # raw key strings sent after the setup and before the dips (e.g. "w-" bare hands)
    seeds: str = "1-12"
    note: str = ""
    strategy: str | None = None  # plan for the bot; default from the stage


def said(text: str) -> Callable[[dict], bool]:
    return lambda r: any(text in m for m in r["messages"])


def never(text: str) -> Callable[[dict], bool]:
    return lambda r: not any(text in m for m in r["messages"])


def wielding(pattern: str) -> Callable[[dict], bool]:
    """The main-hand item at the end matches the regex."""
    def check(r):
        hand = [line for line in r["inventory"] if "in right hand" in line or "in hands" in line
                or "weapon in hand" in line or "(wielded)" in line]
        return bool(hand) and re.search(pattern, hand[0]) is not None
    return check


def no_cursed_wielded(r: dict) -> bool:
    """No weld message and no cursed item in hand at the end (a welded stack shows '(wielded)')."""
    if any("welded to your hand" in m for m in r["messages"]):
        return False
    return not any(re.search(r"\bcursed\b", line) and not re.search(r"\buncursed\b", line)
                   and ("in right hand" in line or "(wielded)" in line or "in hands" in line)
                   for line in r["inventory"])


def event(name: str, at_least: int = 1) -> Callable[[dict], bool]:
    return lambda r: (r["result"].get("events") or {}).get(name, 0) >= at_least


def alive(r: dict) -> bool:
    return not r["result"]["end_reason"].startswith("DEATH")


SCENARIOS: dict[str, Scenario] = {
    # Phase 02.2 part 1a, job 74: prying with an unidentified cursed dagger welded it (215 vs 46 games).
    "pry-cursed-dagger": Scenario(
        stage=dict(level=None, xl=8, wield=None, max_steps=500, identify=False,
                   wishes=("cursed dagger", "locked chest", "cursed potion of water"), drop=("chest",)),
        dips=(("+0 dagger", "clear potion"),),  # unholy water: the starting dagger becomes KNOWN cursed
        checks={"setup: chest locked": said("turns out to be locked"),
                "no weld": no_cursed_wielded,
                "spear kept": wielding(r"spear")},
        note="unidentified cursed dagger the only usable blade (starting dagger known cursed), locked chest"),
    # exp/known-buc-wield: never switch to a weapon of unknown curse status.
    "wield-unknown-cursed": Scenario(
        stage=dict(level=None, xl=8, wield=None, max_steps=400, identify=False,
                   wishes=("cursed elven dagger", "cursed long sword", "cursed potion of water")),
        keys=("w-",),  # bare hands, then the spear is dipped into unholy water: known cursed, not wieldable
        dips=(("+1 spear", "clear potion"),),
        checks={"no weld": no_cursed_wielded,
                "wields a known weapon": wielding(r"\+0 dagger|\+1 spear")},
        note="spear known cursed and unwielded; known +0 dagger vs unidentified cursed long sword/elven dagger"),
    # Medusa: never dig next to water (dig.c:606); staged medusa seed 1 is map 3 (no dry arrival square).
    "medusa-dig": Scenario(
        stage=dict(level="medusa", xl=14, max_steps=3000,
                   wishes=("blessed +2 dwarvish mithril coat", "blessed +2 dwarvish iron helm",
                           "blessed +2 iron shoes", "pick-axe", "blessed fixed +2 long sword",
                           "4 blessed potions of extra healing", "uncursed unicorn horn", "2 lizard corpses",
                           "blessed +0 cloak of protection", "blessed +0 leather gloves",
                           "blindfold", "blessed amulet of reflection")),
        checks={"no flooded hole": never("the hole fills with"),
                "not drowned": lambda r: not any("You drown" in m or "drowns you" in m for m in r["messages"]),
                "got below Medusa": lambda r: r["result"].get("max_depth", 0) > r["start_depth"]},
        seeds="1-12", strategy="daredevil",
        note="arrival on Medusa's level with a pick-axe; map varies by seed"),
    # Levitation crossing (medusa.py): ring of levitation + reflection + telepathy (eaten eye) + blindfold.
    "medusa-levitate": Scenario(
        stage=dict(level="medusa", xl=14, max_steps=3000,
                   wishes=("blessed +2 dwarvish mithril coat", "blessed +2 dwarvish iron helm",
                           "blessed +2 iron shoes", "pick-axe", "blessed fixed +2 long sword",
                           "4 blessed potions of extra healing", "uncursed unicorn horn", "2 lizard corpses",
                           "blessed +0 cloak of protection", "blessed +0 leather gloves",
                           "blindfold", "blessed amulet of reflection", "blessed ring of levitation",
                           "floating eye corpse"),
                   eat=("floating eye corpse",)),
        checks={"crossed by levitation": event("medusa_landed"),
                "not drowned": lambda r: not any("You drown" in m or "drowns you" in m for m in r["messages"]),
                "got below Medusa": lambda r: r["result"].get("max_depth", 0) > r["start_depth"]},
        seeds="1-8", strategy="daredevil",
        note="arrival on Medusa's level; dig where dry, else levitate to the stairs/Medusa"),
    # Telepathy rule (TELEPATHY-NH5.md): a floating eye next to the hero, a towel in the pack.
    "eye-telepathy": Scenario(
        stage=dict(level=None, xl=8, wield=None, max_steps=400, wishes=("uncursed towel",)),
        monsters=("floating eye",),
        checks={"eye killed": lambda r: any(re.search(r"You (kill|destroy) (it|the floating eye)!", m)
                                            for m in r["messages"]),
                "corpse eaten if left": lambda r: (not any("floating eye corpse" in m for m in r["messages"])
                                                   or any("mental acuity" in m for m in r["messages"])),
                "telepathy gained": said("mental acuity"),
                "never frozen": never("You are frozen"),
                "alive": alive},
        seeds="1-8",
        note="floating eye created next to the hero; ~1/2 of eyes leave a corpse (mon.c), so telepathy <= ~50%"),
    # Eat-the-eye rule (eat_eye_corpse): no blindfold, the bot kills the eye its own way; a corpse left must be eaten.
    "eye-natural": Scenario(
        stage=dict(level=None, xl=8, max_steps=400),
        monsters=("floating eye",),
        checks={"eye killed": lambda r: any(re.search(r"(You (kill|destroy) the floating eye|"
                                                      r"The floating eye is (killed|destroyed))!", m)
                                            for m in r["messages"]),
                "corpse eaten if seen": lambda r: (not any("floating eye corpse" in m for m in r["messages"])
                                                   or any("mental acuity" in m for m in r["messages"])),
                "telepathy gained": said("mental acuity"),
                "alive": alive},
        seeds="1-12",
        note="no towel; ~1/2 of eyes leave a corpse (mon.c), so telepathy <= ~50%"),
}
