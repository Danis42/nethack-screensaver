"""Castle passtune Mastermind (Phase 02.2 Part 1c).

Played next to the drawbridge, a wrong 5-note tune (notes A-G) answers "You hear N tumblers click and M gears
turn." Gears are notes in the right place; tumblers are right notes in the wrong place, counted by NetHack's own
asymmetric rule (music.c do_play_instrument), which `feedback` copies exactly: a guess note at a wrong place
matches the first unmatched tune note equal to it whose own place is not already right. No message means 0/0.
"""
import itertools
import random
import re

NOTES = "ABCDEFG"
ALL_TUNES = tuple("".join(t) for t in itertools.product(NOTES, repeat=5))
FIRST_GUESS = "AABBC"
SAMPLE = 400  # candidate guesses scored per turn (all of them when fewer remain)


def feedback(guess: str, tune: str) -> tuple[int, int]:
    """(tumblers, gears) exactly as music.c computes them."""
    tumblers = gears = 0
    matched = [False] * 5
    for x in range(5):
        if guess[x] == tune[x]:
            gears += 1
            matched[x] = True
        else:
            for y in range(5):
                if not matched[y] and guess[x] == tune[y] and guess[y] != tune[y]:
                    tumblers += 1
                    matched[y] = True
                    break
    return tumblers, gears


_HEARD = re.compile(r"You hear (\d+) tumblers? click(?: and (\d+) gears? turn)?|You hear (\d+) gears? turn")


def parse(message: str) -> tuple[int, int] | None:
    """(tumblers, gears) from the game's message; (0, 0) when the tune drew no sound at all."""
    m = _HEARD.search(message or "")
    if m is None:
        return (0, 0)
    if m.group(3) is not None:
        return 0, int(m.group(3))
    return int(m.group(1)), int(m.group(2) or 0)


class Solver:
    def __init__(self, seed: int = 0):
        self.candidates = list(ALL_TUNES)
        self.rng = random.Random(seed)
        self.history: list[tuple[str, tuple[int, int]]] = []

    def next_guess(self) -> str:
        if not self.history:
            return FIRST_GUESS
        if len(self.candidates) <= 2:
            return self.candidates[0]
        pool = self.candidates if len(self.candidates) <= SAMPLE else self.rng.sample(self.candidates, SAMPLE)
        targets = self.candidates if len(self.candidates) <= 2000 else self.rng.sample(self.candidates, 2000)
        best, best_score = None, None
        for guess in pool:  # smallest worst-case partition of the (sampled) remaining tunes
            counts = {}
            for tune in targets:
                key = feedback(guess, tune)
                counts[key] = counts.get(key, 0) + 1
            score = max(counts.values())
            if best_score is None or score < best_score:
                best, best_score = guess, score
        return best

    def record(self, guess: str, result: tuple[int, int]) -> None:
        self.history.append((guess, result))
        self.candidates = [t for t in self.candidates if feedback(guess, t) == result]

    @property
    def solved(self) -> bool:
        return bool(self.history) and self.history[-1][1] == (0, 5)
