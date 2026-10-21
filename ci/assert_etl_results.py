"""Fail unless the local ETL run really used Delta and every ground-truth check passed.

run_local.py falls back to Parquet when the Delta jar cannot be resolved, and each script only reports its own view,
so CI asserts the combined result here. Run it from anywhere, after run_local.py and compare_ground_truth.py:

    python ci/assert_etl_results.py --spark 4.1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ETL = Path(__file__).resolve().parents[1] / "04-demo-fabric-e2e" / "etl" / "local-validation"
EXPECTED_CHECKS = 39


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spark", help="expected Spark major.minor, for example 3.5 or 4.1")
    args = parser.parse_args()

    summary = read_json(ETL / "artifacts" / "validation-summary.json")
    compare = read_json(ETL / "results" / "ground-truth-compare.json")
    problems: list[str] = []

    if args.spark:
        import pyspark

        if not pyspark.__version__.startswith(args.spark + "."):
            problems.append(f"pyspark {pyspark.__version__} installed, expected {args.spark}.x")
        print(f"pyspark {pyspark.__version__}")

    if summary.get("status") != "ok" or summary.get("mismatches"):
        problems.append(f"run_local.py: status {summary.get('status')!r}, mismatches {summary.get('mismatches')}")
    for label, document in (("run_local.py", summary), ("compare_ground_truth.py", compare)):
        if document.get("storage_format") != "delta":
            problems.append(f"{label}: storage_format {document.get('storage_format')!r}, expected 'delta'")

    rows = compare.get("rows", [])
    failed = [row["metric"] for row in rows if not row.get("ok")]
    if failed or not compare.get("all_ok"):
        problems.append("ground-truth checks failed: " + ", ".join(failed))
    if len(rows) != EXPECTED_CHECKS:
        problems.append(f"{len(rows)} ground-truth checks ran, expected {EXPECTED_CHECKS} (is the drift data missing?)")

    print(f"storage_format={summary.get('storage_format')} checks={len(rows)} failed={len(failed)}")
    for problem in problems:
        print("FAIL:", problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
