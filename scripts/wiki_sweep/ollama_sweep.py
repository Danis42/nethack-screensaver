"""Ask a local Ollama model, page by page, which vanilla 3.6 facts in the NetHack wiki matter to the bot.

Resumable: pages already in the output JSONL are skipped. Usage:
    python3 -I scripts/wiki_sweep/ollama_sweep.py <cleaned-pages-dir-or-batches> <out.jsonl> [model]
"""
import json, os, re, sys, time, urllib.request

PROMPT = """You read one page of the NetHack wiki. The reader is a bot playing vanilla NetHack 3.6 as a lawful \
dwarvish Valkyrie, trying to survive, find the way down, keep fed, and ascend. Cheesy tactics are fine.
Ignore variants (SLASH'EM, dNetHack, EvilHack, xNetHack, UnNetHack, ...), version 3.7 "upcoming" notes, history,
trivia, interface and keyboard details.
List at most 5 facts from THIS page that would change what such a bot should do. For each give:
- "fact": the rule, with numbers if the page has them
- "detect": how the bot can notice the situation (exact message text, monster or item name, map feature)
- "action": what the bot should do
- "danger": 1 (minor) to 5 (often deadly or game-saving)
Answer only JSON: {"facts": [...]} and {"facts": []} if the page has nothing useful.

PAGE TITLE: %s
PAGE TEXT:
%s"""

def pages(src):
    for f in sorted(os.listdir(src)):
        if not re.fullmatch(r"\d{3}\.txt", f): continue
        text = open(os.path.join(src, f), errors="replace").read()
        for chunk in text.split("######## ")[1:]:
            title, _, body = chunk.partition("\n")
            yield title.strip(), body

def ask(model, title, body):
    req = urllib.request.Request("http://localhost:11434/api/generate", data=json.dumps({
        "model": model, "prompt": PROMPT % (title, body), "format": "json", "stream": False,
        "options": {"num_ctx": 8192, "temperature": 0}}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(json.loads(r.read())["response"])

def main():
    src, out = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "qwen2.5:14b"
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["page"] for l in open(out) if l.strip()}
    todo = [(t, b) for t, b in pages(src) if t not in done]
    print(f"{len(done)} done, {len(todo)} to go", flush=True)
    t0 = time.time()
    with open(out, "a") as o:
        for i, (title, body) in enumerate(todo, 1):
            facts = []
            # long pages go in 16k-character parts so prompt + answer fit the 8k context on the GPU
            for part in range(0, max(len(body), 1), 16000):
                try:
                    facts += ask(model, title, body[part:part + 16000]).get("facts", [])
                except Exception as e:
                    facts.append({"error": repr(e)[:200]})
            o.write(json.dumps({"page": title, "chars": len(body), "facts": facts}) + "\n"); o.flush()
            if i % 25 == 0:
                print(f"{i}/{len(todo)} pages, {(time.time() - t0) / i:.1f}s per page", flush=True)

if __name__ == "__main__":
    main()
