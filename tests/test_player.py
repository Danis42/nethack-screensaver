from nethack_screensaver.config import Config
from nethack_screensaver.player import frame_delay


def test_normal_step_uses_delay():
    assert frame_delay(3, 3, Config(delay=0.1, level_pause=1.0)) == 0.1


def test_level_change_uses_level_pause():
    assert frame_delay(3, 4, Config(delay=0.1, level_pause=1.0)) == 1.0


def test_first_frame_uses_delay():
    assert frame_delay(None, 1, Config(delay=0.2)) == 0.2


def test_hangup_and_term_exit_cleanly(monkeypatch):
    import signal

    from nethack_screensaver import player
    from nethack_screensaver.render import Renderer

    installed = {}
    monkeypatch.setattr(signal, "signal", lambda sig, h: installed.__setitem__(sig, h))
    player._install_signals(Renderer())
    assert installed[signal.SIGTERM] is player._on_term
    assert installed[signal.SIGHUP] is player._on_term
