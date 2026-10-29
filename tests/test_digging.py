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
