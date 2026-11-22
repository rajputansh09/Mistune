"""Black-box: Mistune-specific behaviour (expected values from the Mistune
documentation, NOT from CommonMark).  Kept separate so that deliberate design
choices are distinguished from defects (proposal, section 3)."""
import mistune
import pytest

from cases import Case
from oracle import md, md_escape, norm, render

CASES = [
    Case("BB-MS-01", "EP", "escape=True escapes raw HTML block", "<div>x</div>", "<p>&lt;div&gt;x&lt;/div&gt;</p>", mistune_specific=True),
    Case("BB-MS-02", "EP", "escape=True escapes inline HTML", "a <b>x</b>", "<p>a &lt;b&gt;x&lt;/b&gt;</p>", mistune_specific=True),
    Case("BB-MS-03", "EP", "javascript: link replaced by #harmful-link", "[a](javascript:x)", '<p><a href="#harmful-link">a</a></p>', mistune_specific=True),
    Case("BB-MS-04", "EP", "data:image/png is allowed for images", "![a](data:image/png;base64,AA)", '<p><img src="data:image/png;base64,AA" alt="a" /></p>', mistune_specific=True),
    Case("BB-MS-05", "BVA", "Block quote nesting depth 6 (max_nested_level boundary)", "> " * 6 + "x",
         "<blockquote>" * 6 + "<p>x</p>" + "</blockquote>" * 6, mistune_specific=True),
    Case("BB-MS-06", "BVA", "Depth 7: the 7th '>' is text (documented limit)", "> " * 7 + "x",
         "<blockquote>" * 6 + "<p>&gt; x</p>" + "</blockquote>" * 6, mistune_specific=True),
]

PARSERS = {"BB-MS-01": md_escape, "BB-MS-02": md_escape}


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_mistune_feature(case, record):
    assert record(render(case.md, PARSERS.get(case.id, md))) == case.expected


@pytest.mark.technique("EP")
def test_hard_wrap_option_turns_newlines_into_br(record):
    """BB-MS-07 hard_wrap=True: every newline in a paragraph becomes <br />."""
    out = record(norm(mistune.create_markdown(hard_wrap=True)("a\nb")))
    assert out == "<p>a<br />\nb</p>"


@pytest.mark.technique("EP")
def test_strikethrough_plugin(record):
    """BB-MS-08 plugin 'strikethrough': ~~x~~ -> <del>x</del>."""
    out = record(norm(mistune.create_markdown(plugins=["strikethrough"])("~~x~~")))
    assert out == "<p><del>x</del></p>"


@pytest.mark.technique("EP")
def test_ast_renderer_returns_tokens(record):
    """BB-MS-09 renderer='ast' returns a token list instead of HTML."""
    tokens = mistune.create_markdown(renderer="ast")("# h")
    record(repr(tokens))
    assert tokens[0]["type"] == "heading" and tokens[0]["attrs"]["level"] == 1
