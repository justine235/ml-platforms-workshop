from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import fleet_ml_core as core
from common import (
    EXPECTED_LABELLED_ROWS,
    EXPECTED_POSITIVE_RATE,
    EXPECTED_ROWS,
    EXPECTED_SPLIT_COUNTS,
    read_table,
    write_json,
    write_table,
)


def validate_features(df: pd.DataFrame, strict: bool = True) -> dict[str, object]:
    expected_columns = ["erp_asset_id", "obs_date", *core.FEATURES, core.LABEL, core.SPLIT_COL]
    missing = [column for column in expected_columns if column not in df.columns]
    if missing:
        raise ValueError(f"input data is missing required columns: {missing}")

    summary = {
        "rows": len(df),
        "columns": list(df.columns),
        "feature_count": len(core.FEATURES),
        "split_counts": {k: int(v) for k, v in df[core.SPLIT_COL].value_counts().sort_index().to_dict().items()},
        "labelled_rows": int(df[core.LABEL].notna().sum()),
        "positive_rate": round(float(df[core.LABEL].dropna().mean()), 4),
    }
    if strict:
        if len(df) != EXPECTED_ROWS:
            raise ValueError(f"expected {EXPECTED_ROWS} rows, found {len(df)}")
        if summary["feature_count"] != 42:
            raise ValueError(f"expected 42 features, found {summary['feature_count']}")
        if summary["split_counts"] != EXPECTED_SPLIT_COUNTS:
            raise ValueError(f"unexpected split counts: {summary['split_counts']}")
        if summary["labelled_rows"] != EXPECTED_LABELLED_ROWS:
            raise ValueError(f"expected {EXPECTED_LABELLED_ROWS} labelled rows, found {summary['labelled_rows']}")
        if abs(summary["positive_rate"] - EXPECTED_POSITIVE_RATE) > 0.0005:
            raise ValueError(
                f"expected positive rate near {EXPECTED_POSITIVE_RATE:.4f}, found {summary['positive_rate']:.4f}"
            )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and prepare the fleet feature table for AML jobs.")
    parser.add_argument("--input-path", required=True, help="CSV/CSV.GZ/Parquet file or folder containing ml.asset_day_features")
    parser.add_argument("--output-dir", required=True, help="Folder where the prepared dataset and contract summary are written")
    parser.add_argument("--allow-noncanonical", action="store_true", help="Skip the hard row-count and split-count checks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    features = read_table(args.input_path)
    summary = validate_features(features, strict=not args.allow_noncanonical)
    written = write_table(features, args.output_dir, "prepared_features")
    summary.update(
        {
            "output_files": written,
            "feature_columns": list(core.FEATURES),
            "label_column": core.LABEL,
            "split_column": core.SPLIT_COL,
        }
    )
    write_json(Path(args.output_dir) / "data_contract.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
