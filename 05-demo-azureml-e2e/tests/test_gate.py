from __future__ import annotations

from src.gate import gate_decision


def test_gate_passes_when_pr_auc_improves_and_precision_holds() -> None:
    challenger = {"test_pr_auc": 0.39, "test_precision_at_top5pct": 0.58}
    champion = {"test_pr_auc": 0.37, "test_precision_at_top5pct": 0.59}
    report = gate_decision(challenger, champion)
    assert report["approved"] is True


def test_gate_fails_when_precision_drops_too_far() -> None:
    challenger = {"test_pr_auc": 0.40, "test_precision_at_top5pct": 0.50}
    champion = {"test_pr_auc": 0.38, "test_precision_at_top5pct": 0.53}
    report = gate_decision(challenger, champion)
    assert report["approved"] is False
