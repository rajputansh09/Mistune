"""Evaluate one test group with the comparison metrics from the proposal.

  * test validity     - expected outputs checked against the CommonMark
                        reference (markdown-it-py) before execution
  * execution result  - pass / fail / known-defect
  * coverage          - statement and branch coverage of mistune (coverage.py)
  * efficiency        - branch coverage per test case
  * redundancy        - share of test cases that add no coverage beyond a
                        greedy minimal subset with identical arc coverage
  * defect detection  - distinct defect IDs exposed
(Mutation score comes from mutation/mutate.py.)

Usage:  python scripts/evaluate.py NAME PATH [PATH ...]
Writes: results/<NAME>_results.json, results/<NAME>_metrics.json
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))


def run(name, paths):
    res_file = os.path.join(ROOT, "results", f"{name}_results.json")
    cov_file = os.path.join(ROOT, "results", f".coverage.{name}")
    env = dict(os.environ, RESULTS_FILE=res_file, COVERAGE_FILE=cov_file)
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-m", "not slow", "--cov", "--cov-config=.coveragerc",
         "--cov-context=test", "--cov-report=", *paths],
        cwd=ROOT, env=env, check=False,
    )
    return json.load(open(res_file)), cov_file


def coverage_metrics(cov_file):
    import coverage

    cov = coverage.Coverage(data_file=cov_file, config_file=os.path.join(ROOT, ".coveragerc"))
    cov.load()
    import io

    buf = io.StringIO()
    total = cov.report(file=buf)  # combined statement+branch %
    analysis = {"stmts": 0, "miss": 0, "branches": 0, "partial_or_missing": 0}
    for f in cov.get_data().measured_files():
        a = cov._analyze(f)  # noqa: SLF001 - public API lacks branch counts
        n = a.numbers
        analysis["stmts"] += n.n_statements
        analysis["miss"] += n.n_missing
        analysis["branches"] += n.n_branches
        analysis["partial_or_missing"] += n.n_missing_branches
    stmt = 100 * (1 - analysis["miss"] / analysis["stmts"])
    br = 100 * (1 - analysis["partial_or_missing"] / analysis["branches"])

    # per-test arcs for redundancy (dynamic contexts)
    data = cov.get_data()
    per_test = {}
    for ctx in data.measured_contexts():
        if not ctx:
            continue
        data.set_query_context(ctx)
        arcs = set()
        for f in data.measured_files():
            arcs |= {(f, a) for a in (data.arcs(f) or [])}
        key = ctx.split("|")[0]
        per_test.setdefault(key, set()).update(arcs)
    data.set_query_context(None)
    universe = set().union(*per_test.values()) if per_test else set()
    chosen, covered = [], set()
    while covered != universe:  # greedy set cover
        best = max(per_test, key=lambda t: len(per_test[t] - covered))
        if not per_test[best] - covered:
            break
        chosen.append(best)
        covered |= per_test[best]
    return {
        "combined_pct": round(total, 1),
        "statement_pct": round(stmt, 1),
        "branch_pct": round(br, 1),
        "tests_with_coverage": len(per_test),
        "minimal_subset_size": len(chosen),
    }


def oracle_validity(rows):
    """For rows with markdown input + expected HTML: is the expected value
    what CommonMark prescribes?  (Mistune-specific rows are skipped.)"""
    from oracle import reference

    checked = valid = 0
    invalid = []
    for r in rows:
        if r.get("input") is None or r.get("expected") is None or r["id"].startswith("BB-MS"):
            continue
        checked += 1
        if reference(r["input"]) == r["expected"]:
            valid += 1
        else:
            invalid.append(r["id"])
    return checked, valid, invalid


def main():
    name, paths = sys.argv[1], sys.argv[2:]
    rows, cov_file = run(name, paths)
    cm = coverage_metrics(cov_file)
    checked, valid, invalid = oracle_validity(rows)
    n = len(rows)
    verdicts = {}
    for r in rows:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    defects = sorted({r["defect"] for r in rows if r.get("defect")} | {
        r["id"] for r in rows if r["verdict"] == "FAIL"})
    m = {
        "group": name,
        "test_cases": n,
        "verdicts": verdicts,
        **cm,
        "branch_pct_per_test": round(cm["branch_pct"] / n, 3) if n else 0,
        "redundancy_pct": round(100 * (1 - cm["minimal_subset_size"] / max(cm["tests_with_coverage"], 1)), 1),
        "oracle_checked": checked,
        "oracle_valid": valid,
        "oracle_invalid_ids": invalid,
        "defects_or_failures": defects,
    }
    json.dump(m, open(os.path.join(ROOT, "results", f"{name}_metrics.json"), "w"), indent=1)
    print(json.dumps(m, indent=1))


if __name__ == "__main__":
    main()
