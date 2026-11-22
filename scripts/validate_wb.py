"""Validity assessment for white-box tests (LLM or manual).

A unit test that asserts whatever the code returns always passes, so passing is
not evidence of correctness.  For every test in PATH this script reports:

  outcome        PASS / FAIL on unmodified Mistune 3.1.4
  ENCODES-BUG    a PASSING test rendered Markdown whose Mistune output differs
                 from the CommonMark reference (default HTML config only), so it
                 may assert behaviour the spec forbids -> review
  kills          number of sampled mutants (150, seed 322, helpers.py and
                 inline_parser.py) this test detects; 0 -> WEAK
and writes results/<name>_wb_review.csv for the manual review
(VALID / TAUTOLOGICAL / INVALID, two independent reviewers).

Usage: python scripts/validate_wb.py PATH [NAME] [--no-mutation]
"""
import csv
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
from oracle import norm, reference  # noqa: E402

path = sys.argv[1]
name = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else \
    os.path.relpath(path, ROOT).replace("/", "_")
probe = os.path.join(ROOT, "results", f".{name}_probe.json")

# 1. run with the probe plugin
env = dict(os.environ, WB_PROBE_FILE=probe,
           PYTHONPATH=os.pathsep.join([os.path.join(ROOT, "scripts"), os.environ.get("PYTHONPATH", "")]))
subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "wb_probe_plugin", "-m", "not slow", *path.split(",")],
               cwd=ROOT, env=env, capture_output=True)
log = json.load(open(probe))
os.remove(probe)

rows = {}
for nodeid, rec in log.items():
    flagged = []
    for r in rec.get("rendered", []):
        if r["escape"] is False and not r["plugins"] and norm(r["html"]) != reference(r["src"]):
            flagged.append(r["src"])
    rows[nodeid] = {"test": nodeid, "outcome": rec.get("outcome", "?").upper(),
                    "encodes_bug": "ENCODES-BUG" if flagged and rec.get("outcome") == "passed" else "",
                    "nonconformant_inputs": " | ".join(repr(s) for s in flagged[:3]), "kills": ""}

# 2. per-test fault detection on a fixed mutant sample
if "--no-mutation" not in sys.argv:
    out = os.path.join(ROOT, "results", f"{name}_wb_mutation.json")
    subprocess.run([sys.executable, os.path.join(ROOT, "mutation", "mutate.py"), "--groups", f"g={path}",
                    "--only-files", "helpers.py,inline_parser.py", "--sample", "150", "--seed", "322",
                    "--per-test", "--timeout", "30", "--out", out], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    kills = {k: 0 for k in rows}
    for m in json.load(open(out)):
        for t in m.get("failed", {}).get("g", []):
            if t in kills:
                kills[t] += 1
    for k in rows:
        rows[k]["kills"] = kills[k]

# 3. review sheet + summary
csv_path = os.path.join(ROOT, "results", f"{name}_wb_review.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["test", "outcome", "encodes_bug", "kills", "nonconformant_inputs",
                                      "reviewer1 (VALID/TAUTOLOGICAL/INVALID)", "reviewer2", "agreed verdict",
                                      "note"])
    w.writeheader()
    for r in rows.values():
        w.writerow(r)
n = len(rows)
summary = {
    "tests": n,
    "pass": sum(r["outcome"] == "PASSED" for r in rows.values()),
    "fail": sum(r["outcome"] == "FAILED" for r in rows.values()),
    "encodes_bug": sum(bool(r["encodes_bug"]) for r in rows.values()),
}
if "--no-mutation" not in sys.argv:
    summary["weak_zero_kills"] = sum(r["kills"] == 0 for r in rows.values())
    summary["median_kills"] = sorted(r["kills"] for r in rows.values())[n // 2] if n else 0
summary["review_sheet"] = os.path.relpath(csv_path, ROOT)
json.dump(summary, open(os.path.join(ROOT, "results", f"{name}_wb_validity.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
