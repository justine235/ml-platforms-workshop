from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

# Kit-relative, no machine-specific paths: this module and run_local.py both
# resolve data/output locations purely from environment variables (FLEET_RAW_ROOT,
# FLEET_TRUTH_ROOT, ML_MLOPS_LOCAL_OUT_DIR) with in-kit defaults, same convention as
# run_local.py.
ROOT = Path(__file__).resolve().parents[1]  # ml-mlops
FABRIC_GIT_DIR = ROOT / "fabric-git"
WORKSHOP_DIR = ROOT.parents[1]
REFERENCE_DIR = WORKSHOP_DIR / "02-demo-data" / "reference_out"

NOTEBOOK_ORDER = [
    ("nb_04_features", "nb_04_features.Notebook"),
    ("nb_05_train_mlflow", "nb_05_train_mlflow.Notebook"),
    ("nb_06_register_score", "nb_06_register_score.Notebook"),
    ("nb_07_drift_monitor", "nb_07_drift_monitor.Notebook"),
    ("nb_08_promotion_gate", "nb_08_promotion_gate.Notebook"),
]

CELL_MARKER = "# CELL ********************"
MARKDOWN_MARKER = "# MARKDOWN ********************"
METADATA_MARKER = "# METADATA ********************"


def extract_code(notebook_content_path: Path) -> str:
    """Pull the executable CELL bodies out of a Fabric Git notebook-content.py file,
    skipping MARKDOWN cells and METADATA blocks. This is the text Fabric itself would
    run; it is NOT the same text as the percent-format .py source in notebooks dir."""
    lines = notebook_content_path.read_text(encoding="utf-8").split("\n")
    mode = None
    code_lines: list[str] = []
    for line in lines:
        if line == CELL_MARKER:
            mode = "code"
            continue
        if line == MARKDOWN_MARKER:
            mode = "markdown"
            continue
        if line == METADATA_MARKER:
            mode = "metadata"
            continue
        if mode == "code":
            code_lines.append(line)
    return "\n".join(code_lines)


class FakeWriter:
    def __init__(self, tables: dict, pdf: pd.DataFrame):
        self._tables = tables
        self._pdf = pdf

    def format(self, _fmt: str) -> "FakeWriter":
        return self

    def mode(self, _mode: str) -> "FakeWriter":
        return self

    def saveAsTable(self, name: str) -> None:
        self._tables[name] = self._pdf.copy(deep=True)


class FakeDataFrame:
    def __init__(self, tables: dict, pdf: pd.DataFrame):
        self._tables = tables
        self._pdf = pdf

    def toPandas(self) -> pd.DataFrame:
        return self._pdf.copy(deep=True)

    @property
    def write(self) -> FakeWriter:
        return FakeWriter(self._tables, self._pdf)


class AnalysisException(Exception):
    """Same class name as pyspark's AnalysisException; the real Fabric class and message are UNVERIFIED."""


class FakeReader:
    def __init__(self, tables: dict):
        self._tables = tables

    def table(self, name: str) -> FakeDataFrame:
        if name not in self._tables:
            # Mimics Spark 3.5 / 4.x for a missing table (the old KeyError hid that read_model_pointer did not catch this).
            raise AnalysisException("[TABLE_OR_VIEW_NOT_FOUND] The table or view `%s` cannot be found. (fabric_sim: table not seeded)" % name)
        return FakeDataFrame(self._tables, self._tables[name])


class FakeSparkSession:
    """Dict-backed stand-in for the real SparkSession, shared across all five
    simulated notebook runs so a write from one activity is visible to the next --
    exactly like Lakehouse tables persist across TridentNotebook activities."""

    def __init__(self, tables: dict):
        self.tables = tables
        self.read = FakeReader(tables)

    def createDataFrame(self, pdf: pd.DataFrame) -> FakeDataFrame:
        return FakeDataFrame(self.tables, pdf)


class FakeNotebookHandle:
    def __init__(self):
        self.exit_value = None

    def exit(self, value) -> None:
        self.exit_value = value


class FakeNotebookutils:
    """Stand-in for Fabric's notebookutils: only notebook.exit(...) is implemented.
    variableLibrary is deliberately absent so get_env_setting(...) hits its own
    try/except and falls back to the hardcoded default -- same behavior as a
    workspace where the fleet_mlops Variable Library is not attached."""

    def __init__(self):
        self.notebook = FakeNotebookHandle()


def _purge_notebooks_modules() -> None:
    """Drop any 'notebooks' package cached from the real source tree (ROOT/notebooks)
    so the simulated notebooks re-import fresh from the copied Files/code tree -- the
    whole point of this test is to exercise the uploaded-code-folder copy, not the
    original source."""
    for mod_name in list(sys.modules):
        if mod_name == "notebooks" or mod_name.startswith("notebooks."):
            del sys.modules[mod_name]
    root_str = str(ROOT)
    shared_str = str(ROOT / "notebooks" / "shared")
    sys.path[:] = [p for p in sys.path if p not in (root_str, shared_str)]


def seed_tables() -> dict:
    """Build the same local tables run_local.py uses (silver/gold/bronze), via its
    existing reference-pipeline logic, BEFORE the simulated notebooks run. This import
    of run_local (and transitively notebooks.shared.fleet_reference_pipeline) is pre-sim
    setup only; _purge_notebooks_modules() below removes the cached 'notebooks' package
    afterward so the sim never silently uses the real source tree."""
    local_validation_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(local_validation_dir))
    import run_local  # noqa: E402

    data_dir, _truth_dir = run_local.ensure_demo_data()
    tables = run_local.build_local_tables(data_dir)
    _purge_notebooks_modules()
    return tables


def run_one(folder: str, spark: FakeSparkSession, code_dir: Path) -> dict:
    content_path = FABRIC_GIT_DIR / folder / "notebook-content.py"
    code = extract_code(content_path)
    notebookutils_obj = FakeNotebookutils()
    sim_globals: dict = {
        "__name__": "__main__",
        "__file__": str(content_path),
        "notebookutils": notebookutils_obj,
        "spark": spark,
    }
    os.environ["FLEET_CODE_DIR"] = str(code_dir)
    exec(compile(code, str(content_path), "exec"), sim_globals)
    exit_value = notebookutils_obj.notebook.exit_value
    if exit_value is not None:
        # nb_07/nb_08 return their decision as the real notebook exit value.
        return json.loads(exit_value)
    # nb_04/nb_05/nb_06 do not call notebook_exit (only the drift and gate decisions
    # are consumed downstream); fall back to run()'s returned RESULT dict and prove
    # it is JSON-serializable, same bar as the real exit value.
    result = sim_globals.get("RESULT")
    if result is None:
        raise AssertionError("%s: no notebook_exit value and no RESULT from run()" % folder)
    return json.loads(json.dumps(result))


def main() -> None:
    work_dir = Path(tempfile.mkdtemp(prefix="fleet-fabric-sim-"))
    code_dir = work_dir / "Files" / "code"
    notebooks_src = ROOT / "notebooks"
    notebooks_dst = code_dir / "notebooks"
    notebooks_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(notebooks_src / "__init__.py", notebooks_dst / "__init__.py")
    shutil.copy2(notebooks_src / "notebook_common.py", notebooks_dst / "notebook_common.py")
    shutil.copytree(notebooks_src / "shared", notebooks_dst / "shared")
    # Deliberately NOT copied: no reference_out files are visible in Files/code, matching
    # a real workspace where 02-demo-data/reference_out does not exist.

    old_cwd = Path.cwd()
    os.chdir(work_dir)
    try:
        tables = seed_tables()
        spark = FakeSparkSession(tables)

        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))

        import mlflow

        from notebooks.notebook_common import sqlite_tracking_uri  # noqa: E402 (from the copied tree, after purge)

        mlflow.set_tracking_uri(sqlite_tracking_uri(work_dir / "mlruns.db"))

        results: dict[str, dict] = {}
        for name, folder in NOTEBOOK_ORDER:
            results[name] = run_one(folder, spark, code_dir)
            print("ran %s: exit keys = %s" % (name, sorted(results[name].keys())))

        if "ml.asset_day_features" not in tables:
            raise AssertionError("nb_04_features did not write ml.asset_day_features")
        from notebooks.notebook_common import compare_frames_with_tolerance
        from notebooks.shared.fleet_ml_core import FEATURES

        reference_features = pd.read_csv(REFERENCE_DIR / "ml_asset_day_features.csv.gz")
        comparison = compare_frames_with_tolerance(
            tables["ml.asset_day_features"],
            reference_features,
            key_cols=["erp_asset_id", "obs_date", "split"],
            numeric_cols=[*FEATURES, "fail_next_7d"],
            tolerance=1e-6,
        )
        if not comparison["ok"]:
            raise AssertionError("ml.asset_day_features vs reference mismatch: %r" % comparison)

        drift_status = results["nb_07_drift_monitor"].get("status")
        if drift_status not in {"ok", "alert"}:
            raise AssertionError("nb_07 status not in {ok, alert}: %r" % drift_status)

        gate_summary = results["nb_08_promotion_gate"]
        if "decision" not in gate_summary:
            raise AssertionError("nb_08 exit payload has no 'decision' key: %r" % gate_summary)

        summary = {
            "status": "ok",
            "note": "Fabric-simulated (fake spark/notebookutils), NOT a real workspace",
            "asset_day_features_reference_comparison": comparison,
            "drift_status": drift_status,
            "gate_decision": gate_summary["decision"],
            "exit_value_keys": {name: sorted(value.keys()) for name, value in results.items()},
        }
        output_dir = Path(os.environ.get("ML_MLOPS_LOCAL_OUT_DIR", str(ROOT / "local-validation" / "out")))
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / "fabric-sim-summary.json"
        target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
