import pytest

from autoascend import soko_solver


@pytest.mark.parametrize("text", list(soko_solver.maps), ids=lambda t: t.splitlines()[1].strip())
def test_stored_solution_replays_on_its_map(text):
    sokomap = soko_solver.convert_map(text)
    for (y, x), (dy, dx) in soko_solver.maps[text]:
        sokomap.move(y, x, dy, dx)
    assert not (sokomap.sokomap == soko_solver.BOULDER).any()
