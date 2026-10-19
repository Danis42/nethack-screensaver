from autoascend.agent import diagonal_blocked_square


def test_out_of_doorway_blocks_where_we_stand():
    msg = "You can't move diagonally out of an intact doorway."
    assert diagonal_blocked_square(msg, (5, 5), (6, 6)) == (5, 5)


def test_into_doorway_blocks_the_target():
    msg = "You see no objects here.  You can't move diagonally into an intact doorway."
    assert diagonal_blocked_square(msg, (5, 5), (6, 6)) == (6, 6)


def test_other_messages_block_nothing():
    assert diagonal_blocked_square("You see no objects here.", (5, 5), (6, 6)) is None
