"""What NetHack 3.6 prints after a prayer, as seen in recorded human games (standard library only).

The strings below come from the census in .planning/phases/01-midgame-survival/01-HUMAN-STUDY.md
(NLD-NAO ttyrecs: 400 random games reaching Dlvl 4+, the 141 games that ended "while praying" and the
27 games killed by an angry god). God names are removed: every marker is a substring that holds for any
god. Expected but NOT seen in those games, so deliberately absent: "You feel a hopeful feeling.",
"You feel that <god> is bummed/ticklish/full" (hallucination), "Goodbye level N." (the recorded game
that lost a level printed another word), "Thou hast strayed from the path." and the minion summons text.
"""

PRAYER_START = "You begin praying to"

# A prayer that is going to work shows one of these (p_type 3 makes the hero invulnerable for the
# 3 moves, so the shimmering light and "starts to attack you, but pulls back" are certain signs).
SUCCESS_MARKERS = (
    "You are surrounded by a shimmering light.",
    "starts to attack you, but pulls back.",
    "is well-pleased.",
    "is pleased.",
    "is satisfied.",
    "Your stomach feels content.",
    "You feel much better.",
    "You feel better.",
    "You feel purified.",
    "You feel in good health again.",
    "You can hear again.",
    "You are surrounded by a golden glow.",
    "You are surrounded by a light blue aura.",
    "A spellbook appears at your feet!",
    "softly glows amber",
    "light blue for a moment.",
)

# A prayer that went wrong: the god is displeased or angry, or the hero died while praying
# (an unsafe prayer gives no shimmering light, so monsters hit and the hero dies helpless).
FAILURE_MARKERS = (
    "is displeased.",
    "Thou hast angered me.",
    "Thou must relearn thy lessons!",
    "Thou art arrogant, mortal.",
    "Thou durst call upon me?",
    "Then die, mortal!",
    "Suddenly, a bolt of lightning strikes you!",
    "You fry to a crisp!",
    "You feel foolish!",
    "You are being punished for your misbehavior!",
    "A black glow surrounds you.",
    "You die...",
)


def prayer_outcome(lines):
    """"failed", "success" or "unknown" for the message lines that followed "You begin praying to".

    A failure marker wins over a success marker (a god can answer and still smite); no marker at all
    (an empty list, or only unrelated messages) is "unknown", never a guess."""
    lines = list(lines)
    if any(marker in line for line in lines for marker in FAILURE_MARKERS):
        return "failed"
    if any(marker in line for line in lines for marker in SUCCESS_MARKERS):
        return "success"
    return "unknown"
