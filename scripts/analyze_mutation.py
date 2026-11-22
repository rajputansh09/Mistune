"""Analyse mutation results (Lecture 10: mutation testing, fault seeding,
independent tests / capture-recapture).

Usage: python scripts/analyze_mutation.py results/mutation_manual.json [n_indigenous]
"""
import json
import sys
from collections import defaultdict
from math import comb

data = json.load(open(sys.argv[1]))
n_indigenous = int(sys.argv[2]) if len(sys.argv) > 2 else 9
valid = [m for m in data if "stillborn" not in m["result"].values()]
groups = list(valid[0]["result"])
killed = lambda m, g: m["result"][g].startswith("killed")  # noqa: E731
any_k = lambda m: any(killed(m, g) for g in groups)  # noqa: E731

S = len(valid)
print(f"Valid mutants S = {S}   (stillborn: {len(data) - S})\n")
print("## Mutation score by group")
for g in groups:
    k = sum(killed(m, g) for m in valid)
    to = sum(m["result"][g] == "killed(timeout)" for m in valid)
    print(f"| {g} | {k} | {k / S:.1%} | {to} timeouts |")
allk = sum(any_k(m) for m in valid)
print(f"| union of groups | {allk} | {allk / S:.1%} | |")

print("\n## Score by mutation operator class (union of groups)")
by = defaultdict(lambda: [0, 0])
for m in valid:
    by[m["kind"]][1] += 1
    by[m["kind"]][0] += any_k(m)
for k, (a, b) in sorted(by.items()):
    print(f"| {k} | {a}/{b} | {a / b:.1%} |")

print("\n## Score by module, per group")
files = sorted({m["file"] for m in valid})
print("| module | mutants | " + " | ".join(groups) + " | union |")
for f in files:
    ms = [m for m in valid if m["file"] == f]
    cells = [f"{sum(killed(m, g) for m in ms) / len(ms):.0%}" for g in groups]
    print(f"| {f} | {len(ms)} | " + " | ".join(cells) + f" | {sum(any_k(m) for m in ms) / len(ms):.0%} |")

print("\n## Unique kills (killed by this group only)")
for g in groups:
    u = sum(killed(m, g) and not any(killed(m, h) for h in groups if h != g) for m in valid)
    print(f"| {g} | {u} |")

# ---------------- Capture-recapture (independent test groups, lecture 10)
if "blackbox" in groups and "whitebox" in groups:
    N1 = sum(killed(m, "blackbox") for m in valid)
    N2 = sum(killed(m, "whitebox") for m in valid)
    N12 = sum(killed(m, "blackbox") and killed(m, "whitebox") for m in valid)
    est = N1 * N2 / N12 if N12 else float("inf")
    print(f"\n## Capture-recapture: N1(BB)={N1}, N2(WB)={N2}, N12={N12} -> estimated detectable faults "
          f"N = N1*N2/N12 = {est:.0f}; found by BB or WB = {N1 + N2 - N12}; mutants in program = {S}")

# ---------------- Mills fault seeding
s = allk
n = n_indigenous
N_hat = n * S / s
print(f"\n## Mills fault seeding: S={S} seeded (mutants), s={s} detected, n={n} indigenous defects found")
print(f"   estimated indigenous faults N = n*S/s = {N_hat:.1f}; estimated remaining = {N_hat - n:.1f}")
# confidence that the program has at most N indigenous faults (lecture formula, partial detection)
for N in (n, n + 1, n + 2, round(N_hat)):
    if n > N:
        C = 1.0
    elif s >= 1:
        C = comb(S, s - 1) / comb(S + N + 1, N + s)
    else:
        C = 0.0
    print(f"   confidence that N <= {N}: C = {C:.3g}")

surv = [m for m in valid if not any_k(m)]
print(f"\n## Surviving mutants ({len(surv)}): candidates for equivalent mutants or missing tests")
for m in surv[:400]:
    print(f"   {m['id']} {m['file']}:{m['line']} {m['func']}  [{m['kind']}] {m['desc']}")
