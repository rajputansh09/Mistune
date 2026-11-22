# Evaluating Testing Strategies for an Open-Source Markdown Parser (Mistune 3.1.4)

ECE 322 Software Testing and Maintenance · Fall 2026 · Final report ·
Ansh Rajput (arajput3), Vaibhav Baswala (baswala), Aditya Nair (anair5),
Muhammad Abdur Rab Siddiqui (msiddiq6), Ayaan Hafeez (mhafeez1)

> **Draft.** Everything marked **[LLM]** is filled from the ChatGPT sessions
> (protocol in §6). §9 must be completed by the team.

## 1. Software under test

Mistune is a pure-Python Markdown-to-HTML converter, about 2,200 lines of core
code. `Markdown.parse` runs a **block parser** (`block_parser.py`,
`list_parser.py`) that splits the text into block tokens. An **inline parser**
(`inline_parser.py`) then processes the text of each token, and an **HTML
renderer** (`renderers/html.py`) produces the output. Both parsers rely on
regular expressions and small scanners in `helpers.py` and `util.py`. We pinned
`mistune==3.1.4` and used a single configuration, `create_markdown(escape=False)`
(the CommonMark core with raw HTML allowed). Markdown has no syntax errors: every
string is valid input, so faults appear as *wrong structure*, and the rules
interact, for example emphasis inside links inside list items inside quotes.

**Oracle.** Expected outputs are derived from the CommonMark 0.31.2
specification. Each hand-written expected value is checked against
**markdown-it-py 4.3.0**, an independent CommonMark-compliant implementation,
before Mistune is run. This check corrected one of our own expectations
(BB-SY-F03). A normaliser removes layout whitespace that has no meaning. Under
it, markdown-it-py matches all 652 spec examples and Mistune matches 594
(91.1%). The normaliser also hides one systematic cosmetic difference: Mistune
drops the final newline inside indented code. Without normalisation Mistune
matches only 472 examples, almost all because of layout.

## 2. Testing strategy and its justification

| Level | Technique (lecture) | Justification for a Markdown parser |
|---|---|---|
| Black-box | EP and BVA (L4) | The spec has numeric limits: heading level 1–6, indent ≤ 3, list number ≤ 9 digits, fence ≥ 3 |
| | Decision tables (L6) | Emphasis depends on 5–6 interacting conditions (flanking, run length, intraword, character) |
| | Syntax-driven (L7) | Markdown is a grammar; production coverage and delimiter/field errors map onto link and fence syntax |
| | Pairwise, allpairspy (Lab 3) | Faults come from pairs of features (container × inline element) |
| | Random, fuzz, operational profile, stress (L5) | Robustness and security on arbitrary text; realistic usage; denial of service |
| White-box | Statement, branch, loop, basis-path, def-use (L8, L9, Lab 3) | The logic is concentrated in a few loop- and branch-heavy functions |
| Integration | Top-down with stubs, bottom-up with drivers, big-bang (L11, Lab 4) | Clear module tree: Markdown → block, inline, renderer → helpers |
| Fault injection | Mutation testing (L10) | Measures how well each group *detects* faults, not only what it covers |
| LLM | Basic vs refined prompts, first reply scored, 3 repeats (Lab 5) | Required by the brief; evaluated on the same metrics |

Mistune's own test suite was used only as a reference.

## 3. Testing activities

**Black-box (156 cases; 3 slow stress tests are excluded from the coverage and mutation runs).**
- **EP/BVA (63).** Variables, classes and boundaries for four categories,
  e.g. ATX level {1, 2, 6, 7}, indent {3, 4}, ordered start {0, 9 digits,
  10 digits}, fence length {2, 3}.
- **Decision tables (22).** Two tables: DT-1 emphasis (15 rules) and DT-2
  "may a list item interrupt a paragraph" (7 rules).
- **Syntax-driven (27).** A BNF for inline links and fences, with production
  and terminal coverage plus delimiter-error and field-value-error cases.
- **Pairwise (25).** 4 containers × 6 inline elements × 3 positions × 2 block
  types is 144 combinations; allpairspy needs 24, and one more test checks that
  every pair is covered.
- **Random (8).** Fuzzing: 300 documents, 0 crashes; 0 of 200 `<script>`
  leaks in escape mode; 0 of 100 *literal-scheme* harmful URLs survive. A Musa
  operational profile: 200 README-like documents, all equal to the reference.
  Differential fuzzing: 290/300 agree with the reference. Three stress tests.
- **Mistune-specific behaviour (10).** Kept apart from defects.

**White-box (100 cases).** A control-flow graph of `helpers.parse_link_text`
has V(G) = 6. Its 6 basis paths, loop counts of 0, 1 and 2+, and all 10
def-use pairs of `level`, `found` and `pos` are covered. The other selected
units were tested decision by decision (`parse_emphasis`, `parse_codespan`,
`parse_link`, `parse_fenced_code`, `parse_ref_link`, `extract_block_quote`,
HTML-block rules 1–7, every `list_parser` function, `safe_url`). Internal flags
such as `in_link` were set through `InlineState`. Four tests were added for
branches the first coverage run missed.

**Integration (14 cases).**
- **Top-down:** `Markdown.parse` with `unittest.mock` stubs for the parsers and
  renderer. Checks: CRLF normalisation, one inline call per text token, the
  shared `env` carrying link definitions, the renderer contract and hook order.
  The stubs were then replaced one at a time.
- **Bottom-up:** drivers for the inline parser on real helpers, the block and
  list parsers, and the renderer.
- **Big-bang:** a README document, safe mode, file reading and plugins.

**Fault injection.** Our own AST engine (`mutation/mutate.py`) generates 818
single-fault mutants in the five parser modules:
- value: ±1, True↔False;
- decision: `<`↔`<=`, `==`↔`!=`, `in`↔`not in`, and↔or, negated conditions;
- statement: deletion, break→continue, return→None.

Every mutant is run against every group.

## 4. Test cases

The table below is the complete test-case list in compact form. Each row is a
family of cases. Every failed case is listed individually in §5.2. The
one-row-per-case table (270 rows, with input, expected, actual and result) is
in the repository (`docs/test_case_tables.md`); its inclusion as an appendix
depends on the instructor's answer.

| IDs | Technique | # | What varies (inputs / conditions) | Result |
|---|---|---|---|---|
| BB-EP-H01–H13 | EP/BVA | 13 | ATX level 1/2/6/7, missing space, empty, closing `#`, indent 3/4, setext length 1, `-`/`=`, mixed underline | 12 P, 1 F |
| BB-EP-P01–P06, T01–T03 | EP/BVA | 9 | paragraph joins and splits; 1 or 2 trailing spaces, `\`, end of paragraph; break with k = 2/3, mixed characters | 9 P |
| BB-EP-I01–I15 | EP | 15 | `*` `_` `**` `***`, unclosed, intraword; code span; inline, titled, reference, undefined, auto, e-mail links; image | 15 P |
| BB-EP-L01–L10, Q01–Q04 | EP/BVA | 14 | bullet characters, `)` delimiter, start 0 / 9 / 10 digits, loose, nested, indent 1, interruption; quotes: simple, lazy, nested, with list | 14 P |
| BB-EP-E01–E12 | EP/BVA | 12 | escapes, entities (named, hex, unknown), empty or whitespace document, fences (info, 2 backticks, unclosed), NUL | 11 P, 1 F |
| BB-DT-E01–E15 | Decision table | 15 | DT-1 rules R1–R15 (character, left/right flanking, intraword, run lengths, nesting) | 10 P, 5 F |
| BB-DT-L01–L07 | Decision table | 7 | DT-2 rules (paragraph open, ordered, start = 1, empty item) | 7 P |
| BB-SY-P01–P12 | Production coverage | 12 | link productions P1–P7 (empty, angle, bare, nested parentheses, 3 title forms, whitespace, inline text); fences P8–P11 | 10 P, 2 F |
| BB-SY-D01–D11 | Delimiter errors | 11 | missing, wrong, extra, escaped, nested or paired delimiters; unbalanced `(`; fence length and character mismatch | 8 P, 3 F |
| BB-SY-F01–F04 | Field-value errors | 4 | space in destination, unterminated title, newline in `<…>`, backtick in info string | 4 P |
| BB-PW-01–24 + check | Pairwise | 25 | container × inline element × position × block type | 25 P |
| BB-RF-01–08 + 1 | Fuzz, profile, stress | 9 | random strings, XSS payloads, harmful schemes, operational profile, differential, deep nesting, 4000 `[`, scaling; normaliser sanity check | 7 P, 2 F |
| BB-MS-01–10 | Mistune-specific | 10 | escape mode, harmful-URL filter, `data:` images, nesting limit 6/7, hard_wrap, plugin, AST, `%3A` scheme | 10 P |
| WB-H01–H19, U01–U06 | Branch, path, loop, def-use | 25 | `parse_link_text` (6 basis paths), label (500/501 characters), href (B1–B5), title, `parse_link`, util functions | 25 P |
| WB-I01–I24 | Branch | 24 | emphasis D1–D6, code span D1–D3, link D1–D11, inline HTML, auto e-mail, hard_wrap, escapes | 23 P, 1 F |
| WB-B01–B21 (+R1–R7) | Branch | 30 | fences, ATX/setext, link definitions, block quotes, HTML rules 1–7, depth limit | 30 P |
| WB-L01–L08 (+5), WB-R01–R03 (+7) | Branch | 21 | list bullets, continue width, clamp, loose/tight, depth; `safe_url` outcomes; renderer escaping | 21 P |
| TD-01–06, BU-01–04, BB-01–04 | Integration | 14 | stubs replaced level by level; drivers bottom-up; big-bang documents | 14 P |

## 5. Outcomes

**5.1 Execution and coverage** (coverage.py, branch mode; plugins and
directives excluded). *Redundancy* means redundancy **for coverage only**: the
share of cases outside a greedy minimal subset that has the same arc coverage.
It does not mean the cases are useless; every defect sits on code that is also
covered by passing tests (coincidental correctness).

| Group | Cases | Fail | Statement % | Branch % | Branch % per case | Redundancy % (coverage) |
|---|---|---|---|---|---|---|
| Black-box, all (excl. slow) | 153 | 12 | 93.2 | 84.2 | 0.55 | 84.2 |
| — EP/BVA only (budget pair for the LLM, §7) | 63 | 2 | 80.7 | 62.3 | 0.99 | 50.8 |
| White-box, all | 100 | 1 | 91.8 | 83.4 | 0.83 | 32.0 |
| — helpers + inline (budget pair for the LLM, §7) | 49 | 1 | 60.4 | 44.2 | 0.90 | 34.7 |
| Integration | 14 | 0 | 76.7 | 58.3 | 4.16 | 21.4 |
| **All manual** | 267 | 13 | **97.9** | **94.5** | 0.35 | 80.8 |

The remaining uncovered code includes `inline_parser.py:379`, which is
infeasible, and `list_parser.py:110`, which needs a plugin outside our
configuration.

**5.2 Defects** (details: `docs/defects.md`). There are 13 deviations from
CommonMark; **11 were found by our designed tests**, and D8 and D9 only by the
652-example spec run. All 15 failed cases are listed.

| ID | Defect | Failed test cases | Found by |
|---|---|---|---|
| D1 | `a*"foo"*` gets emphasis; punctuation rule for flanking ignored | BB-DT-E09 | decision table |
| D2 | nested runs of the same character (`*foo **bar***`) stay literal | BB-DT-E13, E14 | decision table |
| D3 | unequal run lengths (`**foo*`) stay literal | BB-DT-E10, E11 | decision table |
| D4 | balanced parentheses in a destination: `[a](b(c(d)))` → `href="b(c(d"` | BB-SY-P04, D08 | syntax-driven |
| D5 | `(title)` form not recognised | BB-SY-P07 | production coverage |
| D6 | link nested inside link text is allowed | BB-SY-D07 | paired delimiter |
| D7 | image alt text keeps Markdown of nested images | BB-SY-D11 | paired delimiter |
| D10 | U+0000 not replaced by U+FFFD (spec §2.3, security) | BB-EP-E12 | EP (invalid character) |
| D11 | **quadratic time** on unmatched `[`: 8,000 characters take 12.6 s vs 0.10 s for the reference; time ×4 when input ×2 | BB-RF-07, RF-08 | stress |
| D12 | mixed setext underline `foo\n--=` becomes `<h1>` | BB-EP-H13 | EP (added after peer review) |
| D13 | an autolink containing `]` inside link text cancels the outer link | WB-I19 | white-box validity check |
| D8, D9 | setext inside a lazy quote; HTML comment edge cases | — | spec run only |

D11 was timed on an Apple M2 (8 GB RAM), macOS 26.6, CPython 3.13.17, idle. It
means any service that renders untrusted Markdown with Mistune can be slowed
down on purpose (algorithmic denial of service). The harmful-URL filter misses
percent-encoded schemes (`javascript%3A…`), but these are inert because `%` is
illegal in a URL scheme, so browsers treat them as relative links (BB-MS-10).

D13 is instructive. Our first version of WB-I19 asserted Mistune's output. The
white-box validity check of §6.2 flagged it as asserting behaviour the spec
forbids, which is the risk the brief raises for code-derived oracles, and it
applied to our own tests too.

**5.3 Mutation analysis** (818 valid mutants; a hang caused by the fault counts
as a kill but is shown separately).

| Group | Killed by failing assertion | Killed by hang | Total killed | Score | Unique kills |
|---|---|---|---|---|---|
| Black-box | 586 | 26 | 612 | 74.8% | 41 |
| White-box | 633 | 14 | 647 | **79.1%** | **103** |
| Integration | 395 | 13 | 408 | 49.9% | 1 |
| **Union** | 700 | 22 | 722 | **88.3%** (85.6% without hangs) | – |

By operator: decision 91.2%, statement 90.0%, value 81.4%. Value mutants such as
±1 on the `{0,3}` indentation limits survive most often. By module: util 100%,
helpers 96%, inline 90%, block 85%, list 84%.

Black-box and white-box rank differently on coverage and on mutation score.
White-box kills 103 mutants that no other group kills, so the groups
complement each other. Not every survivor is a test gap:
- **M0010** (`pos < len` → `<=` in `parse_link_text`) is equivalent.
- **M0029** (`break` → `continue`) is not: `parse_link_text("a]b]", 0)`
  returns `('a]b', 4)` instead of `('a', 2)`. No test places a second `]`
  after the closing one. This is a concrete gap.

*Lecture-10 estimators, as an illustration only.*
Capture-recapture, treating the black-box and white-box groups as two testers:
N1 = 612, N2 = 647, N12 = 538, so N̂ = N1·N2/N12 ≈ 736 detectable faults; 721 were
found. Mills fault seeding, with the mutants as seeded faults and *the same
suites* for seeded and real faults: S = 818, s = 722, n = 11 real defects found
by the designed tests, so N̂ = n·S/s ≈ 12.5.
Neither estimate is used as evidence. The mutant population is *known*, so
capture-recapture estimates a number we already have. The two suites exercise
the same code and are not independent. Mills assumes seeded faults are as hard
to find as real ones, but single-token mutants are simpler than defects such
as D11.

## 6. LLM-assisted test generation (ChatGPT)

**6.1 Prompts and how they were formed** (`llm/prompts/PROMPTS.md`). We used
four prompts:
- **P1** basic black-box;
- **P2** refined black-box: role, spec link, four categories × 15 cases,
  EP/BVA required, three examples;
- **P3** basic white-box (source code pasted);
- **P4** refined white-box: target functions, harness, explicit criteria
  (branch coverage, loops run 0/1/2+, every decision T/F, def-use pairs), and
  "derive expected values from the spec, not by running the code".

Budgets are 60 black-box and 40 white-box tests. *All four prompts end with the
same output-format block*, so the only variable is the testing guidance, and
the basic replies can be scored as well.

The refined prompts were formed iteratively: **[LLM: describe drafts tried, what
changed and why]**. The model and date of every session are logged in
`llm/sessions/`.

**6.2 How validity was assessed.**
- **Scored reply.** Every group is scored on the **first reply**. Only
  mechanical edits (stripping prose, fixing imports) are allowed, and each is
  counted as effort. Expected values are never edited.
- **Black-box validity** (`validate_llm.py`). Before execution, each expected
  value is compared with the CommonMark reference and classed as valid,
  *hallucinated* (the LLM is wrong and Mistune right), *both wrong*, or
  *defect found* (the LLM agrees with the spec and Mistune does not).
- **White-box validity** (`validate_wb.py`). A test that asserts whatever the
  code returns always passes, so three checks are made:
  - every Markdown string a test renders is compared with the reference, and a
    passing test with non-conforming output is flagged **ENCODES-BUG**;
  - each test runs against 150 sampled mutants, and a test that kills none is
    flagged **WEAK**;
  - two members independently review failing and sampled passing tests as
    VALID, TAUTOLOGICAL or INVALID, and the agreement rate is reported.
- **Check on our own tests.** We first ran the white-box check on our 49
  manual helper and inline tests. It flagged 2 as ENCODES-BUG: one became
  defect D13, the other is documented Mistune behaviour (M5). It flagged 7 as
  zero-kill, all of which test `util.py` or a constructor that the mutant
  sample does not touch.

**6.3 Results [LLM].** First replies; mean ± spread over 3 runs.

| Measure | P1 basic BB | P2 refined BB | P3 basic WB | P4 refined WB |
|---|---|---|---|---|
| Cases delivered / requested | /60 | /60 | /40 | /40 |
| Runnable without edits (number of edits) | | | | |
| Black-box: valid / hallucinated / both wrong / defect found | | | — | — |
| White-box: pass / ENCODES-BUG / WEAK / reviewed INVALID | — | — | | |
| Statement % / branch % | | | | |
| Mutation score % (hangs) | | | | |
| Defects found (IDs) | | | | |
| Coverage redundancy % | | | | |
| Effort (minutes, prompting + edits) | | | | |
| Jaccard overlap of inputs across runs | | | | |

**6.4 Discussion [LLM].** Answer each question with evidence from the table:
- **Relevance of prompts:** did adding the technique, spec and examples raise
  validity, coverage and mutation score? Were the BVA pairs real (6/7, 3/4,
  9/10 digits)?
- **Quality:** where were the hallucinations? Emphasis and nested links are
  likely. Did expected values copy Mistune instead of the spec?
- **Consecutive replies**, reported separately from the score: how many
  rejected values did F2 fix, and how many new errors did it introduce?
- **Repeatability:** Jaccard overlap and the spread of the scores across the
  3 runs.
- **Complementarity:** unique mutant kills versus the manual groups.

## 7. Comparative evaluation (equal budgets)

The manual suite has 267 cases in total, far more than the 90–120 planned in
the proposal. The proposal's comparable-budget comparison is therefore made
only between matched pairs: **63 manual EP/BVA cases vs 60 LLM black-box cases**,
and **49 manual helper and inline unit tests vs 40 LLM white-box tests**. The
rest of the manual suite is reported in §5 but is not part of this comparison.

| Criterion | Manual BB (63) | LLM BB basic | LLM BB refined | Manual WB (49) | LLM WB basic | LLM WB refined |
|---|---|---|---|---|---|---|
| Statement / branch % | 80.7 / 62.3 | | | 60.4 / 44.2 | | |
| Branch % per case | 0.99 | | | 0.90 | | |
| Mutation score %, all 818 mutants (hangs) | 58.6 (14) | | | 39.4 (5) | | |
| Oracle validity | 63/63 | | | 2 ENCODES-BUG (fixed) | | |
| Defects found | D10, D12 | | | D13 | | |
| Design effort (hours) | [team] | | | [team] | | |

## 8. Conclusions

1. **Specification-based black-box techniques found the defects.** Decision
   tables and syntax-driven testing found 7 of the 11 defects found by designed
   tests. Pairwise and operational-profile testing found none, which fits
   Mistune's 91% conformance on ordinary documents.
2. **Coverage is necessary, not sufficient.** Black-box tests reached 93%
   statement coverage with high coverage-redundancy, and every defect lies on
   covered code.
3. **Code-derived oracles are risky.** Our own white-box test encoded defect
   D13 until the reference-backed check caught it. White-box tests are still
   the strongest fault detectors by mutation score.
4. **Robustness testing found the most severe issue,** D11, a quadratic-time
   denial of service. Functional techniques could not have found it.
5. **[LLM conclusions.]**

**Limitations.** Mutation results rest on the competent-programmer and coupling
hypotheses, and equivalent mutants deflate the scores. Timings come from one
machine. Only one configuration was tested.

## 9. Responsibilities and contributions

**[Team: one row per member with concrete tasks; required by the brief.]**

| Member | Contributions |
|---|---|
| Ansh Rajput | |
| Vaibhav Baswala | |
| Aditya Nair | |
| Muhammad Abdur Rab Siddiqui | |
| Ayaan Hafeez | |

## References

1. CommonMark Spec 0.31.2, https://spec.commonmark.org/0.31.2/ · Mistune 3.1.4,
   https://github.com/lepture/mistune · markdown-it-py,
   https://github.com/executablebooks/markdown-it-py
2. ECE 322 Fall 2026 lecture notes:
   - L4 *Black Box Testing I*: taxonomy, equivalence classes, boundary values;
   - L5 *Black Box Testing II*: random and fuzz testing, operational profiles;
   - L6 *Black Box Testing III*: decision tables;
   - L7 *Black Box Testing IV*: syntax-driven and state-based testing;
   - L8 *White Box Testing I*: control flow, coverage, basis paths;
   - L9 *White Box Testing II*: data-flow testing;
   - L10 *Fault Injection*: fault seeding, capture-recapture, mutation testing;
   - L11 *Integration Testing*.
3. ECE 322 labs: Lab 2 *Black-box testing (EPC, weak n×1)*; Lab 3 *Unit and
   pairwise testing*; Lab 4 *Integration testing*; Lab 5 *LLMs for software
   testing*.
4. J. D. Musa, "Operational profiles in software-reliability engineering,"
   *IEEE Software*, 1993.
5. Y. Jia and M. Harman, "An analysis and survey of the development of mutation
   testing," *IEEE TSE*, 2011.
6. J. Wang et al., "Software testing with large language models: survey,
   landscape, and vision," *IEEE TSE*, 2024.
7. WHATWG URL Standard, https://url.spec.whatwg.org/ (scheme parsing).
