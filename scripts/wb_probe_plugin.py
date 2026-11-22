"""pytest plugin used by validate_wb.py: records every Markdown string a test
renders through mistune.Markdown, plus the test outcome."""
import json
import os

import pytest

_LOG = {}
_CUR = [None]


def pytest_configure(config):
    import importlib

    mm = importlib.import_module("mistune.markdown")  # the attribute is shadowed by a function

    orig = mm.Markdown.parse

    def parse(self, s, state=None):
        out = orig(self, s, state)
        if _CUR[0] and isinstance(out[0], str):
            _LOG.setdefault(_CUR[0], {"rendered": []})["rendered"].append(
                {"src": s, "html": out[0], "escape": getattr(self.renderer, "_escape", None),
                 "plugins": bool(getattr(self, "_plugin_names", None))})
        return out

    mm.Markdown.parse = parse


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    _CUR[0] = item.nodeid
    yield
    _CUR[0] = None


def pytest_runtest_logreport(report):
    if report.when == "call" or report.outcome != "passed":
        _LOG.setdefault(report.nodeid, {"rendered": []})["outcome"] = report.outcome


def pytest_sessionfinish(session):
    with open(os.environ["WB_PROBE_FILE"], "w") as f:
        json.dump(_LOG, f)
