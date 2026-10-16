# NetHack screensaver: source from ~/.zshrc.
# Starts after NETHACK_SCREENSAVER_IDLE seconds (default 300) idle at the prompt.
typeset -g _NETHACK_SCREENSAVER_BIN="${${(%):-%x}:A:h:h}/bin/nethack-screensaver"
TMOUT=${NETHACK_SCREENSAVER_IDLE:-300}

TRAPALRM() {
    [[ -o interactive && -t 0 && -t 1 ]] || return 0
    zle && zle -I
    "$_NETHACK_SCREENSAVER_BIN"
    zle && zle reset-prompt
    return 0
}
