# tests/test_threat.py
import nle.nethack as nh
import pytest

from autoascend.combat import threat


def idx(name):
    return next(i for i in range(nh.NUMMONS) if nh.permonst(i).mname == name)


def test_hit_chance_follows_nethacks_to_hit_roll():
    assert threat.hit_chance(3, 10) == 1.0          # 10 + 10 + 3 = 23 > any d20
    assert threat.hit_chance(0, 10) == pytest.approx(0.95)
    assert threat.hit_chance(3, -5) == pytest.approx(0.45)  # AC -5 counts as -3 on average
    assert threat.hit_chance(0, -30) == 0.0
    assert threat.hit_chance(1, 0) == pytest.approx(0.5)


def test_damage_per_turn_scales_with_dice_and_speed():
    ant = threat.damage_per_turn(idx("soldier ant"), 3, 18, 10)
    assert ant == pytest.approx((2 * 2.5 + 3 * 2.5) * 18 / 12)
    newt = threat.damage_per_turn(idx("newt"), 0, 6, 10)
    assert newt == pytest.approx(0.95 * 1.5 * 6 / 12)
    assert threat.damage_per_turn(idx("soldier ant"), 3, 18, 10, our_speed=16) < ant
    dwarf = threat.damage_per_turn(idx("dwarf"), 2, 6, 10)  # weapon users: monst.c dice only
    assert dwarf == pytest.approx(4.5 * 6 / 12)


def test_passive_and_gaze_attacks_do_no_melee_damage():
    assert threat.damage_per_turn(idx("floating eye"), 2, 1, 10) == 0.0
    assert threat.damage_per_turn(idx("acid blob"), 1, 3, 10) == 0.0


def test_special_attacks():
    for name in ("soldier ant", "werejackal", "chickatrice", "cockatrice", "vampire bat"):
        assert threat.has_special_attack(idx(name)), name
    for name in ("newt", "jackal", "giant bat", "water nymph"):
        assert not threat.has_special_attack(idx(name)), name


def test_unknown_index_is_harmless():
    assert threat.attacks(-1) == () and threat.attacks(10 ** 6) == ()
    assert threat.damage_per_turn(10 ** 6, 5, 12, 10) == 0.0
    assert not threat.has_special_attack(-1)


from types import SimpleNamespace

from autoascend.character import Character
from autoascend.combat import monster_utils as mu
from autoascend.glyph import MON


def mon(name, pet=False):
    glyph = MON.fn(name)
    if pet:
        glyph = nh.GLYPH_PET_OFF + idx(name)
    return (1, 5, 5, MON.permonst(glyph), glyph)


def agent(hp, ac=10, role=Character.VALKYRIE):
    return SimpleNamespace(blstats=SimpleNamespace(hitpoints=hp, max_hitpoints=max(hp, 20), armor_class=ac),
                           character=SimpleNamespace(role=role))


def test_monster_index_maps_monster_and_pet_glyphs():
    assert mu.monster_index(MON.fn("newt")) == idx("newt")
    assert mu.monster_index(nh.GLYPH_PET_OFF + idx("little dog")) == idx("little dog")
    assert mu.monster_index(nh.GLYPH_CMAP_OFF) == -1  # a map symbol, not a monster


def test_dangerous_monsters_by_numbers():
    for name in ("soldier ant", "white unicorn", "giant bat", "werejackal", "killer bee"):
        assert mu.is_dangerous_monster(mon(name)), name
    for name in ("newt", "lichen", "jackal", "gnome"):
        assert not mu.is_dangerous_monster(mon(name)), name
    assert mu.is_dangerous_monster(mon("little dog", pet=True))  # pets as before


def test_faster_uses_real_speed_and_fast_roles():
    assert mu.is_monster_faster(agent(20), mon("giant bat"))
    assert mu.is_monster_faster(agent(20), mon("soldier ant"))
    assert not mu.is_monster_faster(agent(20), mon("gnome lord"))
    assert mu.our_speed(agent(20, role=Character.SAMURAI)) == 16
    assert not mu.is_monster_faster(agent(20, role=Character.SAMURAI), mon("jackal"))


def test_imminent_death_depends_on_the_monster():
    assert mu.imminent_death_on_melee(agent(25, ac=4), mon("soldier ant"))
    assert not mu.imminent_death_on_melee(agent(25, ac=4), mon("newt"))
    assert mu.imminent_death_on_melee(agent(8), mon("newt"))  # old floor kept
    assert not mu.imminent_death_on_melee(agent(9), mon("newt"))


def test_elbereth_counts_weak_monsters_as_weak(monkeypatch):
    from autoascend.combat import fight_heur
    a = agent(10)
    a.blstats.y, a.blstats.x = 5, 6
    a.inventory = SimpleNamespace(engraving_below_me="")
    a.can_engrave = lambda: True
    lichen = fight_heur.elbereth_action(a, [mon("lichen")])
    ant = fight_heur.elbereth_action(a, [mon("soldier ant")])
    # a weak monster counts 0.1 (times the low-HP multiplier 1.5), not 1
    assert lichen[0][0] == pytest.approx(-15 + 20 * 0.1 * 1.5 * (1 - (10 / 20) ** 0.5))
    assert lichen[0][0] < ant[0][0]


def test_predicates_accept_the_placeholder_for_unseen_monsters():
    class dummy_permonst:  # same fields as Agent.get_visible_monsters builds
        mname = 'unknown'
        mlet = '0'
        mmove = 12

    unseen = (1, 5, 5, dummy_permonst(), nh.GLYPH_INVISIBLE)
    assert not mu.is_dangerous_monster(unseen)
    assert mu.imminent_death_on_melee(agent(8), unseen)
    assert not mu.imminent_death_on_melee(agent(9), unseen)
    assert not mu.is_monster_faster(agent(20), unseen)
    assert not mu.is_monster_faster(agent(20, role=Character.SAMURAI), unseen)
