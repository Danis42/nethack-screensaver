"""What NetHack 3.6 prints after a prayer, as seen in recorded human games (standard library only).

The strings below come from the census in .planning/phases/01-midgame-survival/01-HUMAN-STUDY.md
(NLD-NAO ttyrecs: 400 random games reaching Dlvl 4+, the 141 games that ended "while praying" and the
27 games killed by an angry god). God names are removed: every marker is a substring that holds for any
god. Expected but NOT seen in those games, so deliberately absent: "You feel a hopeful feeling.",
"You feel that <god> is bummed/ticklish/full" (hallucination), "Goodbye level N." (the recorded game
that lost a level printed another word), "Thou hast strayed from the path." and the minion summons text.
"""

PRAYER_START = "You begin praying to"  # fact:prayer-start-message

# A prayer that is going to work shows one of these (p_type 3 makes the hero invulnerable for the
# 3 moves, so the shimmering light and "starts to attack you, but pulls back" are certain signs).
SUCCESS_MARKERS = (
    "You are surrounded by a shimmering light.",  # fact:prayer-safe-prayer-shimmering-light
    "starts to attack you, but pulls back.",  # fact:prayer-invulnerable-attack-pulls-back
    "is well-pleased.",  # fact:prayer-god-mood-message
    "is pleased.",  # fact:prayer-god-mood-message
    "is satisfied.",  # fact:prayer-god-mood-message
    "Your stomach feels content.",  # fact:prayer-fix-hunger-message
    "You feel much better.",  # fact:prayer-fix-low-hp-message
    "You feel better.",  # fact:prayer-fix-low-hp-feel-better
    "You feel purified.",  # fact:prayer-fix-lycanthropy-message
    "You feel in good health again.",  # fact:prayer-fix-illness-message
    "You can hear again.",  # fact:prayer-fix-deafness-message
    "You are surrounded by a golden glow.",  # fact:prayer-boon-golden-glow
    "You are surrounded by a light blue aura.",  # fact:prayer-boon-light-blue-aura
    "A spellbook appears at your feet!",  # fact:prayer-boon-spellbook-at-feet
    "softly glows amber",  # fact:prayer-fix-cursed-item-amber-glow
    "light blue for a moment.",  # fact:prayer-altar-water-light-blue
)

# A prayer that went wrong: the god is displeased or angry, or the hero died while praying
# (an unsafe prayer gives no shimmering light, so monsters hit and the hero dies helpless).
FAILURE_MARKERS = (
    "is displeased.",  # fact:prayer-angry-displeased
    "Thou hast angered me.",  # fact:prayer-angry-hast-angered-me
    "Thou must relearn thy lessons!",  # fact:prayer-angry-arrogant-relearn
    "Thou art arrogant, mortal.",  # fact:prayer-angry-arrogant-relearn
    "Thou durst call upon me?",  # fact:prayer-angry-durst-then-die
    "Then die, mortal!",  # fact:prayer-angry-durst-then-die
    "Suddenly, a bolt of lightning strikes you!",  # fact:prayer-angry-lightning
    "You fry to a crisp!",  # fact:prayer-angry-fry
    "You feel foolish!",  # fact:prayer-angry-wis-loss-foolish
    "You are being punished for your misbehavior!",  # fact:prayer-angry-punished
    "A black glow surrounds you.",  # fact:prayer-angry-black-glow
    "You die...",  # fact:death-you-die-message
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
