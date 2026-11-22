"""Validates the hand-written test oracle (expected outputs) against an
independent CommonMark reference implementation (markdown-it-py).

This is NOT a test of Mistune: it guards against mistakes in our expected
values, so that a failing black-box test means a Mistune defect rather than
an oracle error.  Mistune-specific expectations are excluded."""
import importlib
import pkgutil

import pytest

import blackbox
from oracle import reference

ALL = []
for mod in pkgutil.iter_modules(blackbox.__path__):
    m = importlib.import_module("blackbox." + mod.name)
    ALL += [c for c in getattr(m, "CASES", []) if not c.mistune_specific]


@pytest.mark.parametrize("case", ALL, ids=[c.id for c in ALL])
def test_expected_matches_reference(case):
    assert reference(case.md) == case.expected
