import random

from autoascend.passtune import ALL_TUNES, Solver, feedback, parse


def test_feedback_follows_music_c():
    assert feedback("ABCDE", "ABCDE") == (0, 5)
    assert feedback("EDCBA", "ABCDE") == (4, 1)
    assert feedback("AAAAA", "ABCDE") == (0, 1)
    # a wrong-place note never matches a tune note whose own place is right
    assert feedback("BAAAA", "AABBB") == (2, 1)


def test_parse_messages():
    assert parse("You hear 2 tumblers click and 1 gear turn.") == (2, 1)
    assert parse("You hear 1 tumbler click.") == (1, 0)
    assert parse("You hear 3 gears turn.") == (0, 3)
    assert parse("You extract a strange sound from the wooden flute!") == (0, 0)


def test_solver_finds_tunes_within_eight_guesses():
    rng = random.Random(7)
    for i in range(5):
        tune, solver = rng.choice(ALL_TUNES), Solver(i)
        for n in range(1, 9):
            guess = solver.next_guess()
            if guess == tune:
                break
            solver.record(guess, feedback(guess, tune))
        else:
            raise AssertionError(tune)
