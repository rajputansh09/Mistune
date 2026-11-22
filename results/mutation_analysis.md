Valid mutants S = 818   (stillborn: 0)

## Mutation score by group
| group | killed by a failing assertion | killed by hang (timeout) | total killed | score |
|---|---|---|---|---|
| blackbox | 586 | 26 | 612 | 74.8% |
| whitebox | 633 | 14 | 647 | 79.1% |
| integration | 395 | 13 | 408 | 49.9% |
| llm_basic_bb_run1 | 412 | 13 | 425 | 52.0% |
| llm_basic_bb_run2 | 444 | 11 | 455 | 55.6% |
| llm_basic_bb_run3 | 268 | 2 | 270 | 33.0% |
| llm_basic_wb_run1 | 158 | 3 | 161 | 19.7% |
| llm_basic_wb_run2 | 138 | 3 | 141 | 17.2% |
| llm_basic_wb_run3 | 138 | 3 | 141 | 17.2% |
| llm_refined_bb_run1 | 373 | 11 | 384 | 46.9% |
| llm_refined_bb_run2 | 379 | 14 | 393 | 48.0% |
| llm_refined_bb_run3 | 380 | 13 | 393 | 48.0% |
| llm_refined_wb_run1 | 71 | 1 | 72 | 8.8% |
| llm_refined_wb_run2 | 107 | 4 | 111 | 13.6% |
| llm_refined_wb_run3 | 138 | 4 | 142 | 17.4% |
| union of groups | 709 | 22 | 731 | 89.4% |

Score excluding hangs (union): 86.7%

## Score by mutation operator class (union of groups)
| DECISION | 188/205 | 91.7% |
| STATEMENT | 383/419 | 91.4% |
| VALUE | 160/194 | 82.5% |

## Score by module, per group
| module | mutants | blackbox | whitebox | integration | llm_basic_bb_run1 | llm_basic_bb_run2 | llm_basic_bb_run3 | llm_basic_wb_run1 | llm_basic_wb_run2 | llm_basic_wb_run3 | llm_refined_bb_run1 | llm_refined_bb_run2 | llm_refined_bb_run3 | llm_refined_wb_run1 | llm_refined_wb_run2 | llm_refined_wb_run3 | union |
| block_parser.py | 246 | 67% | 80% | 44% | 38% | 50% | 30% | 0% | 0% | 0% | 26% | 26% | 28% | 0% | 0% | 0% | 86% |
| helpers.py | 99 | 91% | 95% | 45% | 46% | 46% | 46% | 80% | 55% | 68% | 47% | 47% | 43% | 70% | 35% | 69% | 97% |
| inline_parser.py | 234 | 79% | 79% | 49% | 67% | 64% | 59% | 34% | 37% | 32% | 56% | 60% | 59% | 0% | 32% | 32% | 91% |
| list_parser.py | 210 | 71% | 69% | 60% | 56% | 59% | 0% | 0% | 0% | 0% | 60% | 61% | 61% | 0% | 0% | 0% | 86% |
| util.py | 29 | 79% | 100% | 52% | 38% | 52% | 41% | 10% | 0% | 0% | 48% | 48% | 45% | 10% | 0% | 0% | 100% |

## Unique kills (killed by this group only)
| blackbox | 19 |
| whitebox | 84 |
| integration | 1 |
| llm_basic_bb_run1 | 1 |
| llm_basic_bb_run2 | 0 |
| llm_basic_bb_run3 | 0 |
| llm_basic_wb_run1 | 1 |
| llm_basic_wb_run2 | 2 |
| llm_basic_wb_run3 | 0 |
| llm_refined_bb_run1 | 0 |
| llm_refined_bb_run2 | 0 |
| llm_refined_bb_run3 | 0 |
| llm_refined_wb_run1 | 0 |
| llm_refined_wb_run2 | 0 |
| llm_refined_wb_run3 | 0 |

## Illustration only: lecture-10 estimators (see limits below)
Limits: (1) the mutant population is KNOWN (S), so capture-recapture estimates a quantity
we already know; (2) black-box and white-box suites exercise the same code and are not
independent samplers, which biases N downward; (3) Mills assumes seeded faults are as hard
to find as real ones, but single-token mutants are simpler than real defects.

## Capture-recapture: N1(BB)=612, N2(WB)=647, N12=538 -> estimated detectable faults N = N1*N2/N12 = 736; found by BB or WB = 721; mutants in program = 818

## Mills fault seeding: S=818 seeded (mutants), s=731 detected, n=11 indigenous defects found
   estimated indigenous faults N = n*S/s = 12.3; estimated remaining = 1.3
   confidence that N <= 11: C = 0.258
   confidence that N <= 12: C = 0.231
   confidence that N <= 13: C = 0.206
   confidence that N <= 12: C = 0.231

## Surviving mutants (87): candidates for equivalent mutants or missing tests
   M0010 helpers.py:115 parse_link_text  [DECISION] Lt -> LtE
   M0029 helpers.py:126 parse_link_text  [STATEMENT] break -> continue
   M0053 helpers.py:147 parse_link_href  [STATEMENT] delete statement
   M0173 list_parser.py:37 parse_list  [VALUE] 1 -> 0
   M0191 list_parser.py:113 _parse_list_item  [DECISION] If cond -> not cond
   M0208 list_parser.py:110 _parse_list_item  [STATEMENT] delete statement
   M0209 list_parser.py:113 _parse_list_item  [DECISION] Lt -> LtE
   M0211 list_parser.py:115 _parse_list_item  [STATEMENT] delete statement
   M0217 list_parser.py:136 _parse_list_item  [STATEMENT] delete statement
   M0222 list_parser.py:172 _parse_list_item  [STATEMENT] delete statement
   M0227 list_parser.py:113 _parse_list_item  [VALUE] 3 -> 4
   M0228 list_parser.py:113 _parse_list_item  [VALUE] 3 -> 2
   M0229 list_parser.py:117 _parse_list_item  [VALUE] 1 -> 2
   M0230 list_parser.py:117 _parse_list_item  [VALUE] 1 -> 0
   M0236 list_parser.py:144 _parse_list_item  [STATEMENT] delete statement
   M0240 list_parser.py:158 _parse_list_item  [DECISION] If cond -> not cond
   M0244 list_parser.py:168 _parse_list_item  [DECISION] And -> Or
   M0247 list_parser.py:110 _parse_list_item  [VALUE] 1 -> 2
   M0248 list_parser.py:110 _parse_list_item  [VALUE] 1 -> 0
   M0258 list_parser.py:158 _parse_list_item  [DECISION] Eq -> NotEq
   M0265 list_parser.py:115 _parse_list_item  [VALUE] 1 -> 0
   M0285 list_parser.py:210 _compile_list_item_pattern  [DECISION] Gt -> GtE
   M0287 list_parser.py:210 _compile_list_item_pattern  [VALUE] 3 -> 4
   M0288 list_parser.py:210 _compile_list_item_pattern  [VALUE] 3 -> 2
   M0291 list_parser.py:221 _compile_continue_width  [STATEMENT] delete statement
   M0299 list_parser.py:234 _compile_continue_width  [STATEMENT] delete statement
   M0300 list_parser.py:220 _compile_continue_width  [VALUE] 3 -> 4
   M0301 list_parser.py:220 _compile_continue_width  [VALUE] 3 -> 2
   M0313 list_parser.py:246 _clean_list_item_text  [DECISION] If cond -> not cond
   M0314 list_parser.py:247 _clean_list_item_text  [STATEMENT] delete statement
   M0315 list_parser.py:250 _clean_list_item_text  [STATEMENT] delete statement
   M0319 list_parser.py:247 _clean_list_item_text  [VALUE] 1 -> 0
   M0342 inline_parser.py:104 parse_escape  [VALUE] 0 -> 1
   M0365 inline_parser.py:121 parse_link  [STATEMENT] return x -> return None
   M0371 inline_parser.py:146 parse_link  [STATEMENT] return x -> return None
   M0378 inline_parser.py:179 parse_link  [STATEMENT] delete statement
   M0386 inline_parser.py:140 parse_link  [DECISION] GtE -> Gt
   M0455 inline_parser.py:269 parse_emphasis  [STATEMENT] delete statement
   M0467 inline_parser.py:269 parse_emphasis  [VALUE] True -> False
   M0469 inline_parser.py:273 parse_emphasis  [STATEMENT] delete statement
   M0472 inline_parser.py:277 parse_emphasis  [STATEMENT] delete statement
   M0473 inline_parser.py:278 parse_emphasis  [STATEMENT] delete statement
   M0481 inline_parser.py:273 parse_emphasis  [VALUE] True -> False
   M0482 inline_parser.py:277 parse_emphasis  [VALUE] True -> False
   M0483 inline_parser.py:278 parse_emphasis  [VALUE] True -> False
   M0503 inline_parser.py:303 parse_codespan  [DECISION] And -> Or
   M0523 inline_parser.py:359 parse  [STATEMENT] return x -> return None
   M0526 inline_parser.py:335 parse  [DECISION] Lt -> LtE
   M0545 inline_parser.py:354 parse  [VALUE] 0 -> -1
   M0558 inline_parser.py:381 precedence_scan  [STATEMENT] delete statement
   M0569 inline_parser.py:369 precedence_scan  [STATEMENT] delete statement
   M0572 inline_parser.py:390 precedence_scan  [DECISION] Lt -> LtE
   M0595 block_parser.py:132 parse_indent_code  [STATEMENT] delete statement
   M0597 block_parser.py:134 parse_indent_code  [STATEMENT] delete statement
   M0600 block_parser.py:129 parse_indent_code  [STATEMENT] return x -> return None
   M0617 block_parser.py:156 parse_fenced_code  [DECISION] And -> Or
   M0623 block_parser.py:173 parse_fenced_code  [DECISION] And -> Or
   M0626 block_parser.py:179 parse_fenced_code  [STATEMENT] delete statement
   M0628 block_parser.py:155 parse_fenced_code  [VALUE] 0 -> 1
   M0629 block_parser.py:155 parse_fenced_code  [VALUE] 0 -> -1
   M0643 block_parser.py:196 parse_atx_heading  [VALUE] 1 -> 2
   M0653 block_parser.py:210 parse_setex_heading  [STATEMENT] delete statement
   M0663 block_parser.py:212 parse_setex_heading  [VALUE] 1 -> 2
   M0682 block_parser.py:255 parse_ref_link  [STATEMENT] delete statement
   M0690 block_parser.py:282 parse_ref_link  [STATEMENT] delete statement
   M0699 block_parser.py:274 parse_ref_link  [STATEMENT] delete statement
   M0703 block_parser.py:294 extract_block_quote  [STATEMENT] delete statement
   M0715 block_parser.py:294 extract_block_quote  [VALUE] 3 -> 4
   M0716 block_parser.py:294 extract_block_quote  [VALUE] 3 -> 2
   M0721 block_parser.py:308 extract_block_quote  [STATEMENT] delete statement
   M0734 block_parser.py:353 extract_block_quote  [STATEMENT] delete statement
   M0739 block_parser.py:328 extract_block_quote  [STATEMENT] delete statement
   M0740 block_parser.py:329 extract_block_quote  [STATEMENT] delete statement
   M0747 block_parser.py:306 extract_block_quote  [VALUE] 0 -> 1
   M0749 block_parser.py:308 extract_block_quote  [VALUE] 3 -> 4
   M0750 block_parser.py:308 extract_block_quote  [VALUE] 3 -> 2
   M0752 block_parser.py:335 extract_block_quote  [STATEMENT] delete statement
   M0754 block_parser.py:353 extract_block_quote  [VALUE] 3 -> 4
   M0755 block_parser.py:353 extract_block_quote  [VALUE] 3 -> 2
   M0758 block_parser.py:328 extract_block_quote  [VALUE] 3 -> 4
   M0759 block_parser.py:328 extract_block_quote  [VALUE] 3 -> 2
   M0782 block_parser.py:413 parse_raw_html  [STATEMENT] delete statement
   M0797 block_parser.py:417 parse_raw_html  [DECISION] If cond -> not cond
   M0804 block_parser.py:417 parse_raw_html  [DECISION] In -> NotIn
   M0812 block_parser.py:438 parse_raw_html  [DECISION] And -> Or
   M0815 block_parser.py:415 parse_raw_html  [VALUE] 2 -> 3
   M0816 block_parser.py:415 parse_raw_html  [VALUE] 2 -> 1
