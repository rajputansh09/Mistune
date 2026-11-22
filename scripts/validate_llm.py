"""Pre-execution validity check for LLM-generated tests (proposal: "invalid
outputs recorded before execution").

For every test file under PATH:
  1. syntax  - does it parse?
  2. import  - does it import with our helpers on sys.path?
  3. oracle  - for each Case(...), is `expected` what CommonMark 0.31.2
               prescribes (markdown-it-py reference)?  Each invalid case is
               classified:
                 HALLUCINATED  expected != reference  and mistune == reference
                                (LLM was wrong, Mistune right)
                 BOTH-WRONG    expected != reference  and mistune != reference
                 DEFECT-FOUND  expected == reference  and mistune != reference
                                (a genuine Mistune deviation found by the LLM)
Usage: python scripts/validate_llm.py llm/generated/refined_bb/run1
"""
import ast
import glob
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from oracle import reference, render  # noqa: E402

out = {"files": [], "cases": 0, "valid": 0, "hallucinated": [], "both_wrong": [], "defect_found": []}
for path in sorted(glob.glob(os.path.join(sys.argv[1], "**", "test_*.py"), recursive=True)):
    rec = {"file": os.path.relpath(path, ROOT)}
    src = open(path).read()
    try:
        ast.parse(src)
        rec["syntax"] = "ok"
    except SyntaxError as e:
        rec["syntax"] = f"SyntaxError line {e.lineno}"
        out["files"].append(rec)
        continue
    spec = importlib.util.spec_from_file_location("llm_mod", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        rec["import"] = "ok"
    except Exception as e:  # noqa: BLE001
        rec["import"] = repr(e)
        out["files"].append(rec)
        continue
    for c in getattr(mod, "CASES", []):
        out["cases"] += 1
        ref, got = reference(c.md), render(c.md)
        if c.expected == ref:
            out["valid"] += 1
            if got != ref:
                out["defect_found"].append({"id": c.id, "md": c.md, "expected": c.expected, "mistune": got})
        else:
            bucket = "hallucinated" if got == ref else "both_wrong"
            out[bucket].append({"id": c.id, "md": c.md, "llm_expected": c.expected, "reference": ref, "mistune": got})
    out["files"].append(rec)

if out["cases"]:
    out["validity_pct"] = round(100 * out["valid"] / out["cases"], 1)
print(json.dumps(out, indent=1, ensure_ascii=False))
