# ChatGPT prompts for the LLM groups

Four prompts: basic and refined, for black-box (BB) and white-box (WB).
They follow the Lab 5 pattern: a barebone prompt first, then a structured
prompt. Paste each one into a new ChatGPT chat with no memory or custom
instructions. Record every session in `llm/sessions/` (see `SESSION_TEMPLATE.md`).

The test budgets match the manual counterparts, so the comparison is fair:
- BB: 60 cases (manual counterpart: `tests/blackbox/test_bb_partition_boundary.py`, 62 cases)
- WB: 40 tests (manual counterpart: `tests/whitebox/test_wb_helpers.py`, `test_wb_inline.py` and the list-parser part of `test_wb_block_list.py`)

---

## P1-BB-basic (barebone)

```
I am testing the Python Markdown parser Mistune version 3.1.4
(mistune.create_markdown(escape=False)). Write 60 black-box test cases for it
as pytest tests.
```

## P2-BB-refined (structured)

```
ROLE: You are an expert software tester applying black-box techniques from a
university software-testing course.

SYSTEM UNDER TEST: Mistune 3.1.4, a Python Markdown-to-HTML converter, used as
    import mistune
    md = mistune.create_markdown(escape=False)
It is intended to follow the CommonMark 0.31.2 specification
(https://spec.commonmark.org/0.31.2/). Expected outputs MUST come from the
CommonMark spec, not from guessing what Mistune does.

SCOPE (4 categories, 15 cases each = 60 cases):
 A. headings (ATX and setext), paragraphs, soft and hard line breaks
 B. inline formatting: emphasis, strong, code spans, links, images, autolinks
 C. ordered and unordered lists (including nesting and loose or tight), block quotes
 D. backslash escapes, entities, unusual or malformed syntax, empty or boundary input

TECHNIQUES: For every category, first list the input variables and their
equivalence classes (valid and invalid), then derive cases with
 - Equivalence Partitioning (one case per class)
 - Boundary Value Analysis (at, just below, just above each boundary, e.g.
   heading level 6 or 7, 3 or 4 leading spaces, ordered-list number 9 or 10 digits)
Label each case EP or BVA.

OUTPUT FORMAT: Output ONLY a Python file. Each case is one Case(...) row:
    Case(id, technique, description, markdown_input, expected_html)
expected_html is NORMALISED: no newline between block tags, no trailing
newline, newlines inside paragraphs kept. Example rows:

    Case("LLM-BB-01", "BVA", "ATX level 6 (upper bound)", "###### T", "<h6>T</h6>"),
    Case("LLM-BB-02", "EP", "Loose list", "- a\n\n- b", "<ul><li><p>a</p></li><li><p>b</p></li></ul>"),
    Case("LLM-BB-03", "EP", "Hard break with two spaces", "a  \nb", "<p>a<br />\nb</p>"),

End the file with exactly:

    @pytest.mark.parametrize("case", params(CASES))
    def test_llm_bb(case, record):
        assert record(render(case.md)) == case.expected

and start it with:
    import pytest
    from cases import Case, params
    from oracle import render
    CASES = [
```

### Refinement turns (send in the same chat, record each one)

- R1, if the output contains anything other than the file: "Output only the
  Python file, no explanation."
- R2, if any category has fewer than 15 cases: "Category X has only N cases;
  add boundary cases until it has 15."
- R3, after our validator reports invalid expected values (scripts/validate_llm.py):
  "These expected outputs contradict CommonMark 0.31.2: <ids + reference output>.
  Re-derive them from the spec." Record how many it fixed.

---

## P3-WB-basic (barebone)

```
Here is part of the source code of the Mistune 3.1.4 Markdown parser.
Write 40 white-box unit tests for it with pytest.

<paste llm/prompts/_snippet_helpers.py, _snippet_inline.py, _snippet_list.py>
```

## P4-WB-refined (structured)

```
ROLE: You are an expert in white-box (structural) unit testing.

CODE UNDER TEST (Mistune 3.1.4; import paths shown):
  from mistune import helpers        -> parse_link_text, parse_link_label,
                                         parse_link_href, parse_link_title, parse_link
  from mistune import list_parser as lp -> _get_list_bullet, _compile_list_item_pattern,
                                         _compile_continue_width, _clean_list_item_text,
                                         _is_loose_list
  InlineParser methods parse_emphasis and parse_codespan, driven through:
      from mistune.core import InlineState
      from mistune.inline_parser import InlineParser
      def tokens(src, **flags):
          p = InlineParser(); st = InlineState({}); st.src = src
          for k, v in flags.items(): setattr(st, k, v)   # in_emphasis, in_strong, in_link, in_image
          return p.render(st)

<paste the three snippet files>

TASK: Write 40 pytest unit tests that together achieve:
 1. 100% statement and 100% branch coverage of the functions above;
 2. every loop executed 0 times, once, and at least twice (parse_link_text);
 3. every decision outcome true and false (state it in the docstring, for
    example "D3=F: closing regex not found");
 4. for parse_link_text, every def-use pair of the variables level, found and pos.
Each test asserts the exact return value, not just "is not None".
Name tests test_llm_wb_NN_<what>, and put the covered branch or path in the docstring.
Output ONLY the Python file. Add `pytestmark = pytest.mark.technique("WB")`.
```

### Refinement turns

- R1: give the coverage report lines that are still missing:
  "Lines X–Y and branch A->B are not covered; add tests for them."
- R2: give the failing assertions: "These tests fail on Mistune 3.1.4: <pytest
  output>. Is the test or the code wrong? Fix the test only if its expected value is wrong."

---

## Repeatability protocol

Run P2-BB-refined and P4-WB-refined three times each (run1, run2, run3), each
in a fresh chat on the same model, and save them as
`llm/generated/refined_bb/run{1,2,3}/test_llm_bb.py`. Then run
`python scripts/consistency.py llm/generated/refined_bb` to compute:
- overlap of test inputs between runs (Jaccard),
- spread of validity, coverage and mutation score across runs.
