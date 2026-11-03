import numpy as np

from autoascend.digging import dig_outcome, dig_square
from autoascend.glyph import C, SS


def _map():
    objects = np.full((C.SIZE_Y, C.SIZE_X), SS.S_stone, np.int16)
    shop = np.zeros((C.SIZE_Y, C.SIZE_X), bool)
    dis = np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16)
    return objects, shop, dis


def test_digs_where_it_stands_on_floor():
    objects, shop, dis = _map()
    objects[5, 5] = SS.S_room
    dis[5, 5] = 0
    assert dig_square(objects, shop, dis, (5, 5)) == (5, 5)


def test_steps_off_stairs_to_the_nearest_floor():
    objects, shop, dis = _map()
    objects[5, 5] = SS.S_dnstair
    objects[5, 6], objects[5, 9] = SS.S_room, SS.S_corr
    dis[5, 5], dis[5, 6], dis[5, 9] = 0, 1, 4
    assert dig_square(objects, shop, dis, (5, 5)) == (5, 6)


def test_never_digs_in_a_shop_doorway_or_unreachable_floor():
    objects, shop, dis = _map()
    objects[5, 5] = SS.S_ndoor
    objects[5, 6] = SS.S_room
    shop[5, 6] = True
    objects[8, 8] = SS.S_room  # unreachable
    dis[5, 5], dis[5, 6] = 0, 1
    assert dig_square(objects, shop, dis, (5, 5)) is None


def test_reads_dig_messages():
    assert dig_outcome('You dig a pit in the floor.') == 'pit'
    assert dig_outcome('You dig a hole through the floor.  You fall through...') == 'fell'
    assert dig_outcome('The floor here is too hard to dig in.') == 'undiggable'
    assert dig_outcome('You stop digging.') == 'stopped'


# dig.c:606 fillholetyp: a moat (Medusa's sea, castle moat) next to the hole fills it with water and the hero falls
# in; pools count a third. Staged medusa seed 1 (map 3): twice "As you dig, the hole fills with water!".
def test_never_digs_next_to_water():
    objects, shop, dis = _map()
    objects[3:8, 3:10] = SS.S_room
    objects[5, 3] = SS.S_pool
    dis[3:8, 3:10] = 9
    dis[5, 4:9] = [0, 1, 2, 3, 4]
    assert dig_square(objects, shop, dis, (5, 4)) == (5, 5)


def test_never_digs_next_to_lava():
    objects, shop, dis = _map()
    objects[3:8, 3:10] = SS.S_room
    objects[4, 5] = SS.S_lava
    dis[3:8, 3:10] = 9
    dis[5, 4:9] = [0, 1, 2, 3, 4]
    assert dig_square(objects, shop, dis, (5, 4)) == (5, 7)


def test_on_a_water_level_unknown_neighbours_count_as_water():
    objects, shop, dis = _map()
    objects[4:7, 10:20] = SS.S_room
    objects[20, 70] = SS.S_pool  # the level has water somewhere
    dis[4:7, 10:20] = 1
    dis[5, 10] = 0
    # (5,10) touches unexplored stone at x=9; the first square with all 8 neighbours known is (5,11)
    assert dig_square(objects, shop, dis, (5, 10)) == (5, 11)


def test_on_a_water_level_never_seen_squares_count_as_water():
    objects, shop, dis = _map()
    objects[:] = -1  # Level.objects: never seen
    objects[4:7, 10:20] = SS.S_room
    objects[20, 70] = SS.S_pool
    dis[4:7, 10:20] = 1
    dis[5, 10] = 0
    assert dig_square(objects, shop, dis, (5, 10)) == (5, 11)


def test_corridor_in_rock_stays_diggable_on_a_dry_level():
    objects, shop, dis = _map()
    objects[5, 5] = SS.S_corr
    dis[5, 5] = 0
    assert dig_square(objects, shop, dis, (5, 5)) == (5, 5)
