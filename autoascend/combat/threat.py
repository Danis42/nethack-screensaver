"""How dangerous a monster is, from NetHack's own numbers (sub-project 1, docs/ROADMAP.md).

Pure functions over the attack table in monster_data.py. A melee attack hits when
10 + our AC + monster level > d20 (mattacku); negative AC counts as -rnd(-AC). Weapon
users get their monst.c dice only, without the weapon's own damage."""
from .monster_data import MONSTERS

BASE_SPEED = 12
FAST_SPEED = 16  # intrinsic Fast: about one extra move in three
DANGER_HP_PER_TURN = 4  # against AC 10 and speed 12

# include/monattk.h
MELEE = frozenset({1, 2, 3, 4, 5, 6, 7, 11, 16, 254})  # claw bite kick butt touch sting hug engulf tentacle weapon
SPECIAL = frozenset({
    7, 30, 31,  # poison: drain Str, Dex, Con
    14,  # paralysis
    15,  # level drain
    18,  # stoning
    26,  # digestion
    29,  # lycanthropy
    32,  # brain eating
    33,  # disease
    40,  # sliming
})


def attacks(index):
    return MONSTERS[index][1] if 0 <= index < len(MONSTERS) else ()


def hit_chance(mlevel, our_ac):
    ac = our_ac if our_ac >= 0 else (our_ac - 1) / 2
    return min(max((10 + ac + mlevel - 1) / 20, 0.0), 1.0)


def damage_per_turn(index, mlevel, mspeed, our_ac, our_speed=BASE_SPEED):
    """Expected HP this monster takes from us per turn of ours in melee."""
    hit = hit_chance(mlevel, our_ac)
    per_move = sum(hit * n * (d + 1) / 2 for at, ad, n, d in attacks(index) if at in MELEE)
    return per_move * mspeed / our_speed


def has_special_attack(index):
    """An attack that ends runs in ways HP does not show (poison, lycanthropy, stoning, ...)."""
    return any(ad in SPECIAL for at, ad, n, d in attacks(index))
