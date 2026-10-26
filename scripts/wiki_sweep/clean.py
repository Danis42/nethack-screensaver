import re, sys
P = "reference/nethackwiki/text/pages/"
DROP = re.compile(r"histor|trivia|origin|encyclop|variant|slash|unnethack|dnethack|evilhack|xnethack|splicehack|gnollhack|fiqhack|nethack4|sporkhack|grunthack|hack'em|nerfhack|see also|external link|reference|gallery|in other|other games|etymology|literature|mythology|dungeons (&|and) dragons|tile|3\.7", re.I)
def clean(t):
    s = open(P + t + ".txt", errors="replace").read()
    out, keep = [], True
    for line in s.split("\n"):
        m = re.match(r"^(=+)\s*(.*?)\s*=+\s*$", line)
        if m and len(m.group(1)) >= 2:
            keep = not DROP.search(m.group(2))
            if keep: out.append("## " + m.group(2))
            continue
        if not keep: continue
        line = re.sub(r"\[\[(?:Image|File):[^\]]*\]\]", "", line)
        line = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", line)
        line = re.sub(r"\[\[([^\]]*)\]\]", r"\1", line)
        line = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", line)
        line = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>|<[^>]+>", "", line)
        line = re.sub(r"'''?", "", line)
        line = re.sub(r"\{\{(sfn|cite|reflist|stub|nethack-\d+|DISPLAYTITLE|Wikipedia|otheruses|for|about|main|redirect|clear|-)[^}]*\}\}", "", line, flags=re.I)
        line = re.sub(r"\s+", " ", line).strip()
        if line and not re.match(r"^\{\{\s*\}\}$|^__\w+__$|^\[\[Category|^Category:|^\{\{ASCII\}\}", line): out.append(line)
    return "\n".join(out)
if __name__ == "__main__":
    for t in sys.argv[1:]:
        print(f"######## {t}\n{clean(t)}")
