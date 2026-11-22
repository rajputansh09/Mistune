"""White-box unit tests: mistune/block_parser.py, mistune/list_parser.py and
HTMLRenderer.safe_url.  Each docstring states the decision/branch covered."""
import mistune
import pytest

from mistune import list_parser as lp
from mistune.block_parser import BlockParser
from mistune.renderers.html import HTMLRenderer
from oracle import md, norm, render

pytestmark = pytest.mark.technique("WB")


# ------------------------------------------------------------ parse_fenced_code
def test_wb_b01_fence_info_with_backtick_rejected(record):
    """WB-B01 info and c=='`' and '`' in info -> return None (not a fence)."""
    assert record(render("```a`\nx\n```")).startswith("<p>")


def test_wb_b02_fence_tilde_info_may_contain_backtick(record):
    """WB-B02 c=='~' -> backtick allowed in info string."""
    assert record(render("~~~ a`b\nx\n~~~")) == '<pre><code class="language-a`b">x</code></pre>'


def test_wb_b03_fence_indented_content_trimmed(record):
    """WB-B03 `spaces and code` true -> up to len(spaces) spaces removed."""
    assert record(render("  ```\n   x\n  y\n  ```")) == "<pre><code> x\ny</code></pre>"


def test_wb_b04_fence_unclosed_empty(record):
    """WB-B04 m2 None and code empty: `spaces and code` false."""
    assert record(render("  ```")) == "<pre><code></code></pre>"


# ------------------------------------------------------------ headings
def test_wb_b05_atx_trailing_hashes_only(record):
    """WB-B05 `if text` true and _ATX_HEADING_TRIM removes a hash-only title."""
    assert record(render("# ###")) == "<h1></h1>"


def test_wb_b06_setext_after_paragraph(record):
    """WB-B06 parse_setex_heading: last token is paragraph -> heading."""
    assert record(render("a\nb\n===")) == "<h1>a\nb</h1>"


def test_wb_b07_setext_without_paragraph_is_thematic_break(record):
    """WB-B07 no paragraph -> fallback compile_sc(thematic_break|list) matches."""
    assert record(render("---")) == "<hr />"


def test_wb_b08_setext_without_paragraph_no_fallback(record):
    """WB-B08 no paragraph and fallback does not match -> None -> paragraph."""
    assert record(render("===")) == "<p>===</p>"


# ------------------------------------------------------------ parse_ref_link
def test_wb_b09_ref_link_title_on_next_line(record):
    """WB-B09 title found and followed by newline (m2 matched)."""
    assert record(render("[a]\n\n[a]: /u\n  'T'")) == '<p><a href="/u" title="T">a</a></p>'


def test_wb_b10_ref_link_garbage_after_title(record):
    """WB-B10 title found but m2 fails -> title discarded; href on own line kept."""
    assert record(render("[a]\n\n[a]: /u\n'T' junk")) == '<p><a href="/u">a</a></p><p>\'T\' junk</p>'


def test_wb_b11_ref_link_garbage_after_href(record):
    """WB-B11 no title and m3 fails -> not a definition."""
    assert record(render("[a]: /u junk")) == "<p>[a]: /u junk</p>"


def test_wb_b12_ref_link_first_definition_wins(record):
    """WB-B12 `key not in ref_links` false for the 2nd definition."""
    assert record(render("[a]\n\n[a]: /one\n[a]: /two")) == '<p><a href="/one">a</a></p>'


def test_wb_b13_ref_link_empty_label(record):
    """WB-B13 `if not key` -> return None for a whitespace-only label."""
    assert record(render("[ ]: /u")) == "<p>[ ]: /u</p>"


# ------------------------------------------------------------ block quotes
def test_wb_b14_blockquote_require_marker_path(record):
    """WB-B14 first line is code -> require_marker=True: lazy line not absorbed."""
    assert record(render(">     code\nlazy")) == "<blockquote><pre><code>code</code></pre></blockquote><p>lazy</p>"


def test_wb_b15_blockquote_prev_blank_line_breaks(record):
    """WB-B15 loop: prev_blank_line True -> break (CommonMark ex. 249)."""
    assert record(render("> a\n>\nb")) == "<blockquote><p>a</p></blockquote><p>b</p>"


def test_wb_b16_blockquote_interrupted_by_break_rule(record):
    """WB-B16 loop: break_sc (thematic_break) matches -> end_pos set, prepend."""
    assert record(render("> a\n---")) == "<blockquote><p>a</p></blockquote><hr />"


def test_wb_b17_blockquote_depth_limit_branch(record):
    """WB-B17 depth >= max_nested_level-1 -> 'block_quote' rule removed.
    Uses a parser with max_nested_level=2 to reach the branch cheaply."""
    p = mistune.Markdown(renderer=mistune.HTMLRenderer(escape=False), block=BlockParser(max_nested_level=2))
    assert record(p("> > > x").replace("\n", "")) == "<blockquote><blockquote><p>&gt; x</p></blockquote></blockquote>"


# ------------------------------------------------------------ raw html rules 1-7
@pytest.mark.parametrize(
    "src,expected",
    [
        ("<!-- c -->\nx", "<!-- c --><p>x</p>"),  # rule 2
        ("<?php x ?>", "<?php x ?>"),  # rule 3
        ("<![CDATA[x]]>", "<![CDATA[x]]>"),  # rule 5
        ("<!DOCTYPE html>", "<!DOCTYPE html>"),  # rule 4
        ("<pre>\n\nx</pre>", "<pre>\n\nx</pre>"),  # rule 1 (blank line inside kept)
        ("<div>\n*a*\n\n*b*", "<div>\n*a*<p><em>b</em></p>"),  # rule 6 ends at blank line
        ("</div>\nx", "</div>\nx"),  # rule 6 close tag
        ("<custom>\nx\n\ny", "<custom>\nx<p>y</p>"),  # rule 7 complete open tag
        ("a\n<custom>", "<p>a\n<custom></p>"),  # rule 7 cannot interrupt paragraph
        ("<custom x", "<p>&lt;custom x</p>"),  # rule 7 incomplete tag -> None
    ],
    ids=["R2", "R3", "R5", "R4", "R1", "R6-open", "R6-close", "R7", "R7-para", "R7-none"],
)
def test_wb_b18_raw_html_rules(src, expected, record):
    """WB-B18 every branch of parse_raw_html (CommonMark HTML block rules)."""
    assert record(render(src)) == norm(expected)


# ------------------------------------------------------------ list_parser
@pytest.mark.parametrize(
    "c,expected", [(".", r"\d{0,9}\."), (")", r"\d{0,9}\)"), ("*", r"\*"), ("+", r"\+"), ("-", "-")]
)
def test_wb_l01_get_list_bullet_all_branches(c, expected, record):
    """WB-L01 all 5 branches of _get_list_bullet."""
    assert record(lp._get_list_bullet(c)) == expected


def test_wb_l02_continue_width_paths(record):
    """WB-L02 _compile_continue_width: (a) >=5 spaces -> width 1 (indented
    code), (b) normal text, (c) empty text -> width 1 and text ''."""
    assert lp._compile_continue_width("     code", 2) == ("    code\n", 3)
    assert lp._compile_continue_width("  item", 1) == ("item\n", 3)
    assert record(lp._compile_continue_width("", 2)) == ("", 3)


def test_wb_l03_item_pattern_leading_width_clamped(record):
    """WB-L03 leading_width > 3 is clamped to 3 in _compile_list_item_pattern."""
    assert record(lp._compile_list_item_pattern("-", 7)).startswith(r"^(?P<listitem_1> {0,3})")


def test_wb_l04_is_loose_list_three_outcomes(record):
    """WB-L04 _is_loose_list: blank_line -> True; 2 paragraphs -> True;
    single paragraph -> False (loop completes)."""
    assert lp._is_loose_list([{"type": "blank_line"}]) is True
    assert lp._is_loose_list([{"type": "paragraph"}, {"type": "paragraph"}]) is True
    assert record(lp._is_loose_list([{"type": "paragraph"}, {"type": "list"}])) is False


def test_wb_l05_transform_tight_list_recurses(record):
    """WB-L05 _transform_tight_list converts paragraphs to block_text and
    recurses into nested lists; loose list untouched."""
    inner = {"type": "list", "tight": True, "children": [{"type": "list_item", "children": [{"type": "paragraph"}]}]}
    outer = {"tight": True, "children": [{"type": "list_item", "children": [{"type": "paragraph"}, inner]}]}
    lp._transform_tight_list(outer)
    assert outer["children"][0]["children"][0]["type"] == "block_text"
    assert record(inner["children"][0]["children"][0]["type"]) == "block_text"
    loose = {"tight": False, "children": [{"type": "list_item", "children": [{"type": "paragraph"}]}]}
    lp._transform_tight_list(loose)
    assert loose["children"][0]["children"][0]["type"] == "paragraph"


def test_wb_l06_list_item_begins_with_two_blank_lines(record):
    """WB-L06 'Example 280' branch: an item may begin with at most one blank line."""
    assert record(render("-\n\n  foo")) == "<ul><li></li></ul><p>foo</p>"


def test_wb_l07_list_interrupted_by_heading(record):
    """WB-L07 list-item loop: break rule (atx_heading) parses -> _end_pos path."""
    assert record(render("- a\n# h")) == "<ul><li>a</li></ul><h1>h</h1>"


def test_wb_l08_list_depth_limit_branch(record):
    """WB-L08 depth >= max_nested_level-1 -> 'list' removed from rules."""
    p = mistune.Markdown(renderer=mistune.HTMLRenderer(escape=False), block=BlockParser(max_nested_level=2))
    out = record(p("- a\n  - b\n    - c").replace("\n", ""))
    assert out == "<ul><li>a<ul><li>b- c</li></ul></li></ul>"


# ------------------------------------------------------------ safe_url
@pytest.mark.parametrize(
    "allow,url,expected",
    [
        (True, "javascript:x", "javascript:x"),  # allow all branch
        (["javascript:"], "javascript:x", "javascript:x"),  # allow-list branch
        (["vbscript:"], "javascript:x", "#harmful-link"),  # allow-list miss
        (None, "JAVASCRIPT:x", "#harmful-link"),  # case-insensitive harmful
        (None, "data:image/png;base64,A", "data:image/png;base64,A"),  # good data
        (None, "data:text/html,x", "#harmful-link"),  # bad data
        (None, "/a&b", "/a&amp;b"),  # normal url escaped
    ],
)
def test_wb_r01_safe_url_branches(allow, url, expected, record):
    """WB-R01 every decision outcome of HTMLRenderer.safe_url."""
    assert record(HTMLRenderer(allow_harmful_protocols=allow).safe_url(url)) == expected


def test_wb_r02_renderer_escape_vs_safe_entity(record):
    """WB-R02 HTMLRenderer.text: escape=True escapes, escape=False keeps
    entities but escapes bare '<'."""
    assert HTMLRenderer(escape=True).text("<&amp;") == "&lt;&amp;amp;"
    assert record(HTMLRenderer(escape=False).text("<&amp;")) == "&lt;&amp;"


def test_wb_r03_full_pipeline_smoke(record):
    """WB-R03 smoke: module-level md object used by all groups is configured
    with escape=False (raw HTML passes through)."""
    assert record(md("<b>x</b>").strip()) == "<p><b>x</b></p>"


# ------------------------------------------------------------ added after first coverage run
def test_wb_b19_ref_link_cannot_interrupt_paragraph(record):
    """WB-B19 parse_ref_link: state.append_paragraph() returns a position
    (a definition cannot interrupt a paragraph), so the definition is text."""
    assert record(render("a\n[b]: /u\n\n[b]")) == "<p>a\n[b]: /u</p><p>[b]</p>"


def test_wb_b20_ref_link_missing_destination(record):
    """WB-B20 parse_ref_link: href is None -> not a definition."""
    assert record(render("[a]:\n\n[a]")) == "<p>[a]:</p><p>[a]</p>"


def test_wb_b21_blockquote_require_marker_continues_with_markers(record):
    """WB-B21 extract_block_quote require_marker=True and _STRICT_BLOCK_QUOTE
    matches following '>' lines (loop body for marked lines)."""
    assert record(render(">     c1\n>     c2\nlazy")) == "<blockquote><pre><code>c1\nc2</code></pre></blockquote><p>lazy</p>"
