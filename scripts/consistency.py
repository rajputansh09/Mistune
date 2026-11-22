"""Repeatability of LLM generation across runs (proposal section 3).
Usage: python scripts/consistency.py llm/generated/refined_bb
Expects sub-folders run1, run2, ... each with test_*.py containing CASES."""
import glob
import importlib.util
import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from oracle import reference  # noqa: E402

runs = {}
for d in sorted(glob.glob(os.path.join(sys.argv[1], "run[0-9]"))):
    inputs, valid, total, techniques = set(), 0, 0, {}
    for f in glob.glob(os.path.join(d, "test_*.py")):
        spec = importlib.util.spec_from_file_location("m", f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        for c in getattr(m, "CASES", []):
            total += 1
            inputs.add(c.md.strip())
            valid += c.expected == reference(c.md)
            techniques[c.technique] = techniques.get(c.technique, 0) + 1
    runs[os.path.basename(d)] = {"inputs": inputs, "cases": total, "valid": valid, "techniques": techniques}

report = {r: {k: v for k, v in x.items() if k != "inputs"} | {"distinct_inputs": len(x["inputs"])} for r, x in runs.items()}
pairs = {}
for a, b in itertools.combinations(runs, 2):
    A, B = runs[a]["inputs"], runs[b]["inputs"]
    pairs[f"{a}~{b}"] = round(len(A & B) / len(A | B), 3) if A | B else None
report["jaccard_overlap"] = pairs
if runs:
    common = set.intersection(*(r["inputs"] for r in runs.values()))
    report["inputs_in_all_runs"] = len(common)
print(json.dumps(report, indent=1))
