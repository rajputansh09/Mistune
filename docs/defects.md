# Defect log: Mistune 3.1.4 vs CommonMark 0.31.2

The oracle is the CommonMark 0.31.2 specification. Each expected value was also
checked against markdown-it-py 4.3.0, which passes all 652 spec examples under
our normaliser (`tests/oracle.py`). A defect means Mistune output that differs
from the spec. Deliberate Mistune design choices are listed separately and are
not counted as defects.

**Spec conformance (reference measurement, not counted for any group):**
Mistune passes 594 of the 652 spec examples (91.1%). The 58 failing examples are
45 emphasis, 8 links, 2 raw HTML, 1 setext, 1 HTML block and 1 image example.

| ID | Area | Minimal failing input | Expected (CommonMark) | Actual (Mistune 3.1.4) | Spec examples | Severity | Found by our tests |
|---|---|---|---|---|---|---|---|
| D1 | Emphasis: flanking rule with punctuation | `a*"foo"*` | `<p>a*&quot;foo&quot;*</p>` | `<p>a<em>&quot;foo&quot;</em></p>` | 352, 354, 368, 380, 392 | Low | BB-DT-E09 (decision table) |
| D2 | Emphasis: nested runs of the same character / rule of 3 | `*foo **bar***` | `<p><em>foo <strong>bar</strong></em></p>` | `<p>*foo **bar***</p>` | 369, 373, 389, 407-432, 461-468, 478-479 | Medium (text silently loses formatting) | BB-DT-E13, BB-DT-E14 |
| D3 | Emphasis: unequal opener and closer run lengths | `**foo*` | `<p>*<em>foo</em></p>` | `<p>**foo*</p>` | 442-447, 454-459, 471-472 | Low | BB-DT-E10, BB-DT-E11 |
| D4 | Link destination with balanced nested parentheses | `[a](b(c(d)))` | `<a href="b(c(d))">a</a>` | `<a href="b(c(d">a</a>))` | 496, 497 | Medium (wrong URL; stray `)` in text) | BB-SY-P04, BB-SY-D08 (syntax-driven) |
| D5 | Link title in parentheses `(title)` is not recognised | `[a](/b (t))` | `<a href="/b" title="t">a</a>` | literal text | 505 | Low | BB-SY-P07 (production coverage) |
| D6 | Links nested inside link text are allowed (spec forbids them) | `[a [b](/c)](/d)` | `[a <a href="/c">b</a>](/d)` | `<a href="/d">a [b](/c)</a>` | 518, 519, 520, 532, 533 | Medium | BB-SY-D07 (paired-delimiter error) |
| D7 | Image alt text keeps raw Markdown of nested images | `![a ![b](/x)](/y)` | `alt="a b"` | `alt="a ![b](/x)"` | 574 | Low | BB-SY-D11 |
| D8 | Setext underline accepted inside a lazy block-quote continuation | `> foo\nbar\n===` | `<blockquote><p>foo bar ===</p></blockquote>` | `<blockquote><h1>foo bar</h1></blockquote>` | 93 | Low | Spec run only (no designed test hit it) |
| D9 | HTML comment and HTML block edge cases | `foo <!--> foo -->` | comment kept as raw HTML | escaped as text | 191, 625, 626 | Low | Spec run only |
| D10 | U+0000 (NUL) not replaced by U+FFFD (spec §2.3, security requirement) | `a\x00b` | `<p>a�b</p>` | raw NUL byte in output | n/a | Medium (security) | BB-EP-E12 (EP: invalid character class) |
| D11 | Quadratic run time on unmatched `[`, `*`, `[a](` (algorithmic denial of service) | `"[" * 8000` | linear time (reference: 0.10 s) | 12.6 s; time ×4 when input ×2 | n/a | High (DoS on untrusted input) | BB-RF-07, BB-RF-08 (stress / fuzz) |

## D11 measurements (single run, same machine, idle)

| input | n=1000 | n=2000 | n=4000 | n=8000 |
|---|---|---|---|---|
| `[` × n, Mistune | 0.21 s | 0.80 s | 3.17 s | 12.55 s |
| `[` × n, markdown-it-py | 0.07 s | 0.02 s | 0.05 s | 0.10 s |
| `*a **b ` × n/7, Mistune | 0.011 s | 0.042 s | 0.165 s | 0.648 s |
| `[a](` × n/4, Mistune | 0.013 s | 0.048 s | 0.183 s | 0.721 s |

Probable cause (white-box reading): `InlineParser.parse_link` calls
`parse_link_text` for every `[`. That function scans forward to the end of the
input when no `]` exists, so n openers cost O(n²). `parse_emphasis` has the same
shape through `EMPHASIS_END_RE[...].search`.

## Mistune-specific behaviour (by design, not defects)

| ID | Behaviour | Test |
|---|---|---|
| M1 | URLs with `javascript:`, `vbscript:`, `file:` or non-image `data:` become `#harmful-link` | BB-MS-03, BB-RF-03, WB-R01 |
| M2 | `max_nested_level = 6`: deeper block quotes or lists are not nested further | BB-MS-05/06, WB-B17, WB-L08 |
| M3 | Indented code blocks drop the final newline inside `<code>` (cosmetic; removed by the normaliser) | oracle.norm |
| M4 | `escape=True` escapes all raw HTML | BB-MS-01/02, BB-RF-02 |
