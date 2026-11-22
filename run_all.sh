#!/usr/bin/env bash
# Reproduce every result in the report.  Usage: ./run_all.sh [--with-mutation]
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -x "$PY" ] || { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; }

echo "== 1. Full suite (incl. slow stress tests) + test-case tables"
RESULTS_FILE=results/full_results.json $PY -m pytest tests -q || true
$PY scripts/make_tables.py

echo "== 2. Per-group metrics (coverage, efficiency, redundancy, oracle validity)"
$PY scripts/evaluate.py blackbox    tests/blackbox    > /dev/null
$PY scripts/evaluate.py whitebox    tests/whitebox    > /dev/null
$PY scripts/evaluate.py integration tests/integration > /dev/null
$PY scripts/evaluate.py manual_all  tests/blackbox tests/whitebox tests/integration > /dev/null
for d in llm/generated/*/run*; do
  [ -n "$(ls "$d"/test_*.py 2>/dev/null)" ] || continue
  name="llm_$(basename "$(dirname "$d")")_$(basename "$d")"
  case "$d" in
    *_wb/*) $PY scripts/validate_wb.py "$d" "$name" > /dev/null ;;
    *)      $PY scripts/validate_llm.py "$d" > "results/${name}_validity.json" ;;
  esac
  $PY scripts/evaluate.py "$name" "$d" > /dev/null
done
$PY scripts/summary.py

echo "== 3. HTML coverage report -> results/htmlcov/index.html"
COVERAGE_FILE=results/.coverage.html $PY -m pytest tests/blackbox tests/whitebox tests/integration -q -m "not slow" \
   --cov --cov-config=.coveragerc --cov-report=html:results/htmlcov > /dev/null || true

if [ "${1:-}" = "--with-mutation" ]; then
  echo "== 4. Mutation testing (~15-30 min)"
  GROUPS="blackbox=tests/blackbox whitebox=tests/whitebox integration=tests/integration"
  for d in llm/generated/*/run*; do
    [ -n "$(ls "$d"/test_*.py 2>/dev/null)" ] && GROUPS="$GROUPS llm_$(basename "$(dirname "$d")")_$(basename "$d")=$d"
  done
  $PY mutation/mutate.py --groups $GROUPS --timeout 15 --out results/mutation_all.json
  $PY scripts/analyze_mutation.py results/mutation_all.json > results/mutation_analysis.md
fi
