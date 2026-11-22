# ChatGPT prompts and scoring protocol for the LLM groups

There are four groups: basic and refined prompts, for black-box (BB) and
white-box (WB) tests, following the Lab 5 pattern (barebone prompt, then
structured prompt). Paste each prompt into a **new** ChatGPT chat with memory
and custom instructions turned off. Record every session in `llm/sessions/`
using `SESSION_TEMPLATE.md`.

## Experimental design (read first)

**The only variable is the guidance.** Basic and refined prompts share the same
*output-format block* (`FORMAT-BB` or `FORMAT-WB` below), so every reply can be
scored by the same scripts. The refined prompt adds a role, the specification,
the required techniques and coverage criteria, and worked examples. The format
block says nothing about *what* to test.

**Scored artefact = the first reply.** For every group, the file scored is
ChatGPT's first answer to the prompt, saved as
`llm/generated/<group>/run<k>/test_*.py`. Only *mechanical* edits are allowed
before scoring (stripping prose or markdown fences, fixing an import line). Each
edit is recorded in the session log as effort. Expected values are never
changed.

**Follow-up turns are reported separately.** They are optional, the same for
basic and refined prompts, and saved as `llm/generated/<group>/run<k>_followup/`.
They answer the brief's "usefulness of consecutive replies" and never replace
the first-reply score.

**Budgets** (proposal: comparable budgets). These pairings are the headline
comparison:

| LLM group | Requested | Manual counterpart | Manual cases |
|---|---|---|---|
| P1/P2 black-box | 60 | `tests/blackbox/test_bb_partition_boundary.py` | 62 |
| P3/P4 white-box | 40 | `tests/whitebox/test_wb_helpers.py` + `test_wb_inline.py` | 49 |

The rest of the manual suite (decision tables, syntax-driven, pairwise, fuzz,
integration) is reported, but it is *not* part of the equal-budget comparison.

**Repeats.** Run every prompt 3 times (run1–run3) in fresh chats on the same
model and on the same day, so repeatability can be measured for both basic and
refined prompts. If time runs short, the minimum is 3 runs of each refined
prompt and 1 of each basic prompt.

---

## Shared format blocks (append verbatim to the matching prompt)

### FORMAT-BB

```
OUTPUT FORMAT (mandatory): Output ONLY one Python file, no prose. It must start with
    import pytest
    from cases import Case, params
    from oracle import render
    CASES = [
and contain one row per test case:
    Case("LLM-BB-01", "<technique>", "<description>", "<markdown input>", "<expected html>"),
where <expected html> has no newline between block tags and no trailing newline
(newlines inside a paragraph are kept). End the file with exactly:
    ]

    @pytest.mark.parametrize("case", params(CASES))
    def test_llm_bb(case, record):
        assert record(render(case.md)) == case.expected
```

### FORMAT-WB

```
OUTPUT FORMAT (mandatory): Output ONLY one pytest file, no prose. Start it with
    import pytest
    from mistune import helpers
    from mistune.core import InlineState
    from mistune.inline_parser import InlineParser
    def tokens(src, **flags):
        p = InlineParser(); st = InlineState({}); st.src = src
        for k, v in flags.items(): setattr(st, k, v)
        return p.render(st)
Name tests test_llm_wb_NN_<what>.
```

---

## P1-BB-basic

```
I am testing the Python Markdown parser Mistune version 3.1.4
(mistune.create_markdown(escape=False)). Write 60 black-box test cases for it.
<FORMAT-BB>
```

## P2-BB-refined

```
ROLE: You are an expert software tester applying black-box techniques from a
university software-testing course.

SYSTEM UNDER TEST: Mistune 3.1.4 Markdown-to-HTML converter, used as
mistune.create_markdown(escape=False). It is intended to follow CommonMark
0.31.2 (https://spec.commonmark.org/0.31.2/). Expected outputs MUST come from
the CommonMark spec, not from guessing what Mistune does.

SCOPE (4 categories, 15 cases each = 60):
 A. headings (ATX and setext), paragraphs, soft and hard line breaks
 B. emphasis, strong, code spans, links, images, autolinks
 C. ordered and unordered lists (nesting, loose or tight), block quotes
 D. backslash escapes, entities, malformed syntax, empty or boundary input

TECHNIQUES: For each category, list the input variables and their valid and
invalid equivalence classes, then derive cases with Equivalence Partitioning
(one per class) and Boundary Value Analysis (at, just below and just above each
boundary, e.g. heading level 6/7, 3/4 leading spaces, ordered-list number
9/10 digits). Put "EP" or "BVA" as the technique.

EXAMPLES:
    Case("LLM-BB-01", "BVA", "ATX level 6 (upper bound)", "###### T", "<h6>T</h6>"),
    Case("LLM-BB-02", "EP", "Loose list", "- a\n\n- b", "<ul><li><p>a</p></li><li><p>b</p></li></ul>"),
    Case("LLM-BB-03", "EP", "Hard break with two spaces", "a  \nb", "<p>a<br />\nb</p>"),
<FORMAT-BB>
```

## P3-WB-basic

```
Here is part of the source code of the Mistune 3.1.4 Markdown parser.
Write 40 white-box unit tests for it.
<paste llm/prompts/_snippet_helpers.py and _snippet_inline.py>
<FORMAT-WB>
```

## P4-WB-refined

```
ROLE: You are an expert in white-box (structural) unit testing.

CODE UNDER TEST (Mistune 3.1.4): helpers.parse_link_text, parse_link_label,
parse_link_href, parse_link_title, parse_link; InlineParser.parse_emphasis and
parse_codespan (call them through tokens(); flags: in_emphasis, in_strong,
in_link, in_image).
<paste llm/prompts/_snippet_helpers.py and _snippet_inline.py>

TASK: Write 40 pytest unit tests that together achieve:
 1. 100% statement and branch coverage of these functions;
 2. the loop in parse_link_text executed 0, 1 and at least 2 times;
 3. every decision outcome true and false (state which in the docstring,
    e.g. "D3=F: closing regex not found");
 4. every def-use pair of level, found and pos in parse_link_text.
Derive each expected value from the CommonMark 0.31.2 spec or the documented
purpose of the function, NOT by running the code. Assert exact return values.
<FORMAT-WB>
```

---

## Optional follow-up turns (identical for basic and refined; reported separately)

- **F1, gaps:** "These requirements are not met yet: <categories with too few
  cases / uncovered lines from the coverage report>. Add tests for them."
- **F2, correctness:** paste the cases rejected by `validate_llm.py` or
  `validate_wb.py`: "These expected values contradict CommonMark 0.31.2 (the
  reference output is shown). Re-derive them from the spec."

Save the full file after the last follow-up in `run<k>_followup/`. Report how
many rejected cases were fixed, how many new errors appeared, and the change in
coverage and mutation score versus the first reply.

## Scoring commands

```bash
.venv/bin/python scripts/validate_llm.py llm/generated/refined_bb/run1
```

```bash
.venv/bin/python scripts/validate_wb.py llm/generated/refined_wb/run1
```

```bash
.venv/bin/python scripts/consistency.py llm/generated/refined_bb
```

```bash
./run_all.sh --with-mutation
```

`validate_llm.py` checks the black-box first reply. `validate_wb.py` checks
white-box validity (see below). `consistency.py` measures repeatability across
run1–run3. `run_all.sh` then produces coverage, mutation score and redundancy
for every run folder.

## How white-box validity is assessed (`scripts/validate_wb.py`)

A unit test that asserts whatever Mistune returns always passes, so passing is
not evidence of correctness. Each LLM white-box test therefore gets three checks:

1. **Spec cross-check (automatic):** every Markdown string the test renders
   through Mistune is also rendered by the CommonMark reference. A *passing*
   test whose observed Mistune output differs from the reference is flagged
   **ENCODES-BUG**: it asserts behaviour the spec forbids.
2. **Fault-detection check (automatic):** each test is run against a fixed
   sample of 150 mutants (seed 322). A test that kills no mutant is flagged
   **WEAK**: its assertion does not constrain the code.
3. **Manual review (two team members, independently):** for every *failing*
   test, and for a sample of passing ones, decide whether the expected value
   follows from the spec or docstring (VALID), was copied from observed
   behaviour (TAUTOLOGICAL), or is wrong (INVALID). Disagreements are resolved
   together and the agreement rate is reported. `validate_wb.py` writes a CSV
   to fill in.
