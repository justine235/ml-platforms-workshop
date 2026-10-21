from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "foundry-agent"))

from b4_fleet_demo import load_eval_cases, score_structured_result
from eval_harness import run_harness
from guardrails import GuardrailViolation, enforce_readonly_sql


def _case(case_id: str):
    return next(case for case in load_eval_cases() if case.case_id == case_id)


def test_oracle_agent_scores_perfectly() -> None:
    payload = run_harness("oracle")
    assert payload["summary"]["pass_rate"] == 1.0


def test_naive_agent_fails() -> None:
    payload = run_harness("naive")
    assert payload["summary"]["pass_rate"] == 0.0


def test_guardrails_block_write_sql() -> None:
    with pytest.raises(GuardrailViolation):
        enforce_readonly_sql("DELETE FROM gold.fact_recon_exception")


def test_scoring_accepts_expected_counts() -> None:
    result = score_structured_result(
        _case("Q21"),
        {"High": 9, "Medium": 7, "Low": 248, "top_sites": ["FR-PAR-01"], "top_site_high_count": 3},
    )
    assert result.passed is True
