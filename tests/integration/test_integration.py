"""Integration testing (Lecture 11, Lab 4) using unittest.mock stubs/drivers.

Module dependency tree of the Mistune pipeline (functional decomposition):

                     A  Markdown.parse()          (markdown.py)
              ┌──────────┼───────────────┐
   B BlockParser     D InlineParser    E HTMLRenderer
   (block_parser)    (inline_parser)   (renderers/html)
        │                 │                 │
   C list_parser     H helpers ─────────► U util
        └──────────────► H / U ◄────────────┘

* Top-down (TD-*): test A first with B, D, E replaced by stubs, then replace
  stubs with the real modules one level at a time.
* Bottom-up (BU-*): drivers exercise U/H, then D on top of real H/U, then B+C
  with a stub inline parser, then the whole tree.
* Big-bang (BB-*): all real modules at once on end-to-end documents.
"""
from unittest import mock

import mistune
import pytest
from mistune.block_parser import BlockParser
from mistune.core import BlockState, InlineState
from mistune.inline_parser import InlineParser
from mistune.renderers.html import HTMLRenderer

from oracle import norm

pytestmark = pytest.mark.technique("INTEGRATION")


# ============================================================ TOP-DOWN
def test_td01_markdown_drives_block_parser_once_with_normalised_source(record):
    """TD-01 A + stub B: Markdown.parse normalises CRLF/CR, appends a final
    newline, and calls BlockParser.parse exactly once with that state."""
    stub_block = mock.Mock(spec=BlockParser, state_cls=BlockState)
    md = mistune.Markdown(renderer=None, block=stub_block, inline=mock.Mock())
    _, state = md.parse("a\r\nb\rc")
    stub_block.parse.assert_called_once_with(state)
    assert record(state.src) == "a\nb\nc\n"


def test_td02_markdown_sends_only_text_tokens_to_inline_stub(record):
    """TD-02 A + real B + stub D: the inline parser is invoked once per token
    with 'text' (heading, paragraph), with text stripped, and its return value
    becomes the token's children."""
    stub_inline = mock.Mock(return_value=[{"type": "text", "raw": "STUB"}])
    md = mistune.Markdown(renderer=None, inline=stub_inline)
    tokens = md("# Title  \n\npara\n\n---\n")
    record(stub_inline.call_args_list)
    assert [c.args[0] for c in stub_inline.call_args_list] == ["Title", "para"]
    assert tokens[0]["children"] == [{"type": "text", "raw": "STUB"}]
    assert tokens[-1] == {"type": "thematic_break"}  # no text -> no inline call


def test_td03_inline_receives_shared_env_with_ref_links(record):
    """TD-03 interface check B->D: link definitions collected by the block
    parser are passed to the inline parser through the shared env dict."""
    stub_inline = mock.Mock(return_value=[])
    mistune.Markdown(renderer=None, inline=stub_inline)("[x]\n\n[x]: /url 'T'\n")
    env = stub_inline.call_args.args[1]
    record(env)
    assert env["ref_links"]["X"] == {"url": "/url", "label": "x", "title": "T"}


def test_td04_renderer_stub_receives_token_stream(record):
    """TD-04 A + real B + real D + stub E: the renderer is called once with
    the token iterator and the state, and its result is returned unchanged."""
    stub_renderer = mock.Mock(return_value="RENDERED")
    md = mistune.Markdown(renderer=stub_renderer)
    assert record(md("*a*")) == "RENDERED"
    data, state = stub_renderer.call_args.args
    tokens = list(data)
    assert tokens[0]["type"] == "paragraph"
    assert tokens[0]["children"][0]["type"] == "emphasis"
    assert isinstance(state, BlockState)


def test_td05_hooks_called_in_order(record):
    """TD-05 A's extension interface: before_parse -> before_render ->
    after_render hooks run in order; after_render can replace the result."""
    calls = []
    md = mistune.create_markdown()
    md.before_parse_hooks.append(lambda m, s: calls.append("before_parse"))
    md.before_render_hooks.append(lambda m, s: calls.append("before_render"))
    md.after_render_hooks.append(lambda m, r, s: calls.append("after_render") or r.upper())
    out = md("x")
    record(calls)
    assert calls == ["before_parse", "before_render", "after_render"] and out == "<P>X</P>\n"


def test_td06_all_real_modules_replace_stubs(record):
    """TD-06 final top-down step: all stubs replaced by real modules."""
    md = mistune.Markdown(renderer=HTMLRenderer(escape=False), block=BlockParser(), inline=InlineParser())
    assert record(norm(md("> - *a*"))) == "<blockquote><ul><li><em>a</em></li></ul></blockquote>"


# ============================================================ BOTTOM-UP
def test_bu01_driver_inline_parser_on_real_helpers(record):
    """BU-01 driver for D over real H/U: a link with title and entity."""
    st = InlineState({})
    st.src = '[a&amp;b](/u "t")'
    toks = InlineParser().render(st)
    record(toks)
    assert toks[0]["type"] == "link" and toks[0]["attrs"] == {"url": "/u", "title": "t"}


def test_bu02_block_and_list_parser_with_inline_stub(record):
    """BU-02 driver for B+C (inline parsing not involved): nested list token
    structure, tight flag and block_text conversion."""
    state = BlockState()
    state.process("- a\n  - b\n- c\n")
    BlockParser().parse(state)
    record(state.tokens)
    lst = state.tokens[0]
    assert lst["type"] == "list" and lst["tight"] is True
    assert [li["children"][0]["type"] for li in lst["children"]] == ["block_text", "block_text"]
    assert lst["children"][0]["children"][1]["type"] == "list"


def test_bu03_renderer_driver_with_handmade_tokens(record):
    """BU-03 driver for E (renderer) with hand-made tokens (stub for B and D)."""
    toks = [{"type": "heading", "attrs": {"level": 2}, "children": [{"type": "text", "raw": "<x>"}]}]
    assert record(HTMLRenderer(escape=True)(toks, BlockState())) == "<h2>&lt;x&gt;</h2>\n"


def test_bu04_block_plus_inline_plus_renderer(record):
    """BU-04 top of the bottom-up order: B+C+D+E integrated via Markdown."""
    md = mistune.create_markdown(escape=False)
    assert record(norm(md("1. [a](/u)\n2. `c`"))) == '<ol><li><a href="/u">a</a></li><li><code>c</code></li></ol>'


# ============================================================ BIG-BANG
README = """\
Project
=======

Install with `pip install x` and read the [docs][d].

* fast
* **safe**: escapes `<script>`

> Note: works on Python 3.

```python
print("hi")
```

[d]: https://example.com/docs "Docs"
"""


def test_bb01_big_bang_readme_document(record):
    """BB-01 all modules at once on a realistic README (compared with the
    CommonMark reference implementation)."""
    from oracle import reference

    assert record(norm(mistune.create_markdown(escape=False)(README))) == reference(README)


def test_bb02_big_bang_safe_mode_end_to_end(record):
    """BB-02 all modules + escape=True + harmful URL: nothing executable."""
    out = record(mistune.create_markdown(escape=True)("<script>x</script>\n\n[a](javascript:alert`1`)"))
    assert "<script>" not in out and "javascript:" not in out


def test_bb03_module_read_file_interface(tmp_path, record):
    """BB-03 Markdown.read(): file -> decode -> parse integration, env records
    the file name."""
    p = tmp_path / "doc.md"
    p.write_text("# é\n", encoding="utf-8")
    html, state = mistune.create_markdown().read(str(p))
    record(html)
    assert html == "<h1>é</h1>\n" and state.env["__file__"] == str(p)


def test_bb04_plugins_integrate_with_core(record):
    """BB-04 plugin integration: table + strikethrough + footnotes together."""
    md = mistune.create_markdown(plugins=["table", "strikethrough", "footnotes"])
    out = record(norm(md("| a |\n|---|\n| ~~b~~[^1] |\n\n[^1]: n")))
    assert "<table>" in out and "<del>b</del>" in out and 'class="footnotes"' in out
