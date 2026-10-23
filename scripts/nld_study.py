"""Human-game studies on NLD-NAO for Phase 1. Usage: uv run python scripts/nld_study.py prayers|food ...

Reads recorded NetHack 3.6 games (ttyrecs) from the NLD-NAO dataset, read-only. Only aggregate numbers
and anonymised message lines are printed (god names are replaced by <god>; no game ids, names or uids).

  prayers  what the message line shows after "You begin praying to" (census of the following lines)
  food     (task 2) food and prayer habits on Dlvl 4-12: humans who got through versus humans who starved
"""
import argparse
import random
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoascend.prayer import PRAYER_START, prayer_outcome  # noqa: E402

DEFAULT_DB = "/ssd2/nethackFiles/db/nld.db"
DATASET = "nld-nao-aa"
SEQ_LENGTH = 512

# NetHack 3.6 pantheons (Priests draw a random one); replaced by <god> in every printed line
GODS = (
    "Quetzalcoatl", "Camaxtli", "Huhetotl", "Mitra", "Crom", "Set", "Anu", "Ishtar", "Anshar",
    "Athena", "Hermes", "Poseidon", "Lugh", "Brigit", "Manannan Mac Lir", "Shan Lai Ching",
    "Chih Sung-tzu", "Huan Ti", "Issek", "Mog", "Kos", "Mercury", "Venus", "Mars",
    "Amaterasu Omikami", "Raijin", "Susanowo", "Blind Io", "The Lady", "Offler", "Tyr", "Odin",
    "Loki", "Ptah", "Thoth", "Anhur", "Moloch",
)
_GOD_RE = re.compile(r"\b(?:" + "|".join(re.escape(g) for g in sorted(GODS, key=len, reverse=True)) + r")\b")
_DLVL_RE = re.compile(r"Dlvl:(\d+)")
_TURN_RE = re.compile(r"\bT:(\d+)")
_HUNGER_RE = re.compile(r"\b(Hungry|Weak|Fainting|Fainted)\b")
_SPLIT_RE = re.compile(r"\s{2,}")
WIDTH = 80
TERMINATORS = (".", "!", "?", ")", "\"", "'")
HUNGER_ORDER = {"": 0, "Hungry": 1, "Weak": 2, "Fainting": 3, "Fainted": 4}


def message_line(frame):
    """Row 0 of a (24, 80) tty frame, decoded and stripped."""
    return bytes(frame[0]).decode("ascii", errors="replace").replace("\x00", " ").strip()


def status(frame):
    """(dlvl or None, turn or None, hunger word or "") from the two status rows 22-23."""
    text = (bytes(frame[22]) + b" " + bytes(frame[23])).decode("ascii", errors="replace").replace("\x00", " ")
    return _parse_status(text)


def _parse_status(text):
    dlvl = _DLVL_RE.search(text)
    turn = _TURN_RE.search(text)
    hunger = _HUNGER_RE.search(text)
    return (int(dlvl[1]) if dlvl else None, int(turn[1]) if turn else None, hunger[1] if hunger else "")


def normalise(line):
    """The line with every god name replaced by <god>."""
    return _GOD_RE.sub("<god>", line)


def sentences(line):
    """Split a message line into its messages (NetHack joins them with two spaces); --More-- dropped."""
    line = line.replace("--More--", " ").strip()
    return [s.strip() for s in _SPLIT_RE.split(line) if s.strip()]


def looks_like_prompt(sentence):
    """An interface prompt (menu, direction, count), not a game message; the god's "Thou ...?" is a message."""
    return not sentence.startswith("Thou") and sentence.endswith(("?", "]", "(n)", "(q)", ")")) \
        or sentence.startswith(("Count:", "cmdassist"))


def weak_or_worse(hunger):
    return HUNGER_ORDER.get(hunger, 0) >= HUNGER_ORDER["Weak"]


def hungry_or_worse(hunger):
    return HUNGER_ORDER.get(hunger, 0) >= HUNGER_ORDER["Hungry"]


class GameScanner:
    """Feed the frames of ONE game in order; collects what the studies need.

    The message line is redrawn piece by piece (a ttyrec has every partial write), so a displayed
    message is only reported once it is replaced or cleared; growth of the same text is one message.
    The status (dlvl, turn, hunger) is the reading from the frame where the message first appeared.

    prayers: one dict per "You begin praying to" with the turn, dlvl and hunger word at that moment and
    the next distinct messages (normalised) that followed, up to FOLLOW_LINES within FOLLOW_TURNS."""

    FOLLOW_LINES = 6
    FOLLOW_TURNS = 3  # a prayer takes 3 moves; the god answers in the last one
    FOLLOW_FRAMES = 400

    def __init__(self):
        self.prayers = []
        self.frames = 0
        self._row0 = b""
        self._shown = ""
        self._shown_status = (None, None, "")
        self._prayer_status = None
        self._status_rows = None
        self._status = (None, None, "")
        self._pending = None

    def feed(self, frame):
        self.frames += 1
        rows = bytes(frame[22]) + bytes(frame[23])
        if rows != self._status_rows:
            self._status_rows = rows
            text = rows.decode("ascii", errors="replace").replace("\x00", " ")
            reading = _parse_status(text)
            # a transient redraw without the status text must not erase the last good reading
            if reading[0] is not None:
                self._status = reading
        if self._pending is not None:
            self._pending["_frames"] += 1
            if self._pending["_frames"] > self.FOLLOW_FRAMES:
                self._close_prayer()
        row0 = bytes(frame[0])
        if row0 == self._row0:
            return
        self._row0 = row0
        text = row0.decode("ascii", errors="replace").replace("\x00", " ").strip()
        if self._shown and text.startswith(self._shown):
            self._shown = text  # the same message growing (partial redraw or a second message appended)
        else:
            self._flush()
            self._shown = text
            self._shown_status = self._status
        if self._prayer_status is None and PRAYER_START in self._shown:
            self._prayer_status = self._status  # the reading from before the prayer takes effect

    def _flush(self):
        if self._shown:
            parts = sentences(self._shown)
            if parts and len(self._shown) >= WIDTH - 2 and not self._shown.replace("--More--", "").rstrip().endswith(TERMINATORS):
                parts.pop()  # the 80-column line cut the last message short; a fragment is not evidence
            for sentence in parts:
                if PRAYER_START in sentence:
                    self._on_message(sentence, self._prayer_status or self._shown_status)
                else:
                    self._on_message(sentence, self._shown_status)
        self._shown = ""
        self._prayer_status = None

    def _on_message(self, sentence, reading):
        if PRAYER_START in sentence:
            self._close_prayer()
            dlvl, turn, hunger = reading
            self._pending = {"dlvl": dlvl, "turn": turn, "hunger": hunger, "lines": [], "_frames": 0}
            return
        if self._pending is None:
            return
        turn, start = reading[1], self._pending["turn"]
        if turn is not None and start is not None and turn > start + self.FOLLOW_TURNS:
            self._close_prayer()
            return
        if looks_like_prompt(sentence):
            self._close_prayer()  # the next thing the player did, not the god's answer
            return
        line = normalise(sentence)
        if line not in self._pending["lines"]:
            self._pending["lines"].append(line)
        if len(self._pending["lines"]) >= self.FOLLOW_LINES:
            self._close_prayer()

    def _close_prayer(self):
        if self._pending is not None:
            self._pending.pop("_frames")
            self.prayers.append(self._pending)
            self._pending = None

    def finish(self):
        self._flush()
        self._close_prayer()
        return self


def iter_frames(db, gameids):
    """Yield (gameid, frame) for every real frame of these games, in game order (read-only decode)."""
    import nle.dataset as nld

    ds = nld.TtyrecDataset(DATASET, batch_size=1, seq_length=SEQ_LENGTH, dbfilename=db,
                           gameids=list(gameids), shuffle=False)
    for mb in ds:
        chars = mb["tty_chars"][0]
        ids = mb["gameids"][0]
        for t in range(chars.shape[0]):
            gid = int(ids[t])
            if gid == 0:
                continue
            yield gid, chars[t]


def scan_games(db, gameids, scanner=GameScanner):
    """Yield one finished scanner per game (game identifiers never leave this function)."""
    current, scan = None, None
    for gid, frame in iter_frames(db, gameids):
        if gid != current:
            if scan is not None:
                yield scan.finish()
            current, scan = gid, scanner()
        scan.feed(frame)
    if scan is not None:
        yield scan.finish()


def connect(db):
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def sample_ids(db, where, n, seed):
    """Random sample (fixed seed) of 3.6.x game ids matching the SQL condition; n=None takes all."""
    con = connect(db)
    ids = sorted(r[0] for r in con.execute(f"select gameid from games where version like '3.6%' and ({where})"))
    con.close()
    if n is not None and n < len(ids):
        ids = random.Random(seed).sample(ids, n)
    return ids


def census(prayers, top):
    """Markdown table of the most common following lines over a list of prayer dicts."""
    counts = Counter(line for p in prayers for line in p["lines"])
    rows = ["| # | count | line after \"You begin praying\" |", "|---|---|---|"]
    for i, (line, n) in enumerate(counts.most_common(top), 1):
        rows.append(f"| {i} | {n} | {line.replace('|', '/')} |")
    return "\n".join(rows)


COHORTS = {
    "random": "maxlvl >= 4",
    # humans whose last act was a prayer: the only way to see how a failed prayer reads (failures are rare)
    "died-praying": "maxlvl >= 4 and death like '%while praying%'",
    # humans killed by an angry god: the only way to see how an angry god's answer reads
    "wrath": "death like '%wrath%'",
}


def cmd_prayers(args):
    ids = sample_ids(args.db, COHORTS[args.cohort], args.games, args.seed)
    prayers = []
    for scan in scan_games(args.db, ids):
        prayers.extend(scan.prayers)
    print(f"games scanned: {len(ids)}   prayers seen: {len(prayers)}   (NetHack 3.6.x, cohort {args.cohort}, seed {args.seed})")
    print()
    print(census(prayers, args.top))
    verdicts = Counter(prayer_outcome(p["lines"]) for p in prayers)
    print()
    print("autoascend.prayer.prayer_outcome over these prayers: "
          + ", ".join(f"{name} {verdicts[name]}" for name in ("success", "failed", "unknown")))
    return 0 if prayers else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, default_games in (("prayers", cmd_prayers, 400),):
        p = sub.add_parser(name)
        p.add_argument("--db", default=DEFAULT_DB)
        p.add_argument("--games", type=int, default=default_games, help="games to sample")
        p.add_argument("--seed", type=int, default=0, help="sampling seed (fixed, so numbers are reproducible)")
        if name == "prayers":
            p.add_argument("--top", type=int, default=40, help="rows of the census table")
            p.add_argument("--cohort", choices=sorted(COHORTS), default="random",
                           help="random: 3.6.x games reaching Dlvl 4+; died-praying: those that ended while praying; "
                                "wrath: those killed by an angry god")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
