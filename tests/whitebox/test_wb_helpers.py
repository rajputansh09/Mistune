"""White-box unit tests: mistune/helpers.py and mistune/util.py.

Control-flow graphs and def-use tables for each function are in
docs/whitebox_cfg.md.  Each test names the CFG path / branch it exercises.

parse_link_text(src, pos)  (helpers.py:110-133)   cyclomatic complexity V(G)=6
  n1  level=1, found=False, start_pos=pos
  n2  while pos < len(src)            -- loop predicate
  n3  m = search(...);  if not m: break
  n4  pos = m.end(); marker = m.group(0)
  n5  if marker == "]"
  n6     level -= 1; if level == 0: found=True; break
  n7  else level += 1
  n8  if found: return text, pos   else return None, None
"""
import pytest

from mistune import helpers, util

pytestmark = pytest.mark.technique("WB")


# ------------------------------------------------------------ parse_link_text
def test_wb_h01_link_text_single_bracket_found(record):
    """WB-H01 path n1-n2-n3-n4-n5-n6(found)-n8T : one ']' closes level 1."""
    assert record(helpers.parse_link_text("abc](x)", 0)) == ("abc", 4)


def test_wb_h02_link_text_loop_twice_nested(record):
    """WB-H02 loop body executed >= 2 times, n7 branch ('[' increments level)
    then two ']' : def(level)@n7 -> use(level)@n6 du-pair covered."""
    assert record(helpers.parse_link_text("a[b]c]rest", 0)) == ("a[b]c", 6)


def test_wb_h03_link_text_no_bracket_breaks(record):
    """WB-H03 path n3 (not m -> break) then n8F: no closing bracket."""
    assert record(helpers.parse_link_text("no closing", 0)) == (None, None)


def test_wb_h04_link_text_loop_not_entered(record):
    """WB-H04 loop predicate false on entry (pos == len(src)) -> n8F."""
    assert record(helpers.parse_link_text("abc", 3)) == (None, None)


def test_wb_h05_link_text_unbalanced_exhausts_loop(record):
    """WB-H05 loop exits through its predicate with found=False: more '['
    than ']' so level never reaches 0."""
    assert record(helpers.parse_link_text("[[a]", 0)) == (None, None)


def test_wb_h06_link_text_escaped_bracket_skipped(record):
    """WB-H06 PREVENT_BACKSLASH: an escaped ']' is not a marker."""
    assert record(helpers.parse_link_text(r"a\]b]", 0)) == (r"a\]b", 5)


# ------------------------------------------------------------ parse_link_label
def test_wb_h07_link_label_match_and_no_match(record):
    """WB-H07 both branches of parse_link_label (match / no match)."""
    assert helpers.parse_link_label("foo]bar", 0) == ("foo", 4)
    assert record(helpers.parse_link_label("foo", 0)) == (None, None)


def test_wb_h08_link_label_boundary_500_chars(record):
    """WB-H08 BVA on the regex quantifier {0,500}: 500 chars ok, 501 rejected."""
    assert helpers.parse_link_label("a" * 500 + "]", 0)[1] == 501
    assert record(helpers.parse_link_label("a" * 501 + "]", 0)) == (None, None)


# ------------------------------------------------------------ parse_link_href
#  B1 bracket-start matched?  B2 bracket body matched?  B3 block?  B4 regex matched?
#  B5 block and src[end-1] == href[-1]
def test_wb_h09_href_angle_brackets(record):
    """WB-H09 B1=T,B2=T: <dest> form returns inner text."""
    assert record(helpers.parse_link_href("<a b>)", 0)) == ("a b", 5)


def test_wb_h10_href_angle_unclosed(record):
    """WB-H10 B1=T,B2=F: '<' without matching '>' -> (None, None)."""
    assert record(helpers.parse_link_href("<a b)", 0)) == (None, None)


def test_wb_h11_href_inline_bare(record):
    """WB-H11 B1=F,B3=F,B4=T: inline bare destination ends before ')'."""
    assert record(helpers.parse_link_href("/url)", 0)) == ("/url", 4)


def test_wb_h12_href_block_at_end_of_input(record):
    """WB-H12 B3=T,B5=T: block href at end of string (src[end-1]==href[-1])."""
    assert record(helpers.parse_link_href(" /url", 0, block=True)) == ("/url", 5)


def test_wb_h13_href_block_followed_by_space(record):
    """WB-H13 B3=T,B5=F: block href followed by whitespace."""
    assert record(helpers.parse_link_href(" /url 'x'", 0, block=True)) == ("/url", 5)


def test_wb_h14_href_block_no_match(record):
    """WB-H14 B3=T,B4=F: nothing but whitespace -> (None, None)."""
    assert record(helpers.parse_link_href("   ", 0, block=True)) == (None, None)


# ------------------------------------------------------------ parse_link_title / parse_link
def test_wb_h15_title_quoted_with_escape(record):
    """WB-H15 match branch + unescape_char applied to the title."""
    assert record(helpers.parse_link_title(' "a\\"b")', 0, 8)) == ('a"b', 7)


def test_wb_h16_title_absent(record):
    """WB-H16 no-match branch."""
    assert record(helpers.parse_link_title(")", 0, 1)) == (None, None)


def test_wb_h17_parse_link_with_title(record):
    """WB-H17 parse_link: href found, title found, ')' found."""
    attrs, pos = helpers.parse_link('/u "t")', 0)
    record((attrs, pos))
    assert attrs == {"url": "/u", "title": "t"} and pos == 7


def test_wb_h18_parse_link_missing_paren(record):
    """WB-H18 parse_link: PAREN_END_RE fails -> (None, None)."""
    assert record(helpers.parse_link("/u x", 0)) == (None, None)


def test_wb_h19_parse_link_href_none(record):
    """WB-H19 parse_link: href is None branch (unclosed angle bracket)."""
    assert record(helpers.parse_link("<oops", 0)) == (None, None)


# ------------------------------------------------------------ util.py
def test_wb_u01_escape_quote_true_false(record):
    """WB-U01 both branches of the `quote` flag in util.escape."""
    assert util.escape('<a href="x">&') == "&lt;a href=&quot;x&quot;&gt;&amp;"
    assert record(util.escape('"', quote=False)) == '"'


def test_wb_u02_unescape_fast_path_and_entities(record):
    """WB-U02 '&' not in s -> early return; numeric/named/invalid entities."""
    assert util.unescape("plain") == "plain"
    assert util.unescape("&#65;&#x42;&amp;&bogus") == "AB&&bogus"
    record(util.unescape("&copy"))
    assert util.unescape("&copy") == "&copy"  # no trailing ';' -> not decoded


def test_wb_u03_unikey_normalises_case_and_space(record):
    """WB-U03 unikey collapses whitespace and case-folds (incl. Unicode ß)."""
    assert util.unikey("  Foo \n Bar ") == util.unikey("foo bar")
    assert record(util.unikey("ẞ")) == util.unikey("ß".upper())


def test_wb_u04_escape_url_keeps_reserved_and_encodes_space(record):
    """WB-U04 escape_url percent-encodes unsafe chars, keeps RFC3986 delims,
    does not double-encode existing %XX."""
    assert record(util.escape_url("/a b?x=1&y=%20#f")) == "/a%20b?x=1&y=%20#f"


def test_wb_u05_expand_leading_tab(record):
    """WB-U05 tab after 0-3 spaces expands to the next tab stop of width 4."""
    assert util.expand_leading_tab("\tx") == "    x"
    assert record(util.expand_leading_tab("  \tx")) == "    x"


def test_wb_u06_striptags(record):
    """WB-U06 striptags removes tags and comments."""
    assert record(util.striptags("a<b>c</b><!-- x -->d")) == "acd"
