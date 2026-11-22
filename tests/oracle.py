"""Shared test oracle helpers (used by every test group).

Two independent oracles are used for black-box tests:
  1. The expected HTML written by hand from the CommonMark 0.31.2 spec.
  2. markdown-it-py (a CommonMark-0.31.2-compliant reference implementation),
     used only to *validate* the hand-written oracle (differential check).

Mistune and the reference renderer differ in insignificant whitespace
(newline between block tags, trailing newline inside <pre><code>).  ``norm``
removes only those differences, so assertions compare meaning not layout.
"""
import re

import mistune

# One configuration used by all groups (proposal: same version + configuration)
md = mistune.create_markdown(escape=False)  # CommonMark core, raw HTML allowed
md_escape = mistune.create_markdown(escape=True)  # "safe" mode, raw HTML escaped

_BLOCK = r"(?:p|ul|ol|li|blockquote|pre|h[1-6]|hr|table|thead|tbody|tr|th|td|div)"
_WS_BEFORE_BLOCK = re.compile(r"\s+(?=</?" + _BLOCK + r"[\s>/])")
_WS_AFTER_BLOCK = re.compile(r"(</?" + _BLOCK + r"(?:\s[^>]*)?/?>)\s+")
_CODE_END = re.compile(r"\n+</code></pre>")


def norm(html: str) -> str:
    html = _CODE_END.sub("</code></pre>", html)
    html = _WS_BEFORE_BLOCK.sub("", html)
    html = _WS_AFTER_BLOCK.sub(r"\1", html)
    return html.strip()


def render(src: str, parser=md) -> str:
    """Render Markdown with the project configuration and normalise it."""
    return norm(parser(src))


def reference(src: str) -> str:
    """Render with markdown-it-py in strict CommonMark mode (oracle check)."""
    from markdown_it import MarkdownIt

    return norm(MarkdownIt("commonmark").render(src))
