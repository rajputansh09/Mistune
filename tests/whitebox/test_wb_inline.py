"""White-box unit tests: mistune/inline_parser.py.

Functions under test and their decisions (see docs/whitebox_cfg.md):

parse_emphasis (L241-287)
  D1 mlen==1 and in_emphasis     D2 mlen==2 and in_strong
  D3 closing regex not found     D4 precedence_scan returned a position
  D5 mlen==1 / D6 mlen==2 / else (mlen==3)
parse_codespan (L289-309)
  D1 closing run found   D2 code not all spaces   D3 starts and ends with space
parse_link (L114-182)
  D1 image in image   D2 link in link   D3 label None   D4 text None
  D5 end_pos >= len and label None   D6 precedence   D7 next char '(' / '['
  D8 inline link parsed   D9 label None (after)   D10 no ref_links  D11 key found
parse_inline_html (L319-327): <a> sets in_link, </a> clears it.
"""
import pytest

from mistune.core import InlineState
from mistune.inline_parser import InlineParser
from oracle import render

pytestmark = pytest.mark.technique("WB")


def tokens(src, env=None, **flags):
    p = InlineParser()
    st = InlineState(env or {})
    st.src = src
    for k, v in flags.items():
        setattr(st, k, v)
    return p.render(st)


# ------------------------------------------------------------ parse_emphasis
def test_wb_i01_emphasis_single(record):
    """WB-I01 D1=F,D2=F,D3=F,D4=F,D5=T -> emphasis token."""
    assert record(tokens("*a*")) == [{"type": "emphasis", "children": [{"type": "text", "raw": "a"}]}]


def test_wb_i02_emphasis_double(record):
    """WB-I02 D6=T -> strong token."""
    assert record(tokens("**a**"))[0]["type"] == "strong"


def test_wb_i03_emphasis_triple(record):
    """WB-I03 else-branch (mlen==3) -> emphasis(strong(...))."""
    t = record(tokens("***a***"))
    assert t[0]["type"] == "emphasis" and t[0]["children"][0]["type"] == "strong"


def test_wb_i04_emphasis_no_closer(record):
    """WB-I04 D3=T: no closing delimiter -> marker kept as text."""
    assert record(tokens("*a")) == [{"type": "text", "raw": "*"}, {"type": "text", "raw": "a"}]


def test_wb_i05_emphasis_inside_emphasis_state(record):
    """WB-I05 D1=T: '*' while state.in_emphasis is already set is literal."""
    assert record(tokens("*a*", in_emphasis=True))[0] == {"type": "text", "raw": "*"}


def test_wb_i06_strong_inside_strong_state(record):
    """WB-I06 D2=T: '**' while state.in_strong is already set is literal."""
    assert record(tokens("**a**", in_strong=True))[0] == {"type": "text", "raw": "**"}


def test_wb_i07_emphasis_precedence_code_span_wins(record):
    """WB-I07 D4=T: a code span that crosses the closer takes precedence."""
    assert record(render("*a `*` b")) == "<p>*a <code>*</code> b</p>"


# ------------------------------------------------------------ parse_codespan
def test_wb_i08_codespan_strip_one_space(record):
    """WB-I08 D1=T,D2=T,D3=T: one leading+trailing space stripped."""
    assert record(tokens("`` `a` ``")) == [{"type": "codespan", "raw": "`a`"}]


def test_wb_i09_codespan_only_spaces_not_stripped(record):
    """WB-I09 D2=F: code consisting only of spaces is kept as-is."""
    assert record(tokens("`  `")) == [{"type": "codespan", "raw": "  "}]


def test_wb_i10_codespan_newline_becomes_space(record):
    """WB-I10 line endings inside code spans are converted to spaces."""
    assert record(tokens("`a\nb`")) == [{"type": "codespan", "raw": "a b"}]


def test_wb_i11_codespan_unmatched_run_length(record):
    """WB-I11 D1=F: opener ``` with only `` closer -> literal backticks."""
    assert record(tokens("```a``"))[0] == {"type": "text", "raw": "```"}


# ------------------------------------------------------------ parse_link
def test_wb_i12_image_inside_image_alt_is_text(record):
    """WB-I12 D1=T: '![' while in_image is literal text."""
    assert record(tokens("![a](b)", in_image=True))[0] == {"type": "text", "raw": "!["}


def test_wb_i13_link_inside_link_is_text(record):
    """WB-I13 D2=T: '[' while in_link is literal text."""
    assert record(tokens("[a](b)", in_link=True))[0] == {"type": "text", "raw": "["}


def test_wb_i14_label_none_text_none(record):
    """WB-I14 D3=T,D4=T: no closing ']' at all -> parse_link returns None."""
    assert record(render("[abc")) == "<p>[abc</p>"


def test_wb_i15_shortcut_ref_without_env(record):
    """WB-I15 D9=F,D10=T: shortcut ref but no definitions -> literal."""
    assert record(tokens("[a] b")) == [{"type": "text", "raw": "["}, {"type": "text", "raw": "a] b"}]


def test_wb_i16_collapsed_reference(record):
    """WB-I16 D7='[' with empty second label (collapsed) and D11=T."""
    env = {"ref_links": {"A": {"url": "/u"}}}
    t = record(tokens("[a][]", env))
    assert t[0]["type"] == "link" and t[0]["attrs"]["url"] == "/u" and t[0]["ref"] == "A"


def test_wb_i17_full_reference_unknown_key(record):
    """WB-I17 D7='[' with label2 set, D11=F (key not defined) -> literal."""
    env = {"ref_links": {"X": {"url": "/u"}}}
    assert record(tokens("[a][b]", env))[0] == {"type": "text", "raw": "["}


def test_wb_i18_inline_link_parse_fails_falls_to_ref(record):
    """WB-I18 D7='(' but D8=F (bad destination) -> falls through to ref lookup
    and, with no refs, renders literally."""
    assert record(render("[a](b c)")) == "<p>[a](b c)</p>"


def test_wb_i19_link_text_precedence_autolink(record):
    """WB-I19 D6=T: an autolink spanning ']' takes precedence over the link."""
    assert record(render("[a <http://x.y/]>](/u)")) == '<p>[a <a href="http://x.y/%5D">http://x.y/]</a>](/u)</p>'


# ------------------------------------------------------------ html / auto links
def test_wb_i20_inline_html_anchor_toggles_in_link(record):
    """WB-I20 parse_inline_html sets in_link on <a ...> so an autolink inside
    is not converted, and clears it on </a> so one after is converted."""
    out = record(render('<a href="/x"><http://in.x></a> <http://out.x>'))
    assert '<a href="/x">&lt;http://in.x&gt;</a>' in out
    assert '<a href="http://out.x">http://out.x</a>' in out


def test_wb_i21_auto_email_inside_link_state(record):
    """WB-I21 parse_auto_email in_link branch -> processed as plain text."""
    assert record(tokens("<a@b.co>", in_link=True)) == [{"type": "text", "raw": "<a@b.co>"}]


def test_wb_i22_hard_wrap_constructor_branch(record):
    """WB-I22 InlineParser(hard_wrap=True) branch replaces the linebreak rule
    and does not register 'softbreak'."""
    p = InlineParser(hard_wrap=True)
    record(p.rules)
    assert "softbreak" not in p.rules and p.specification["linebreak"] == InlineParser.HARD_LINEBREAK


def test_wb_i23_escape_run(record):
    """WB-I23 parse_escape: a run of escapes becomes one text token."""
    assert record(tokens(r"\*\_")) == [{"type": "text", "raw": "*_"}]


def test_wb_i24_link_text_reaches_end_of_input(record):
    """WB-I24 parse_link D5=T: label regex fails (nested '['), parse_link_text
    succeeds but end_pos == len(src) -> return None (literal text)."""
    assert record(render("[a[b]]")) == "<p>[a[b]]</p>"
