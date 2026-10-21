"""ETL to ML integration check: run the ML notebooks on the Delta tables the ETL notebooks really wrote.

Optional and local only (plain Python, no Spark, no Fabric tenant). run_local.py feeds the ML notebooks pandas tables built from the raw
CSVs; this check feeds them the tables written by the ETL kit's notebooks (default: ../etl/local-validation/artifacts). The tables are
read through their Delta log (active files only) and converted the way spark.table(...).toPandas() does it in Fabric (date ->
datetime.date, array<string> -> list, timestamps -> datetime64[ns]), then compared with the frozen contract in 02-demo-data/reference_out.

    python local-validation/integration_etl_to_ml.py
    python local-validation/integration_etl_to_ml.py --tables-root <a Tables, lh_fleet or artifacts folder>
    python local-validation/integration_etl_to_ml.py --features-only     # nb_04 + nb_07 only
    python local-validation/integration_etl_to_ml.py --out <short folder> # tables, artifacts and MLflow store

Exit code: 0 = every check passed, 1 = a check failed, 2 = tables not found. On a deeply nested checkout pass a short --out folder
(or set ML_MLOPS_LOCAL_OUT_DIR, like run_local.py) so MLflow artifact paths stay below the Windows MAX_PATH limit.

Feature comparison rule. Keys, labels, counts and the NaN pattern must be identical. nb_04 rounds the 42 features to 4 decimals and the
ETL daily table holds Spark means whose last float bits differ from pandas', so a handful of values that sit exactly on a rounding tie
(about 0.03 % of the cells) land one unit (1e-4) away from the reference. That is accepted (TIE_TOLERANCE); a larger difference, or more
than 0.1 % of the cells above 1e-6, fails.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time
import traceback
from pathlib import Path
from urllib.parse import unquote

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_DIR = ROOT.parents[1]
REFERENCE_DIR = WORKSHOP_DIR / "02-demo-data" / "reference_out"
DEFAULT_TABLES_ROOT = ROOT.parent / "etl" / "local-validation" / "artifacts"

TABLE_NAMES = (
    "silver.telemetry",
    "silver.telemetry_drift",
    "gold.fact_telemetry_daily",
    "gold.fact_work_order",
    "gold.dim_asset",
    "bronze.fault_code_catalog",
)
TIE_TOLERANCE = 1e-4 + 1e-9
STRICT_TOLERANCE = 1e-6
MAX_TIE_CELL_FRACTION = 0.001
METRIC_TOLERANCE = 0.03
BAND_TOLERANCE = 2

_COMMIT_FILE = re.compile(r"^\d{20}\.json$")


# --- Delta reader ---------------------------------------------------------------------------------------------------------------------


def resolve_tables_root(path: Path) -> Path:
    """Accept a Tables, lh_fleet or artifacts folder and return the Tables folder."""
    path = Path(path)
    for candidate in (path, path / "Tables", path / "lh_fleet" / "Tables"):
        if (candidate / "silver" / "telemetry" / "_delta_log").is_dir():
            return candidate
    raise FileNotFoundError(
        "no Delta tables found under %s (expected <root>/silver/telemetry/_delta_log; run the ETL validation first or pass --tables-root)" % path
    )


def _replay_log(log_dir: Path) -> tuple[dict[str, dict], dict]:
    """Replay a Delta log (latest checkpoint, then newer JSON commits): returns ({relative path: add action}, latest metaData)."""
    active: dict[str, dict] = {}
    metadata: dict = {}
    start = 0
    marker = log_dir / "_last_checkpoint"
    if marker.exists():
        import pyarrow.parquet as pq

        version = int(json.loads(marker.read_text(encoding="utf-8"))["version"])
        parts = sorted(log_dir.glob("%020d.checkpoint*.parquet" % version))
        for part in parts:
            names = pq.read_schema(part).names
            table = pq.read_table(part, columns=[c for c in ("add", "metaData") if c in names])
            for add in table.column("add").to_pylist():
                if add:
                    active[add["path"]] = add
            if "metaData" in table.column_names:
                metadata = next((m for m in table.column("metaData").to_pylist() if m), metadata)
        if parts:
            start = version + 1
    commits = sorted(p for p in log_dir.iterdir() if _COMMIT_FILE.match(p.name))
    if start == 0 and (not commits or int(commits[0].stem) != 0):
        raise ValueError("the Delta log in %s does not start at version 0 and has no usable checkpoint" % log_dir.parent.name)
    for commit in commits:
        if int(commit.stem) < start:
            continue
        for line in commit.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            action = json.loads(line)
            if "add" in action:
                active[action["add"]["path"]] = action["add"]
            elif "remove" in action:
                active.pop(action["remove"]["path"], None)
            elif "metaData" in action:
                metadata = action["metaData"]
    return active, metadata


def _to_spark_like_pandas(table) -> pd.DataFrame:
    import pyarrow as pa

    try:
        frame = table.to_pandas(date_as_object=True, coerce_temporal_nanoseconds=True)
    except TypeError:  # pyarrow < 13 has no coerce_temporal_nanoseconds
        frame = table.to_pandas(date_as_object=True)
    for field in table.schema:
        if pa.types.is_list(field.type) or pa.types.is_large_list(field.type):
            frame[field.name] = frame[field.name].map(lambda cell: None if cell is None else list(cell))
    return frame


def read_delta_table(table_dir: Path) -> pd.DataFrame:
    """Rows of a Delta table as spark.table(...).toPandas() returns them: only the files that are active in the log, never a blind glob."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table_dir = Path(table_dir)
    active, metadata = _replay_log(table_dir / "_delta_log")
    if not metadata:
        raise ValueError("no metaData action in the Delta log of %s" % table_dir.name)
    if metadata.get("partitionColumns"):
        raise NotImplementedError("partitioned Delta tables are not supported by this reader (%s)" % table_dir.name)
    if dict(metadata.get("configuration") or {}).get("delta.columnMapping.mode", "none") != "none":
        raise NotImplementedError("Delta column mapping is not supported by this reader (%s)" % table_dir.name)
    if any(add.get("deletionVector") for add in active.values()):
        raise NotImplementedError("Delta deletion vectors are not supported by this reader (%s)" % table_dir.name)
    if not active:
        columns = [field["name"] for field in json.loads(metadata["schemaString"])["fields"]]
        return pd.DataFrame({name: [] for name in columns})
    tables = [pq.read_table(table_dir / unquote(relative)) for relative in sorted(active)]
    return _to_spark_like_pandas(pa.concat_tables(tables))


def load_tables(tables_root: Path) -> dict[str, pd.DataFrame]:
    return {name: read_delta_table(tables_root.joinpath(*name.split("."))) for name in TABLE_NAMES}


# --- checks ---------------------------------------------------------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, check: str, ok: bool, detail: str = "") -> bool:
        self.rows.append({"check": check, "ok": bool(ok), "detail": detail})
        return bool(ok)

    def skip(self, check: str, why: str) -> None:
        self.rows.append({"check": check, "ok": None, "detail": why})

    @property
    def failed(self) -> int:
        return sum(1 for row in self.rows if row["ok"] is False)

    def print(self) -> None:
        width = max(len(row["check"]) for row in self.rows)
        for row in self.rows:
            tag = {True: "PASS", False: "FAIL", None: "SKIP"}[row["ok"]]
            print("  %s  %-*s  %s" % (tag, width, row["check"], row["detail"]))


def fault_code_cells_equivalent(telemetry: pd.DataFrame, catalog: pd.DataFrame) -> tuple[bool, str]:
    """spark.table().toPandas() gives list cells or numpy arrays for array<string>, depending on the Arrow setting: both must work."""
    from notebooks.shared.fleet_reference_pipeline import fault_occurrences

    if "fault_codes" not in telemetry.columns:
        return False, "silver.telemetry has no fault_codes column"
    from_lists = fault_occurrences(telemetry, catalog).reset_index(drop=True)
    arrays = telemetry.assign(fault_codes=telemetry["fault_codes"].map(lambda cell: None if cell is None else np.asarray(cell, dtype=object)))
    from_arrays = fault_occurrences(arrays, catalog).reset_index(drop=True)
    return from_lists.equals(from_arrays), "%d fault occurrences, list cells == ndarray cells" % len(from_lists)


def compare_features(features: pd.DataFrame, reference: pd.DataFrame) -> dict:
    from notebooks.notebook_common import compare_frames_with_tolerance
    from notebooks.shared.fleet_ml_core import FEATURES, LABEL

    keys = ["erp_asset_id", "obs_date", "split"]
    frame_check = compare_frames_with_tolerance(features, reference, key_cols=keys, numeric_cols=[*FEATURES, LABEL], tolerance=TIE_TOLERANCE)
    result: dict = {"frame_check": frame_check, "keys_equal": frame_check.get("reason") != "key_mismatch"}
    if not result["keys_equal"]:
        return result
    left = features.sort_values(keys, kind="stable").reset_index(drop=True)
    right = reference.sort_values(keys, kind="stable").reset_index(drop=True)
    a = left[FEATURES].to_numpy(dtype=float)
    e = right[FEATURES].to_numpy(dtype=float)
    delta = np.abs(np.nan_to_num(a, nan=0.0) - np.nan_to_num(e, nan=0.0))
    over = delta > STRICT_TOLERANCE
    result.update(
        rows=int(len(left)),
        cells=int(delta.size),
        max_abs_diff=float(delta.max()),
        cells_over_1e6=int(over.sum()),
        nan_mismatches=int((np.isnan(a) != np.isnan(e)).sum()),
        label_mismatches=int((left[LABEL].fillna(-1).to_numpy() != right[LABEL].fillna(-1).to_numpy()).sum()),
        columns_over_1e6={name: int(count) for name, count in zip(FEATURES, over.sum(axis=0), strict=True) if count},
    )
    return result


def check_features(report: Report, summary: dict, context, truth: dict, tables: dict[str, pd.DataFrame]) -> bool:
    from notebooks import nb_04_features

    equivalent, detail = fault_code_cells_equivalent(tables["silver.telemetry"], tables["bronze.fault_code_catalog"])
    ok = report.add("fault_codes: list == ndarray cells", equivalent, detail)

    features_summary = nb_04_features.run(params={"validate_against_reference": False}, context=context)
    summary["features"] = features_summary
    expected = truth["ml"]
    expected_splits = {name: {"rows": split["rows"], "positives": split["positives"]} for name, split in expected["by_split"].items()}
    counts_ok = (
        features_summary["rows"] == expected["rows"]
        and features_summary["labelled_rows"] == expected["labelled_rows"]
        and features_summary["positive_rate_labelled"] == expected["positive_rate_labelled"]
        and features_summary["split_counts"] == expected_splits
    )
    ok &= report.add(
        "nb_04 counts == contract",
        counts_ok,
        "%d rows, %d labelled, positive rate %.4f, %d splits" % (
            features_summary["rows"],
            features_summary["labelled_rows"],
            features_summary["positive_rate_labelled"],
            len(features_summary["split_counts"]),
        ),
    )

    comparison = compare_features(context.read_table("ml.asset_day_features"), context.read_reference("ml_asset_day_features"))
    summary["feature_comparison"] = comparison
    if not comparison["keys_equal"]:
        return report.add("nb_04 keys + labels == reference", False, "key mismatch: %s" % comparison["frame_check"].get("details")) and ok
    ok &= report.add(
        "nb_04 keys + labels == reference",
        comparison["label_mismatches"] == 0 and not comparison["frame_check"]["exact_failures"],
        "%d keys equal, %d label mismatches, exact columns %s" % (
            comparison["rows"],
            comparison["label_mismatches"],
            "equal" if not comparison["frame_check"]["exact_failures"] else comparison["frame_check"]["exact_failures"],
        ),
    )
    fraction = comparison["cells_over_1e6"] / comparison["cells"]
    features_ok = (
        comparison["frame_check"]["ok"]
        and comparison["nan_mismatches"] == 0
        and comparison["max_abs_diff"] <= TIE_TOLERANCE
        and fraction <= MAX_TIE_CELL_FRACTION
    )
    ok &= report.add(
        "nb_04 42 features ~ reference",
        features_ok,
        "max abs diff %.1e; %d of %d cells (%.3f %%) above 1e-6 (rounding ties); NaN mismatches %d" % (
            comparison["max_abs_diff"],
            comparison["cells_over_1e6"],
            comparison["cells"],
            100 * fraction,
            comparison["nan_mismatches"],
        ),
    )
    return ok


def check_drift(report: Report, summary: dict, context, truth: dict) -> bool:
    from notebooks import nb_07_drift_monitor

    drift_summary = nb_07_drift_monitor.run(context=context)
    summary["drift"] = drift_summary
    expected = truth["drift"]
    wanted = (len(expected["major_shift"]), len(expected["moderate_shift"]), expected["combinations"])
    rows = len(context.read_table("ml.drift_report"))
    found = (drift_summary["major_shift_count"], drift_summary["moderate_shift_count"], rows)
    comparison = drift_summary["reference_comparison"]
    ok = report.add(
        "nb_07 drift == reference",
        comparison.get("ok") is True and comparison.get("max_abs_diff", 1.0) <= STRICT_TOLERANCE,
        "max abs diff %s over %d combinations" % (comparison.get("max_abs_diff"), rows),
    )
    ok &= report.add(
        "nb_07 major / moderate / stable",
        found == wanted,
        "%d / %d / %d (contract %d / %d / %d)" % (found[0], found[1], found[2] - found[0] - found[1], wanted[0], wanted[1], wanted[2] - wanted[0] - wanted[1]),
    )
    return ok


def check_chain(report: Report, summary: dict, context, truth: dict) -> None:
    from notebooks import nb_05_train_mlflow, nb_06_register_score, nb_08_promotion_gate

    first = nb_05_train_mlflow.run(context=context)
    second = nb_05_train_mlflow.run(context=context)
    hgb = second["child_runs"]["hist_gradient_boosting"]
    wanted = truth["ml"]["metrics_approximate"]["hist_gradient_boosting"]
    for split in ("valid", "test"):
        for metric in ("pr_auc", "roc_auc"):
            got = hgb["%s_%s" % (split, metric)]
            report.add(
                "nb_05 HGB %s %s" % (split, metric.replace("_", "-").upper()),
                abs(got - wanted[split][metric]) <= METRIC_TOLERANCE,
                "%.4f (contract %.4f +/- %.2f)" % (got, wanted[split][metric], METRIC_TOLERANCE),
            )
    score = nb_06_register_score.run(context=context)
    expected_bands = truth["risk_scoring"]["bands"]
    bands_ok = all(abs(score["bands"].get(band, 0) - count) <= BAND_TOLERANCE for band, count in expected_bands.items())
    reasons = score["frozen_reference_comparison"].get("reason_code_matches")
    report.add(
        "nb_06 scored assets / bands",
        score["rows"] == truth["risk_scoring"]["assets_scored"] and bands_ok,
        "%d assets, High/Medium/Low %s/%s/%s (contract %s/%s/%s +/- %d)" % (
            score["rows"],
            score["bands"].get("High"),
            score["bands"].get("Medium"),
            score["bands"].get("Low"),
            expected_bands["High"],
            expected_bands["Medium"],
            expected_bands["Low"],
            BAND_TOLERANCE,
        ),
    )
    report.add("nb_06 reason codes == frozen", reasons == truth["risk_scoring"]["assets_scored"], "%s of %d" % (reasons, score["rows"]))
    gate = nb_08_promotion_gate.run(
        params={"champion_version": first["registered_version"], "challenger_version": second["registered_version"]},
        context=context,
    )
    report.add(
        "nb_08 gate decision recorded",
        gate["decision"] in {"hold", "promote"},
        "%s (PR-AUC gain %.4f, pointer not moved: report-only)" % (gate["decision"], gate["pr_auc_gain"]),
    )
    summary["chain"] = {
        "models_second_run": {name: {key: value for key, value in payload.items() if key != "run_id"} for name, payload in second["child_runs"].items()},
        "registered_versions": [first["registered_version"], second["registered_version"]],
        "score_bands": score["bands"],
        "gate": {key: gate[key] for key in ("decision", "pr_auc_gain", "precision_drop")},
    }


# --- driver ---------------------------------------------------------------------------------------------------------------------------


def package_versions() -> dict[str, str]:
    from importlib import metadata

    versions = {"python": platform.python_version()}
    for name in ("pandas", "numpy", "pyarrow", "scikit-learn", "scipy", "mlflow", "mlflow-skinny"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return versions


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSHOP_DIR).as_posix()
    except ValueError:
        return ".../" + "/".join(path.resolve().parts[-3:])


def guarded(report: Report, check: str, step):
    """Run one stage; an exception becomes a FAIL row (with the traceback on stderr) instead of ending the script."""
    try:
        return step()
    except Exception as exc:
        traceback.print_exc()
        report.add(check, False, "%s: %s" % (type(exc).__name__, str(exc)[:300]))
        return False


def default_out_dir() -> Path:
    base = os.environ.get("ML_MLOPS_LOCAL_OUT_DIR")
    return (Path(base) if base else ROOT / "local-validation" / "out") / "etl-to-ml"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ML notebooks on the Delta tables written by the ETL notebooks.")
    parser.add_argument("--tables-root", default=str(DEFAULT_TABLES_ROOT), help="a Tables, lh_fleet or artifacts folder (default: the ETL kit's artifacts)")
    parser.add_argument("--features-only", action="store_true", help="run nb_04 + nb_07 only (skip training, scoring and the gate)")
    parser.add_argument("--out", help="folder for tables, artifacts and the MLflow store (default: local-validation/out/etl-to-ml)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        tables_root = resolve_tables_root(Path(args.tables_root))
    except FileNotFoundError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2

    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "notebooks" / "shared"))
    from notebooks.notebook_common import make_local_context, sqlite_tracking_uri

    out_dir = Path(args.out) if args.out else default_out_dir()
    (out_dir / "mlflow").mkdir(parents=True, exist_ok=True)
    truth = json.loads((REFERENCE_DIR / "ground_truth.json").read_text(encoding="utf-8"))
    started = time.perf_counter()

    print("ETL -> ML integration check")
    print("  tables : %s" % display_path(tables_root))
    tables = load_tables(tables_root)
    print("  loaded : %s" % ", ".join("%s=%d" % (name, len(frame)) for name, frame in tables.items()))
    summary: dict = {"tables_root": display_path(tables_root), "packages": package_versions(), "rows": {name: len(frame) for name, frame in tables.items()}}

    report = Report()
    wanted_rows = {name: truth["gold_row_counts"][name.split(".")[1]] for name in ("gold.dim_asset", "gold.fact_telemetry_daily", "gold.fact_work_order")}
    report.add(
        "tables: 6 read, gold row counts == contract",
        all(len(frame) for frame in tables.values()) and all(len(tables[name]) == count for name, count in wanted_rows.items()),
        ", ".join("%s %d" % (name.split(".")[1], len(tables[name])) for name in wanted_rows),
    )

    context = make_local_context(
        reference_dir=REFERENCE_DIR,
        output_dir=out_dir,
        artifact_dir=out_dir / "artifacts",
        tracking_uri=sqlite_tracking_uri(out_dir / "mlflow" / "mlruns.db"),
        tables=tables,
    )
    inputs_ok = guarded(report, "nb_04 features", lambda: check_features(report, summary, context, truth, tables))
    inputs_ok = guarded(report, "nb_07 drift", lambda: check_drift(report, summary, context, truth)) and inputs_ok
    if args.features_only:
        report.skip("nb_05 -> nb_06 -> nb_08 chain", "skipped (--features-only)")
    elif not inputs_ok:
        report.skip("nb_05 -> nb_06 -> nb_08 chain", "skipped: the feature or drift check failed")
    else:
        guarded(report, "nb_05 -> nb_06 -> nb_08 chain", lambda: check_chain(report, summary, context, truth))

    print()
    report.print()
    passed = sum(1 for row in report.rows if row["ok"] is True)
    skipped = sum(1 for row in report.rows if row["ok"] is None)
    verdict = "PASS" if report.failed == 0 else "FAIL"
    print("\nRESULT: %s (%d passed, %d failed, %d skipped, %.0f s)" % (verdict, passed, report.failed, skipped, time.perf_counter() - started))
    summary.update(checks=report.rows, result=verdict)
    target = out_dir / "integration-etl-to-ml-summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print("summary: %s" % display_path(target))
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
