"""Optional follow-up turns F1 (gaps) and F2 (correctness) from llm/prompts/PROMPTS.md, via the OpenAI API.

For <group>/run1 the conversation is replayed exactly: [prompt, first reply (verbatim from llm/sessions/<P>_run1_raw.txt),
F1, reply, F2, reply]. F1/F2 are built from the scored first reply, with the same wording for basic and refined groups:

  F1 (gaps)  BB: Mistune parser functions never executed by the first reply's tests (coverage data of run1).
             WB: statements of the code under test never executed (source lines, from the same coverage data).
  F2 (fixes) BB: cases rejected by validate_llm.py, with the CommonMark reference output.
             WB: tests judged INVALID in the two-reviewer review, with the reviewers' reason. Mistune's actual value is
             deliberately NOT shown, so the model cannot simply copy observed behaviour.

Each turn ends with the same instruction to output the complete updated file in the original format. The file after the
last turn is saved to llm/generated/<group>/run1_followup/ (scored separately; never replaces the first-reply score).

Usage: set -a; . ~/.config/ece322/openai.env; set +a
       .venv/bin/python scripts/run_llm_followup.py [--groups P1 P2 P3 P4] [--dry-run]
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_llm_api as base  # noqa: E402

ROOT = base.ROOT
RESEND = ("\n\nOutput the complete updated Python file only (all previous test cases plus your changes), "
          "in exactly the same format as before.")
WB_SCOPE = {"helpers.py": ["parse_link_text", "parse_link_label", "parse_link_href", "parse_link_title", "parse_link"],
            "inline_parser.py": ["InlineParser.parse_emphasis", "InlineParser.parse_codespan"]}
BB_FILES = ["block_parser.py", "inline_parser.py", "list_parser.py"]


def coverage_report(group):
    import coverage
    cov = coverage.Coverage(data_file=os.path.join(ROOT, "results", f".coverage.llm_{group}_run1"),
                            config_file=os.path.join(ROOT, ".coveragerc"))
    cov.load()
    out = os.path.join(ROOT, "results", f".cov_{group}_run1.json")
    cov.json_report(outfile=out, show_contexts=False)
    rep = json.load(open(out))
    os.remove(out)
    return {k.split("mistune/")[-1]: v for k, v in rep["files"].items()}


def f1_text(group, kind):
    files = coverage_report(group)
    if kind == "bb":
        never = []
        for f in BB_FILES:
            for fn, d in files[f]["functions"].items():
                if fn and d["summary"]["covered_lines"] == 0 and d["summary"]["num_statements"] > 0:
                    never.append(f"{f[:-3]}.{fn}")
        return ("F1 (gaps): These requirements are not met yet. The following Mistune 3.1.4 parser functions were never "
                "executed by any of your test inputs, so the Markdown features they handle are untested:\n"
                + "\n".join(f"  - {n}" for n in never) + "\nAdd test cases for them." + RESEND), never
    gaps, missing_count = [], 0
    for f, fns in WB_SCOPE.items():
        src = open(os.path.join(ROOT, ".venv/lib/python3.13/site-packages/mistune", f)).read().splitlines()
        for fn in fns:
            d = files[f]["functions"].get(fn)
            if not d or not d["missing_lines"]:
                continue
            missing_count += len(d["missing_lines"])
            gaps.append(f"  {fn}:\n" + "\n".join(f"      {src[n - 1].strip()}" for n in d["missing_lines"]))
    return ("F1 (gaps): These requirements are not met yet. The following statements of the code under test are never "
            "executed by your tests:\n" + "\n".join(gaps) + "\nAdd tests for them." + RESEND), missing_count


def f2_text(group, kind):
    if kind == "bb":
        v = json.load(open(os.path.join(ROOT, "results", f"llm_{group}_run1_validity.json")))
        bad = v["hallucinated"] + v["both_wrong"]
        lines = [f"  {x['id']}: input {x['md']!r}\n      your expected: {x['llm_expected']!r}\n      reference:     {x['reference']!r}"
                 for x in bad]
        return ("F2 (correctness): These expected values do not match the CommonMark 0.31.2 reference output in the "
                "required normalised form (the reference is shown). Re-derive them from the spec.\n" + "\n".join(lines) + RESEND), [x["md"] for x in bad]
    rows = list(csv.DictReader(open(os.path.join(ROOT, "results", f"llm_{group}_run1_wb_review.csv"))))
    bad = [r for r in rows if r["agreed verdict"] == "INVALID"]
    lines = [f"  {r['test'].split('::')[1]}: {r['note'].split(' [R')[0]}" for r in bad]
    return ("F2 (correctness): Independent review judged these tests' expected values wrong (the reason is shown). "
            "Re-derive them from the CommonMark 0.31.2 spec and the code's contract, not by guessing what Mistune does.\n"
            + "\n".join(lines) + RESEND), [r["test"].split("::")[1] for r in bad]


def chat(messages):
    import urllib.request
    body = {"model": base.MODEL, "messages": messages}
    req = urllib.request.Request(base.API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="+", default=list(base.PROMPTS), choices=list(base.PROMPTS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sess = os.path.join(ROOT, "llm/sessions")
    for pid in a.groups:
        _, group, kind = base.PROMPTS[pid]
        prompt = base.assemble(pid)
        first = open(os.path.join(sess, f"{pid}_run1_raw.txt")).read()
        f1, f1_info = f1_text(group, kind)
        f2, f2_items = f2_text(group, kind)
        if a.dry_run:
            print(f"===== {pid} F1 ({len(f1)} chars)\n{f1[:1500]}\n===== {pid} F2 ({len(f2)} chars, {len(f2_items)} items)\n{f2[:1500]}\n")
            continue
        msgs = [{"role": "user", "content": prompt}, {"role": "assistant", "content": first},
                {"role": "user", "content": f1}]
        r1 = chat(msgs)
        reply1 = r1["choices"][0]["message"]["content"] or ""
        msgs += [{"role": "assistant", "content": reply1}, {"role": "user", "content": f2}]
        r2 = chat(msgs)
        reply2 = r2["choices"][0]["message"]["content"] or ""
        open(os.path.join(sess, f"{pid}_run1_F1_raw.txt"), "w").write(reply1)
        open(os.path.join(sess, f"{pid}_run1_F2_raw.txt"), "w").write(reply2)
        json.dump({"messages_sent": msgs, "response_F1": r1, "response_F2": r2, "F1_gap_items": f1_info, "F2_rejected": f2_items},
                  open(os.path.join(sess, f"{pid}_run1_followup_api.json"), "w"), indent=1, ensure_ascii=False)
        out_dir = os.path.join(ROOT, "llm/generated", group, "run1_followup")
        os.makedirs(out_dir, exist_ok=True)
        code, edits = base.extract(reply2)
        open(os.path.join(out_dir, f"test_llm_{kind}.py"), "w").write(code)
        f1_code, _ = base.extract(reply1)
        open(os.path.join(sess, f"{pid}_run1_F1_file.py"), "w").write(f1_code)
        u1, u2 = r1["usage"], r2["usage"]
        open(os.path.join(sess, f"{pid}_run1_followup.md"), "w").write(f"""# LLM session log: {base.PROMPTS[pid][0]} run1 follow-ups (F1 + F2)

| Field | Value |
|---|---|
| Date / time | {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')} |
| Model | `{r2.get('model')}` via OpenAI Chat Completions API, default sampling |
| Conversation | prompt → first reply (verbatim, `{pid}_run1_raw.txt`) → F1 → reply → F2 → reply |
| F1 content | {'parser functions never executed: ' + str(len(f1_info)) if kind == 'bb' else 'unexecuted statements in scope: ' + str(f1_info)} |
| F2 content | {len(f2_items)} rejected {'cases (validate_llm.py)' if kind == 'bb' else 'tests (two-reviewer review, INVALID)'} |
| Tokens F1 (in/out) | {u1['prompt_tokens']} / {u1['completion_tokens']} |
| Tokens F2 (in/out) | {u2['prompt_tokens']} / {u2['completion_tokens']} |
| Raw replies | `{pid}_run1_F1_raw.txt`, `{pid}_run1_F2_raw.txt`; full conversation in `{pid}_run1_followup_api.json` |
| File after F1 (analysis only) | `llm/sessions/{pid}_run1_F1_file.py` |
| File after F2 (SCORED SEPARATELY) | `llm/generated/{group}/run1_followup/test_llm_{kind}.py` |
| Mechanical edits to final reply | {'; '.join(p for p, _ in edits) or 'none'} |
""")
        print(f"{pid}: F1 {u1['prompt_tokens']}/{u1['completion_tokens']}  F2 {u2['prompt_tokens']}/{u2['completion_tokens']}  "
              f"edits={len(edits)} -> {os.path.relpath(os.path.join(out_dir, f'test_llm_{kind}.py'), ROOT)}")


if __name__ == "__main__":
    main()
