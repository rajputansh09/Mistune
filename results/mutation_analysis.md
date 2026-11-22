Valid mutants S = 818   (stillborn: 0)

## Mutation score by group
| blackbox | 612 | 74.8% | 26 timeouts |
| whitebox | 649 | 79.3% | 14 timeouts |
| integration | 408 | 49.9% | 13 timeouts |
| union of groups | 723 | 88.4% | |

## Score by mutation operator class (union of groups)
| DECISION | 187/205 | 91.2% |
| STATEMENT | 378/419 | 90.2% |
| VALUE | 158/194 | 81.4% |

## Score by module, per group
| module | mutants | blackbox | whitebox | integration | union |
| block_parser.py | 246 | 67% | 80% | 44% | 85% |
| helpers.py | 99 | 91% | 95% | 45% | 96% |
| inline_parser.py | 234 | 79% | 79% | 49% | 91% |
| list_parser.py | 210 | 71% | 69% | 60% | 84% |
| util.py | 29 | 79% | 100% | 52% | 100% |

## Unique kills (killed by this group only)
| blackbox | 40 |
| whitebox | 104 |
| integration | 1 |

## Capture-recapture: N1(BB)=612, N2(WB)=649, N12=539 -> estimated detectable faults N = N1*N2/N12 = 737; found by BB or WB = 722; mutants in program = 818

## Mills fault seeding: S=818 seeded (mutants), s=723 detected, n=9 indigenous defects found
   estimated indigenous faults N = n*S/s = 10.2; estimated remaining = 1.2
   confidence that N <= 9: C = 0.29
   confidence that N <= 10: C = 0.256
   confidence that N <= 11: C = 0.226
   confidence that N <= 10: C = 0.256

## Surviving mutants (95): candidates for equivalent mutants or missing tests
   M0010 helpers.py:115 parse_link_text  [DECISION] Lt -> LtE
   M0029 helpers.py:126 parse_link_text  [STATEMENT] break -> continue
   M0053 helpers.py:147 parse_link_href  [STATEMENT] delete statement
   M0092 helpers.py:189 parse_link  [STATEMENT] delete statement
   M0173 list_parser.py:37 parse_list  [VALUE] 1 -> 0
   M0191 list_parser.py:113 _parse_list_item  [DECISION] If cond -> not cond
   M0208 list_parser.py:110 _parse_list_item  [STATEMENT] delete statement
   M0209 list_parser.py:113 _parse_list_item  [DECISION] Lt -> LtE
   M0211 list_parser.py:115 _parse_list_item  [STATEMENT] delete statement
   M0217 list_parser.py:136 _parse_list_item  [STATEMENT] delete statement
   M0222 list_parser.py:172 _parse_list_item  [STATEMENT] delete statement
   M0225 list_parser.py:181 _parse_list_item  [STATEMENT] delete statement
   M0227 list_parser.py:113 _parse_list_item  [VALUE] 3 -> 4
   M0228 list_parser.py:113 _parse_list_item  [VALUE] 3 -> 2
   M0229 list_parser.py:117 _parse_list_item  [VALUE] 1 -> 2
   M0230 list_parser.py:117 _parse_list_item  [VALUE] 1 -> 0
   M0231 list_parser.py:131 _parse_list_item  [STATEMENT] delete statement
   M0236 list_parser.py:144 _parse_list_item  [STATEMENT] delete statement
   M0240 list_parser.py:158 _parse_list_item  [DECISION] If cond -> not cond
   M0244 list_parser.py:168 _parse_list_item  [DECISION] And -> Or
   M0246 list_parser.py:181 _parse_list_item  [VALUE] False -> True
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
   M0317 list_parser.py:253 _clean_list_item_text  [STATEMENT] delete statement
   M0319 list_parser.py:247 _clean_list_item_text  [VALUE] 1 -> 0
   M0342 inline_parser.py:104 parse_escape  [VALUE] 0 -> 1
   M0365 inline_parser.py:121 parse_link  [STATEMENT] return x -> return None
   M0378 inline_parser.py:179 parse_link  [STATEMENT] delete statement
   M0386 inline_parser.py:140 parse_link  [DECISION] GtE -> Gt
   M0449 inline_parser.py:248 parse_emphasis  [STATEMENT] return x -> return None
   M0455 inline_parser.py:269 parse_emphasis  [STATEMENT] delete statement
   M0464 inline_parser.py:251 parse_emphasis  [STATEMENT] return x -> return None
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
   M0550 inline_parser.py:368 precedence_scan  [DECISION] If cond -> not cond
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
   M0756 block_parser.py:326 extract_block_quote  [VALUE] 0 -> 1
   M0758 block_parser.py:328 extract_block_quote  [VALUE] 3 -> 4
   M0759 block_parser.py:328 extract_block_quote  [VALUE] 3 -> 2
   M0782 block_parser.py:413 parse_raw_html  [STATEMENT] delete statement
   M0797 block_parser.py:417 parse_raw_html  [DECISION] If cond -> not cond
   M0804 block_parser.py:417 parse_raw_html  [DECISION] In -> NotIn
   M0812 block_parser.py:438 parse_raw_html  [DECISION] And -> Or
   M0815 block_parser.py:415 parse_raw_html  [VALUE] 2 -> 3
   M0816 block_parser.py:415 parse_raw_html  [VALUE] 2 -> 1
