from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

import fleet_ml_core as core
from common import write_json, write_table

SENSOR_LIMITS = {
    "engine_temp_c": (0.0, 150.0),
    "oil_pressure_kpa": (0.0, 800.0),
    "hydraulic_pressure_bar": (0.0, 450.0),
    "vibration_mm_s": (0.0, 30.0),
    "fuel_rate_lph": (0.0, 200.0),
    "load_pct": (0.0, 100.0),
}


def parse_timestamp(value: object) -> pd.Timestamp:
    if isinstance(value, (int, float)):
        return pd.to_datetime(int(value), unit="ms", utc=True)
    return pd.to_datetime(value, utc=True)


def iter_jsonl(paths: Iterable[Path]) -> Iterable[dict]:
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def load_run_readings(folder: Path, dim_asset: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    rows = []
    for item in iter_jsonl(sorted(folder.glob("*.jsonl"))):
        payload = item.get("payload") or {}
        event_ts = parse_timestamp(item["ts"])
        ingest_ts = pd.to_datetime(item["ingest_ts"], utc=True)
        rows.append(
            {
                "event_id": item["event_id"],
                "device_id": item.get("device_id"),
                "event_ts": event_ts,
                "ingest_ts": ingest_ts,
                "engine_state": payload.get("engine_state"),
                "engine_temp_c": payload.get("engine_temp_c"),
                "oil_pressure_kpa": payload.get("oil_pressure_kpa"),
                "hydraulic_pressure_bar": payload.get("hydraulic_pressure_bar"),
                "vibration_mm_s": payload.get("vibration_mm_s"),
                "fuel_rate_lph": payload.get("fuel_rate_lph"),
                "load_pct": payload.get("load_pct"),
            }
        )
    df = pd.DataFrame(rows)
    df = df.sort_values(["event_id", "ingest_ts"], ascending=[True, True], kind="stable").drop_duplicates("event_id", keep="first")
    for column, (low, high) in SENSOR_LIMITS.items():
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df.loc[(df[column] < low) | (df[column] > high), column] = pd.NA
    frame = df.merge(dim_asset[["device_id", "equipment_class"]], on="device_id", how="inner")
    frame = frame[frame["engine_state"].eq("RUN")]
    frame = frame[frame["event_ts"].between(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"), inclusive="both")]
    return frame


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute PSI drift from reference and current telematics JSONL folders.")
    parser.add_argument("--reference-dir", required=True, help="Folder with telematics JSONL files for the reference window")
    parser.add_argument("--current-dir", required=True, help="Folder with drift JSONL files for the current window")
    parser.add_argument("--dim-asset-path", required=True, help="dim_asset.csv path used to map device_id to equipment_class")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--reference-start", default="2026-09-01T00:00:00Z")
    parser.add_argument("--reference-end", default="2026-09-30T23:59:59Z")
    parser.add_argument("--current-start", default="2026-10-01T00:00:00Z")
    parser.add_argument("--current-end", default="2026-10-14T23:59:59Z")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dim_asset = pd.read_csv(args.dim_asset_path, dtype={"erp_asset_id": str, "device_id": str})
    reference = load_run_readings(Path(args.reference_dir), dim_asset, args.reference_start, args.reference_end)
    current = load_run_readings(Path(args.current_dir), dim_asset, args.current_start, args.current_end)
    drift = core.psi_table(reference, current)
    drift = drift.sort_values(["equipment_class", "sensor"], kind="stable").reset_index(drop=True)
    written = write_table(drift, args.output_dir, "drift_report")
    summary = {
        "rows": len(drift),
        "major_count": int((drift["status"] == "major").sum()),
        "major_pairs": drift.loc[drift["status"] == "major", ["equipment_class", "sensor", "psi"]].to_dict(orient="records"),
        "output_files": written,
    }
    write_json(Path(args.output_dir) / "drift_summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
