"""Pure ANSI renderer for NLE's 80x24 tty observation."""
import numpy as np

W, H = 80, 24
TOO_SMALL = "Terminal too small for NetHack (need 80x24)"
CLEAR = "\x1b[0m\x1b[2J"
RESET = "\x1b[0m"


def _sgr(color: int) -> int:
    c = int(color) & 15
    if c == 0:
        return 90
    if c < 8:
        return 30 + c
    if c == 8:
        return 39
    return 90 + (c - 8)


def _ch(code: int) -> str:
    return chr(code) if 32 <= code <= 126 else " "


def format_status(game_no: int, role: str, depth: int, turn: int, best_depth: int) -> str:
    return f"Game #{game_no} · {role} · Dlvl {depth} · T:{turn} · Best: Dlvl {best_depth}"


class Renderer:
    def __init__(self):
        self.invalidate()

    def invalidate(self) -> None:
        self._chars = None
        self._colors = None
        self._status = None
        self._size = None

    def message(self, text: str, cols: int, rows: int) -> str:
        self.invalidate()
        text = text[: max(cols, 1)]
        row = rows // 2
        col = max((cols - len(text)) // 2, 0) + 1
        return f"{CLEAR}\x1b[{row};{col}H{text}"

    def frame(self, tty_chars, tty_colors, cols, rows, status=None) -> str:
        need_rows = H + (1 if status is not None else 0)
        if cols < W or rows < need_rows:
            if self._size == ("small", cols, rows):
                return ""
            out = self.message(TOO_SMALL, cols, rows)
            self._size = ("small", cols, rows)
            return out

        full = self._size != (cols, rows) or self._chars is None
        top = (rows - need_rows) // 2
        left = (cols - W) // 2
        parts = [CLEAR] if full else []
        for y in range(H):
            row_c, row_k = tty_chars[y], tty_colors[y]
            if full:
                start, end = 0, W
            else:
                diff = np.nonzero((row_c != self._chars[y]) | (row_k != self._colors[y]))[0]
                if diff.size == 0:
                    continue
                start, end = int(diff[0]), int(diff[-1]) + 1
            parts.append(f"\x1b[{top + y + 1};{left + start + 1}H")
            cur = None
            for x in range(start, end):
                sgr = _sgr(row_k[x])
                if sgr != cur:
                    parts.append(f"\x1b[{sgr}m")
                    cur = sgr
                parts.append(_ch(int(row_c[x])))
        if status is not None and (full or status != self._status):
            parts.append(f"{RESET}\x1b[{top + H + 1};{left + 1}H\x1b[2K{status[:W]}")
        self._chars = tty_chars.copy()
        self._colors = tty_colors.copy()
        self._status = status
        self._size = (cols, rows)
        if not parts:
            return ""
        out = "".join(parts)
        return out + RESET if not out.endswith(RESET) else out
