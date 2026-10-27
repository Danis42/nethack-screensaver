"""NetHack 5 glyphs mapped onto the glyph set the bot was written for.

NetHack 5 splits monster, pet, detected, ridden and statue glyphs by gender, draws walls per dungeon
branch (Mines, Gehennom, Ludios, Sokoban), has five altar glyphs, marks branch stairs and engraved
floor with their own symbols. The bot does not use any of these distinctions, so each glyph is mapped
to its male / main-dungeon / plain counterpart. The result is still a valid NetHack 5 glyph, so
nle.nethack.glyph_* functions keep working on it.
"""
import nle.nethack as nh
import numpy as np

from . import screen_symbol_consts as SS

# same symbol as the plain one for the bot's purposes
_PLAIN_SYMBOL = {
    'S_brupstair': 'S_upstair',
    'S_brdnstair': 'S_dnstair',
    'S_brupladder': 'S_upladder',
    'S_brdnladder': 'S_dnladder',
    'S_engroom': 'S_room',
    'S_engrcorr': 'S_corr',
}

# gendered ranges: female glyphs follow the male ones (include/display.h)
_GENDERED = (nh.GLYPH_MON_OFF, nh.GLYPH_PET_OFF, nh.GLYPH_DETECT_OFF, nh.GLYPH_RIDDEN_OFF,
             nh.GLYPH_STATUE_OFF)


def _table():
    canon = np.arange(nh.MAX_GLYPH + 1, dtype=np.int16)  # MAX_GLYPH (NO_GLYPH) maps to itself; int16 like NLE
    for male_off in _GENDERED:
        fem_off = male_off + nh.NUMMONS
        canon[fem_off:fem_off + nh.NUMMONS] = np.arange(male_off, male_off + nh.NUMMONS)

    symbol_names = [name for name in dir(SS) if name.startswith('S_')]
    index_of = {getattr(SS, name): name for name in symbol_names}
    for glyph in range(nh.MAX_GLYPH):
        if not nh.glyph_is_cmap(glyph):
            continue
        index = nh.glyph_to_cmap(glyph)
        if index >= SS.MAXPCHARS:
            continue
        plain = SS.CMAP_GLYPH[index]
        name = index_of.get(plain)
        if name in _PLAIN_SYMBOL:
            plain = getattr(SS, _PLAIN_SYMBOL[name])
        if index < SS.CMAP_GLYPH.index(SS.S_vbeam) or index == SS.CMAP_GLYPH.index(SS.S_altar):
            canon[glyph] = plain  # walls, doors, floor, stairs, altars, traps; not beams or effects
    return canon


CANONICAL = _table()


def canonical(glyphs):
    return CANONICAL[glyphs]
