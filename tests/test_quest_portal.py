import numpy as np

from autoascend import quest_portal as qp


def test_first_visit_message_is_recognised():
    assert qp.is_portal_level_message("You receive a faint telepathic message from Norn:")
    assert qp.is_portal_level_message("Look for a ...ic transporter.")


def test_reminder_is_recognised():
    assert qp.is_portal_level_message("You again sense the Norn pleading for help.")
    assert qp.is_portal_level_message("You again sense the Master of Thieves demanding your attendance.")


def test_other_messages_are_not():
    assert not qp.is_portal_level_message("You feel a strange vibration under your feet.")
    assert not qp.is_portal_level_message("You hear the footsteps of a guard on patrol.")


def _strip(n=6):
    walkable = np.zeros((3, n), bool)
    walkable[1, :] = True
    return walkable


def test_nearest_unvisited_square_first():
    walkable = _strip()
    visited = np.zeros_like(walkable)
    visited[1, :3] = True
    assert qp.next_portal_square(walkable, visited, np.zeros(walkable.shape, int), (1, 0)) == (1, 3)


def test_dead_ends_when_all_is_visited():
    walkable = _strip()
    visited = walkable.copy()
    searched = np.zeros(walkable.shape, int)
    searched[1, 0] = qp.DEAD_END_SEARCHES
    assert qp.next_portal_square(walkable, visited, searched, (1, 2)) == (1, 5)


def test_none_when_everything_is_done():
    walkable = _strip()
    searched = np.full(walkable.shape, qp.DEAD_END_SEARCHES)
    assert qp.next_portal_square(walkable, walkable.copy(), searched, (1, 2)) is None


def test_unreachable_squares_are_ignored():
    walkable = _strip()
    walkable[1, 3] = False
    visited = np.zeros_like(walkable)
    visited[1, :3] = True
    searched = np.full(walkable.shape, qp.DEAD_END_SEARCHES)
    assert qp.next_portal_square(walkable, visited, searched, (1, 0)) is None
