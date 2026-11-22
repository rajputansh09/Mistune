"""Black-box: random testing, fuzzing, operational profile and stress tests
(Lecture 5, Black-box II).

* Fuzzing: random strings over the Markdown-significant alphabet; the oracle
  is a robustness property (no exception, string out, safe in escape mode).
* Operational profile (Musa): random but *realistic* documents whose block
  types follow a usage profile; the oracle is differential (must equal the
  CommonMark reference implementation).
* Stress / DoS: pathological inputs listed in Lecture 5 ("denial of service")
  must be processed in bounded time.

Seeds are fixed so every run (and every mutant run) is repeatable.
"""
import random
import time

import pytest

from oracle import md, md_escape, norm, reference, render

FUZZ_ALPHABET = list("*_`[]()<>!#-+=>\\&;:/\"' \n\tabc1.~|") + ["\n\n", "    ", "http://", "<a>", "&amp;"]
N_FUZZ = 300


def _fuzz_docs(seed, n=N_FUZZ, max_len=60):
    rnd = random.Random(seed)
    return ["".join(rnd.choice(FUZZ_ALPHABET) for _ in range(rnd.randint(0, max_len))) for _ in range(n)]


@pytest.mark.technique("FUZZ")
def test_fuzz_never_crashes(record):
    """BB-RF-01 Fuzz: 300 random documents never raise and always return str."""
    errors = []
    for doc in _fuzz_docs(seed=322):
        try:
            assert isinstance(md(doc), str)
        except Exception as e:  # noqa: BLE001 - any exception is a failure
            errors.append((doc, repr(e)))
    record(f"{N_FUZZ - len(errors)}/{N_FUZZ} documents processed without error")
    assert errors == []


@pytest.mark.technique("FUZZ")
def test_fuzz_escape_mode_never_emits_raw_script(record):
    """BB-RF-02 Fuzz (security): with escape=True no raw <script> survives."""
    rnd = random.Random(7)
    payloads = ["<script>alert(1)</script>", "<SCRIPT>x</SCRIPT>", "<img src=x onerror=alert(1)>"]
    leaks = []
    for doc in _fuzz_docs(seed=99, n=200):
        doc = doc + rnd.choice(payloads)
        out = md_escape(doc).lower()
        if "<script" in out or "<img src=x" in out:
            leaks.append(doc)
    record(f"{len(leaks)} leaks in 200 documents")
    assert leaks == []


@pytest.mark.technique("FUZZ")
def test_fuzz_harmful_url_scheme_is_neutralised(record):
    """BB-RF-03 Fuzz (security): URLs with a *literal* javascript:/vbscript:/
    file: scheme (any case) in links, images and reference definitions are
    replaced by '#harmful-link'.  Encoded schemes are out of scope here; see
    BB-MS-10."""
    rnd = random.Random(11)
    bad = []
    for _ in range(100):
        scheme = rnd.choice(["javascript:", "JavaScript:", "vbscript:", "file:", " javascript:"])
        tmpl = rnd.choice(["[x]({u}alert)", "![x]({u}alert)", "[x]\n\n[x]: {u}alert"])
        out = md(tmpl.format(u=scheme)).lower()
        if 'href="javascript' in out or 'src="javascript' in out or "vbscript:" in out or 'href="file:' in out:
            bad.append(tmpl.format(u=scheme))
    record(f"{len(bad)} of 100 literal-scheme harmful URLs emitted")
    assert bad == []


# ---------------------------------------------------------------- operational profile
PROFILE = [  # (block generator, probability) - estimated from README-style docs
    (lambda r: "# " + r.choice(["Install", "Usage", "API", "License"]), 0.15),
    (lambda r: " ".join(r.choice(["the", "parser", "*fast*", "`code`", "**bold**", "[link](/x)"]) for _ in range(r.randint(3, 9))), 0.40),
    (lambda r: "\n".join("- " + r.choice(["item", "`pip install`", "*note*"]) for _ in range(r.randint(1, 4))), 0.20),
    (lambda r: "> " + r.choice(["Note: read this.", "**Warning** be careful"]), 0.10),
    (lambda r: "```" + r.choice(["", "python", "sh"]) + "\nprint(1)\n```", 0.10),
    (lambda r: "1. first\n2. second", 0.05),
]


def _profile_doc(rnd):
    gens, weights = zip(*PROFILE)
    blocks = [rnd.choices(gens, weights)[0](rnd) for _ in range(rnd.randint(2, 8))]
    return "\n\n".join(blocks)


@pytest.mark.technique("OP-PROFILE")
def test_operational_profile_matches_reference(record):
    """BB-RF-04 Operational profile: 200 realistic documents render exactly as
    the CommonMark reference implementation renders them."""
    rnd = random.Random(2026)
    mismatches = [d for d in (_profile_doc(rnd) for _ in range(200)) if render(d) != reference(d)]
    record(f"{200 - len(mismatches)}/200 documents identical to reference")
    assert mismatches == []


@pytest.mark.technique("FUZZ-DIFF")
def test_fuzz_differential_agreement_rate(record):
    """BB-RF-05 Differential fuzzing: agreement with the reference on random
    (mostly malformed) input.  Disagreements are triaged, not asserted; the
    test only asserts the measurement ran.  The rate is used in the report."""
    docs = _fuzz_docs(seed=5, n=300)
    agree = sum(render(d) == reference(d) for d in docs)
    record(f"agreement {agree}/{len(docs)} = {agree / len(docs):.1%}")
    assert 0 < agree <= len(docs)


# ---------------------------------------------------------------- stress / DoS
def _elapsed(src):
    t0 = time.perf_counter()
    md(src)
    return time.perf_counter() - t0


@pytest.mark.slow
@pytest.mark.technique("STRESS")
def test_stress_deep_blockquote_nesting_no_recursion_error(record):
    """BB-RF-06 Stress: 5000 nested '>' do not overflow the stack."""
    record(f"{_elapsed('>' * 5000 + ' x'):.3f}s")


@pytest.mark.slow
@pytest.mark.technique("STRESS")
@pytest.mark.xfail(reason="D11", strict=False)
def test_stress_unmatched_brackets_bounded_time(record):
    """BB-RF-07 Stress (DoS): 4000 unmatched '[' render in under 0.5 s
    (reference implementation: ~0.05 s)."""
    t = _elapsed("[" * 4000)
    record(f"{t:.2f}s")
    assert t < 0.5


@pytest.mark.slow
@pytest.mark.technique("STRESS")
@pytest.mark.xfail(reason="D11", strict=False)
def test_stress_bracket_parsing_scales_linearly(record):
    """BB-RF-08 Stress (DoS): doubling the input at most ~doubles the time
    (ratio < 3).  Mistune shows ~4x (quadratic)."""
    t1, t2 = _elapsed("[" * 1500), _elapsed("[" * 3000)
    record(f"ratio {t2 / t1:.2f}")
    assert t2 / t1 < 3


def test_norm_is_idempotent():
    """Sanity check of the oracle helper used by every test group."""
    html = md("- a\n- b\n\n> q\n\n    code\n")
    assert norm(norm(html)) == norm(html)
