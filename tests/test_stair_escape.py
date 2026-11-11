from autoascend.combat import stair_escape as se


class P:
    def __init__(self, stalk=False):
        self.mflags2 = se.M2_STALK if stalk else 0


def test_escapes_deep_low_hp_on_stairs_from_non_stalker():
    assert se.should_escape(23, 0, 60, 127, [P()])


def test_stays_when_any_condition_missing():
    assert not se.should_escape(20, 0, 60, 127, [P()])  # above Medusa: natural play unchanged
    assert not se.should_escape(23, None, 60, 127, [P()])  # no reachable up stairs
    assert not se.should_escape(23, se.REACH + 1, 60, 127, [P()])  # too far
    assert se.should_escape(23, 3, 60, 127, [P()])  # walk back first
    assert not se.should_escape(23, 0, 64, 127, [P()])  # half HP or more
    assert not se.should_escape(23, 0, 60, 127, [])  # nobody adjacent


def test_stalkers_alone_follow_so_no_escape():
    assert not se.should_escape(23, 0, 60, 127, [P(stalk=True)])
    assert se.should_escape(23, 0, 60, 127, [P(stalk=True), P()])


def test_invisible_unknown_monster_counts_as_non_stalker():
    class Dummy:
        mname = 'unknown'
    assert se.should_escape(23, 0, 60, 127, [Dummy()])


def test_rest_stops():
    assert se.rest_done(115, 127, 10, False, False)
    assert se.rest_done(50, 127, 10, True, False)
    assert se.rest_done(50, 127, 10, False, True)
    assert se.rest_done(50, 127, se.REST_TURNS, False, False)
    assert not se.rest_done(50, 127, 10, False, False)
