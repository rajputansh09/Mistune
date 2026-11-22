"""Black-box: Equivalence Partitioning (EP) and Boundary Value Analysis (BVA).

Lecture 4 (Black-box I): partition each input variable into valid/invalid
classes, pick one representative per class, then add values at and just
beyond every boundary.  Expected outputs come from CommonMark 0.31.2; they are
independently cross-checked against markdown-it-py in test_oracle_validation.

Input variables and their partitions are listed in docs/test_design.md.
"""
import pytest

from cases import Case, params
from oracle import render

CASES = [
    # ---------------- Category A: headings, paragraphs, line breaks ------------
    # ATX heading level n = number of '#'.  Valid class 1..6, invalid n<1, n>6.
    Case("BB-EP-H01", "BVA", "ATX level n=1 (lower bound)", "# Title", "<h1>Title</h1>"),
    Case("BB-EP-H02", "BVA", "ATX level n=2 (just above lower bound)", "## Title", "<h2>Title</h2>"),
    Case("BB-EP-H03", "BVA", "ATX level n=6 (upper bound)", "###### Title", "<h6>Title</h6>"),
    Case("BB-EP-H04", "BVA", "ATX level n=7 (just above upper bound) -> paragraph", "####### Title", "<p>####### Title</p>"),
    Case("BB-EP-H05", "EP", "Invalid class: no space after '#' -> paragraph", "#Title", "<p>#Title</p>"),
    Case("BB-EP-H06", "EP", "Empty heading (only marker)", "#", "<h1></h1>"),
    Case("BB-EP-H07", "EP", "Optional closing sequence is removed", "## Title ##", "<h2>Title</h2>"),
    Case("BB-EP-H08", "EP", "Closing '#' not preceded by space is content", "# Title#", "<h1>Title#</h1>"),
    # Leading indentation i: valid 0..3, i>=4 becomes indented code.
    Case("BB-EP-H09", "BVA", "Heading indented 3 spaces (upper bound)", "   # Title", "<h1>Title</h1>"),
    Case("BB-EP-H10", "BVA", "Heading indented 4 spaces -> code block", "    # Title", "<pre><code># Title</code></pre>"),
    # Setext underline length L: valid L>=1
    Case("BB-EP-H11", "BVA", "Setext '=' underline of length 1 (lower bound)", "Title\n=", "<h1>Title</h1>"),
    Case("BB-EP-H12", "EP", "Setext '-' underline -> h2", "Title\n-----", "<h2>Title</h2>"),
    Case(
        "BB-EP-H13", "EP", "Invalid class: underline mixing '-' and '=' is not setext",
        "Title\n--=", "<p>Title\n--=</p>", defect="D12",
    ),
    # Paragraphs / line breaks: trailing spaces t before newline. t<=1 soft, t>=2 hard
    Case("BB-EP-P01", "EP", "Two lines without blank line form one paragraph", "line one\nline two", "<p>line one\nline two</p>"),
    Case("BB-EP-P02", "EP", "Blank line separates paragraphs", "para one\n\npara two", "<p>para one</p><p>para two</p>"),
    Case("BB-EP-P03", "BVA", "1 trailing space -> soft break (below boundary)", "a \nb", "<p>a\nb</p>"),
    Case("BB-EP-P04", "BVA", "2 trailing spaces -> hard break (boundary)", "a  \nb", "<p>a<br />\nb</p>"),
    Case("BB-EP-P05", "EP", "Backslash before newline -> hard break", "a\\\nb", "<p>a<br />\nb</p>"),
    Case("BB-EP-P06", "EP", "Trailing spaces at end of paragraph are not a break", "a  ", "<p>a</p>"),
    # Thematic break: k marker characters. valid k>=3
    Case("BB-EP-T01", "BVA", "Thematic break with k=2 '-' -> paragraph", "--", "<p>--</p>"),
    Case("BB-EP-T02", "BVA", "Thematic break with k=3 '*' (boundary)", "***", "<hr />"),
    Case("BB-EP-T03", "EP", "Mixed marker characters are not a break", "*-*", "<p><em>-</em></p>"),
    # ---------------- Category B: inline formatting and links -------------------
    Case("BB-EP-I01", "EP", "Single '*' emphasis", "*text*", "<p><em>text</em></p>"),
    Case("BB-EP-I02", "EP", "Single '_' emphasis", "_text_", "<p><em>text</em></p>"),
    Case("BB-EP-I03", "EP", "Double '**' strong", "**text**", "<p><strong>text</strong></p>"),
    Case("BB-EP-I04", "EP", "Triple '***' strong+emphasis", "***text***", "<p><em><strong>text</strong></em></p>"),
    Case("BB-EP-I05", "EP", "Unclosed delimiter stays literal (invalid class)", "*text", "<p>*text</p>"),
    Case("BB-EP-I06", "EP", "Intraword '_' is literal", "snake_case_name", "<p>snake_case_name</p>"),
    Case("BB-EP-I07", "EP", "Intraword '*' gives emphasis", "un*frigging*believable", "<p>un<em>frigging</em>believable</p>"),
    Case("BB-EP-I08", "EP", "Code span protects its content", "`*not em*`", "<p><code>*not em*</code></p>"),
    Case("BB-EP-I09", "EP", "Inline link", "[home](/index)", '<p><a href="/index">home</a></p>'),
    Case("BB-EP-I10", "EP", "Inline link with double-quoted title", '[a](/u "T")', '<p><a href="/u" title="T">a</a></p>'),
    Case("BB-EP-I11", "EP", "Full reference link (case-insensitive label)", "[a][Ref]\n\n[ref]: /u", '<p><a href="/u">a</a></p>'),
    Case("BB-EP-I12", "EP", "Undefined reference stays literal", "[a][nope]", "<p>[a][nope]</p>"),
    Case("BB-EP-I13", "EP", "URI autolink", "<https://example.com>", '<p><a href="https://example.com">https://example.com</a></p>'),
    Case("BB-EP-I14", "EP", "Email autolink", "<me@example.com>", '<p><a href="mailto:me@example.com">me@example.com</a></p>'),
    Case("BB-EP-I15", "EP", "Image", "![logo](/l.png)", '<p><img src="/l.png" alt="logo" /></p>'),
    # ---------------- Category C: lists and block quotes ------------------------
    Case("BB-EP-L01", "EP", "Bullet list with '-'", "- a\n- b", "<ul><li>a</li><li>b</li></ul>"),
    Case("BB-EP-L02", "EP", "Changing bullet char starts a new list", "- a\n+ b", "<ul><li>a</li></ul><ul><li>b</li></ul>"),
    Case("BB-EP-L03", "EP", "Ordered list with ')' delimiter", "1) a\n2) b", "<ol><li>a</li><li>b</li></ol>"),
    # Ordered start number s: digits d valid 1..9
    Case("BB-EP-L04", "BVA", "Start number 0 (lower bound)", "0. a", '<ol start="0"><li>a</li></ol>'),
    Case("BB-EP-L05", "BVA", "Start number with 9 digits (upper bound)", "123456789. a", '<ol start="123456789"><li>a</li></ol>'),
    Case("BB-EP-L06", "BVA", "Start number with 10 digits -> paragraph", "1234567890. a", "<p>1234567890. a</p>"),
    Case("BB-EP-L07", "EP", "Loose list (blank line between items)", "- a\n\n- b", "<ul><li><p>a</p></li><li><p>b</p></li></ul>"),
    Case("BB-EP-L08", "EP", "Nested list (2 levels)", "- a\n  - b", "<ul><li>a<ul><li>b</li></ul></li></ul>"),
    Case("BB-EP-L09", "BVA", "Sub-item indented 1 space (< content width) stays sibling", "- a\n - b", "<ul><li>a</li><li>b</li></ul>"),
    Case("BB-EP-L10", "EP", "List starting with 2 cannot interrupt a paragraph", "text\n2. b", "<p>text\n2. b</p>"),
    Case("BB-EP-Q01", "EP", "Simple block quote", "> quote", "<blockquote><p>quote</p></blockquote>"),
    Case("BB-EP-Q02", "EP", "Lazy continuation line", "> a\nb", "<blockquote><p>a\nb</p></blockquote>"),
    Case("BB-EP-Q03", "EP", "Nested block quote", "> > a", "<blockquote><blockquote><p>a</p></blockquote></blockquote>"),
    Case("BB-EP-Q04", "EP", "List inside block quote", "> - a\n> - b", "<blockquote><ul><li>a</li><li>b</li></ul></blockquote>"),
    # ---------------- Category D: escapes, unusual syntax, boundaries ------------
    Case("BB-EP-E01", "EP", "Escaped '*' is literal", "\\*a\\*", "<p>*a*</p>"),
    Case("BB-EP-E02", "EP", "Escaped '#' prevents heading", "\\# a", "<p># a</p>"),
    Case("BB-EP-E03", "EP", "Backslash before non-punctuation is kept", "\\a", "<p>\\a</p>"),
    Case("BB-EP-E04", "EP", "Named entity is decoded", "&copy;", "<p>©</p>"),
    Case("BB-EP-E05", "EP", "Unknown entity is escaped literally", "&nosuch;", "<p>&amp;nosuch;</p>"),
    Case("BB-EP-E06", "EP", "Hex numeric entity", "&#x41;", "<p>A</p>"),
    Case("BB-EP-E07", "BVA", "Empty document", "", ""),
    Case("BB-EP-E08", "BVA", "Whitespace-only document", "   \n\n  ", ""),
    Case("BB-EP-E09", "EP", "Fenced code with info string", "```py\nx = 1\n```", '<pre><code class="language-py">x = 1</code></pre>'),
    Case("BB-EP-E10", "BVA", "Fence of 2 backticks is not a fence", "``\ncode\n``", "<p><code>code</code></p>"),
    Case("BB-EP-E11", "EP", "Unclosed fence runs to end of document", "~~~\ncode", "<pre><code>code</code></pre>"),
    Case(
        "BB-EP-E12",
        "EP",
        "NUL character must be replaced by U+FFFD (spec 2.3)",
        "a\x00b",
        "<p>a�b</p>",
        defect="D10",
    ),
]


@pytest.mark.parametrize("case", params(CASES))
def test_partition_boundary(case, record):
    assert record(render(case.md)) == case.expected
