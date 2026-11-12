"""A GlobalLogic over a fake level, so tests can call the bot's real ladder_facts without a game."""
import numpy as np


def fake_logic(hallu=False, objects=None, seen=None, glyphs=None, key=(0, 22)):
    from types import SimpleNamespace

    from autoascend.global_logic import GlobalLogic
    from autoascend.glyph import C
    logic = GlobalLogic.__new__(GlobalLogic)
    level = SimpleNamespace(dungeon_number=np.int64(key[0]), level_number=np.int64(key[1]), key=lambda: key,
                            objects=objects if objects is not None else np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16),
                            seen=seen if seen is not None else np.ones((C.SIZE_Y, C.SIZE_X), bool))
    logic.agent = SimpleNamespace(
        current_level=lambda: level, blstats=SimpleNamespace(time=np.int64(123)),
        character=SimpleNamespace(prop=SimpleNamespace(hallu=hallu)),
        glyphs=glyphs if glyphs is not None else np.zeros((C.SIZE_Y, C.SIZE_X), np.int16),
        inventory=SimpleNamespace(items=[]), message="")
    logic.oracle_level = logic.minetown_level = None
    return logic
