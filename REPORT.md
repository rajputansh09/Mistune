# Evaluating Testing Strategies for an Open-Source Markdown Parser (Mistune 3.1.4)

ECE 322 Software Testing and Maintenance · Fall 2026 · Final report

Ansh Rajput (arajput3) · Vaibhav Baswala (baswala) · Aditya Nair (anair5) ·
Muhammad Abdur Rab Siddiqui (msiddiq6) · Ayaan Hafeez (mhafeez1)

> **Draft status.** Sections 1–5 and 8 contain measured results from the manual
> test groups. Sections 6–7 describe the LLM protocol, and the cells marked
> **[TBD-LLM]** must be filled after the team runs the ChatGPT sessions
> (`llm/prompts/PROMPTS.md`). Section 9 lists the work but does not yet say who
> did each part; the team must assign it.

---

## 1. Software under test

Mistune is a pure-Python Markdown-to-HTML converter, about 2,200 lines of core
code. A `Markdown` object (`markdown.py`) runs a **block parser**
(`block_parser.py`, `list_parser.py`) that splits the text into block tokens. It
then runs an **inline parser** (`inline_parser.py`) on the text of each token,
and passes the token tree to an **HTML renderer** (`renderers/html.py`). Both
parsers rely on regular expressions and small scanners in `helpers.py` and
`util.py`. We pinned `mistune==3.1.4` and used one configuration throughout,
`create_markdown(escape=False)`: the CommonMark core with raw HTML allowed.

Markdown is a good target for testing because it has no syntax errors. Every
string is valid input, so faults appear as *wrong structure*, not crashes. The
rules also interact: emphasis inside links inside list items inside quotes.

**Oracle.** Expected outputs come from the CommonMark 0.31.2 specification. To
show that our hand-written oracle is correct, every expected value is compared
with **markdown-it-py 4.3.0**, an independent CommonMark-compliant
implementation (`tests/test_oracle_validation.py`). A normaliser removes layout
whitespace that has no meaning. Under it, markdown-it-py passes all 652 spec
examples. The check caught one oracle mistake of ours before Mistune was run
(BB-SY-F03: `<b c>` is a valid raw-HTML tag).

## 2. Testing strategy and its justification

| Level | Technique (course source) | Why it fits a Markdown parser |
|---|---|---|
| Black-box | Equivalence partitioning and boundary values (L4) | The spec defines numeric limits: heading level 1–6, indent ≤ 3, list number ≤ 9 digits, fence ≥ 3 |
| | Decision tables (L6) | Emphasis is decided by 5–6 interacting conditions (flanking, run length, intraword, character) |
| | Syntax-driven testing (L7) | Markdown is a grammar. Production coverage, plus delimiter and field-value errors, map directly to link and fence syntax |
| | Pairwise testing (Lab 3, allpairspy) | Faults come from *pairs* of features (container × inline element) |
| | Random, fuzz, operational profile, stress (L5) | Robustness and security on arbitrary text, realistic usage, denial of service |
| White-box | Statement, branch and loop coverage, basis paths, def-use (L8, L9, Lab 3) | The parsing logic is dense in a few functions with loops and many branches |
| Integration | Top-down with stubs, bottom-up with drivers, big-bang (L11, Lab 4) | Clear module tree (Markdown → block, inline, renderer → helpers) |
| Fault injection | Mutation testing (value, decision, statement); Mills seeding; capture-recapture (L10) | Measures how good *each test group* is at finding faults, not just at covering code |
| LLM-assisted | Basic vs refined prompts, repeated runs (Lab 5) | Required by the project. Compared on the same metrics |

Mistune's own test suite was used only as a reference. It does not count toward
any group.

## 3. Testing activities

**3.1 Black-box (151 executed cases).**
`test_bb_partition_boundary.py` holds 62 EP and BVA cases across the four
categories in the proposal. The variables, classes and boundaries are listed in
`docs/test_design.md`, for example the ATX level {1, 2, 6, 7}, indent {3, 4},
ordered start {0, 9 digits, 10 digits} and fence length {2, 3}.
`test_bb_decision_table.py` has two decision tables: DT-1 for emphasis (15 rules)
and DT-2 for "may a list item interrupt a paragraph" (7 rules).
`test_bb_syntax.py` defines a BNF for inline links and fences and achieves
production and terminal coverage (12 cases). It adds the L7 *delimiter-error*
classes (missing, wrong, extra, escaped, paired or nested, 11 cases) and
*field-value* errors (4 cases).
`test_bb_pairwise.py` covers four factors (4 containers × 6 inline elements × 3
positions × 2 block types). That is 144 combinations exhaustively; allpairspy
reduces them to **24**, and a test checks that every pair is still covered.
`test_bb_random.py` contains:
- fuzzing over a Markdown-significant alphabet: 300 documents with no crash; in
  escape mode, 0 of 200 leak `<script>`; 0 of 100 harmful URLs survive;
- a Musa **operational profile** (headings 15%, paragraphs 40%, lists 20%,
  quotes 10%, code 10%, ordered 5%): 200 realistic documents, each compared with
  the reference;
- **differential fuzzing**: 290 of 300 malformed documents (96.7%) agree with
  the reference;
- **stress** tests.

Nine more cases check documented Mistune-specific behaviour (escaping, harmful
URLs, `max_nested_level`, plugins) and keep it apart from defects.

**3.2 White-box (100 cases).** We drew control-flow graphs for the selected
units. The full analysis of `helpers.parse_link_text` is in
`docs/whitebox_cfg.md`: V(G) = 6, six basis paths, the loop run 0, 1 and 2 or
more times, and all ten def-use pairs of `level`, `found` and `pos` covered. The
other units were tested decision by decision: `parse_emphasis`,
`parse_codespan`, `parse_link`, `parse_fenced_code`, `parse_setex_heading`,
`parse_ref_link`, `extract_block_quote`, all 7 CommonMark HTML-block rules of
`parse_raw_html`, every function in `list_parser`, and `safe_url`. Internal
state flags (`in_link`, `in_emphasis`, …) were set directly through
`InlineState` to reach branches that black-box input cannot reach cheaply. After
the first coverage run, four tests were added for lines it showed as missed
(WB-B19–B21, WB-I24).

**3.3 Integration (14 cases).** Top-down: `Markdown.parse` first ran with
`unittest.mock` stubs for the block parser, inline parser and renderer. We
checked the interfaces: CRLF normalisation, one inline call per text token, the
shared `env` carrying link definitions, the renderer contract, and hook order.
The stubs were then replaced one at a time. Bottom-up: drivers for
InlineParser over the real helpers, then for BlockParser + list_parser, then for
the renderer with hand-made tokens. Big-bang: a README document, safe mode end
to end, file reading, and plugins.

**3.4 Fault injection.** `mutation/mutate.py` is our own AST mutation engine. We
did not use mutmut, so the operators match the lecture and every mutant can be
reproduced. It produced **818 single-fault mutants** in the five parser modules:
- value: integer ±1, True↔False;
- decision: `<`↔`<=`, `==`↔`!=`, `in`↔`not in`, and↔or, negated `if`/`while`;
- statement: delete, break→continue, return→None.

Every mutant was run against every group. A hang (an infinite loop caused by the
fault) counts as a kill.

## 4. Test cases

The full tables are in `docs/test_case_tables.md` (generated from the run: ID,
technique, description, input, expected, actual, result; failed cases in bold).
Representative rows:

| ID | Technique | Input | Expected (CommonMark) | Actual | Result |
|---|---|---|---|---|---|
| BB-EP-H04 | BVA level 7 | `####### Title` | `<p>####### Title</p>` | same | PASS |
| BB-EP-L06 | BVA 10 digits | `1234567890. a` | `<p>1234567890. a</p>` | same | PASS |
| BB-EP-E12 | EP invalid char | `a\x00b` | `<p>a�b</p>` | raw NUL | **FAIL D10** |
| BB-DT-E09 | DT rule R9 | `a*"foo"*` | `<p>a*&quot;foo&quot;*</p>` | `<p>a<em>…</em></p>` | **FAIL D1** |
| BB-DT-E13 | DT rule R13 | `*foo **bar***` | `<em>foo <strong>bar</strong></em>` | literal | **FAIL D2** |
| BB-SY-P04 | Production P3 | `[a](b(c(d)))` | `href="b(c(d))"` | `href="b(c(d"` + `))` | **FAIL D4** |
| BB-SY-D07 | Paired delimiter | `[a [b](/c)](/d)` | inner link only | outer link wins | **FAIL D6** |
| BB-RF-07 | Stress | `"[" * 4000` | < 0.5 s | 3.2 s | **FAIL D11** |
| WB-H02 | Loop ×2, du(level) | `parse_link_text("a[b]c]rest",0)` | `("a[b]c", 6)` | same | PASS |
| TD-03 | Top-down interface | `[x]` + definition | env passed to the inline stub | same | PASS |

## 5. Results (manual groups)

**5.1 Execution and coverage.** All non-defect tests pass. 13 test cases fail
because of real defects; they are kept as strict `xfail`. Coverage of the five
parser modules plus the renderer and core was measured with coverage.py, branch
mode, excluding plugins and directives:

| Group | Cases | Fail | Statement % | Branch % | Branch % per case | Redundancy % | Oracle valid |
|---|---|---|---|---|---|---|---|
| Black-box (all) | 151 | 11 (+2 slow) | 93.2 | 84.2 | 0.56 | 84.0 | 135/135 |
| – EP/BVA only (budget reference for the LLM) | 62 | 1 | 80.7 | 62.3 | 1.01 | 50.0 | 62/62 |
| White-box | 100 | 0 | 91.8 | 83.4 | 0.83 | 32.0 | n/a |
| Integration | 14 | 0 | 76.7 | 58.3 | 4.16 | 21.4 | n/a |
| **All manual** | 265 | 13 | **97.9** | **94.5** | 0.36 | 81.1 | 135/135 |

*Redundancy* is 1 − |greedy minimal subset with the same arc coverage| / |cases|,
computed from per-test coverage contexts. The black-box cases are highly
redundant *for coverage*, yet they found every defect: the defects sit on
lines that are *already covered* by passing tests. This is the lecture's point
that coverage alone does not show the absence of faults (coincidental
correctness). Of the remaining uncovered code, `inline_parser.py:379` is
infeasible, and `list_parser.py:110` needs a plugin that is outside our
configuration.

**5.2 Defects.** 11 deviations from CommonMark were confirmed (`docs/defects.md`).
Our designed tests found **9 of them**: D1–D7, D10 and D11. D8 (setext inside a
lazy quote) and D9 (HTML comment edge cases) were found only by the 652-example
spec run, which we use as an external reference. Mistune passes 594/652 spec
examples (91.1%), and 45 of the 58 failures are emphasis. The most serious
defect is **D11**: **quadratic run time** on unmatched `[` (8,000 characters
take 12.6 s, against 0.10 s for the reference parser; doubling the input
quadruples the time). Any service that renders untrusted Markdown with Mistune
can therefore be slowed down on purpose (algorithmic DoS). **D10** (NUL not
replaced) breaks a security requirement of the spec. Results by technique:

| Technique | Defects found |
|---|---|
| Decision tables | D1, D2, D3 |
| Syntax-driven | D4, D5, D6, D7 |
| EP/BVA | D10 |
| Stress/fuzz | D11 |
| Pairwise, operational profile, white-box, integration | none |

White-box tests were written *from* the code, so they confirm what the code does
rather than what the spec requires. They found no spec defects. Their value
shows in coverage and in mutation kills (5.3).

**5.3 Mutation analysis.** 818 valid mutants (0 stillborn) were run against each group (`results/mutation_analysis.md`).

| Group | Killed | Mutation score | Unique kills (only this group) |
|---|---|---|---|
| Black-box | 612 | 74.8% | 40 |
| White-box | 649 | **79.3%** | **104** |
| Integration | 408 | 49.9% | 1 |
| **Union** | 723 | **88.4%** | – |

By operator class: decision 91.2%, statement 90.2%, value 81.4%. Value
mutants (±1 on constants such as `{0,3}` indentation limits) survive most
often. By module: helpers 96%, util 100%, inline 91%, block 85%, list 84%.
Black-box and white-box rank differently by coverage and by mutation score.
White-box tests kill 104 mutants that no other group kills, so the groups
**complement** each other.

Sampled survivors include both equivalent and non-equivalent mutants:
- **M0010** (`pos < len` → `<=` in `parse_link_text`) is **equivalent**. At
  `pos == len` the regex search fails and the loop breaks anyway.
- **M0029** (`break` → `continue` after the matching `]`) is **not
  equivalent**. `parse_link_text("a]b]", 0)` returns `('a]b', 4)` instead of
  `('a', 2)`. It survives because black-box input reaches this function only
  when the faster label regex has already failed, and our unit tests never put
  a second `]` after the closing one. This is a concrete test gap, and one unit
  test fixes it.

**Capture-recapture** (lecture 10), with the black-box and white-box groups as
independent "testers": N1 = 612, N2 = 649, N12 = 539, so the estimated number of
detectable faults is N = N1·N2/N12 ≈ 737. The two groups found 722 of them,
which means they are close to the detection limit of this pair of techniques.

**Mills fault seeding**, with the mutants as seeded faults: S = 818 seeded,
s = 723 detected, n = 9 indigenous defects found by our designed tests. The
estimated number of indigenous defects is N̂ = n·S/s = **10.2**. This is close
to the **11** defects that actually exist, since the spec run found two more
(D8, D9). The confidence that no defect remains beyond the 9 found is only
C ≈ 0.29, consistent with the two defects that the spec run did find.

## 6. LLM-assisted test generation (ChatGPT)

**Protocol** (`llm/prompts/PROMPTS.md`). We used four prompts in the Lab 5 style:
- **P1** basic black-box ("write 60 black-box tests for Mistune 3.1.4");
- **P2** refined black-box: role, spec link, the four categories, EP and BVA
  required, the exact `Case(...)` output format, and three examples;
- **P3** basic white-box (source pasted, "write 40 unit tests");
- **P4** refined white-box: target functions, harness code, explicit criteria
  (100% branch coverage, loop 0/1/2+, every decision outcome T and F, def-use
  pairs of `level`/`found`/`pos`).

The budgets match the manual counterparts: 60 vs 62 EP/BVA cases, and 40
white-box tests. Each refined prompt was followed by refinement turns:
- R1: output format;
- R2: missing categories or coverage;
- R3: we send back the expected values our validator rejected.

The model, version and date of every session are recorded in `llm/sessions/`.
P2 and P4 were each run **3 times in fresh chats** to measure repeatability.

**Validity assessment, done before execution** (`scripts/validate_llm.py`):
1. Does the file parse and import?
2. Each expected value is compared with the CommonMark reference and classed as:
   - *valid*;
   - *hallucinated*: the LLM is wrong and Mistune is right;
   - *both wrong*;
   - *defect found*: the LLM agrees with CommonMark and Mistune does not.

Manual edits needed to make a file run are counted in the session log as effort.
The tool was first checked on our own black-box suite: it classified all 11
defect cases as *defect found* and flagged only the 2 deliberate Mistune-specific
cases.

**Results.** **[TBD-LLM]**: paste the output of `results/summary.md`,
`validate_llm.py` and `consistency.py`.

| Measure | P1 basic BB | P2 refined BB (mean of 3 runs) | P3 basic WB | P4 refined WB (mean of 3) |
|---|---|---|---|---|
| Cases delivered / requested | /60 | /60 | /40 | /40 |
| Runnable without edits (edits needed) | | | | |
| Oracle validity % (hallucinated / both wrong) | | | n/a | n/a |
| Statement % / branch % | | | | |
| Mutation score % | | | | |
| Defects found (IDs) | | | | |
| Redundancy % | | | | |
| Time spent (prompting + fixing, min) | | | | |
| Jaccard overlap between runs | – | | – | |

**What to look for** (use this to write the discussion):
- Does prompt specificity raise validity and coverage?
- Does the refined prompt produce real BVA pairs (6/7, 3/4, 9/10 digits), or
  only "typical" cases?
- Do LLM expected values copy what Mistune does instead of what CommonMark says?
  Emphasis is the most likely place.
- Do consecutive replies (R3) fix rejected values, or introduce new errors?
- How stable are the three runs (inputs in common, variance of the scores)?
- Do LLM tests *complement* ours, i.e. kill mutants our groups missed? Compare
  the unique kills in `results/mutation_analysis.md`.

## 7. Comparative evaluation

| Criterion | Manual (black-box, EP/BVA, 62) | Manual (white-box, 100) | LLM basic | LLM refined |
|---|---|---|---|---|
| Design effort (person-hours) | **[team]** | **[team]** | [TBD-LLM] | [TBD-LLM] |
| Statement / branch coverage % | 80.7 / 62.3 | 91.8 / 83.4 | | |
| Branch % per case | 1.01 | 0.83 | | |
| Mutation score % | 74.8 (all BB) | 79.3 | | |
| Test validity | 62/62 (100%) | 100% | | |
| Defects found | D10 (all BB: 9 IDs) | none | | |

## 8. Conclusions

1. **Specification-based black-box techniques found the defects.** Decision
   tables and syntax-driven testing together found 7 of the 9 defects found by
   designed tests, and the defects cluster where the spec is most complex
   (emphasis, nested links). Pairwise and operational-profile testing found
   none. Combined with 91% spec conformance, this suggests that Mistune works
   well on everyday documents and fails on edge-case syntax.
2. **Coverage is necessary, not sufficient.** Black-box tests reached 93%
   statement coverage while 81–84% of them were redundant *for coverage*, and
   every defect was on covered code. White-box tests had the best coverage per
   case but found no spec defects.
3. **Mutation scores show complementarity.** White-box tests found no spec
   defects but have the highest mutation score (79.3%) and 104 unique kills.
   Black-box tests find spec defects. Only the union reaches 88.4%. Mills
   seeding estimated 10.2 defects against the 11 that exist.
4. **Robustness testing found the highest-severity issue** (D11, quadratic DoS).
   Functional techniques could not have found it.
5. **An independent oracle matters.** The differential check against
   markdown-it-py removed a wrong expectation before execution. The same tool
   is what lets us judge LLM output objectively.
6. LLM conclusions: **[TBD-LLM]**.

**Limitations.** The validity of mutation analysis rests on the
competent-programmer and coupling hypotheses. Equivalent mutants (estimated in
5.3) lower the scores. Timings come from one machine. One configuration only.

## 9. Responsibilities and contributions

**[Team to assign; one row per member, as the project description requires.]**

| Member | Responsibilities |
|---|---|
| Ansh Rajput | |
| Vaibhav Baswala | |
| Aditya Nair | |
| Muhammad Abdur Rab Siddiqui | |
| Ayaan Hafeez | |

Work packages to assign:
- EP/BVA suite;
- decision tables and syntax-driven suite;
- pairwise, fuzz and stress;
- white-box CFG and unit tests;
- integration tests;
- mutation and fault seeding;
- LLM sessions and validation;
- report and presentation.

## References

1. CommonMark Spec 0.31.2, https://spec.commonmark.org/0.31.2/
2. Mistune 3.1.4, https://github.com/lepture/mistune
3. markdown-it-py, https://github.com/executablebooks/markdown-it-py
4. ECE 322 lecture notes 4–11 and Labs 1–5, Fall 2026.
5. J. D. Musa, "Operational profiles in software-reliability engineering," *IEEE Software*, 1993.
6. Y. Jia and M. Harman, "An analysis and survey of the development of mutation testing," *IEEE TSE*, 2011.
7. H. D. Mills, "On the statistical validation of computer programs," IBM FSD, 1972.
8. J. Wang et al., "Software testing with large language models: survey, landscape, and vision," *IEEE TSE*, 2024.
