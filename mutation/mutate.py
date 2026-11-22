"""Fault injection by mutation testing (Lecture 10, textbook 9.2.2).

A small, transparent mutation engine (used instead of mutmut so every mutant
is reproducible and the operators match the lecture's taxonomy):

  VALUE     integer constant c -> c+1, c-1 ; True <-> False
  DECISION  <  <-> <=,  >  <-> >=,  == <-> !=,  and <-> or,  `if c` -> `if not c`,
            `in` <-> `not in`
  STATEMENT delete a statement (-> pass), `break` -> `continue`,
            `return x` -> `return None`

Each mutant changes exactly ONE node of ONE function of the selected modules
(competent-programmer hypothesis).  Every mutant is run against every test
group; a group *kills* a mutant if at least one of its tests fails (or the
run times out, i.e. the fault caused a hang).

Usage:
  python mutation/mutate.py --groups blackbox=tests/blackbox whitebox=tests/whitebox \
        integration=tests/integration --jobs 8 --out results/mutation.json
"""
import argparse
import ast
import copy
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import mistune  # noqa: E402

PKG = os.path.dirname(mistune.__file__)

# Units selected for white-box testing (proposal: block + inline parsers)
TARGETS = {
    "helpers.py": None,  # None = every function
    "util.py": None,
    "list_parser.py": None,
    "inline_parser.py": {
        "parse_escape", "parse_link", "parse_emphasis", "parse_codespan",
        "parse_inline_html", "parse_auto_link", "parse_auto_email", "parse", "precedence_scan",
    },
    "block_parser.py": {
        "parse_fenced_code", "parse_atx_heading", "parse_setex_heading", "parse_ref_link",
        "extract_block_quote", "parse_block_quote", "parse_raw_html", "parse_indent_code",
        "_parse_html_to_end", "_parse_html_to_newline",
    },
}

CMP_SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In}


class Site:
    def __init__(self, file, func, lineno, op, desc, kind):
        self.file, self.func, self.lineno, self.op, self.desc, self.kind = file, func, lineno, op, desc, kind


def _funcs(tree, wanted):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if wanted is None or node.name in wanted:
                yield node


def enumerate_mutants(file, wanted):
    """Yield (Site, index) for every mutation point; index is the visit order
    of the mutated node inside a fresh parse, so mutants are reproducible."""
    src = open(os.path.join(PKG, file)).read()
    tree = ast.parse(src)
    out = []
    for fn in _funcs(tree, wanted):
        for node in ast.walk(fn):
            ln = getattr(node, "lineno", fn.lineno)
            if isinstance(node, ast.Constant) and type(node.value) is int:
                out += [(fn.name, ln, "VALUE", f"{node.value} -> {node.value + 1}", ("int", +1)),
                        (fn.name, ln, "VALUE", f"{node.value} -> {node.value - 1}", ("int", -1))]
            elif isinstance(node, ast.Constant) and type(node.value) is bool:
                out.append((fn.name, ln, "VALUE", f"{node.value} -> {not node.value}", ("bool",)))
            elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in CMP_SWAP:
                a, b = type(node.ops[0]).__name__, CMP_SWAP[type(node.ops[0])].__name__
                out.append((fn.name, ln, "DECISION", f"{a} -> {b}", ("cmp",)))
            elif isinstance(node, ast.BoolOp):
                a = type(node.op).__name__
                out.append((fn.name, ln, "DECISION", f"{a} -> {'Or' if a == 'And' else 'And'}", ("boolop",)))
            elif isinstance(node, (ast.If, ast.While)):
                out.append((fn.name, ln, "DECISION", f"{type(node).__name__} cond -> not cond", ("negate",)))
            elif isinstance(node, ast.Break):
                out.append((fn.name, ln, "STATEMENT", "break -> continue", ("break",)))
            elif isinstance(node, ast.Return) and node.value is not None and not (
                isinstance(node.value, ast.Constant) and node.value.value is None
            ):
                out.append((fn.name, ln, "STATEMENT", "return x -> return None", ("return",)))
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.Expr)) and node is not fn.body[0]:
                out.append((fn.name, ln, "STATEMENT", "delete statement", ("delete",)))
    return src, out


def apply_mutant(src, wanted, k):
    """Re-walk the tree in the same order and apply the k-th mutation."""
    tree = ast.parse(src)
    i = 0
    for fn in _funcs(tree, wanted):
        for node in ast.walk(fn):
            ops = []
            if isinstance(node, ast.Constant) and type(node.value) is int:
                ops = ["int+", "int-"]
            elif isinstance(node, ast.Constant) and type(node.value) is bool:
                ops = ["bool"]
            elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in CMP_SWAP:
                ops = ["cmp"]
            elif isinstance(node, ast.BoolOp):
                ops = ["boolop"]
            elif isinstance(node, (ast.If, ast.While)):
                ops = ["negate"]
            elif isinstance(node, ast.Break):
                ops = ["break"]
            elif isinstance(node, ast.Return) and node.value is not None and not (
                isinstance(node.value, ast.Constant) and node.value.value is None
            ):
                ops = ["return"]
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.Expr)) and node is not fn.body[0]:
                ops.append("delete")
            for op in ops:
                if i == k:
                    _mutate(node, op, fn)
                    return ast.unparse(ast.fix_missing_locations(tree))
                i += 1
    raise IndexError(k)


def _mutate(node, op, fn):
    if op == "int+":
        node.value += 1
    elif op == "int-":
        node.value -= 1
    elif op == "bool":
        node.value = not node.value
    elif op == "cmp":
        node.ops = [CMP_SWAP[type(node.ops[0])]()]
    elif op == "boolop":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif op == "negate":
        node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
    elif op == "break":
        node.__class__ = ast.Continue
    elif op == "return":
        node.value = ast.Constant(value=None)
    elif op == "delete":
        # replace the statement in its parent body with `pass`
        for parent in ast.walk(fn):
            for field in ("body", "orelse", "finalbody"):
                body = getattr(parent, field, None)
                if isinstance(body, list) and node in body:
                    body[body.index(node)] = ast.Pass()
                    return


def run_group(workdir, test_path, timeout, per_test=False):
    """Run one test group against the mutant in `workdir`.
    Returns (status, failed_test_ids).  With per_test=False the run stops at
    the first failure (-x) and failed_test_ids is empty."""
    env = dict(os.environ, PYTHONPATH=workdir, PYTHONDONTWRITEBYTECODE="1")
    args = [sys.executable, "-m", "pytest", "-q", "-m", "not slow", "--no-header", "-p", "no:cacheprovider"]
    args += ["-rfE"] if per_test else ["-x"]
    try:
        r = subprocess.run(args + test_path.split(","), cwd=ROOT, env=env, capture_output=True, text=True,
                           timeout=timeout)
        status = "survived" if r.returncode == 0 else ("killed" if r.returncode == 1 else f"error{r.returncode}")
        failed = [ln.split(" ", 2)[1] for ln in r.stdout.splitlines() if ln.startswith(("FAILED ", "ERROR "))]
    except subprocess.TimeoutExpired:
        status, failed = "killed(timeout)", []
    return status, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="+", required=True, help="name=path pairs")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--sample", type=int, default=0, help="random sample size (0 = all mutants)")
    ap.add_argument("--seed", type=int, default=322)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "mutation.json"))
    ap.add_argument("--only-files", default="", help="comma-separated module names to mutate")
    ap.add_argument("--per-test", action="store_true", help="record which tests kill each mutant (no -x)")
    a = ap.parse_args()
    groups = dict(g.split("=", 1) for g in a.groups)

    mutants = []
    for file, wanted in TARGETS.items():
        src, sites = enumerate_mutants(file, wanted)
        for k, (func, ln, kind, desc, _) in enumerate(sites):
            mutants.append({"id": f"M{len(mutants) + 1:04d}", "file": file, "func": func, "line": ln,
                            "kind": kind, "desc": desc, "k": k})
    if a.only_files:
        keep = set(a.only_files.split(","))
        mutants = [m for m in mutants if m["file"] in keep]
    if a.sample:
        mutants = sorted(random.Random(a.seed).sample(mutants, a.sample), key=lambda m: m["id"])
    print(f"{len(mutants)} mutants, groups: {list(groups)}", flush=True)

    sources = {f: open(os.path.join(PKG, f)).read() for f in TARGETS}
    pool_dirs = []
    for _ in range(a.jobs):
        d = tempfile.mkdtemp(prefix="mut_")
        shutil.copytree(PKG, os.path.join(d, "mistune"), ignore=shutil.ignore_patterns("__pycache__"))
        pool_dirs.append(d)
    free = list(pool_dirs)

    def work(m):
        d = free.pop()
        try:
            path = os.path.join(d, "mistune", m["file"])
            try:
                mutated = apply_mutant(sources[m["file"]], TARGETS[m["file"]], m["k"])
                compile(mutated, path, "exec")
            except (SyntaxError, ValueError, IndexError) as e:
                m["result"] = {g: "stillborn" for g in groups}
                m["error"] = repr(e)
                return m
            with open(path, "w") as f:
                f.write(mutated)
            m["result"], m["failed"] = {}, {}
            for g, p in groups.items():
                m["result"][g], m["failed"][g] = run_group(d, p, a.timeout, a.per_test)
            return m
        finally:
            with open(os.path.join(d, "mistune", m["file"]), "w") as f:
                f.write(sources[m["file"]])
            free.append(d)

    done = []
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(work, m) for m in mutants]
        for i, fu in enumerate(as_completed(futs), 1):
            done.append(fu.result())
            if i % 25 == 0:
                print(f"{i}/{len(mutants)}", flush=True)
    for d in pool_dirs:
        shutil.rmtree(d, ignore_errors=True)

    done.sort(key=lambda m: m["id"])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(done, open(a.out, "w"), indent=1)
    summarize(done, groups)


def summarize(done, groups):
    valid = [m for m in done if "stillborn" not in m["result"].values()]
    print(f"\nvalid mutants: {len(valid)} (stillborn {len(done) - len(valid)})")
    for g in groups:
        k = sum(m["result"][g].startswith("killed") for m in valid)
        print(f"  {g:14s} killed {k:4d}/{len(valid)}  score {k / len(valid):.1%}")
    allk = sum(any(r.startswith("killed") for r in m["result"].values()) for m in valid)
    print(f"  {'ANY GROUP':14s} killed {allk:4d}/{len(valid)}  score {allk / len(valid):.1%}")


if __name__ == "__main__":
    main()
