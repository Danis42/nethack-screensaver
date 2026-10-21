# nethack-screensaver

After 5 minutes idle at your zsh prompt, your terminal shows NetHack played by
[AutoAscend](https://github.com/maciej-sypetkowski/autoascend) (ported to
Python 3.13 / NLE 1.3.0). Any key returns to your prompt.

## Install

```sh
cd ~/screens
uv sync
echo 'source ~/screens/zsh/nethack-screensaver.zsh' >> ~/.zshrc
```

Optional: `ln -s ~/screens/bin/nethack-screensaver ~/.local/bin/` to start it manually.

## Configure

Idle time: `export NETHACK_SCREENSAVER_IDLE=300` (before sourcing the hook).

`~/.config/nethack-screensaver/config.toml` (all optional):

```toml
delay = 0.1          # seconds per move
fast_delay = 0.005   # per move while nothing happens (known map, no monsters near)
level_pause = 1.0    # pause on a new dungeon level
end_pause = 5.0      # hold the final screen
status_line = false  # "Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14" (» = fast-forward)
role = "random"      # or arc bar cav hea kni mon pri ran rog sam tou val wiz
strategy = "pilgrim" # ascension route; "random" = secret mix: pilgrim daredevil sightseer treasure
reveal_goal = false  # true: show the secret goal on the game-over screen
```

Pacing: moves play at `delay` while the bot explores new map, fights (except while
farming XP on Dlvl 1) or has low HP; after 10 quiet moves it fast-forwards at
`fast_delay` (set it equal to `delay` to turn this off).

Goals: every game plays the ascension route (pilgrim), the project's only priority
since 2026-10-21 (see `docs/ROADMAP.md`). With `strategy = "random"` each game
secretly follows one strategy instead, picked once the character is known: strong roles (Bar, Sam, Val, Mon) get the hard goals more often, weak ones
(Arc, Tou, Rog, Hea, Wiz) the easier ones; every role can still get any goal. Pilgrim (aims to ascend)
tours the Mines, Minetown and Sokoban, then dives; Daredevil (aims to escape in
celestial disgrace) dives straight down; Sightseer visits Minetown and climbs
back out of the dungeon; Treasure hunter solves Sokoban, loots its prize and
escapes. Only the two escapes are reachable for this bot; both head home early
when they run out of food and prayer. The log records each
game's `strategy`, `outcome` and the last plan `milestone` it reached.

What to expect (benchmarks of v0.2.0, see `autoascend/PORTING.md`): Sightseer escapes in
about 20% of its games, Treasure hunter in about 15-20% (with the Sokoban prize only
around 1-2%), Daredevil reaches Dlvl 10+ in about 12-20%; Pilgrim rarely completes its
tour. Ascension is out of reach for this bot.

Game history: `~/.local/state/nethack-screensaver/games.jsonl`.
Errors: `~/.local/state/nethack-screensaver/player.log`.

## Develop

```sh
uv run pytest                 # fast tests
uv run pytest -m slow         # plays real games
uv run python scripts/benchmark.py -n 50 -j 8
```

AutoAscend is MIT licensed (`autoascend/LICENSE`); port notes and benchmark in
`autoascend/PORTING.md`.

## Bench server (for working on the bot)

`uv run screens-bench serve` starts a local server on http://localhost:8765 that plays bot
games on demand, stores every game per commit, and compares commits:

- **Baseline:** play a commit up to N games (`main` by default); the page's dashboard shows
  killers, depths, outcomes and crashes of the newest `main` commit with games.
- **Experiment:** candidate branch vs baseline, judged on one metric (default "reached Dlvl
  6+") at 192/384/576/1152 games per side; stored baseline games are reused.
- **Ascenders:** `screens-bench import xlog <url>` and `screens-bench import dumplogs` load
  real ascensions from public servers (e.g. hardfought.org) as a yardstick.

Claude drives it through the MCP server in `.mcp.json`. Only committed code can be
benchmarked; each commit runs from its own worktree under `~/.cache/screens-bench/`.
Results live in `~/.local/share/screens-bench/results.db`.
