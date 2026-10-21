from __future__ import annotations

from notebooks.notebook_common import gate_decision


def test_gate_promotes_when_pr_auc_improves_and_precision_holds() -> None:
    result = gate_decision(
        {"test_pr_auc": 0.38, "test_precision_at_top5pct": 0.40},
        {"test_pr_auc": 0.40, "test_precision_at_top5pct": 0.39},
    )
    assert result["decision"] == "promote"
    assert result["passed"] is True


def test_gate_holds_when_precision_drops_too_far() -> None:
    result = gate_decision(
        {"test_pr_auc": 0.38, "test_precision_at_top5pct": 0.40},
        {"test_pr_auc": 0.41, "test_precision_at_top5pct": 0.35},
    )
    assert result["decision"] == "hold"
    assert result["rule"]["passed_precision_guardrail"] is False
