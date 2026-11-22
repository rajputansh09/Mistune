"""Black-box: Syntax-driven testing (Lecture 7, Black-box IV; textbook 9.1).

Grammar under test (inline link and fenced code subset of CommonMark):

  <link>      ::= "[" <text> "]" "(" <ws>? <dest>? (<ws> <title>)? <ws>? ")"   P1
  <dest>      ::= "<" <no-gt-chars> ">"                                       P2
               |  <bare-chars-with-balanced-parens>                           P3
  <title>     ::= '"' <chars> '"'                                             P4
               |  "'" <chars> "'"                                             P5
               |  "(" <chars> ")"                                             P6
  <text>      ::= <inline>*      (emphasis, code, escaped bracket ...)        P7
  <fence>     ::= <open> <info>? NL <line>* <close>                           P8
  <open>      ::= "```" "`"* | "~~~" "~"*                                    P9/P10
  <close>     ::= same char, length >= open                                   P11

Production coverage (PDC): every production above is used at least once.
Terminal coverage (TSC): [ ] ( ) < > " ' ` ~ appear in some test.
Delimiter-error tests: missing, wrong, extra, unpaired/nested delimiters.
Field-value errors: illegal characters inside a field.
"""
import pytest

from cases import Case, params
from oracle import render

PRODUCTIONS = [
    Case("BB-SY-P01", "SYN-PDC", "P1 with empty destination", "[a]()", '<p><a href="">a</a></p>'),
    Case("BB-SY-P02", "SYN-PDC", "P2 angle-bracket destination with space", "[a](<b c>)", '<p><a href="b%20c">a</a></p>'),
    Case("BB-SY-P03", "SYN-PDC", "P3 bare destination", "[a](/b)", '<p><a href="/b">a</a></p>'),
    Case(
        "BB-SY-P04", "SYN-PDC", "P3 bare destination with balanced nested parens",
        "[a](b(c(d)))", '<p><a href="b(c(d))">a</a></p>', defect="D4",
    ),
    Case("BB-SY-P05", "SYN-PDC", 'P4 "title"', '[a](/b "t")', '<p><a href="/b" title="t">a</a></p>'),
    Case("BB-SY-P06", "SYN-PDC", "P5 'title'", "[a](/b 't')", '<p><a href="/b" title="t">a</a></p>'),
    Case(
        "BB-SY-P07", "SYN-PDC", "P6 (title) in parentheses",
        "[a](/b (t))", '<p><a href="/b" title="t">a</a></p>', defect="D5",
    ),
    Case("BB-SY-P08", "SYN-PDC", "P1 optional whitespace around destination", "[a](  /b  )", '<p><a href="/b">a</a></p>'),
    Case("BB-SY-P09", "SYN-PDC", "P7 inline emphasis and code inside link text", "[*a* `b`](/c)", '<p><a href="/c"><em>a</em> <code>b</code></a></p>'),
    Case("BB-SY-P10", "SYN-PDC", "P8/P9 backtick fence with info", "```js\nx\n```", '<pre><code class="language-js">x</code></pre>'),
    Case("BB-SY-P11", "SYN-PDC", "P10 tilde fence", "~~~\nx\n~~~", "<pre><code>x</code></pre>"),
    Case("BB-SY-P12", "SYN-PDC", "P11 closing fence longer than opening", "```\nx\n`````", "<pre><code>x</code></pre>"),
]

DELIMITER_ERRORS = [
    Case("BB-SY-D01", "SYN-DELIM", "Missing ']' delimiter", "[a(/b)", "<p>[a(/b)</p>"),
    Case("BB-SY-D02", "SYN-DELIM", "Missing ')' delimiter", "[a](/b", "<p>[a](/b</p>"),
    Case("BB-SY-D03", "SYN-DELIM", "Wrong delimiter '{' instead of '('", "[a]{/b}", "<p>[a]{/b}</p>"),
    Case("BB-SY-D04", "SYN-DELIM", "Extra space between ']' and '('", "[a] (/b)", "<p>[a] (/b)</p>"),
    Case("BB-SY-D05", "SYN-DELIM", "Too many '[' delimiters", "[[a]](/b)", '<p><a href="/b">[a]</a></p>'),
    Case("BB-SY-D06", "SYN-DELIM", "Escaped ']' is not a delimiter", "[a\\]](/b)", '<p><a href="/b">a]</a></p>'),
    Case(
        "BB-SY-D07", "SYN-DELIM", "Paired delimiters: link nested in link text (inner wins)",
        "[a [b](/c)](/d)", '<p>[a <a href="/c">b</a>](/d)</p>', defect="D6",
    ),
    Case(
        "BB-SY-D08", "SYN-DELIM", "Unbalanced '(' in bare destination -> not a link",
        "[a](b(c)", "<p>[a](b(c)</p>", defect="D4",
    ),
    Case("BB-SY-D09", "SYN-DELIM", "Closing fence shorter than opening is content", "````\nx\n```", "<pre><code>x\n```</code></pre>"),
    Case("BB-SY-D10", "SYN-DELIM", "Fence char mismatch (``` closed by ~~~) is content", "```\nx\n~~~", "<pre><code>x\n~~~</code></pre>"),
    Case(
        "BB-SY-D11", "SYN-DELIM", "Paired delimiters: image nested in image alt text",
        "![a ![b](/x)](/y)", '<p><img src="/y" alt="a b" /></p>', defect="D7",
    ),
]

FIELD_VALUE_ERRORS = [
    Case("BB-SY-F01", "SYN-FIELD", "Space inside bare destination", "[a](b c)", "<p>[a](b c)</p>"),
    Case("BB-SY-F02", "SYN-FIELD", "Unterminated title", '[a](/b "t)', '<p>[a](/b &quot;t)</p>'),
    Case("BB-SY-F03", "SYN-FIELD", "Newline inside angle-bracket destination", "[a](<1\n2>)", "<p>[a](&lt;1\n2&gt;)</p>"),
    Case("BB-SY-F04", "SYN-FIELD", "Backtick in info string of backtick fence", "``` a`b\nx", "<p>``` a`b\nx</p>"),
]

CASES = PRODUCTIONS + DELIMITER_ERRORS + FIELD_VALUE_ERRORS


@pytest.mark.parametrize("case", params(CASES))
def test_syntax_driven(case, record):
    assert record(render(case.md)) == case.expected
