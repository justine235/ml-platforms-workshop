from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_SPLIT_COUNTS = {
    "train": 28520,
    "test": 6111,
    "valid": 6591,
    "gap": 3830,
    "warmup": 3976,
    "unlabeled": 1584,
    "score": 264,
}
EXPECTED_ROWS = 50876
EXPECTED_LABELLED_ROWS = 49028
EXPECTED_POSITIVE_RATE = 0.0547


def ensure_dir(path: Path | str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_json(path: Path | str, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def first_existing(paths: list[Path]) -> Path:
    for candidate in paths:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("none of the candidate paths exist: %s" % [str(p) for p in paths])


def resolve_tabular_input(path: Path | str) -> Path:
    target = Path(path)
    if target.is_file():
        return target
    if not target.exists():
        raise FileNotFoundError(target)
    candidates = []
    for pattern in (
        "prepared_features.parquet",
        "prepared_features.csv",
        "prepared_features.csv.gz",
        "ml_asset_day_features.parquet",
        "ml_asset_day_features.csv",
        "ml_asset_day_features.csv.gz",
        "*.parquet",
        "*.csv",
        "*.csv.gz",
    ):
        candidates.extend(sorted(target.glob(pattern)))
    if not candidates:
        raise FileNotFoundError(f"no tabular file found under {target}")
    return candidates[0]


def read_table(path: Path | str) -> pd.DataFrame:
    source = resolve_tabular_input(path)
    suffixes = "".join(source.suffixes[-2:]) if len(source.suffixes) >= 2 else source.suffix
    if suffixes.endswith(".parquet"):
        return pd.read_parquet(source)
    if suffixes.endswith((".csv", ".csv.gz")):
        return pd.read_csv(source)
    raise ValueError(f"unsupported tabular input: {source}")


def write_table(df: pd.DataFrame, output_dir: Path | str, stem: str) -> dict[str, str]:
    out_dir = ensure_dir(output_dir)
    parquet_path = out_dir / f"{stem}.parquet"
    csv_path = out_dir / f"{stem}.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    return {"parquet": str(parquet_path), "csv": str(csv_path)}


def normalise_metrics(payload: dict[str, Any]) -> dict[str, float]:
    if "metrics" in payload and isinstance(payload["metrics"], dict):
        base = payload["metrics"]
    else:
        base = payload
    out: dict[str, float] = {}
    for key, value in base.items():
        if isinstance(value, (int, float)):
            out[key] = float(value)
    return out


def git_sha(default: str = "unknown") -> str:
    return (
        os.environ.get("GITHUB_SHA")
        or os.environ.get("BUILD_SOURCEVERSION")
        or os.environ.get("CI_COMMIT_SHA")
        or default
    )
