# This folder: NLE moved to NetHack 5.0 for nethack-screensaver

This is a copy of the **NetHack Learning Environment (NLE)** with a small set of changes so that the
screensaver's bot can play **NetHack 5.0**. It is not a separate project; all credit for NLE and NetHack goes to
their authors.

- **NLE:** <https://github.com/NetHack-LE/nle> by the NLE Dev Team (originally Facebook AI Research; see
  `CITATION.cff` and `README.md` in this folder).
- **NetHack:** <https://www.nethack.org> by the NetHack DevTeam. NetHack 5.0 sources come with NLE's
  `NetHack-5-upgrade` work.
- **Licence:** NetHack General Public License, `LICENSE` in this folder. It applies to everything in this folder,
  including our changes. The rest of the repository is MIT (`../../LICENSE`).

## Base

Upstream branch `NetHack-5-upgrade`, commit
[`2a0e3baf10316d3706801ce845d4adb6373ac264`](https://github.com/NetHack-LE/nle/commit/2a0e3baf10316d3706801ce845d4adb6373ac264)
("Move NLE terminal dimension initialization to after NH Globals initialization (#133)", `v1.3.0-12`).

## Our changes

All of them are in `../nle-screens.patch` (`git diff 2a0e3baf cb9d6572`, 10 files, +139 / -69). They were made as
nine commits on a private branch `screens-nh5`, ending at `cb9d6572f3fec9b85a6ee5153c879bd6bab4ba72`, the NLE
commit that the bench jobs of this project record:

1. Link fixes for `_pynethack`.
2. The game starts: Lua 5.4.8, level files in `nhdat`, file prefixes set after `early_init`.
3. A temporary debug aid: panic and `impossible()` messages with a backtrace on stderr (`src/end.c`, `src/pline.c`).
4. `mons[]` / `objects[]` filled in `_pynethack`; `mname` property plus `pmnames`.
5. 3.6-like default options: `notutorial`, `autounlock:none`, `nosafe_wait`, `paranoid_confirmation:pray`, `notips`.
6. `nle_set_seed`: with `lgen` 0 only the dice are reseeded (used by the rewind tool).

One more change made when the folder was copied in (not in the patch): `pyproject.toml` has a fixed
`version = "1.3.0.post21+screens.nh5"` instead of a version from git (setuptools-scm cannot read git history
from a subfolder).

## Use

The main `pyproject.toml` installs it with `nle = { path = "vendor/nle" }`; `uv sync` builds it (needs a C/C++
compiler and cmake). The bench identifies this build by the git tree id of this folder (`bench/provenance.py`).
