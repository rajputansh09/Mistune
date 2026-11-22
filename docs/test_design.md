# Test design

## 1. Technique × category matrix (number of manual test cases)

| Technique (lecture) | A Headings/paras/breaks | B Inline/links | C Lists/quotes | D Escapes/boundary | Cross-cutting | Total |
|---|---|---|---|---|---|---|
| EP + BVA (L4) | 21 | 15 | 14 | 12 | – | 62 |
| Decision table (L6) | – | 15 (emphasis DT-1) | 7 (list-interrupt DT-2) | – | – | 22 |
| Syntax-driven: production, delimiter, field-value (L7) | – | 9 + 9 + 3 (links/images) | – | 3 + 2 + 1 (fences) | – | 27 |
| Pairwise (Lab 3 T3, allpairspy) | | | | | 24 (of 144 exhaustive) + 1 coverage check | 25 |
| Random, fuzz, operational profile, stress (L5) | | | | | 8 | 8 |
| Mistune-specific features | | | | | 9 | 9 |
| White-box: statement, branch, loop, def-use (L8, L9, Lab 3) | | | | | 100 | 100 |
| Integration: top-down, bottom-up, big-bang (L11, Lab 4) | | | | | 14 | 14 |

## 2. Equivalence classes and boundaries (category A–D)

| Input variable | Valid classes | Invalid classes | Boundaries tested | Test IDs |
|---|---|---|---|---|
| ATX `#` count n | 1 ≤ n ≤ 6 | n = 0, n ≥ 7, no space after `#` | 1, 2, 6, 7 | H01–H05 |
| Heading indentation i | 0 ≤ i ≤ 3 | i ≥ 4 (code block) | 3, 4 | H09, H10 |
| Setext underline length L | L ≥ 1 | – | 1 | H11, H12 |
| Trailing spaces t before newline | t ≥ 2 (hard break), `\` | t ≤ 1 (soft) | 1, 2; end of paragraph | P03–P06 |
| Thematic break marker count k | k ≥ 3 | k ≤ 2, mixed characters | 2, 3 | T01–T03 |
| Emphasis delimiter | `*`, `_`, `**`, `__`, `***` | unclosed, intraword `_` | – | I01–I07 |
| Link form | inline, titled, full ref, autolink, e-mail, image | undefined reference | – | I09–I15 |
| Bullet char / ordered delimiter | `-+*`, `.` `)` | changing bullet → new list | – | L01–L03 |
| Ordered start digits d | 1 ≤ d ≤ 9 | d ≥ 10 | 0, 9 digits, 10 digits | L04–L06 |
| Sub-list indent | ≥ content width | < content width (sibling) | 1 space | L08, L09 |
| Document size | non-empty | – | empty, whitespace-only | E07, E08 |
| Fence length f | f ≥ 3 | f = 2 | 2 | E10 |
| Character set | printable Unicode | U+0000 | NUL | E12 |
| Nesting depth (Mistune) | ≤ 6 | > 6 | 6, 7 | MS-05, MS-06 |

## 3. Oracle strategy

1. Expected HTML was written by hand from the CommonMark 0.31.2 prose and examples.
2. `tests/test_oracle_validation.py` compares every expected value with
   markdown-it-py, an independent CommonMark-compliant implementation (differential
   oracle). This found one wrong expectation of ours (BB-SY-F03: `<b c>` is a
   valid raw HTML tag), which we fixed before running Mistune.
3. `tests/oracle.norm` removes whitespace that has no meaning (newlines between
   block tags, trailing newline in `<pre><code>`). Under it, markdown-it-py
   matches all 652/652 spec examples.
4. Known defects are `xfail(strict=True)`. The suite stays green, but each defect
   test still runs, and a fix (XPASS) makes the test fail so the table is updated.
