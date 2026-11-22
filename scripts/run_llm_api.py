"""Generate the LLM test groups through the OpenAI API (replaces pasting into the ChatGPT UI).

Each (prompt, run) is ONE fresh API request: a single user message, no system prompt, no history,
so every run is an independent "fresh chat". The prompts are assembled verbatim from
llm/prompts/PROMPTS.md (format blocks and code snippets substituted in).

For every run it writes:
  llm/sessions/<PROMPT>_run<k>_raw.txt        the model's reply, untouched
  llm/sessions/<PROMPT>_run<k>_api.json       request parameters + full API response (usage, ids); no key
  llm/sessions/<PROMPT>_run<k>.md             filled-in session log (SESSION_TEMPLATE.md fields)
  llm/generated/<group>/run<k>/test_llm_<bb|wb>.py   the SCORED first reply after mechanical edits only

Mechanical edits (the only ones PROMPTS.md allows): strip prose / markdown fences. Each one is logged.
Expected values are never touched.

Usage:
  set -a; . ~/.config/ece322/openai.env; set +a      # OPENAI_API_KEY (never stored in the repo)
  .venv/bin/python scripts/run_llm_api.py --dry-run             # print the assembled prompts only
  .venv/bin/python scripts/run_llm_api.py --runs 1 2 3          # all four prompts, runs 1-3
  .venv/bin/python scripts/run_llm_api.py --prompts P2 --runs 1 # one prompt, one run
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "gpt-5.4-mini-2026-03-17"
API = "https://api.openai.com/v1/chat/completions"

PROMPTS = {  # id -> (PROMPTS.md heading, output group folder, test file kind)
    "P1": ("P1-BB-basic", "basic_bb", "bb"),
    "P2": ("P2-BB-refined", "refined_bb", "bb"),
    "P3": ("P3-WB-basic", "basic_wb", "wb"),
    "P4": ("P4-WB-refined", "refined_wb", "wb"),
}


def block_after(md, heading):
    m = re.search(r"^#+ " + re.escape(heading) + r"\s*\n+```\n(.*?)```", md, re.S | re.M)
    if not m:
        sys.exit(f"could not find a code block under heading '{heading}' in PROMPTS.md")
    return m.group(1).rstrip("\n")


def assemble(pid):
    md = open(os.path.join(ROOT, "llm/prompts/PROMPTS.md")).read()
    text = block_after(md, PROMPTS[pid][0])
    text = text.replace("<FORMAT-BB>", block_after(md, "FORMAT-BB"))
    text = text.replace("<FORMAT-WB>", block_after(md, "FORMAT-WB"))
    paste = re.search(r"<paste llm/prompts/_snippet_helpers\.py and _snippet_inline\.py>", text)
    if paste:
        snippets = "\n\n".join(
            open(os.path.join(ROOT, f"llm/prompts/_snippet_{n}.py")).read().rstrip("\n") for n in ("helpers", "inline")
        )
        text = text[: paste.start()] + snippets + text[paste.end():]
    assert "<" + "paste" not in text and "<FORMAT" not in text, f"unsubstituted placeholder in {pid}"
    return text


def call(prompt):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY not set (load ~/.config/ece322/openai.env)")
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.load(r)
            return body, resp, round(time.time() - t0, 1)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:500]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            sys.exit(f"API error {e.code}: {msg}")


def extract(reply):
    """Mechanical edits only: take the Python out of markdown fences / drop surrounding prose."""
    edits = []
    fences = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", reply, re.S)
    if fences:
        code = max(fences, key=len)
        edits.append(("Reply wrapped in markdown fence(s)" + (f" ({len(fences)} blocks; kept the largest)" if len(fences) > 1 else ""),
                      "Removed the fence lines"))
        outside = re.sub(r"```(?:python|py)?[ \t]*\n.*?```", "", reply, flags=re.S).strip()
        if outside:
            edits.append(("Prose outside the code", f"Removed {len(outside.splitlines())} line(s) of prose"))
    else:
        code = reply
    return code.strip("\n") + "\n", edits


def session_md(pid, run, group, kind, prompt, resp, secs, edits, rel_test):
    u = resp.get("usage", {})
    rows = "\n".join(f"| {i} | {p} | {f} |" for i, (p, f) in enumerate(edits, 1)) or "| – | none | – |"
    return f"""# LLM session log: {PROMPTS[pid][0]} run{run}

| Field | Value |
|---|---|
| Team member | (generated via API by script `scripts/run_llm_api.py`) |
| Date / time | {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')} |
| Model and version | `{resp.get('model')}` via OpenAI Chat Completions API (requested `{MODEL}`) |
| Fresh chat? Memory or custom instructions off? | Yes: one independent API request, single user message, no system prompt, no history |
| Sampling parameters | API defaults (temperature / reasoning effort not set) |
| Prompt file / text | `llm/prompts/PROMPTS.md` {PROMPTS[pid][0]} (assembled text in `{pid}_run{run}_api.json`) |
| First reply saved as (SCORED) | `{rel_test}` |
| Follow-up turns used (F1/F2), saved as | none in this run |
| Wall-clock time: API call (s) | {secs} |
| Tokens (prompt / completion / reasoning) | {u.get('prompt_tokens')} / {u.get('completion_tokens')} / {u.get('completion_tokens_details', {}).get('reasoning_tokens')} |
| Finish reason | {resp['choices'][0].get('finish_reason')} |
| Raw reply saved as | `llm/sessions/{pid}_run{run}_raw.txt` |
| Test file saved as | `{rel_test}` |

## Mechanical edits made to the FIRST reply before scoring
(only stripping prose or fences and fixing imports are allowed; expected values are never changed. Count each one.)

| # | Problem | Fix |
|---|---|---|
{rows}

## Observations
- Did it follow the requested technique(s)? Did it give the requested number of cases?
- Hallucinations: invented APIs, wrong CommonMark claims
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", nargs="+", default=list(PROMPTS), choices=list(PROMPTS))
    ap.add_argument("--runs", nargs="+", type=int, default=[1])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="overwrite an existing run")
    a = ap.parse_args()
    for pid in a.prompts:
        prompt = assemble(pid)
        if a.dry_run:
            print(f"===== {pid} ({len(prompt)} chars)\n{prompt}\n")
            continue
        _, group, kind = PROMPTS[pid]
        for run in a.runs:
            out_dir = os.path.join(ROOT, "llm/generated", group, f"run{run}")
            test_path = os.path.join(out_dir, f"test_llm_{kind}.py")
            if os.path.exists(test_path) and not a.force:
                print(f"{pid} run{run}: exists, skipping (use --force)")
                continue
            body, resp, secs = call(prompt)
            reply = resp["choices"][0]["message"]["content"] or ""
            sess = os.path.join(ROOT, "llm/sessions")
            os.makedirs(sess, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)
            open(os.path.join(sess, f"{pid}_run{run}_raw.txt"), "w").write(reply)
            json.dump({"request": body, "response": resp, "seconds": secs}, open(os.path.join(sess, f"{pid}_run{run}_api.json"), "w"),
                      indent=1, ensure_ascii=False)
            code, edits = extract(reply)
            open(test_path, "w").write(code)
            rel = os.path.relpath(test_path, ROOT)
            open(os.path.join(sess, f"{pid}_run{run}.md"), "w").write(session_md(pid, run, group, kind, prompt, resp, secs, edits, rel))
            u = resp.get("usage", {})
            print(f"{pid} run{run}: {secs}s, tokens in/out {u.get('prompt_tokens')}/{u.get('completion_tokens')}, "
                  f"finish={resp['choices'][0].get('finish_reason')}, edits={len(edits)} -> {rel}")


if __name__ == "__main__":
    main()
