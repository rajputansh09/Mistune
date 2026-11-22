# LLM groups: results (API run, 2026-11-22)

**Setup.** Model `gpt-5.4-mini-2026-03-17` (dated snapshot), OpenAI Chat Completions API, default sampling, one independent
request per run (single user message, no system prompt, no history = fresh chat). Prompts P1–P4 assembled verbatim from
`llm/prompts/PROMPTS.md` by `scripts/run_llm_api.py`. 4 prompts × 3 runs = 12 first replies, all scored. **No follow-up turns
were run.** Raw replies, API metadata and session logs are in `llm/sessions/`. Total cost: 10,947 input + 29,211 output tokens ≈ **$0.14**.
All 12 replies followed the file format: **0 mechanical edits** were needed and all were runnable as-is. Refined-WB run 3 delivered
39 test functions, not 40 (one missing slot); its parametrised tests expand to 57 executed cases.

## Black-box (60 requested; manual counterpart `manual_bb_ep`, 63 cases)

| Group | Valid / 60 (pre-execution) | Invalid: format-only / wrong HTML | Stmt % | Branch % | Mutation score | Defects exposed |
|---|---|---|---|---|---|---|
| Manual EP/BVA (63) | 63/63 | – | 80.7 | 62.3 | 58.6% | D10, D12 |
| P1 basic run1 | 53 | 5 / 2 | 80.3 | 60.6 | 52.0% | D4 (`[site](https://example.com/a_(b))`) |
| P1 basic run2 | 52 | 1 / 7 | 80.4 | 60.8 | 55.6% | – |
| P1 basic run3 | 40 | 17 / 3 | 82.0 | 63.1 | 33.0% | – |
| P2 refined run1 | 54 | 1 / 5 | 74.4 | 54.8 | 46.9% | **new: `&notanentity;`** |
| P2 refined run2 | 51 | 2 / 7 | 74.0 | 54.5 | 48.0% | **new: `&notanentity;`** |
| P2 refined run3 | 56 | 1 / 3 | 74.3 | 56.0 | 48.0% | **new: `&notanentity;`** |

*Format-only* = the expected HTML is correct once it goes through `oracle.norm` (the LLM put newlines between block tags despite
the format block). *Wrong HTML* = semantically wrong expected value (hallucinated). Validity is from `scripts/validate_llm.py`.

**Repeatability** (`scripts/consistency.py`, Jaccard overlap of inputs between runs): basic 0.08–0.11 (3 inputs in all 3 runs);
refined 0.25–0.27 (18 inputs in all 3 runs). Refined labelled its cases EP/BVA as asked (BVA 13/20/27 per run). Basic invented its own
labels and tested features outside the configuration (tables, strikethrough, task lists, definition lists).

## White-box (40 requested; manual counterpart `manual_wb_units`, 49 tests)

| Group | Pass / tests | Passing tests that kill 0 sampled mutants (WEAK) | Stmt % | Branch % | Mutation score |
|---|---|---|---|---|---|
| Manual WB units (49) | 48/49 (D13) | – | 60.4 | 44.2 | 39.4% |
| P3 basic run1 | 30/40 | 5 | 39.6 | 18.6 | 19.7% |
| P3 basic run2 | 26/40 | 4 | 39.9 | 18.6 | 17.2% |
| P3 basic run3 | 22/40 | 3 | 40.2 | 19.6 | 17.2% |
| P4 refined run1 | 14/40 | 1 | 39.9 | 19.1 | 8.8% |
| P4 refined run2 | 21/40 | 2 | 40.0 | 19.3 | 13.6% |
| P4 refined run3 | 27/57 | 0 | 40.0 | 19.6 | 17.4% |

ENCODES-BUG = 0 in every run. Failing WB tests are almost all assertion mismatches (not crashes): the prompt's `tokens()` helper works.
A typical refined failure expects inline tokens wrapped in a `paragraph` token, which the inline parser never produces, so the expected
value is wrong. **The failing WB tests still need the two-reviewer VALID / TAUTOLOGICAL / INVALID review** (`results/llm_*_wb_review.csv`)
to separate LLM errors from real defects.

## Mutation, union view (818 mutants, `results/mutation_analysis.md`)
Manual groups alone (this run): 722 killed (88.3%). All groups including LLM: **731 (89.4%)**, so the LLM groups add **9 kills** the
manual suites missed: M0092, M0225, M0231, M0246, M0317 (list_parser), M0449, M0464, M0550 (inline_parser), M0756 (block_parser). Unique kills by LLM groups: basic-BB run1 1, basic-WB run1 1, run2 2. Refined groups: 0.

## Headline findings for the report
1. **The LLM found a defect the manual suites missed** (refined, all 3 runs): `&notanentity;` → Mistune `<p>¬anentity;</p>`, while
   CommonMark requires `<p>&amp;notanentity;</p>`. Mistune decodes HTML5 legacy entities without the `;` (also `&copyright;` → `©right;`,
   `&ltfoo;` → `&lt;foo;`). Root cause: `mistune/util.py::unescape` is copied from `html.unescape`. **Still present in 3.4.0.** Candidate **D14**.
2. **Refined prompts mostly improved format compliance, not semantic correctness.** Wrong-HTML errors are similar (basic 2/7/3,
   refined 5/7/3). Refined is more repeatable (Jaccard ~0.25 vs ~0.1) and stays in scope.
3. **Basic BB had more coverage and mutation score than refined BB** (≈80% vs 74% stmt; 33–56% vs 47–48% mutation), because it ranged
   over more syntax (code blocks, HTML, plugin-like syntax). It's less consistent though (run3 dropped to 33%).
4. **White-box: the LLM is far below the manual suite** (≈40% vs 60% stmt; 9–20% vs 39% mutation). "Derive expected values from the
   spec, NOT by running the code" (P4) produced *more* failing tests (fewer usable tests → lower mutation score), but the passing ones
   are stronger (fewer WEAK).
5. No group matched the manual equal-budget suites on mutation score. The LLM groups' value is complementary (+9 kills, 1 new defect).

## Harness fixes made to run this (local, not yet pushed)
- `llm/generated/conftest.py` (new): `tests/conftest.py` does not apply under `llm/generated/`, so every LLM case errored with
  "fixture 'record' not found" and no results JSON was written.
- `mutation/mutate.py`: added a **baseline run**. Tests that fail on unmutated Mistune are deselected. Before this, any group containing
  a failing test "killed" every mutant (≈100% score for every LLM group), and `validate_wb.py`'s per-test kill counts were inflated
  (median 148/150). Node-id parsing now tolerates spaces in parametrised ids.
- `run_all.sh`: the variable `GROUPS` is a read-only bash builtin (the user's group IDs), so the mutation group list was silently
  replaced by a number. Renamed to `MUT_GROUPS`.
- `scripts/run_llm_api.py` (new): the API runner.
