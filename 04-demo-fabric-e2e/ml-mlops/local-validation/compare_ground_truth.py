from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = ROOT.parents[1]
GROUND_TRUTH = WORKSHOP_DIR / "02-demo-data" / "reference_out" / "ground_truth.json"
# Same escape hatch as run_local.py: must point at the same out/ dir it used.
_OUT_DIR = Path(os.environ.get("ML_MLOPS_LOCAL_OUT_DIR", str(ROOT / "local-validation" / "out")))
SUMMARY_PATH = _OUT_DIR / "validation-summary.json"
TABLE_DIR = _OUT_DIR / "tables"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_rows(truth: dict, split: str) -> int:
    return int(truth["ml"]["by_split"][split]["rows"])


def expected_positives(truth: dict, split: str) -> int:
    return int(truth["ml"]["by_split"][split]["positives"])


def add_row(rows: list[dict], metric: str, expected, got, ok: bool) -> None:
    rows.append({"metric": metric, "expected": expected, "got": got, "OK": "OK" if ok else "FAIL"})


def render_markdown(rows: list[dict]) -> str:
    lines = ["| metric | expected | got | OK |", "|---|---:|---:|---|"]
    for row in rows:
        lines.append(f"| {row['metric']} | {row['expected']} | {row['got']} | {row['OK']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare local validation outputs with ground_truth.json.")
    parser.add_argument("--markdown-out", help="Optional path for the Markdown comparison table")
    args = parser.parse_args()

    truth = read_json(GROUND_TRUTH)
    summary = read_json(SUMMARY_PATH)
    risk = pd.read_csv(TABLE_DIR / "ml__failure_risk_score.csv")
    drift = pd.read_csv(TABLE_DIR / "ml__drift_report.csv")

    rows: list[dict] = []
    features = summary["features"]
    train = summary["training_second"]["child_runs"]
    score = summary["score"]
    drift_summary = summary["drift"]

    add_row(rows, "features rows", truth["ml"]["rows"], features["rows"], features["rows"] == truth["ml"]["rows"])
    add_row(rows, "labelled rows", truth["ml"]["labelled_rows"], features["labelled_rows"], features["labelled_rows"] == truth["ml"]["labelled_rows"])
    for split in ("warmup", "train", "gap", "valid", "test", "unlabeled", "score"):
        got_rows = int(features["split_counts"][split]["rows"])
        got_pos = int(features["split_counts"][split]["positives"])
        add_row(rows, f"{split} rows", expected_rows(truth, split), got_rows, got_rows == expected_rows(truth, split))
        add_row(rows, f"{split} positives", expected_positives(truth, split), got_pos, got_pos == expected_positives(truth, split))

    add_row(rows, "score rows", truth["risk_scoring"]["assets_scored"], score["rows"], score["rows"] == truth["risk_scoring"]["assets_scored"])

    # Risk-band counts are only guaranteed for the frozen reference_out/ml_failure_risk_score.csv
    # (scenario-contract.md lines 363 and 419): a live re-run can shift a handful of assets across
    # band boundaries because pandas/scikit-learn versions change the HGB model's exact outputs
    # (Fabric Runtime 2.0 ships scikit-learn 1.6.1). So treat this as an approximate/informational
    # check (tolerance = 2 assets per band), not a hard pass/fail, and never assert exact band
    # counts against a live run elsewhere in this codebase.
    band_tolerance = 2
    actual_bands = {str(k): int(v) for k, v in risk["risk_band"].value_counts().sort_index().items()}
    for band in ("High", "Medium", "Low"):
        expected_band = truth["risk_scoring"]["bands"][band]
        got_band = actual_bands.get(band, 0)
        diff = abs(got_band - expected_band)
        add_row(
            rows,
            f"risk band {band} (approx, frozen reference only)",
            expected_band,
            got_band,
            diff <= band_tolerance,
        )

    add_row(rows, "drift combinations", truth["drift"]["combinations"], int(len(drift)), int(len(drift)) == truth["drift"]["combinations"])
    add_row(
        rows,
        "drift major",
        len(truth["drift"]["major_shift"]),
        drift_summary["major_shift_count"],
        drift_summary["major_shift_count"] == len(truth["drift"]["major_shift"]),
    )
    add_row(
        rows,
        "drift moderate",
        len(truth["drift"]["moderate_shift"]),
        drift_summary["moderate_shift_count"],
        drift_summary["moderate_shift_count"] == len(truth["drift"]["moderate_shift"]),
    )
    add_row(rows, "drift stable", 40, int((drift["status"] == "stable").sum()), int((drift["status"] == "stable").sum()) == 40)

    tolerance = 0.03
    metric_pairs = [
        ("prevalence valid_pr_auc", truth["ml"]["metrics_approximate"]["prevalence"]["valid"]["pr_auc"], train["prevalence"]["valid_pr_auc"]),
        ("prevalence test_pr_auc", truth["ml"]["metrics_approximate"]["prevalence"]["test"]["pr_auc"], train["prevalence"]["test_pr_auc"]),
        ("rule baseline valid_pr_auc", truth["ml"]["metrics_approximate"]["rule_baseline"]["valid"]["pr_auc"], train["rule_baseline"]["valid_pr_auc"]),
        ("rule baseline test_pr_auc", truth["ml"]["metrics_approximate"]["rule_baseline"]["test"]["pr_auc"], train["rule_baseline"]["test_pr_auc"]),
        ("logistic valid_pr_auc", truth["ml"]["metrics_approximate"]["logistic_regression"]["valid"]["pr_auc"], train["logistic_regression"]["valid_pr_auc"]),
        ("logistic test_pr_auc", truth["ml"]["metrics_approximate"]["logistic_regression"]["test"]["pr_auc"], train["logistic_regression"]["test_pr_auc"]),
        ("hgb valid_pr_auc", truth["ml"]["metrics_approximate"]["hist_gradient_boosting"]["valid"]["pr_auc"], train["hist_gradient_boosting"]["valid_pr_auc"]),
        ("hgb test_pr_auc", truth["ml"]["metrics_approximate"]["hist_gradient_boosting"]["test"]["pr_auc"], train["hist_gradient_boosting"]["test_pr_auc"]),
        (
            "hgb no fault valid_pr_auc",
            truth["ml"]["metrics_approximate"]["hist_gradient_boosting_no_fault_codes"]["valid"]["pr_auc"],
            train["hist_gradient_boosting_no_fault_codes"]["valid_pr_auc"],
        ),
        (
            "hgb no fault test_pr_auc",
            truth["ml"]["metrics_approximate"]["hist_gradient_boosting_no_fault_codes"]["test"]["pr_auc"],
            train["hist_gradient_boosting_no_fault_codes"]["test_pr_auc"],
        ),
    ]
    for name, expected, got in metric_pairs:
        add_row(rows, name, expected, got, abs(float(got) - float(expected)) <= tolerance)

    markdown = render_markdown(rows)
    print(markdown)
    if args.markdown_out:
        Path(args.markdown_out).write_text(markdown, encoding="utf-8", newline="\n")

    failed = [row for row in rows if row["OK"] != "OK"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
