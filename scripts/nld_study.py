"""Human-game studies on NLD-NAO for Phase 1. Usage: uv run python scripts/nld_study.py prayers|food ...

Reads recorded NetHack 3.6 games (ttyrecs) from the NLD-NAO dataset, read-only. Only aggregate numbers
and anonymised message lines are printed (god names are replaced by <god>; no per-game or per-player identifiers).

  prayers  what the message line shows after "You begin praying to" (census of the following lines)
  food     food and prayer habits on Dlvl 4-12: humans who got through (maxlvl >= 13) versus humans who starved there
"""
import argparse
import random
import re
import sqlite3
import statistics
import sys
from collections import Counter, namedtuple
from multiprocessing import Pool
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
_ATTRIBUTE_RE = re.compile(r"\b(?:St|Dx|Co|In|Wi|Ch):")
_SPLIT_RE = re.compile(r"\s{2,}")
WIDTH = 80
BAND = (4, 12)  # Dlvl range of the food study (the plan's "Dlvl 4-12")
MIN_COVERAGE = 0.8  # a game counts only if its status line was readable up to this share of its real length
SHORT_GAP = 1000  # RESEARCH Pattern 3: a hunger prayer is safe ~77% of the time after a gap of 400, ~95% after 1000
MEAL_STALE_TURNS = 60  # an opener with no closer is forgotten after this many turns
TERMINATORS = (".", "!", "?", ")", "\"", "'")
HUNGER_ORDER = {"": 0, "Hungry": 1, "Weak": 2, "Fainting": 3, "Fainted": 4}


def message_line(frame):
    """Row 0 of a (24, 80) tty frame, decoded and stripped."""
    return bytes(frame[0]).decode("ascii", errors="replace").replace("\x00", " ").strip()


def status(frame):
    """(dlvl or None, turn or None, hunger word or "") from the status line on row 23.

    A screen with a window drawn over the status lines leaves pieces of the attribute line (St: Dx: ... Ch:)
    in row 23 and stale digits after "T:"; such a row is not a reading and gives (None, None, "")."""
    return _parse_status(bytes(frame[23]).decode("ascii", errors="replace").replace("\x00", " "))


def _parse_status(text):
    if _ATTRIBUTE_RE.search(text):
        return (None, None, "")
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


_EAT_OPEN_RE = re.compile(r"^This .+ (?:is|tastes) .+!$")  # "This newt corpse tastes terrible!"
_EAT_CLOSE_RE = re.compile(r"^You finish eating\b")
_EAT_STOP_RE = re.compile(r"^You stop eating\b")
_EAT_MORE_RE = re.compile(r"^You're having a hard time getting all of it down\.|\bhits? the spot!$")


def eat_kind(line):
    """"open" (first bite message), "close" (finished), "stop" (interrupted), "more" (part of a meal) or None."""
    if _EAT_CLOSE_RE.match(line):
        return "close"
    if _EAT_STOP_RE.match(line):
        return "stop"
    if _EAT_MORE_RE.search(line):
        return "more"
    if _EAT_OPEN_RE.match(line):
        return "open"
    return None


def eat_event(line):
    """True for a message that shows the hero eating: finishing or stopping a meal, the taste line, the
    satiated warning."""
    return eat_kind(line) is not None


class BandClock:
    """Turns spent in a Dlvl band from consecutive status readings; each turn delta belongs to the earlier
    reading (its dlvl and hunger word). A reading without T: is counted in `excluded` and skipped.

    Recorded screens are sometimes garbled, so a reading is ignored when its turn counter goes backwards,
    exceeds max_turn (the game's real length, when known), or jumps ahead by more than JUMP turns and the
    next reading does not confirm it (a half-drawn counter with stale digits looks like a huge jump)."""

    JUMP = 500

    def __init__(self, band=BAND, max_turn=None):
        self.band = band
        self.max_turn = max_turn
        self.total = self.hungry = self.weak = self.excluded = 0
        self.has_turn = False
        self._last = None
        self._pending = None

    @property
    def last(self):
        """The last accepted (dlvl, turn, hunger) reading, or None."""
        return self._last

    def update(self, reading):
        """Take one (dlvl, turn, hunger) reading; True when it counts as the hero's current state."""
        dlvl, turn, hunger = reading
        if dlvl is None:
            return False
        if turn is None:
            self.excluded += 1
            return True
        if self.max_turn is not None and turn > self.max_turn:
            return False
        if self._pending is not None:
            if turn >= self._pending[1]:
                self._commit(self._pending)
                self._pending = None
            elif self._last is None or turn >= self._last[1]:
                self._pending = None  # the jump was not confirmed: it was a garbled reading
        last = self._last
        if last is not None and turn < last[1]:
            return False
        if last is not None and turn - last[1] > self.JUMP:
            self._pending = reading
            return False
        self._commit(reading)
        return True

    def _commit(self, reading):
        last = self._last
        self.has_turn = True
        if last is not None and self.band[0] <= last[0] <= self.band[1]:
            delta = reading[1] - last[1]
            self.total += delta
            if hungry_or_worse(last[2]):
                self.hungry += delta
            if weak_or_worse(last[2]):
                self.weak += delta
        self._last = reading


def band_turns(frames, band=BAND):
    """BandClock over the status lines of these frames: .total turns on Dlvl band[0]..band[1], .hungry and
    .weak of them, .excluded = frames that show a Dlvl but no turn counter."""
    clock = BandClock(band)
    for frame in frames:
        clock.update(status(frame))
    return clock


class GameScanner:
    """Feed the frames of ONE game in order; collects what the studies need.

    The message line is redrawn piece by piece (a ttyrec has every partial write), so a displayed
    message is only reported once it is replaced or cleared; growth of the same text is one message.
    The status (dlvl, turn, hunger) is the reading from the frame where the message first appeared.

    prayers: one dict per "You begin praying to" with the turn, dlvl and hunger word at that moment and
    the next distinct messages (normalised) that followed, up to FOLLOW_LINES within FOLLOW_TURNS.
    clock: BandClock over the status lines. meals: one dict (turn, dlvl, hunger) per meal, counted once
    however many of its messages show (taste line, finish line, interruptions)."""

    FOLLOW_LINES = 6
    FOLLOW_TURNS = 3  # a prayer takes 3 moves; the god answers in the last one
    FOLLOW_FRAMES = 400

    def __init__(self, band=BAND, max_turn=None):
        self.prayers = []
        self.meals = []
        self.clock = BandClock(band, max_turn)
        self.frames = 0
        self._meal_open = False
        self._meal_turn = None
        self._row0 = b""
        self._shown = ""
        self._shown_status = (None, None, "")
        self._prayer_status = None
        self._status_rows = None
        self._status = (None, None, "")
        self._pending = None

    def feed(self, frame):
        self.frames += 1
        rows = bytes(frame[23])
        if rows != self._status_rows:
            self._status_rows = rows
            text = rows.decode("ascii", errors="replace").replace("\x00", " ")
            reading = _parse_status(text)
            # a transient redraw without the status text (or a half-drawn turn counter) must not
            # erase the last good reading
            if reading[0] is not None and self.clock.update(reading):
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

    def _on_meal(self, kind, reading):
        dlvl, turn, hunger = reading
        stale = self._meal_open and turn is not None and self._meal_turn is not None \
            and turn - self._meal_turn > MEAL_STALE_TURNS
        if kind == "more":
            if turn is not None:
                self._meal_turn = turn
            return
        if kind == "close":
            if self._meal_open and not stale:
                self._meal_open = False
                return
            self._meal_open = False
        elif kind == "stop":
            if self._meal_open and not stale:
                self._meal_turn = turn
                return
            self._meal_open = True
        else:  # open
            if self._meal_open and not stale:
                self._meal_turn = turn
                return
            self._meal_open = True
        self._meal_turn = turn
        self.meals.append({"turn": turn, "dlvl": dlvl, "hunger": hunger})

    def _on_message(self, sentence, reading):
        kind = eat_kind(sentence)
        if kind is not None:
            self._on_meal(kind, reading)
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

    def record(self):
        """The per-game numbers of the food study (no identifiers): time on the band, prayers and meals on it."""
        lo, hi = self.clock.band

        def in_band(item):
            return item["dlvl"] is not None and lo <= item["dlvl"] <= hi and item["turn"] is not None

        last = self.clock.last
        return {
            "has_turn": self.clock.has_turn,
            # how much of the game the clock followed: a window over the status lines hides stretches of it
            "coverage": last[1] / self.clock.max_turn if last and self.clock.max_turn else None,
            "band_turns": self.clock.total,
            "hungry_turns": self.clock.hungry,
            "weak_turns": self.clock.weak,
            "prayers": [{"turn": p["turn"], "hunger": p["hunger"], "outcome": prayer_outcome(p["lines"])}
                        for p in self.prayers if in_band(p)],
            "meals": sum(1 for m in self.meals if in_band(m)),
        }


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


def scan_games(db, gameids, scanner=GameScanner, max_turns=None):
    """Yield one finished scanner per game (game identifiers never leave this function).
    max_turns: optional {gameid: real number of turns} bounding the turn counter of each game."""
    current, scan = None, None
    for gid, frame in iter_frames(db, gameids):
        if gid != current:
            if scan is not None:
                yield scan.finish()
            current = gid
            scan = scanner(max_turn=max_turns.get(gid)) if max_turns else scanner()
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


def _median(values):
    return statistics.median(values) if values else None


def _percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(pct / 100 * len(ordered)))]


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def summarize(records):
    """Pooled numbers of one cohort from the per-game records (GameScanner.record()); games without a turn
    counter, or whose status line was unreadable for over 20% of the game, are excluded and counted. Rates are per 1000 turns spent on the band, summed over all games."""
    used = [r for r in records if r["has_turn"] and (r.get("coverage") is None or r["coverage"] >= MIN_COVERAGE)]
    band = sum(r["band_turns"] for r in used)
    prayers = [p for r in used for p in r["prayers"]]
    gaps, after_gap = [], []  # after_gap: (gap since the previous prayer, that prayer failed?)
    for r in used:
        ordered = sorted(r["prayers"], key=lambda p: p["turn"])
        for before, prayer in zip(ordered, ordered[1:]):
            gaps.append(prayer["turn"] - before["turn"])
            after_gap.append((prayer["turn"] - before["turn"], prayer["outcome"] == "failed"))
    short = [failed for gap, failed in after_gap if gap < SHORT_GAP]
    long = [failed for gap, failed in after_gap if gap >= SHORT_GAP]
    return {
        "games_used": len(used),
        "games_excluded": len(records) - len(used),
        "median_band_turns": _median([r["band_turns"] for r in used]),
        "band_turns": band,
        "prayers": len(prayers),
        "games_with_prayer": sum(1 for r in used if r["prayers"]),
        "prayers_per_1000": _ratio(1000 * len(prayers), band),
        "gaps": gaps,
        "median_gap": _median(gaps),
        "gap_p25": _percentile(gaps, 25),
        "share_gaps_under_500": _ratio(sum(g < 500 for g in gaps), len(gaps)),
        "failed_after_short_gap": (sum(short), len(short)),
        "failed_after_long_gap": (sum(long), len(long)),
        "share_prayers_weak": _ratio(sum(weak_or_worse(p["hunger"]) for p in prayers), len(prayers)),
        "share_prayers_failed": _ratio(sum(p["outcome"] == "failed" for p in prayers), len(prayers)),
        "meals": sum(r["meals"] for r in used),
        "meals_per_1000": _ratio(1000 * sum(r["meals"] for r in used), band),
        "share_hungry": _ratio(sum(r["hungry_turns"] for r in used), band),
        "share_weak": _ratio(sum(r["weak_turns"] for r in used), band),
    }


def _fmt(value, kind):
    if value is None:
        return "-"
    if kind == "pct":
        return f"{100 * value:.1f}%"
    if kind == "int":
        return f"{value:,.0f}"
    return f"{value:.2f}"


FOOD_ROWS = (
    ("games used / excluded (no T: counter, or status unreadable for over 20% of the game)", lambda s: f"{s['games_used']} / {s['games_excluded']}"),
    ("turns observed on Dlvl 4-12 (median per game)", lambda s: _fmt(s["median_band_turns"], "int")),
    ("turns observed on Dlvl 4-12 (all games)", lambda s: _fmt(s["band_turns"], "int")),
    ("prayers on Dlvl 4-12 (games with at least one)", lambda s: f"{s['prayers']} ({s['games_with_prayer']})"),
    ("prayers per 1000 band turns", lambda s: _fmt(s["prayers_per_1000"], "f")),
    ("median gap between prayers (turns; gaps counted)", lambda s: f"{_fmt(s['median_gap'], 'int')} ({len(s['gaps'])})"),
    ("25th percentile of the gap between prayers", lambda s: _fmt(s["gap_p25"], "int")),
    ("share of gaps under 500 turns", lambda s: _fmt(s["share_gaps_under_500"], "pct")),
    ("failed prayers after a gap under 1000 turns (failed / prayers)", lambda s: "%d / %d" % s["failed_after_short_gap"]),
    ("failed prayers after a gap of 1000+ turns (failed / prayers)", lambda s: "%d / %d" % s["failed_after_long_gap"]),
    ("share of prayers while Weak or worse", lambda s: _fmt(s["share_prayers_weak"], "pct")),
    ("share of prayers that failed", lambda s: _fmt(s["share_prayers_failed"], "pct")),
    ("eating events per 1000 band turns (meals: %s)", lambda s: _fmt(s["meals_per_1000"], "f")),
    ("share of band turns Hungry or worse", lambda s: _fmt(s["share_hungry"], "pct")),
    ("share of band turns Weak or worse", lambda s: _fmt(s["share_weak"], "pct")),
)
FOOD_COLUMNS = (
    ("through", "got through (maxlvl >= 13)"),
    ("starved", "starved or fainted to death (maxlvl 4-12)"),
    ("starved_there", "same, and died on Dlvl 4-12"),
)


def food_table(summaries):
    """Markdown table, one column per cohort in `summaries` ({"through": ..., "starved": ...})."""
    names = [(key, title) for key, title in FOOD_COLUMNS if key in summaries]
    rows = ["| | " + " | ".join(title for _, title in names) + " |", "|---|" + "---|" * len(names)]
    for label, fn in FOOD_ROWS:
        if "%s" in label:
            label = label % " / ".join(str(summaries[key]["meals"]) for key, _ in names)
        rows.append(f"| {label} | " + " | ".join(fn(summaries[key]) for key, _ in names) + " |")
    return "\n".join(rows)


def game_turns(db, ids):
    """{gameid: real number of turns} for these games (bounds the turn counter read off the screen)."""
    con = connect(db)
    turns = {}
    for start in range(0, len(ids), 500):
        part = ids[start:start + 500]
        marks = ",".join("?" * len(part))
        turns.update(con.execute(f"select gameid, turns from games where gameid in ({marks})", part).fetchall())
    con.close()
    return turns


def _scan_chunk(job):
    db, ids, turns = job
    return [scan.record() for scan in scan_games(db, ids, max_turns=turns)]


def scan_records(db, ids, jobs):
    """Per-game records of these games, scanned by `jobs` processes (order does not matter)."""
    turns = game_turns(db, ids)
    chunks = [ids[i::jobs * 3] for i in range(jobs * 3) if ids[i::jobs * 3]]
    if jobs <= 1 or len(chunks) <= 1:
        return [r for chunk in chunks for r in _scan_chunk((db, chunk, turns))]
    with Pool(jobs) as pool:
        return [r for part in pool.imap_unordered(_scan_chunk, [(db, c, turns) for c in chunks]) for r in part]


FOOD_COHORTS = {
    "through": "maxlvl >= 13",
    "starved": "maxlvl between 4 and 12 and (death like '%starv%' or death like '%faint%')",
    # the stricter reading of "starved there": the death level (not only the deepest level) is on the band
    "starved_there": "maxlvl between 4 and 12 and deathlev between 4 and 12 "
                     "and (death like '%starv%' or death like '%faint%')",
}
TABLE_START, TABLE_END = "<!-- food-table:start -->", "<!-- food-table:end -->"
SECTION = "## Food and prayer on Dlvl 4-12"


def write_section(path, table, header):
    """Put `header` + table between the markers under SECTION in the study file (created if absent);
    text outside the markers (the findings written by hand) is kept."""
    block = f"{TABLE_START}\n{header}\n\n{table}\n{TABLE_END}"
    text = Path(path).read_text() if Path(path).exists() else ""
    if TABLE_START in text and TABLE_END in text:
        head, rest = text.split(TABLE_START, 1)
        tail = rest.split(TABLE_END, 1)[1]
        text = head + block + tail
    else:
        text = text.rstrip("\n") + f"\n\n{SECTION}\n\n{block}\n"
    Path(path).write_text(text)


def cmd_food(args):
    summaries, sizes = {}, {}
    for key, where in FOOD_COHORTS.items():
        limit = args.games if key == "through" else args.starved_games
        ids = sample_ids(args.db, where, limit, args.seed)
        sizes[key] = len(ids)
        summaries[key] = summarize(scan_records(args.db, ids, args.jobs))
    table = food_table(summaries)
    header = (f"Cohorts (NetHack 3.6.x): **got through** = {sizes['through']} games sampled from those with maxlvl >= 13 "
              f"(sampling seed {args.seed}); **starved** = {sizes['starved']} games with maxlvl 4-12 whose death line "
              f"names starvation or fainting from lack of food (all of them); **starved, died there** = the "
              f"{sizes['starved_there']} of those whose death level is also on Dlvl 4-12. Band = status line shows Dlvl 4..12 "
              f"(Mines and Sokoban levels count by their Dlvl). Rates pool all games of a cohort.")
    print(header)
    print()
    print(table)
    if args.write:
        write_section(args.write, table, header)
    return 0


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
    for name, fn, default_games in (("prayers", cmd_prayers, 400), ("food", cmd_food, 300)):
        p = sub.add_parser(name)
        p.add_argument("--db", default=DEFAULT_DB)
        p.add_argument("--games", type=int, default=default_games, help="games to sample")
        p.add_argument("--seed", type=int, default=0, help="sampling seed (fixed, so numbers are reproducible)")
        if name == "prayers":
            p.add_argument("--top", type=int, default=40, help="rows of the census table")
            p.add_argument("--cohort", choices=sorted(COHORTS), default="random",
                           help="random: 3.6.x games reaching Dlvl 4+; died-praying: those that ended while praying; "
                                "wrath: those killed by an angry god")
        if name == "food":
            p.add_argument("--starved-games", type=int, default=None,
                           help="cap the starved cohort (default: all of them)")
            p.add_argument("--jobs", type=int, default=6, help="processes decoding games")
            p.add_argument("--write", metavar="FILE", help="put the table into this study file (between markers)")
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
