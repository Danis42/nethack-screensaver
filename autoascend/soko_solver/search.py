"""Live-board Sokoban solver: push boulders until every trap (hole or pit) is filled.

The stored solutions in maps.py only fit an undisturbed board; this searches from whatever
the board looks like now (boulders destroyed, pushed differently, a mimic that wasn't one).
Pushes are ((boulder_y, boulder_x), (dy, dx)), the format of the stored solutions.

NetHack's traps lie along corridors, so they are filled one at a time, always one that a
boulder can reach without crossing another unfilled trap (A* per trap). Greedy fills can
strand the last boulders, so each fill has a few alternatives to backtrack into."""
import heapq
import itertools
import math
import time

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class _OutOfBudget(Exception):
    pass


def _reachable(start, free):
    seen, todo = {start}, [start]
    while todo:
        y, x = todo.pop()
        for n in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if n in free and n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def _push_distances(floor, trap):
    """Pushes a lone boulder on each cell needs to reach `trap` (reverse 'pull' search)."""
    dist, frontier = {trap: 0}, [trap]
    while frontier:
        nxt = []
        for cy, cx in frontier:
            for dy, dx in DIRS:
                prev, push_from = (cy - dy, cx - dx), (cy - 2 * dy, cx - 2 * dx)
                if prev in floor and push_from in floor and prev not in dist:
                    dist[prev] = dist[(cy, cx)] + 1
                    nxt.append(prev)
        frontier = nxt
    return dist


def _unwind(path):
    pushes = []
    while path is not None:
        path, push = path
        pushes.append(push)
    return pushes[::-1]


def _fill_one(floor, boulders, traps, player, target, live, deadline, budget, crossable):
    """A* yielding ways (cheapest first) to drop some boulder into `target`; other traps
    stay untouched. Each yield is (pushes, boulders left, player position)."""
    # A boulder pushed over another unfilled trap falls in there instead, so route around them.
    dist = _push_distances(floor - (traps - {target}), target)
    if not any(b in dist for b in boulders):
        return
    order = itertools.count()
    h = lambda bs: min(dist.get(b, 10 ** 6) for b in bs)
    queue = [(h(boulders), 0, next(order), boulders, player, None)]
    seen, results = set(), set()
    while queue:
        _, g, _, bs, pos, path = heapq.heappop(queue)
        # The player may walk through pits (falls in, climbs out) but never into a hole,
        # which drops you a level; pushing from inside a pit is impossible.
        reach = _reachable(pos, floor - bs - (traps - crossable))
        key = (bs, min(reach))
        if key in seen:
            continue
        seen.add(key)
        budget[0] -= 1
        if budget[0] < 0 or time.monotonic() > deadline:
            raise _OutOfBudget()
        for by, bx in bs:
            for dy, dx in DIRS:
                dest = (by + dy, bx + dx)
                if (by - dy, bx - dx) not in reach or (by - dy, bx - dx) in traps \
                        or dest not in floor or dest in bs:
                    continue
                push = (path, ((by, bx), (dy, dx)))
                if dest == target:
                    left = bs - {(by, bx)}
                    if left not in results:  # alternatives must leave a different board
                        results.add(left)
                        yield _unwind(push), left, (by, bx)
                    continue
                if dest in traps or dest not in live:
                    continue  # wrong trap, or a square from which no boulder fills anything
                nbs = (bs - {(by, bx)}) | {dest}
                heapq.heappush(queue, (g + 1 + h(nbs), g + 1, next(order), nbs, (by, bx), push))


def solve(floor, boulders, traps, player, max_states=300_000, max_seconds=10.0, alternatives=3,
          crossable=frozenset()):
    """Pushes that fill every trap, or None if none is found within the limits.
    `max_seconds=None` drops the wall-clock limit, so only the state budget stops the search.

    `crossable`: traps the player may walk through (the pits of the lower levels)."""
    floor, crossable = frozenset(floor), frozenset(crossable)
    # max_seconds=None: no wall-clock limit, only max_states ends the search (same result under any load)
    deadline = math.inf if max_seconds is None else time.monotonic() + max_seconds
    budget = [max_states]
    failed = set()  # boards already shown to be dead ends

    def search(bs, ts, pos):
        if not ts:
            return []
        if len(bs) < len(ts) or (bs, ts) in failed:
            return None
        live = set().union(*(_push_distances(floor, t) for t in ts))
        order = sorted(ts, key=lambda t: min(_push_distances(floor - (ts - {t}), t).get(b, 10 ** 6) for b in bs))
        for target in order:
            for n, (sub, left, end) in enumerate(_fill_one(floor, bs, ts, pos, target, live, deadline, budget,
                                                           crossable & ts)):
                rest = search(left, ts - {target}, end)
                if rest is not None:
                    return sub + rest
                if n + 1 >= alternatives:
                    break
        failed.add((bs, ts))
        return None

    try:
        return search(frozenset(boulders), frozenset(traps), player)
    except _OutOfBudget:
        return None
