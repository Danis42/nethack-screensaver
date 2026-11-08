"""NetHack options for every game the bot plays (natural and staged)."""
import nle.nethack as nh

# price_quotes (NetHack 5): unidentified items show the shop prices already seen, e.g. "{buy 26-35 sell 10}"
GAME_OPTIONS = tuple(nh.NETHACKOPTIONS) + ("price_quotes",)
