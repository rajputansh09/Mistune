"""Test-case record used by the table-driven black-box suites."""
from dataclasses import dataclass
from typing import Optional

import pytest


@dataclass(frozen=True)
class Case:
    id: str  # e.g. BB-EP-H01
    technique: str  # EP, BVA, DT, SYN, PW, ...
    desc: str
    md: str
    expected: str  # normalised expected HTML (from CommonMark 0.31.2 spec)
    defect: Optional[str] = None  # defect ID if this case exposes a known defect
    mistune_specific: bool = False  # expected value comes from Mistune docs, not CommonMark

    def __repr__(self):  # keeps pytest ids readable
        return self.id


def params(cases):
    """Turn Case objects into pytest params; known defects become strict xfails
    so the suite stays green but every defect is still executed and reported."""
    out = []
    for c in cases:
        marks = []
        if c.defect:
            marks.append(pytest.mark.xfail(reason=c.defect, strict=True))
        out.append(pytest.param(c, id=c.id, marks=marks))
    return out
