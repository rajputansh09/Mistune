"""pytest hooks that record every executed test case for the report tables.

Each test case can expose metadata through a ``case`` parameter (a ``Case``
from ``cases.py``).  After the run, results/<group>_results.json holds one
row per test: ID, technique, description, input, expected, actual, verdict.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

_ROWS = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" and not (rep.when == "setup" and rep.outcome != "passed"):
        return
    case = getattr(item, "callspec", None)
    case = case.params.get("case") if case else None
    actual = getattr(item, "_actual", None)
    xfail = hasattr(rep, "wasxfail")
    verdict = {
        "passed": "PASS",
        "failed": "FAIL",
        "skipped": "FAIL (known defect)" if xfail else "SKIP",
    }[rep.outcome]
    if xfail and rep.outcome == "passed":
        verdict = "XPASS"
    _ROWS.append(
        {
            "nodeid": item.nodeid,
            "id": getattr(case, "id", item.name),
            "technique": getattr(case, "technique", _technique_from_marks(item)),
            "description": getattr(case, "desc", (item.function.__doc__ or "").strip().split("\n")[0]),
            "input": getattr(case, "md", None),
            "expected": getattr(case, "expected", None),
            "actual": actual,
            "verdict": verdict,
            "defect": getattr(case, "defect", None) or (rep.wasxfail.replace("reason: ", "") if xfail else None),
        }
    )


def _technique_from_marks(item):
    for m in item.iter_markers(name="technique"):
        return m.args[0]
    return ""


@pytest.fixture
def record(request):
    """Fixture a test calls with the actual output so the table can show it."""

    def _rec(actual):
        request.node._actual = actual
        return actual

    return _rec


def pytest_configure(config):
    config.addinivalue_line("markers", "technique(name): testing technique used")


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("RESULTS_FILE")
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(_ROWS, f, indent=1, ensure_ascii=False)
