# nethack-screensaver

After 5 minutes idle at your zsh prompt, your terminal shows a game of NetHack. Any key returns to your prompt.

> **Status (2026-11-23).** The project spent its first phase trying to make the bot behind the screensaver
> *ascend* (win NetHack 5.0) in one clean game. It got far in measurement and research but not in play: no game
> passed Medusa. That work is frozen at tag **`ascension-bot-v1`**; read **[HANDOFF.md](HANDOFF.md)** to continue it.
> `main` is turning into a lighter screensaver that replays recorded, interesting games instead of playing live.

## Install (bot version, tag `ascension-bot-v1`)

```sh
git clone https://github.com/Danis42/nethack-screensaver ~/screens && cd ~/screens && git checkout ascension-bot-v1
uv sync          # also builds the patched NLE (NetHack 5.0); needs a C compiler and cmake
echo 'source ~/screens/zsh/nethack-screensaver.zsh' >> ~/.zshrc
```

Optional: `ln -s ~/screens/bin/nethack-screensaver ~/.local/bin/` to start it by hand.

## Configure

Idle time: `export NETHACK_SCREENSAVER_IDLE=300` (before sourcing the hook).

`~/.config/nethack-screensaver/config.toml` (all optional):

```toml
delay = 0.1          # seconds per move
fast_delay = 0.005   # per move while nothing happens (known map, no monsters near)
level_pause = 1.0    # pause on a new dungeon level
end_pause = 5.0      # hold the final screen
status_line = false  # "Game #12 · Mon · Dlvl 7 · T:4310 · Best: Dlvl 14" (» = fast-forward)
role = "random"      # or arc bar cav hea kni mon pri ran rog sam tou val wiz
strategy = "pilgrim" # ascension route; "random" = secret mix: pilgrim daredevil sightseer treasure
reveal_goal = false  # true: show the secret goal on the game-over screen
```

Pacing: moves play at `delay` while the bot explores, fights or has low HP; after 10 quiet moves it fast-forwards
at `fast_delay` (set it equal to `delay` to turn this off).

Strategies: Pilgrim (aims to ascend: Mines, Minetown, Sokoban, then dive), Daredevil (dives straight down),
Sightseer (Minetown and back out of the dungeon), Treasure hunter (Sokoban prize and back out).

Game history: `~/.local/state/nethack-screensaver/games.jsonl`. Errors: `~/.local/state/nethack-screensaver/player.log`.

## What to expect from the bot

Natural Monk games, 10,000 seeds (bench job 23, see HANDOFF.md): 65% reach the Gnomish Mines, 47% Dlvl 10,
5% Dlvl 15, 0.6% Medusa's level, none get further.

## Develop

```sh
uv run pytest                 # fast tests
uv run pytest -m slow         # plays real games
uv run screens-bench serve    # bench dashboard on http://localhost:8765
bash scripts/install_hooks.sh # once per checkout: commit labels
```

Every commit carries a `Kind:` trailer (`refactor`, `behavior` or `docs`); the rule is in
`githooks/commit_kind.py`. The bench, the statistics and the proof rules are described in HANDOFF.md.

## Credits and licences

- Bot: [AutoAscend](https://github.com/maciej-sypetkowski/autoascend) by Maciej Sypetkowski and Michał Sypetkowski,
  MIT (`autoascend/LICENSE`), ported from upstream @ 8527910.
- This repository: MIT (`LICENSE`).
- Game: [NetHack](https://www.nethack.org) 5.0 through the [NetHack Learning Environment](https://github.com/NetHack-LE/nle),
  vendored with our NetHack 5.0 changes in `vendor/nle` (credits and changes: `vendor/nle/SCREENS.md`);
  NetHack General Public License.
