# ECE 322 project: testing strategies for the Mistune Markdown parser

System under test: **Mistune 3.1.4** (pinned in `requirements.txt`), configured as
`mistune.create_markdown(escape=False)` for every test group.
Oracle: **CommonMark 0.31.2**, cross-checked with markdown-it-py 4.3.0.

## Layout

```
tests/
  oracle.py, cases.py, conftest.py     shared oracle, Case record, result recorder
  test_oracle_validation.py            checks our expected values against the reference
  blackbox/   EP+BVA, decision tables, syntax-driven, pairwise, random/fuzz/stress,
              Mistune-specific features
  whitebox/   statement/branch/loop/def-use unit tests (helpers, inline, block, list, renderer)
  integration/ top-down (stubs), bottom-up (drivers), big-bang
mutation/mutate.py      fault injection: value/decision/statement mutants
scripts/                evaluate.py, validate_llm.py (BB validity), validate_wb.py (WB validity),
                        consistency.py, analyze_mutation.py, make_tables.py, summary.py,
                        build_report.py (REPORT.md -> REPORT.pdf + page count)
llm/prompts/PROMPTS.md  ChatGPT prompts (basic and refined, BB and WB) + refinement protocol
llm/sessions/           one log per ChatGPT session (template provided)
llm/generated/          put ChatGPT test files here: <group>/run1/test_*.py
docs/                   test design, CFG and def-use analysis, defect log, test tables
reference/              CommonMark 0.31.2 spec examples (spec.json)
results/                generated metrics, tables, mutation data
```

## Run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
./run_all.sh
```

```bash
./run_all.sh --with-mutation
```

The first `run_all.sh` command runs tests, tables, metrics and the coverage report.
The `--with-mutation` form also runs mutation testing (about 30 minutes on 8 cores).

## Adding the ChatGPT groups

1. Follow `llm/prompts/PROMPTS.md`. Save the **first** reply as
   `llm/generated/<group>/run1/test_*.py`; follow-ups go in `run1_followup/`.
   The groups are `basic_bb`, `refined_bb`, `basic_wb` and `refined_wb`.
2. Fill in one `llm/sessions/*.md` log per session.
3. Check validity before running anything:

   ```bash
   .venv/bin/python scripts/validate_llm.py llm/generated/refined_bb/run1
   ```

   For white-box files use `scripts/validate_wb.py` instead:

   ```bash
   .venv/bin/python scripts/validate_wb.py llm/generated/refined_wb/run1
   ```

4. Run `./run_all.sh --with-mutation`. The LLM groups are picked up automatically,
   and `results/summary.md` and `results/mutation_analysis.md` then include them.
5. Check repeatability:

   ```bash
   .venv/bin/python scripts/consistency.py llm/generated/refined_bb
   ```
