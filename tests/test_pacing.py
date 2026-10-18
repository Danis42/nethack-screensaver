import nle.nethack as nh
import numpy as np

from nethack_screensaver.config import Config
from nethack_screensaver.pacing import QUIET_FRAMES, Pacer
from nethack_screensaver.player import frame_delay

STONE = nh.GLYPH_CMAP_OFF
FLOOR = nh.GLYPH_CMAP_OFF + 19
ME = nh.GLYPH_MON_OFF + 1  # any monster glyph; the player stands on it
JACKAL = nh.GLYPH_MON_OFF + 2
PET = nh.GLYPH_PET_OFF + 3


def obs(seen=10, y=5, x=5, hp=10, maxhp=10, dnum=0, dlvl=1, extra=(), farming=False):
    glyphs = np.full((21, 79), STONE, dtype=np.int16)
    glyphs.flat[:seen] = FLOOR
    glyphs[y, x] = ME
    for gy, gx, g in extra:
        glyphs[gy, gx] = g
    bl = np.zeros(27, dtype=np.int64)
    bl[0], bl[1], bl[10], bl[11], bl[23], bl[24] = x, y, hp, maxhp, dnum, dlvl
    return {"glyphs": glyphs, "blstats": bl, "farming": farming}


def settle(p, **kw):
    """Feed identical frames until the pacer is fast-forwarding."""
    for _ in range(QUIET_FRAMES + 1):
        fast = p.update(obs(**kw))
    return fast


def test_known_map_without_monsters_fast_forwards_after_quiet_frames():
    p = Pacer()
    assert p.update(obs()) is False  # new level: exploring
    for _ in range(QUIET_FRAMES - 1):
        assert p.update(obs()) is False
    assert p.update(obs()) is True


def test_exploring_new_cells_is_normal_speed():
    p = Pacer()
    assert settle(p, seen=10)
    assert p.update(obs(seen=12)) is False


def test_hostile_nearby_is_normal_speed():
    p = Pacer()
    assert settle(p)
    assert p.update(obs(extra=[(5, 7, JACKAL)])) is False


def test_far_monster_and_pet_stay_fast():
    assert settle(Pacer(), extra=[(5, 40, JACKAL), (5, 6, PET)])


def test_fights_while_farming_stay_fast():
    p = Pacer()
    assert settle(p, farming=True)
    assert settle(p, farming=True, extra=[(5, 6, JACKAL)])


def test_exploring_and_low_hp_while_farming_are_normal_speed():
    p = Pacer()
    assert settle(p, farming=True)
    assert p.update(obs(seen=12, farming=True)) is False
    assert settle(p, seen=12, farming=True)
    assert p.update(obs(seen=12, farming=True, hp=4)) is False


def test_low_hp_is_normal_speed():
    p = Pacer()
    assert settle(p)
    assert p.update(obs(hp=4)) is False


def test_revisited_level_is_not_exploring():
    p = Pacer()
    settle(p, seen=30, dlvl=1)
    settle(p, seen=40, dlvl=2)
    assert p.update(obs(seen=30, dlvl=1)) is False  # arriving resets the quiet count...
    assert settle(p, seen=30, dlvl=1)  # ...then fast again, nothing new seen


def test_fast_frames_use_fast_delay():
    cfg = Config(delay=0.1, fast_delay=0.005)
    assert frame_delay(3, 3, cfg, fast=True) == 0.005
    assert frame_delay(3, 4, cfg, fast=True) == cfg.level_pause
