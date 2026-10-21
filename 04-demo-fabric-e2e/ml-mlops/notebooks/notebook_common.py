from __future__ import annotations

import atexit
import json
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

NOTEBOOKS_DIR = Path(__file__).resolve().parent
ML_MLOPS_DIR = NOTEBOOKS_DIR.parent
WORKSHOP_DIR = NOTEBOOKS_DIR.parents[2]
SHARED_DIR = NOTEBOOKS_DIR / "shared"

if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from fleet_ml_core import LABEL, METRIC_KEYS, mlflow_metrics, score_latest  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sqlite_tracking_uri(db_path: Path) -> str:
    return "sqlite:///%s" % db_path.resolve().as_posix()


_STAGED_CODE_DIRS: list[Path] = []


def _cleanup_staged_code_dirs() -> None:
    for staged in _STAGED_CODE_DIRS:
        shutil.rmtree(staged.parent, ignore_errors=True)


atexit.register(_cleanup_staged_code_dirs)


def notebook_source_paths() -> list[str]:
    """Minimal code_paths for mlflow.sklearn.log_model: only what is actually needed
    to unpickle ProbabilityScoringClassifier at serve time (notebooks/__init__.py,
    notebooks/notebook_common.py, notebooks/shared/*.py) -- NOT the nb_0X_*.py notebook
    sources and NOT notebooks/generated-ipynb.

    Copying the whole "notebooks" dir (as an earlier version of this function did) also
    copies generated-ipynb; under a deeply nested Windows working directory this can push
    the local MLflow artifact store path past MAX_PATH (260 chars), failing with
    "[WinError 206] Nom de fichier ou extension trop long" / "filename or extension is too
    long". Staging only the required files keeps the copied tree small and short-named.
    """
    staging_root = Path(tempfile.mkdtemp(prefix="fleet-code-"))
    staging_notebooks = staging_root / "notebooks"
    staging_notebooks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(NOTEBOOKS_DIR / "__init__.py", staging_notebooks / "__init__.py")
    shutil.copy2(NOTEBOOKS_DIR / "notebook_common.py", staging_notebooks / "notebook_common.py")
    shutil.copytree(SHARED_DIR, staging_notebooks / "shared")
    _STAGED_CODE_DIRS.append(staging_notebooks)
    return [str(staging_notebooks)]


def get_env_setting(
    name: str,
    default: Any,
    *,
    library: str = "fleet_mlops",
    notebookutils_obj: Any = None,
) -> tuple[Any, str]:
    """Resolve one Fabric Variable Library value, falling back to a safe default.

    In Fabric: notebookutils.variableLibrary.getLibrary(library) then getattr(lib, name)
    (documented on Learn as "NotebookUtils variable library utilities"; values come back
    already typed; variable names are case-sensitive). Any failure -- wrong name, library
    not deployed, API unavailable -- falls back to `default` rather than raising.

    Locally (notebookutils_obj is None, i.e. not running in Fabric), this returns
    `default`, unless an env var FLEET_VL_<NAME upper-cased> is set; that hook exists so a
    unit test can exercise the precedence logic without a live notebookutils.

    Returns (value, source) where source is "variable library" or "default", so a caller
    can print where the setting actually came from.
    """
    if notebookutils_obj is not None:
        try:
            lib = notebookutils_obj.variableLibrary.getLibrary(library)
            return getattr(lib, name), "variable library"
        except Exception:
            return default, "default"
    env_name = "FLEET_VL_%s" % name.upper()
    if env_name in os.environ:
        raw = os.environ[env_name]
        try:
            return type(default)(raw), "variable library"
        except (TypeError, ValueError):
            return raw, "variable library"
    return default, "default"


class ProbabilityScoringClassifier:
    """Expose probability scoring through both sklearn and pyfunc predict contracts."""

    def __init__(self, base_estimator: Any):
        self.base_estimator = base_estimator
        self.classes_ = np.array([0, 1], dtype=int)

    def __getattr__(self, name: str) -> Any:
        # Use object.__getattribute__ (not self.base_estimator) to avoid infinite
        # recursion: during cloudpickle/mlflow unpickling, __new__ runs without
        # __init__, so base_estimator briefly does not exist yet. self.base_estimator
        # would re-enter __getattr__ forever looking for the attribute it delegates to.
        try:
            base_estimator = object.__getattribute__(self, "base_estimator")
        except AttributeError:
            raise AttributeError(name) from None
        return getattr(base_estimator, name)

    def fit(self, X: pd.DataFrame, y: pd.Series | np.ndarray | None = None) -> ProbabilityScoringClassifier:
        return self

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        proba = self.base_estimator.predict_proba(X)
        if proba.ndim == 1:
            positive = proba.astype(float)
        else:
            positive = proba[:, 1].astype(float)
        return np.column_stack([1.0 - positive, positive])

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.predict_proba(X)[:, 1]


class LocalTableCatalog:
    def __init__(self, tables: dict[str, pd.DataFrame] | None = None, output_dir: Path | None = None):
        self.tables = dict(tables or {})
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def has_table(self, table_name: str) -> bool:
        return table_name in self.tables

    def read_table(self, table_name: str) -> pd.DataFrame:
        if table_name not in self.tables:
            raise KeyError("table %s not loaded in local catalog" % table_name)
        return self.tables[table_name].copy(deep=True)

    def write_table(self, table_name: str, frame: pd.DataFrame) -> pd.DataFrame:
        stored = frame.copy(deep=True)
        self.tables[table_name] = stored
        if self.output_dir is not None:
            path = self.output_dir / ("%s.csv" % table_name.replace(".", "__"))
            stored.to_csv(path, index=False, lineterminator="\n")
        return stored


@dataclass
class NotebookContext:
    mode: str
    reference_dir: Path
    artifact_dir: Path
    output_dir: Path
    tracking_uri: str | None = None
    registry_uri: str | None = None
    catalog: LocalTableCatalog | None = None
    spark: Any | None = None
    notebookutils: Any | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def read_table(self, table_name: str) -> pd.DataFrame:
        if self.mode == "fabric":
            return self.spark.read.table(table_name).toPandas()
        if self.catalog and self.catalog.has_table(table_name):
            return self.catalog.read_table(table_name)
        base_name = table_name.split(".", 1)[-1]
        return read_reference_frame(self.reference_dir, base_name)

    def write_table(self, table_name: str, frame: pd.DataFrame) -> pd.DataFrame:
        if self.mode == "fabric":
            self.spark.createDataFrame(frame).write.format("delta").mode("overwrite").saveAsTable(table_name)
            return frame
        if not self.catalog:
            self.catalog = LocalTableCatalog(output_dir=self.output_dir / "tables")
        return self.catalog.write_table(table_name, frame)

    def read_reference(self, base_name: str) -> pd.DataFrame:
        return read_reference_frame(self.reference_dir, base_name)

    def has_reference(self, base_name: str) -> bool:
        """True if a reference file for base_name can actually be read.

        A real Fabric workspace normally has no reference_out files at all (they are
        a local-validation fixture copied from 02-demo-data); callers must check this
        before calling read_reference so a live run degrades to a 'skipped' summary
        entry instead of raising FileNotFoundError.
        """
        try:
            self.read_reference(base_name)
            return True
        except FileNotFoundError:
            return False

    def write_json_artifact(self, name: str, payload: dict[str, Any]) -> Path:
        target = self.artifact_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, allow_nan=False)
            handle.write("\n")
        return target

    def notebook_exit(self, payload: dict[str, Any]) -> str:
        rendered = json.dumps(payload, indent=2, sort_keys=True)
        if self.mode == "fabric" and self.notebookutils is not None:
            self.notebookutils.notebook.exit(rendered)
        return rendered


def read_reference_frame(reference_dir: Path, base_name: str) -> pd.DataFrame:
    candidates = [
        reference_dir / base_name,
        reference_dir / ("%s.csv" % base_name),
        reference_dir / ("%s.csv.gz" % base_name),
    ]
    for candidate in candidates:
        if candidate.exists():
            return pd.read_csv(candidate)
    raise FileNotFoundError("no reference file found for %s under %s" % (base_name, reference_dir))


def make_local_context(
    *,
    reference_dir: Path | None = None,
    output_dir: Path | None = None,
    artifact_dir: Path | None = None,
    tracking_uri: str | None = None,
    registry_uri: str | None = None,
    tables: dict[str, pd.DataFrame] | None = None,
) -> NotebookContext:
    reference_dir = Path(reference_dir or (WORKSHOP_DIR / "02-demo-data" / "reference_out"))
    output_dir = Path(output_dir or (ML_MLOPS_DIR / "local-validation" / "out"))
    artifact_dir = Path(artifact_dir or (output_dir / "artifacts"))
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return NotebookContext(
        mode="local",
        reference_dir=reference_dir,
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        tracking_uri=tracking_uri,
        registry_uri=registry_uri or tracking_uri,
        catalog=LocalTableCatalog(tables=tables, output_dir=output_dir / "tables"),
    )


def make_fabric_context(notebookutils_obj: Any, spark_session: Any, reference_dir: str | None = None) -> NotebookContext:
    # Never write into the uploaded code folder (Files/code): use a throwaway
    # scratch dir. Plots/CSVs built during a run are logged to MLflow right away,
    # so nothing here needs to survive past the notebook run.
    import tempfile

    scratch_dir = Path(tempfile.mkdtemp(prefix="fleet-"))
    artifact_dir = scratch_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_dir = scratch_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return NotebookContext(
        mode="fabric",
        reference_dir=Path(reference_dir or artifact_dir),
        artifact_dir=artifact_dir,
        output_dir=output_dir,
        spark=spark_session,
        notebookutils=notebookutils_obj,
    )


def default_context(globals_dict: dict[str, Any], *, local_tables: dict[str, pd.DataFrame] | None = None) -> NotebookContext:
    in_fabric = "notebookutils" in globals_dict
    if in_fabric:
        return make_fabric_context(globals_dict["notebookutils"], globals_dict.get("spark"))
    return make_local_context(tables=local_tables)


def ensure_mlflow_experiment(context: NotebookContext, experiment_name: str) -> tuple[Any, Any]:
    import mlflow

    if context.mode == "fabric":
        # Fabric's MLflow artifact store is managed by the service: just creating/
        # selecting the Experiment item with set_experiment is the documented way.
        # Calling create_experiment with an explicit artifact_location (the local-mode
        # path below) is not meaningful in a workspace and is skipped entirely here.
        mlflow.set_experiment(experiment_name)
        client = mlflow.MlflowClient()
        return mlflow, client

    if context.tracking_uri:
        mlflow.set_tracking_uri(context.tracking_uri)
    if context.registry_uri:
        mlflow.set_registry_uri(context.registry_uri)
    artifact_location = (context.artifact_dir / "mlruns-artifacts" / experiment_name).resolve().as_uri()
    client = mlflow.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = client.create_experiment(experiment_name, artifact_location=artifact_location)
        experiment = client.get_experiment(experiment_id)
    mlflow.set_experiment(experiment_name)
    return mlflow, client


def flatten_metrics(metrics: dict[str, dict[str, float]]) -> dict[str, float]:
    return mlflow_metrics(metrics)


def create_pr_curve_artifact(y_true: pd.Series, scores: np.ndarray, output_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import precision_recall_curve

    precision, recall, _ = precision_recall_curve(y_true, scores)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.plot(recall, precision, linewidth=2)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-recall curve")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def feature_importance_frame(model: Any, X: pd.DataFrame, y: pd.Series, feature_names: list[str]) -> pd.DataFrame:
    from sklearn.inspection import permutation_importance

    if hasattr(model, "named_steps") and "logisticregression" in model.named_steps:
        weights = np.abs(model.named_steps["logisticregression"].coef_[0])
    elif hasattr(model, "feature_importances_"):
        weights = np.asarray(model.feature_importances_, dtype=float)
    else:
        result = permutation_importance(model, X, y, scoring="average_precision", n_repeats=3, random_state=0)
        weights = np.asarray(result.importances_mean, dtype=float)
    frame = pd.DataFrame({"feature": feature_names, "importance": weights})
    frame = frame.sort_values(["importance", "feature"], ascending=[False, True], kind="stable").reset_index(drop=True)
    return frame


def compare_frames_with_tolerance(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    *,
    key_cols: list[str],
    numeric_cols: list[str] | None = None,
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    numeric_cols = list(numeric_cols or [])
    joined = actual.merge(expected, on=key_cols, how="outer", indicator=True, suffixes=("_actual", "_expected"))
    if (joined["_merge"] != "both").any():
        mismatch = joined.loc[joined["_merge"] != "both", key_cols + ["_merge"]]
        return {"ok": False, "reason": "key_mismatch", "details": mismatch.head(10).to_dict(orient="records")}
    max_diff = 0.0
    failing: dict[str, float] = {}
    for col in numeric_cols:
        diff = (joined["%s_actual" % col] - joined["%s_expected" % col]).abs().fillna(0.0)
        col_max = float(diff.max())
        max_diff = max(max_diff, col_max)
        if col_max > tolerance:
            failing[col] = col_max
    exact_cols = [c for c in actual.columns if c in expected.columns and c not in set(key_cols + numeric_cols)]
    exact_mismatches = {}
    for col in exact_cols:
        bad = joined["%s_actual" % col].fillna("") != joined["%s_expected" % col].fillna("")
        if bad.any():
            exact_mismatches[col] = int(bad.sum())
    return {"ok": not failing and not exact_mismatches, "max_abs_diff": max_diff, "numeric_failures": failing, "exact_failures": exact_mismatches}


def build_risk_score_table(features_df: pd.DataFrame, dim_asset: pd.DataFrame, model: Any, model_version: str) -> pd.DataFrame:
    scored = score_latest(features_df, model, model_version=model_version)
    joined = scored.merge(
        dim_asset[["erp_asset_id", "site_code", "equipment_class"]].drop_duplicates(),
        on="erp_asset_id",
        how="left",
    )
    ordered = joined[["score_date", "erp_asset_id", "site_code", "equipment_class", "risk_score", "risk_band", "risk_rank", "top_drivers", "model_version"]]
    return ordered.sort_values(["risk_rank", "erp_asset_id"], kind="stable").reset_index(drop=True)


def load_sklearn_model(model_uri: str) -> Any:
    import mlflow.sklearn

    return mlflow.sklearn.load_model(model_uri)


def load_pyfunc_scores(model_uri: str, frame: pd.DataFrame) -> np.ndarray:
    import mlflow.pyfunc

    return np.asarray(mlflow.pyfunc.load_model(model_uri).predict(frame), dtype=float)


def get_model_versions(client: Any, model_name: str) -> list[Any]:
    return sorted(client.search_model_versions("name = '%s'" % model_name), key=lambda item: int(item.version))


def get_holdout_metrics(client: Any, model_name: str, version: str) -> dict[str, float]:
    """Read the honest, already-logged holdout metrics from a model version's SOURCE run.

    The registered model artifact is refit on every labelled split (train+gap+valid+test,
    see fleet_ml_core.fit_final_model) before it is used to score brand-new unlabeled days.
    Re-scoring that refit artifact against the frozen test split would be in-sample, because
    the artifact was itself fit on those same test rows. The gate therefore reads the holdout
    metrics logged with the registered version instead of re-scoring the model on training data:
    the test_pr_auc / test_precision_at_top5pct (and siblings) metrics that nb_05_train_mlflow
    already logged on the architecture-selection run (the model BEFORE the final
    refit-on-everything), which is an honest holdout evaluation.
    """
    details = client.get_model_version(model_name, version)
    run_id = details.run_id
    metrics = client.get_run(run_id).data.metrics
    missing = [key for key in METRIC_KEYS if key not in metrics]
    if missing:
        raise KeyError(
            "run %s for %s v%s is missing expected holdout metrics %s -- was it registered from a "
            "candidate that never called mlflow.log_metrics (e.g. rule_baseline/prevalence)?"
            % (run_id, model_name, version, missing)
        )
    return {key: float(metrics[key]) for key in METRIC_KEYS}


def model_pointer_schema() -> list[str]:
    return ["model_name", "champion_version", "updated_at_utc", "updated_by", "note"]


def read_model_pointer(context: NotebookContext, table_name: str = "ml.model_pointer") -> pd.DataFrame:
    try:
        frame = context.read_table(table_name)
    except (FileNotFoundError, KeyError):
        frame = pd.DataFrame(columns=model_pointer_schema())
    return frame.reindex(columns=model_pointer_schema())


def upsert_model_pointer(
    context: NotebookContext,
    *,
    model_name: str,
    champion_version: str,
    note: str,
    updated_by: str = "nb_08_promotion_gate",
    table_name: str = "ml.model_pointer",
) -> pd.DataFrame:
    pointer = read_model_pointer(context, table_name=table_name)
    pointer = pointer[pointer["model_name"] != model_name]
    pointer = pd.concat(
        [
            pointer,
            pd.DataFrame(
                [
                    {
                        "model_name": model_name,
                        "champion_version": str(champion_version),
                        "updated_at_utc": utc_now(),
                        "updated_by": updated_by,
                        "note": note,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    pointer = pointer.sort_values(["model_name", "updated_at_utc"], kind="stable").reset_index(drop=True)
    context.write_table(table_name, pointer)
    return pointer


def resolve_model_version(client: Any, model_name: str, requested_version: str | None = None, pointer: pd.DataFrame | None = None) -> str:
    if requested_version:
        return str(requested_version)
    if pointer is not None and not pointer.empty:
        hit = pointer.loc[pointer["model_name"] == model_name, "champion_version"]
        if not hit.empty:
            return str(hit.iloc[-1])
    versions = get_model_versions(client, model_name)
    if not versions:
        raise ValueError("no registered versions found for %s" % model_name)
    return str(versions[-1].version)


def gate_decision(
    champion: dict[str, float],
    challenger: dict[str, float],
    *,
    min_pr_auc_gain: float = 0.01,
    max_precision_drop: float = 0.02,
) -> dict[str, Any]:
    pr_auc_gain = float(challenger["test_pr_auc"] - champion["test_pr_auc"])
    precision_drop = float(champion["test_precision_at_top5pct"] - challenger["test_precision_at_top5pct"])
    passed_pr = challenger["test_pr_auc"] >= champion["test_pr_auc"] + min_pr_auc_gain
    passed_precision = challenger["test_precision_at_top5pct"] >= champion["test_precision_at_top5pct"] - max_precision_drop
    decision = "promote" if (passed_pr and passed_precision) else "hold"
    return {
        "decision": decision,
        "passed": decision == "promote",
        "champion_test_pr_auc": float(champion["test_pr_auc"]),
        "challenger_test_pr_auc": float(challenger["test_pr_auc"]),
        "pr_auc_gain": pr_auc_gain,
        "champion_test_precision_at_top5pct": float(champion["test_precision_at_top5pct"]),
        "challenger_test_precision_at_top5pct": float(challenger["test_precision_at_top5pct"]),
        "precision_drop": precision_drop,
        "rule": {
            "min_pr_auc_gain": min_pr_auc_gain,
            "max_precision_drop": max_precision_drop,
            "passed_pr_auc_gain": passed_pr,
            "passed_precision_guardrail": passed_precision,
        },
    }


def compute_split_counts(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    counts = {}
    for split_name, split_frame in frame.groupby("split", sort=False):
        positives = split_frame[LABEL].sum(skipna=True)
        counts[split_name] = {"rows": int(len(split_frame)), "positives": int(positives) if not pd.isna(positives) else 0}
    return counts


def major_shift_summary(report: pd.DataFrame) -> tuple[list[str], list[str]]:
    major = [
        "%s %s psi=%.4f" % (row.equipment_class, row.sensor, row.psi)
        for row in report[report["status"] == "major"].sort_values(["equipment_class", "sensor"]).itertuples()
    ]
    expected_moderate = [
        "%s %s psi=%.4f" % (row.equipment_class, row.sensor, row.psi)
        for row in report[(report["status"] == "moderate") & (report["sensor"] == "engine_temp_c")]
        .sort_values(["equipment_class", "sensor"])
        .itertuples()
    ]
    return major, expected_moderate


def next_day_cutoff_epoch(dates: pd.Series) -> int:
    latest = pd.to_datetime(dates).max().date()
    return int(datetime.combine(latest + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp())


def notebook_logical_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://contoso-fleet.local/%s" % name))
