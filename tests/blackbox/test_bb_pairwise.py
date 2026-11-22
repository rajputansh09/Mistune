"""Black-box: Pairwise (all-pairs) combinatorial testing (Lab 3 Task 3).

Feature-interaction defects in a Markdown parser usually involve two features
at a time (e.g. "link inside a list item", "code span inside a heading").
Factors:
  container  : none | blockquote | bullet item | ordered item         (4)
  inline     : emphasis | strong | code | link | image | escape       (6)
  position   : alone | after text | before text                       (3)
  block      : paragraph | ATX heading                                (2)
Exhaustive = 4*6*3*2 = 144 combinations; allpairspy reduces this to the
set below while still covering every pair of factor values.

Expected HTML is composed from the CommonMark rule for each factor, and every
composed oracle is validated against markdown-it-py (test_oracle_validation).
"""
from allpairspy import AllPairs
import pytest

from cases import Case, params
from oracle import render

CONTAINERS = ["none", "blockquote", "bullet", "ordered"]
INLINES = {
    "emphasis": ("*x*", "<em>x</em>"),
    "strong": ("**x**", "<strong>x</strong>"),
    "code": ("`x`", "<code>x</code>"),
    "link": ("[x](/u)", '<a href="/u">x</a>'),
    "image": ("![x](/i)", '<img src="/i" alt="x" />'),
    "escape": ("\\*x\\*", "*x*"),
}
POSITIONS = ["alone", "after", "before"]
BLOCKS = ["paragraph", "heading"]


def compose(container, inline, position, block):
    md_in, html_in = INLINES[inline]
    if position == "after":
        md_in, html_in = "t " + md_in, "t " + html_in
    elif position == "before":
        md_in, html_in = md_in + " t", html_in + " t"
    if block == "heading":
        md_line, inner = "# " + md_in, "<h1>" + html_in + "</h1>"
        tight_inner = inner
    else:
        md_line, inner = md_in, "<p>" + html_in + "</p>"
        tight_inner = html_in  # tight list items drop the <p>
    if container == "none":
        return md_line, inner
    if container == "blockquote":
        return "> " + md_line, "<blockquote>" + inner + "</blockquote>"
    if container == "bullet":
        return "- " + md_line, "<ul><li>" + tight_inner + "</li></ul>"
    return "1. " + md_line, "<ol><li>" + tight_inner + "</li></ol>"


PAIRS = list(AllPairs([CONTAINERS, list(INLINES), POSITIONS, BLOCKS]))
EXHAUSTIVE = len(CONTAINERS) * len(INLINES) * len(POSITIONS) * len(BLOCKS)

CASES = []
for i, (c, inl, pos, blk) in enumerate(PAIRS, 1):
    src, exp = compose(c, inl, pos, blk)
    CASES.append(Case(f"BB-PW-{i:02d}", "PAIRWISE", f"{c} / {inl} / {pos} / {blk}", src, exp))


@pytest.mark.parametrize("case", params(CASES))
def test_pairwise(case, record):
    assert record(render(case.md)) == case.expected


def test_pairwise_reduction_covers_all_pairs():
    """Every pair of factor values appears in at least one generated case."""
    factors = [CONTAINERS, list(INLINES), POSITIONS, BLOCKS]
    seen = set()
    for row in PAIRS:
        for i in range(4):
            for j in range(i + 1, 4):
                seen.add((i, row[i], j, row[j]))
    needed = {
        (i, a, j, b)
        for i in range(4)
        for j in range(i + 1, 4)
        for a in factors[i]
        for b in factors[j]
    }
    assert needed <= seen
    assert len(PAIRS) < EXHAUSTIVE
