from nethack_screensaver.config import Config
from nethack_screensaver.player import frame_delay


def test_normal_step_uses_delay():
    assert frame_delay(3, 3, Config(delay=0.1, level_pause=1.0)) == 0.1


def test_level_change_uses_level_pause():
    assert frame_delay(3, 4, Config(delay=0.1, level_pause=1.0)) == 1.0


def test_first_frame_uses_delay():
    assert frame_delay(None, 1, Config(delay=0.2)) == 0.2
