from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import normalise_metrics, read_json, write_json


def gate_decision(challenger: dict[str, float], champion: dict[str, float] | None) -> dict[str, Any]:
    if not champion:
        return {
            "approved": True,
            "reason": "No champion metrics were supplied; allow the first candidate to register.",
            "deltas": {},
        }
    challenger_pr = challenger["test_pr_auc"]
    champion_pr = champion["test_pr_auc"]
    challenger_precision = challenger["test_precision_at_top5pct"]
    champion_precision = champion["test_precision_at_top5pct"]
    pr_delta = round(challenger_pr - champion_pr, 4)
    precision_delta = round(challenger_precision - champion_precision, 4)
    approved = challenger_pr >= champion_pr + 0.01 and challenger_precision >= champion_precision - 0.02
    return {
        "approved": approved,
        "reason": (
            "Approved: challenger cleared the +0.01 PR-AUC threshold and stayed within the precision guardrail."
            if approved
            else "Rejected: challenger did not beat the champion strongly enough on PR-AUC or precision@top5%."
        ),
        "deltas": {
            "test_pr_auc": pr_delta,
            "test_precision_at_top5pct": precision_delta,
        },
        "rule": "challenger test_pr_auc >= champion + 0.01 and precision@top5% not worse by more than 0.02",
    }


def build_report(challenger_payload: dict[str, Any], champion_payload: dict[str, Any] | None) -> dict[str, Any]:
    challenger_metrics = normalise_metrics(challenger_payload)
    champion_metrics = normalise_metrics(champion_payload or {})
    decision = gate_decision(challenger_metrics, champion_metrics or None)
    return {
        "challenger_metrics": challenger_metrics,
        "champion_metrics": champion_metrics or None,
        **decision,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply the fleet AML champion/challenger gate.")
    parser.add_argument("--challenger-json", required=True, help="Evaluation JSON for the challenger run")
    parser.add_argument("--champion-json", help="Optional champion metrics JSON")
    parser.add_argument("--output-path", required=True, help="Where to write the gate report JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    challenger = read_json(args.challenger_json)
    champion = read_json(args.champion_json) if args.champion_json else None
    report = build_report(challenger, champion)
    write_json(Path(args.output_path), report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
