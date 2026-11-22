"""Give LLM-generated test files the same harness as tests/ (the `record` fixture and the
results-recording hooks). tests/conftest.py only applies to files under tests/, so without this
every LLM case errors with "fixture 'record' not found" and no results JSON is written.

Loaded under a different module name so it cannot clash with tests/conftest.py.
Do not run tests/ and llm/generated/ in the same pytest session (hooks would be registered twice).
"""
import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "conftest.py")
_spec = importlib.util.spec_from_file_location("_shared_tests_conftest", _path)
_shared = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_shared)

pytest_runtest_makereport = _shared.pytest_runtest_makereport
pytest_configure = _shared.pytest_configure
pytest_sessionfinish = _shared.pytest_sessionfinish
record = _shared.record
