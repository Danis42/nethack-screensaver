import re

import numpy as np

from nethack_screensaver.render import TOO_SMALL, Renderer, format_status

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def screen(text_rows=None):
    chars = np.full((24, 80), ord(" "), dtype=np.uint8)
    colors = np.zeros((24, 80), dtype=np.int8)
    for y, line in (text_rows or {}).items():
        chars[y, : len(line)] = list(line.encode())
    return chars, colors


def moves(out):
    return [(int(r), int(c)) for r, c in re.findall(r"\x1b\[(\d+);(\d+)H", out)]


def test_first_frame_is_full_redraw_centered():
    r = Renderer()
    chars, colors = screen({0: "Hello"})
    out = r.frame(chars, colors, cols=100, rows=30)
    assert "\x1b[2J" in out
    assert (4, 11) in moves(out)  # row 0 → (30-24)//2+1, col 0 → (100-80)//2+1
    assert "Hello" in ANSI.sub("", out)


def test_unchanged_frame_emits_nothing():
    r = Renderer()
    chars, colors = screen({0: "Hello"})
    r.frame(chars, colors, 80, 24)
    assert r.frame(chars, colors, 80, 24) == ""


def test_diff_only_rewrites_changed_span():
    r = Renderer()
    chars, colors = screen({5: "abcdef"})
    r.frame(chars, colors, 80, 24)
    chars2 = chars.copy()
    chars2[5, 2] = ord("X")
    out = r.frame(chars2, colors, 80, 24)
    assert "\x1b[2J" not in out
    assert moves(out) == [(6, 3)]
    assert ANSI.sub("", out) == "X"


def test_colors_mapped():
    r = Renderer()
    chars, colors = screen({0: "@"})
    colors[0, 0] = 1  # red
    out = r.frame(chars, colors, 80, 24)
    assert "\x1b[31m@" in out


def test_too_small():
    r = Renderer()
    chars, colors = screen()
    out = r.frame(chars, colors, cols=60, rows=20)
    assert TOO_SMALL[:40] in ANSI.sub("", out)


def test_invalidate_forces_full_redraw():
    r = Renderer()
    chars, colors = screen({0: "x"})
    r.frame(chars, colors, 80, 24)
    r.invalidate()
    assert "\x1b[2J" in r.frame(chars, colors, 80, 24)


def test_size_change_forces_full_redraw():
    r = Renderer()
    chars, colors = screen({0: "x"})
    r.frame(chars, colors, 80, 24)
    assert "\x1b[2J" in r.frame(chars, colors, 90, 30)


def test_status_line_needs_25_rows_and_is_drawn_below():
    r = Renderer()
    chars, colors = screen()
    small = r.frame(chars, colors, 80, 24, status="Game #1")
    assert TOO_SMALL[:20] in ANSI.sub("", small)
    r.invalidate()
    out = r.frame(chars, colors, 80, 25, status="Game #1")
    assert (25, 1) in moves(out) and "Game #1" in out


def test_status_line_redrawn_only_when_changed():
    r = Renderer()
    chars, colors = screen()
    r.frame(chars, colors, 80, 25, status="A")
    assert r.frame(chars, colors, 80, 25, status="A") == ""
    assert "B" in r.frame(chars, colors, 80, 25, status="B")


def test_message_centered():
    r = Renderer()
    out = r.message("hi", cols=80, rows=24)
    assert "\x1b[2J" in out and (12, 40) in moves(out)


def test_format_status():
    assert format_status(12, "Val", 7, 4310, 14) == "Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14"


class _ResizeMidFrame(np.ndarray):
    """Array whose row access simulates SIGWINCH arriving during frame()."""
    renderer = None

    def __getitem__(self, idx):
        if _ResizeMidFrame.renderer is not None:
            _ResizeMidFrame.renderer.request_redraw()
        return np.asarray(self)[idx]


def test_resize_signal_during_frame_is_safe_and_redraws_next():
    r = Renderer()
    chars, colors = screen({0: "a"})
    r.frame(chars, colors, 80, 24)
    chars2 = chars.copy()
    chars2[0, 0] = ord("b")
    racy = chars2.view(_ResizeMidFrame)
    _ResizeMidFrame.renderer = r
    try:
        r.frame(racy, colors, 80, 24)
    finally:
        _ResizeMidFrame.renderer = None
    assert "\x1b[2J" in r.frame(chars2, colors, 80, 24)
