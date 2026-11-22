# LLM groups: results (API run, 2026-11-22)

**Setup.** Model `gpt-5.4-mini-2026-03-17` (dated snapshot), OpenAI Chat Completions API, default sampling, one independent
request per run (single user message, no system prompt, no history = fresh chat). Prompts P1–P4 assembled verbatim from
`llm/prompts/PROMPTS.md` by `scripts/run_llm_api.py`. 4 prompts × 3 runs = 12 first replies, all scored. Follow-up turns F1 + F2
were then run on run1 of each group and scored separately (section *Consecutive replies* below). Raw replies, API metadata and session logs
are in `llm/sessions/`. Cost: first replies 10,947 in + 29,211 out ≈ $0.14; follow-ups 41,769 in + 22,371 out ≈ $0.13 (at list price).
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
value is wrong.

### White-box validity review (two independent reviewers)
**What was reviewed:** all **117 failing** LLM white-box tests, plus a random sample of **5 passing tests per run** (seed 322), so 147 tests.
Each one was labelled VALID / TAUTOLOGICAL / INVALID against the code under test (including the regexes the LLM never saw) and CommonMark 0.31.2.
**Reviewers:** reviewer 1 was Claude Opus 5.5. Reviewer 2 was GPT-6.2 Sol via opencode, given the same evidence but **blind** to reviewer 1's labels.
*In the report, state that both reviewers were AI models, not team members.*
**Agreement:** 145/147 (**98.6%**), Cohen's κ ≈ **0.96**. The two disagreements were resolved against the code: one passing test was
re-labelled INVALID because it passes by coincidence, and one stays VALID because it's misnamed but correct.
Per-test verdicts and reasons are in `results/llm_*_wb_review.csv`; the summary is in `results/llm_wb_review_summary.json`; reviewer 2's raw
output is in `results/llm_wb_review_reviewer2_raw.txt`.

| Group | Failing: INVALID / VALID | Passing sample: VALID / INVALID | Main causes of INVALID |
|---|---|---|---|
| P3 basic (3 runs) | 40 / **2** | 13 / 2 | wrong start position 23, incomplete token list 10, missing title whitespace 3, block-mode href 2 |
| P4 refined (3 runs) | 75 / 0 | 14 / 1 | wrong start position 36, `paragraph` wrapper 13, missing title whitespace 11, incomplete token list 6, off-by-one end 3 |

- **No TAUTOLOGICAL tests.** Even the basic prompt's passing expected values all follow from the spec or contract. The LLM didn't just copy Mistune.
- **Only 2 of 117 failures are real Mistune defects**: basic run2 #18 and basic run3 #17, `parse_link_title(" (title)")` → `None`.
  CommonMark §6.3 allows parenthesised titles, so this is the **known D5**. White-box LLM tests found **no new** defects.
- **Refined prompts more often had the right *intent* but a wrong precondition.** Four refined tests aim at D5 but call without the leading
  whitespace the regex needs. That regex was not in the prompt, which is a prompt-design lesson: give the model the preconditions too.
- **The dominant error is an API misunderstanding, not spec knowledge.** Callers must pass `pos` just *after* `[` / `(`. Nothing in the
  snippet's docstrings says so, and the LLM guessed wrong in 59 of 115 invalid failures.

## Mutation, union view (818 mutants, `results/mutation_analysis.md`)
Manual groups alone (this run): 722 killed (88.3%). All groups including LLM: **731 (89.4%)**, so the LLM groups add **9 kills** the
manual suites missed: M0092, M0225, M0231, M0246, M0317 (list_parser), M0449, M0464, M0550 (inline_parser), M0756 (block_parser). Unique kills by LLM groups: basic-BB run1 1, basic-WB run1 1, run2 2. Refined groups: 0.

## Consecutive replies (follow-ups F1 + F2 on run1; scored separately, never replaces first-reply scores)
`scripts/run_llm_followup.py` replays [prompt → first reply (verbatim) → F1 → reply → F2 → reply] in one conversation, with the same
wording for basic and refined. The file after F2 is in `llm/generated/<group>/run1_followup/`; details are in
`results/llm_followup_analysis.json` and `llm/sessions/P*_run1_followup.md`.
- **F1 (gaps):** BB was told which parser functions its inputs never executed; WB was told which source lines in scope were never executed.
- **F2 (correctness):** BB got each rejected case with the CommonMark reference output. WB got each INVALID test with the reviewers' reason;
  Mistune's actual value was deliberately withheld.

| Group | First reply → after F1+F2 | Valid (BB) / pass (WB) | Stmt % / Branch % | Mutation score |
|---|---|---|---|---|
| P1 basic BB | 60 → 66 cases | 53/60 → 62/66 | 80.3/60.6 → 81.7/62.1 | 52.0% → **58.4%** |
| P2 refined BB | 60 → 68 cases | 54/60 → 65/68 | 74.4/54.8 → 81.9/63.6 | 46.9% → **57.6%** |
| P3 basic WB | 40 → 50 tests | 30/40 → 40/50 | 39.6/18.6 → 40.5/19.6 | 19.7% → 21.6% |
| P4 refined WB | 40 → 44 tests | 14/40 → 26/44 | 39.9/19.1 → 40.4/19.8 | 8.8% → **19.7%** |

- **F1 closed most gaps.** Refined BB executed 4 of the 5 functions it was pointed to (fenced code, reference links, HTML blocks,
  inline HTML); basic BB executed 1 of 2. In-scope WB lines never executed: basic 12 → 2, refined 8 → 3 (of 110). For refined BB this
  closed the coverage gap to basic and to the manual suite (≈82% stmt).
- **F2 on black-box "fixed" every rejected case** (basic 7/7, refined 6/6). The reference was shown, though, so this mostly measures
  willingness to copy a given answer, not spec understanding. F2 also **introduced new invalid cases**: basic 4 (3 format-only, 1 wrong
  HTML), refined 3 (all format-only, in the new F1 cases). So the model didn't generalise the normalised-format rule from the feedback.
- **F2 on white-box only half-worked without the answer:**
  - Basic: 7 of 10 flagged tests now pass, but 7 new failures appeared.
  - Refined: only 10 of 26 flagged tests now pass. 16 are still wrong despite being told the exact reason (e.g. "pos must point just
    after '['"), and 2 new failures appeared.
  - I checked every new failure (single reviewer). All of them repeat known error types: pos 0 on `[`, a valid block destination expected
    to fail, text tokens expected merged, an empty label expected to be rejected (but Mistune must return `''` for collapsed references
    like `[foo][]`). **No new defects.**
- **One consecutive reply broke the file:** the refined-WB F2 reply had a SyntaxError (a stray `}`), so it wasn't runnable as-is. One
  mechanical fix was logged in `llm/sessions/P4_run1_followup.md`. The F1 reply had parsed fine.
- Defects: the follow-ups kept the earlier finds (D4 in basic, `&notanentity;` in refined) and **found nothing new**.

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
6. **Consecutive replies help coverage more than correctness.** Gap feedback (F1) lifted BB mutation scores to ≈58%, level with the
   manual EP/BVA suite (58.6%). Correctness feedback (F2) only "worked" when the right answer was shown. Without it (WB), 16 of 26
   flagged refined tests stayed wrong, every round introduced new errors, and one reply wasn't even runnable.

## Harness fixes made to run this
- `llm/generated/conftest.py` (new): `tests/conftest.py` does not apply under `llm/generated/`, so every LLM case errored with
  "fixture 'record' not found" and no results JSON was written.
- `mutation/mutate.py`: added a **baseline run**. Tests that fail on unmutated Mistune are deselected. Before this, any group containing
  a failing test "killed" every mutant (≈100% score for every LLM group), and `validate_wb.py`'s per-test kill counts were inflated
  (median 148/150). Node-id parsing now tolerates spaces in parametrised ids.
- `run_all.sh`: the variable `GROUPS` is a read-only bash builtin (the user's group IDs), so the mutation group list was silently
  replaced by a number. Renamed to `MUT_GROUPS`.
- `scripts/run_llm_api.py` (new): the API runner.
- `scripts/run_llm_followup.py` (new): the follow-up (F1 + F2) runner.
