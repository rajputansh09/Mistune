# LLM session log: <prompt id, e.g. P2-BB-refined run1>

| Field | Value |
|---|---|
| Team member | |
| Date / time | |
| Model and version (as shown in ChatGPT) | |
| Fresh chat? Memory or custom instructions off? | |
| Prompt file / text | |
| First reply saved as (SCORED) | `llm/generated/<group>/run<k>/test_*.py` |
| Follow-up turns used (F1/F2), saved as | `llm/generated/<group>/run<k>_followup/` (reported separately) |
| Wall-clock time: prompting + fixing (min) | |
| Raw reply saved as | `llm/sessions/<id>_raw.txt` |
| Test file saved as | `llm/generated/<group>/<run>/test_*.py` |

## Mechanical edits made to the FIRST reply before scoring
(only stripping prose or fences and fixing imports are allowed; expected values are never changed. Count each one.)

| # | Problem | Fix |
|---|---|---|

## Observations
- Did it follow the requested technique(s)? Did it give the requested number of cases?
- Hallucinations: invented APIs, wrong CommonMark claims
- Follow-ups (scored separately): how many rejected cases F2 fixed, how many new errors appeared, and the change in coverage and mutation score
