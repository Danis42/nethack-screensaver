# AutoAscend port notes

Upstream: maciej-sypetkowski/autoascend @ 8527910 (MIT).
Target: Python 3.13, NLE 1.3.0 (gymnasium), numpy 2, modern numba/opencv.

## Removed
- visualization/, rl_utils.py, rl_scoring.init_fight2_model (torch/RL, tile viewer)
- utils.plot_dashboard (matplotlib/seaborn)
- nltk (replaced by agent._edit_distance)

## Changes
- character.py, item/inventory.py: regex literals with invalid escapes (`\d`, `\.`, `\?`, `\]`) made raw strings (SyntaxWarning on 3.12+, future error). Behavior unchanged.
