"""Import real ascensions from public NetHack servers: xlogfiles and dumplogs."""
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "screens-bench (local NetHack bot research; 1 request per second)"
HARDFOUGHT_DUMPLOG = "https://www.hardfought.org/userdata/{initial}/{name}/nethack/dumplog/{starttime}.nh.txt"

# NetHack 3.6 'achieve' bits; newer servers write the names in 'achieveX'
ACHIEVE_36 = {
    0x001: "obtained_the_bell_of_opening", 0x002: "entered_gehennom",
    0x004: "obtained_the_candelabrum_of_invocation", 0x008: "obtained_the_book_of_the_dead",
    0x010: "performed_the_invocation_ritual", 0x020: "obtained_the_amulet_of_yendor",
    0x040: "entered_elemental_planes", 0x080: "entered_astral_plane", 0x100: "ascended",
    0x200: "obtained_the_luckstone_from_the_mines", 0x400: "obtained_the_sokoban_prize",
    0x800: "defeated_medusa",
}

_last_request = [0.0]


def fetch(url, cache_dir=None, min_interval=1.0):
    """Download text; with cache_dir each URL is fetched only once. At most one request per second."""
    cache = None
    if cache_dir is not None:
        cache = Path(cache_dir) / "downloads" / hashlib.sha1(url.encode()).hexdigest()
        if cache.exists():
            return cache.read_text(errors="replace")
    wait = _last_request[0] + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
            text = r.read().decode("utf-8", errors="replace")
    finally:
        _last_request[0] = time.monotonic()
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text)
    return text


def parse_xlog_line(line):
    """One xlogfile record as a dict of strings (fields split by TAB, or ':' in old files)."""
    sep = "\t" if "\t" in line else ":"
    record = dict(f.split("=", 1) for f in line.rstrip("\n").split(sep) if "=" in f)
    return record if "name" in record and "death" in record else None


def achievements(record):
    if record.get("achieveX"):
        return record["achieveX"].split(",")
    bits = int(record.get("achieve", "0"), 16)
    return [name for bit, name in sorted(ACHIEVE_36.items()) if bits & bit]


def _source(url):
    host = urlparse(url).hostname or "unknown"
    return "hardfought" if host.endswith("hardfought.org") else host


def import_xlog(store, url, source=None, fetcher=fetch):
    source = source or _source(url)
    lines = ascensions = added = 0
    for line in fetcher(url, None).splitlines():
        record = parse_xlog_line(line)
        if record is None:
            continue
        lines += 1
        if record["death"] != "ascended" or "starttime" not in record:
            continue
        ascensions += 1
        record["achievements"] = achievements(record)
        added += store.add_reference(source, record)
    return {"lines": lines, "ascensions": ascensions, "added": added}


def dumplog_url(source, record):
    if source == "hardfought":
        name = record["name"]
        return HARDFOUGHT_DUMPLOG.format(initial=name[0], name=name, starttime=record["starttime"])
    return None


def import_dumplogs(store, cache_dir, limit=500, fetcher=fetch):
    out = {"fetched": 0, "failed": 0, "unsupported": 0}
    for ref in store.references():
        if ref["dumplog"] is not None:
            continue
        url = dumplog_url(ref["source"], ref["record"])
        if url is None:
            out["unsupported"] += 1
            continue
        if out["fetched"] + out["failed"] >= limit:
            break
        try:
            text = fetcher(url, cache_dir)
        except (OSError, ValueError):  # missing file, network error: retried next time
            out["failed"] += 1
            continue
        store.set_dumplog(ref["id"], text)
        out["fetched"] += 1
    return out


_HEADING = re.compile(r"^(\S[^:]*):\s*$")
_ITEM = re.compile(r"^\s+[a-zA-Z$#] - (.*)$")
_EVENT = re.compile(r"^\s*(\d+): (.*)$")
_WAND = re.compile(r"wand of ([a-z ]+?)(?: \(|$| named| called)")


def sections(text):
    out, current = {}, None
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def _int(match):
    return int(match.group(1)) if match else None


def parse_dumplog(text):
    s = sections(text)
    carried = s.get("Inventory", []) + [l for name, lines in s.items() if name.startswith("Contents of")
                                         for l in lines]
    inventory = [m.group(1) for line in carried if (m := _ITEM.match(line))]
    attributes = [l.strip() for l in s.get("Final Attributes", []) if l.strip()]
    vanquished = " ".join(s.get("Vanquished creatures", []))
    return {
        "inventory": inventory,
        "attributes": attributes,
        "conducts": [l.strip() for l in s.get("Voluntary challenges", []) if l.strip()],
        "vanquished": _int(re.search(r"(\d+) creatures vanquished", vanquished)),
        "ac": _int(re.search(r"Your armor class was (-?\d+)", " ".join(s.get("Basics", [])))),
        "xl": _int(re.search(r"a level (\d+) ", " ".join(s.get("Background", [])))),
        "events": [(int(m.group(1)), m.group(2).strip())
                   for line in s.get("Major events", []) if (m := _EVENT.match(line))],
        "reflection": any("reflection" in a for a in attributes),
        "magic_resistance": any("magic-protected" in a for a in attributes),
        "bag_of_holding": any("bag of holding" in i for i in inventory),
        "wands": sorted({m.group(1).strip() for i in inventory if (m := _WAND.search(i))}),
    }
