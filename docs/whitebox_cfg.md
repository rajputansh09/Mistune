# White-box analysis: control flow and data flow

Units were chosen where the parsing logic is densest: `helpers.py` (link
syntax), `inline_parser.py` (emphasis, code, links), `block_parser.py` (fences,
headings, link definitions, block quotes, HTML blocks), `list_parser.py`, and
`HTMLRenderer.safe_url`.

## 1. `helpers.parse_link_text(src, pos)`: CFG, basis paths, def-use

```
        ┌──────────────┐
        │ n1 level=1   │
        │ found=False  │
        │ start=pos    │
        └──────┬───────┘
               ▼
   ┌──────► n2 while pos < len(src) ──F──────────────┐
   │           │T                                    │
   │           ▼                                     │
   │       n3 m = search(src,pos); not m? ──T(break)─┤
   │           │F                                    │
   │           ▼                                     │
   │       n4 pos = m.end(); marker = m.group(0)     │
   │           ▼                                     │
   │       n5 marker == "]" ? ──F──► n7 level += 1 ──┤(back to n2)
   │           │T                                    │
   │           ▼                                     │
   │       n6 level -= 1; level == 0 ? ──T: found=True; break ─┤
   │           │F                                    │
   └───────────┘                                     ▼
                                    n8 found ? T: return text,pos  F: return None,None
```

Decisions: n2, n3, n5, n6, n8, so the cyclomatic complexity is V(G) = 5 + 1 = 6.

| Basis path | Description | Test |
|---|---|---|
| 1 | n1-n2F-n8F (loop not entered) | WB-H04 |
| 2 | n1-n2T-n3T(break)-n8F | WB-H03 |
| 3 | n1-n2T-n3F-n4-n5T-n6T-n8T | WB-H01 |
| 4 | …n5F-n7-n2… (opening `[`) then n5T-n6F-…-n6T | WB-H02 |
| 5 | loop leaves through the n2 predicate with found=False | WB-H05 |
| 6 | escaped `]` skipped by the regex (path 3 with a longer prefix) | WB-H06 |

Loop coverage: 0 iterations (H04), 1 iteration (H01), 2 or more iterations (H02, H05).

Def-use pairs:

| Variable | Definition | Use (c = computation, p = predicate) | Covered by |
|---|---|---|---|
| level | n1 | n6 (p) | H01 |
| level | n1 | n7 (c) | H02 |
| level | n7 | n6 (p) | H02 |
| level | n6 | n6 (p, next iteration) | H02 |
| level | n7 | n7 (c, next iteration) | H05 |
| found | n1 | n8 (p) | H03, H04, H05 |
| found | n6 | n8 (p) | H01 |
| pos | n1 (parameter) | n2 (p) | H04 |
| pos | n4 | n2 (p) | H02 |
| pos | n4 | n8 (c: `src[start:pos-1]`) | H01 |

This gives all-du-paths coverage. Static anomaly check: no `dd`, `ku` or `kk`
pattern exists. `marker` is defined and used in the same iteration.

## 2. Decision lists for the other units (test IDs in brackets)

**`InlineParser.parse_emphasis`**: D1 `mlen==1 and in_emphasis` [I05], D2
`mlen==2 and in_strong` [I06], D3 closer not found [I04], D4 precedence wins
[I07], D5/D6/else for mlen 1, 2, 3 [I01, I02, I03].

**`InlineParser.parse_codespan`**: closer found or not [I08, I11]; code is all
spaces [I09]; strip one space on each side [I08]; newline becomes a space [I10].

**`InlineParser.parse_link`**: image inside an image [I12]; link inside a link
[I13]; label and text both None [I14]; end of input [I24]; precedence [I19];
`(` path fails and falls back to a reference [I18]; `[` collapsed or full
reference [I16, I17]; no `ref_links` [I15].

**`BlockParser.parse_ref_link`**: cannot interrupt a paragraph [B19]; empty
key [B13]; href None [B20]; title followed by a newline or by junk [B09, B10];
junk after the href [B11]; duplicate key [B12].

**`BlockParser.extract_block_quote`**: require_marker true [B14, B21]; lazy
continuation; blank line then break [B15]; break rule interrupts [B16];
depth limit [B17].

**`BlockParser.parse_raw_html`**: CommonMark HTML block rules 1–7, every branch [B18 × 10].

**`list_parser`**: `_get_list_bullet` 5 branches [L01]; `_compile_continue_width`
3 paths [L02]; pattern clamp [L03]; `_is_loose_list` 3 outcomes [L04];
`_transform_tight_list` recursion [L05]; spec example 280 branch [L06];
break-rule `_end_pos` [L07]; depth limit [L08].

**`HTMLRenderer.safe_url`**: allow-all, allow-list hit or miss, harmful
(case-insensitive), good `data:` and bad `data:` [R01 × 7].

## 3. Lines left uncovered by the manual suite and why

- `inline_parser.py:379`: `if not lastgroup` in `precedence_scan`. Unreachable:
  every alternative of the compiled pattern is a named group (infeasible path).
- `list_parser.py:110`: only runs when the `fenced_directive` plugin is loaded
  (outside the configuration under test).
- `markdown.py` and `__init__.py`: the `read()` helpers and the cached
  `mistune.markdown()` wrapper, which are not used by our configuration.
