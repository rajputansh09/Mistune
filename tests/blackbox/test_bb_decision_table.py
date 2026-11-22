"""Black-box: Decision-table testing (Lecture 6, Black-box III).

DT-1  Emphasis.  Conditions (CommonMark 6.2):
  C1 delimiter character       '*' | '_'
  C2 opener is left-flanking   T | F
  C3 closer is right-flanking  T | F
  C4 delimiters are intraword  T | F
  C5 opener/closer run length  equal | opener longer | closer longer
  C6 nested delimiter of same char inside span   T | F
Actions: A1 <em>, A2 <strong>, A3 literal text, A4 partial match (+ leftover)

DT-2  Can a list item interrupt a paragraph?  (CommonMark 5.2/5.3)
  C1 a paragraph is open   C2 ordered   C3 start == 1   C4 item is empty
Actions: A1 new list, A2 text stays in paragraph
"""
import pytest

from cases import Case, params
from oracle import render

EMPHASIS = [
    #                                  C1  C2 C3 C4 C5    C6
    Case("BB-DT-E01", "DT", "R1: * LF RF !intra equal -> em", "*a*", "<p><em>a</em></p>"),
    Case("BB-DT-E02", "DT", "R2: * opener not LF (space after) -> literal", "x * a*", "<p>x * a*</p>"),
    Case("BB-DT-E03", "DT", "R3: * closer not RF (space before) -> literal", "*a *", "<p>*a *</p>"),
    Case("BB-DT-E04", "DT", "R4: * intraword -> em", "a*b*c", "<p>a<em>b</em>c</p>"),
    Case("BB-DT-E05", "DT", "R5: _ intraword -> literal", "a_b_c", "<p>a_b_c</p>"),
    Case("BB-DT-E06", "DT", "R6: _ LF RF !intra -> em", "_a_", "<p><em>a</em></p>"),
    Case("BB-DT-E07", "DT", "R7: _ closer followed by alnum -> literal", "_foo_bar", "<p>_foo_bar</p>"),
    Case("BB-DT-E08", "DT", "R8: run length 2/2 -> strong", "__a__", "<p><strong>a</strong></p>"),
    Case(
        "BB-DT-E09", "DT", "R9: * preceded by alnum, followed by punctuation -> not LF -> literal",
        'a*"foo"*', "<p>a*&quot;foo&quot;*</p>", defect="D1",
    ),
    Case(
        "BB-DT-E10", "DT", "R10: opener longer (2/1) -> leftover '*' + em",
        "**foo*", "<p>*<em>foo</em></p>", defect="D3",
    ),
    Case(
        "BB-DT-E11", "DT", "R11: closer longer (1/2) -> em + leftover '*'",
        "*foo**", "<p><em>foo</em>*</p>", defect="D3",
    ),
    Case("BB-DT-E12", "DT", "R12: em nested in strong, different char", "**a _b_ c**", "<p><strong>a <em>b</em> c</strong></p>"),
    Case(
        "BB-DT-E13", "DT", "R13: strong nested in em sharing closer run",
        "*foo **bar***", "<p><em>foo <strong>bar</strong></em></p>", defect="D2",
    ),
    Case(
        "BB-DT-E14", "DT", "R14: same-char em nested in em",
        "*foo *bar**", "<p><em>foo <em>bar</em></em></p>", defect="D2",
    ),
    Case("BB-DT-E15", "DT", "R15: em spanning punctuation inside", "*(foo)*", "<p><em>(foo)</em></p>"),
]

LIST_INTERRUPT = [
    #                                      para ordered start1 empty
    Case("BB-DT-L01", "DT", "R1: no para, bullet, non-empty -> list", "- b", "<ul><li>b</li></ul>"),
    Case("BB-DT-L02", "DT", "R2: para, bullet, non-empty -> interrupts", "a\n- b", "<p>a</p><ul><li>b</li></ul>"),
    Case("BB-DT-L03", "DT", "R3: para, bullet, empty -> no interrupt", "a\n*", "<p>a\n*</p>"),
    Case("BB-DT-L04", "DT", "R4: para, ordered, start=1 -> interrupts", "a\n1. b", "<p>a</p><ol><li>b</li></ol>"),
    Case("BB-DT-L05", "DT", "R5: para, ordered, start!=1 -> no interrupt", "a\n5. b", "<p>a\n5. b</p>"),
    Case("BB-DT-L06", "DT", "R6: no para, ordered, start!=1 -> list with start", "5. b", '<ol start="5"><li>b</li></ol>'),
    Case("BB-DT-L07", "DT", "R7: no para, bullet, empty -> empty item", "-", "<ul><li></li></ul>"),
]

CASES = EMPHASIS + LIST_INTERRUPT


@pytest.mark.parametrize("case", params(CASES))
def test_decision_table(case, record):
    assert record(render(case.md)) == case.expected
