from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from b4_fleet_demo import load_eval_cases, score_structured_result


def _case(case_id: str):
    return next(case for case in load_eval_cases() if case.case_id == case_id)


def test_scoring_accepts_correct_structured_result() -> None:
    result = score_structured_result(
        _case("Q01"),
        {"total": 316, "Active": 300, "Retired": 10, "Disposed": 6},
    )
    assert result.passed is True


def test_scoring_rejects_wrong_structured_result() -> None:
    result = score_structured_result(
        _case("Q21"),
        {"High": 8, "Medium": 7, "Low": 249, "top_sites": ["FR-PAR-01"], "top_site_high_count": 3},
    )
    assert result.passed is False


def test_scoring_accepts_refusal_for_unanswerable() -> None:
    result = score_structured_result(_case("Q26"), {"answerable": False, "refused": True})
    assert result.passed is True
