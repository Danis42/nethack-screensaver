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


class _Hero:
    def __init__(self):
        from types import SimpleNamespace
        self.dungeon, self.depth = 0, 12
        self.message = ""
        self.blstats = SimpleNamespace(time=1000, y=5, x=5)
        self.events = []
        self.stats_logger = SimpleNamespace(log_event=self.events.append)

    def current_level(self):
        from types import SimpleNamespace
        import numpy as np
        from autoascend.glyph import C
        return SimpleNamespace(dungeon_number=self.dungeon, key=lambda: (self.dungeon, self.depth),
                               objects=np.full((C.SIZE_Y, C.SIZE_X), -1, np.int16))


def _portal_logic():
    from autoascend.global_logic import GlobalLogic
    logic = GlobalLogic.__new__(GlobalLogic)
    logic.agent = _Hero()
    logic.portal_level, logic._portal_hunt_since, logic._quest_arrival, logic._quest_left = None, None, None, False
    logic._quest_portal_found_logged = False
    return logic


def test_hunt_starts_only_on_the_level_of_the_message():
    logic = _portal_logic()
    assert not logic._hunting_portal()
    logic.agent.message = "You receive a faint telepathic message from the Norn:"
    logic._update_portal()
    assert logic.portal_level == (0, 12) and logic._hunting_portal()
    logic.agent.depth = 13
    assert not logic._hunting_portal()


def test_hunt_gives_up_after_its_budget():
    from autoascend.global_logic import PORTAL_HUNT_TURNS
    logic = _portal_logic()
    logic.agent.message = "You again sense the Norn pleading for help."
    logic._update_portal()
    assert logic._hunting_portal()
    logic.agent.blstats.time += PORTAL_HUNT_TURNS + 1
    assert not logic._hunting_portal() and not logic._hunting_portal()
    assert logic.agent.events == ['quest_portal_level_seen', 'quest_portal_gave_up']


def test_entering_and_leaving_the_quest_is_counted_once():
    logic = _portal_logic()
    logic.agent.message = "You receive a faint telepathic message from the Norn:"
    logic._update_portal()
    logic.agent.dungeon, logic.agent.depth = 3, 1
    logic._update_portal()
    logic._update_portal()
    assert logic._quest_arrival == (5, 5)
    logic.agent.dungeon, logic.agent.depth = 0, 12
    logic._update_portal()
    assert not logic._hunting_portal()
    assert logic.agent.events == ['quest_portal_level_seen', 'quest_portal_entered', 'quest_portal_left']


def test_message_in_another_dungeon_does_not_mark_a_level():
    logic = _portal_logic()
    logic.agent.dungeon = 2
    logic.agent.message = "You again sense the Norn pleading for help."
    logic._update_portal()
    assert logic.portal_level is None
