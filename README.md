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
strategy = "random"  # secret goal per game: pilgrim daredevil sightseer treasure
reveal_goal = false  # true: show the secret goal on the game-over screen
```

Pacing: moves play at `delay` while the bot explores new map, fights (except while
farming XP on Dlvl 1) or has low HP; after 10 quiet moves it fast-forwards at
`fast_delay` (set it equal to `delay` to turn this off).

Secret goals: each game secretly follows one strategy, picked once the character
is known: strong roles (Bar, Sam, Val, Mon) get the hard goals more often, weak ones
(Arc, Tou, Rog, Hea, Wiz) the easier ones; every role can still get any goal. Pilgrim (aims to ascend)
solves Sokoban, tours the Mines and Minetown, then dives (dwarves and gnomes, for
whom the Mines are peaceful, do the Mines first); Daredevil (aims to escape in
celestial disgrace) dives straight down; Sightseer visits Minetown and climbs
back out of the dungeon; Treasure hunter solves Sokoban, loots its prize and
escapes. Only the two escapes are reachable for this bot; both head home early
when they run out of food and prayer. The log records each
game's `strategy`, `outcome` and the last plan `milestone` it reached.

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
