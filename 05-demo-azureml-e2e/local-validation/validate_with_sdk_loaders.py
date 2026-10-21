"""Validate the Azure ML demo files with the real azure-ai-ml SDK (the same loaders the `az ml` CLI v2 uses).

Why this exists: `yaml.safe_load` and the public JSON schemas accept files that the CLI/SDK then reject
(for example a bare relative `environment:` path, a typed `git_sha` input in a pipeline job, or
`from __future__ import annotations` in a module that uses the pipeline DSL). The SDK is the authority.

What it does (offline, nothing is sent to Azure, no workspace needed):
  1. Loads every YAML that starts with a `$schema:` line with the matching SDK loader and, for
     pipeline jobs, runs the SDK's local validation.
  2. Imports every `sdk/*.py` script and builds the pipeline of `sdk/run_pipeline.py` with the SDK DSL.
  3. Checks that each job's `experiment_name` equals the `--experiment-name` that train.py passes to
     `mlflow.set_experiment()` (inside an AML job a mismatch makes MLflow refuse to start the run).
  4. Checks that every `azureml:name:version` asset and every `azureml://datastores/<name>/` a job,
     endpoint or script points at is created by a YAML in this folder (or at run time by the register
     step / the endpoint deployments, or is a default datastore of every workspace).
  5. Checks that every data asset with a local `path:` points at a file or folder that exists
     (paths are relative to the YAML, so the kit must stay next to `02-demo-data`).

Usage (Python 3.9+ with `pip install azure-ai-ml`; validated with azure-ai-ml 1.35.2):

    python local-validation/validate_with_sdk_loaders.py [--verbose]

Exit code 1 when anything fails. NOT covered: server-side validation (asset existence, quota, RBAC,
region). Do a real `az ml ... create` dry run in your workspace before Friday.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

try:
    import yaml
    from azure.ai.ml import (
        load_batch_deployment,
        load_batch_endpoint,
        load_component,
        load_data,
        load_datastore,
        load_environment,
        load_job,
        load_online_deployment,
        load_online_endpoint,
    )

    try:
        from azure.ai.ml import load_schedule
    except ImportError:
        from azure.ai.ml.entities._load_functions import load_schedule
except ImportError as exc:
    sys.exit(f"This check needs azure-ai-ml (pip install azure-ai-ml). Import failed: {exc}")

DEMO = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"out", "local-validation", "mlops", "infra", "tests", "__pycache__", ".pytest_cache", ".ruff_cache"}
LOADERS = {
    "commandjob": load_job,
    "pipelinejob": load_job,
    "sweepjob": load_job,
    "commandcomponent": load_component,
    "environment": load_environment,
    "data": load_data,
    "onelakedatastore": load_datastore,
    "managedonlineendpoint": load_online_endpoint,
    "managedonlinedeployment": load_online_deployment,
    "batchendpoint": load_batch_endpoint,
    "batchdeployment": load_batch_deployment,
    "schedule": load_schedule,
}


def short(text: str, limit: int = 600) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + " ..."


def schema_kind(first_line: str) -> str:
    url = first_line.split(":", 1)[1].strip()
    return url.rsplit("/", 1)[-1].replace(".schema.json", "").replace(".json", "").lower()


def local_validation_errors(entity) -> list[str]:
    validate = getattr(entity, "_validate", None)
    if validate is None:
        return []
    try:
        result = validate()
    except NotImplementedError:
        return []
    if result is None or result.passed:
        return []
    messages = result.error_messages
    return [short(m) for m in (messages.values() if isinstance(messages, dict) else [messages])]


def check_yaml_files(verbose: bool) -> list[str]:
    failures: list[str] = []
    for path in sorted(DEMO.rglob("*.y*ml")):
        rel = path.relative_to(DEMO)
        if SKIP_DIRS & set(rel.parts[:-1]):
            continue
        first = next((line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()), "")
        if not first.startswith("$schema:"):
            continue
        kind = schema_kind(first)
        label = rel.as_posix()
        loader = LOADERS.get(kind)
        if loader is None:
            failures.append(f"{label}: no SDK loader known for schema kind '{kind}'")
            print(f"FAIL  {label:<52} unknown kind {kind}")
            continue
        try:
            entity = loader(source=str(path))
            problems = local_validation_errors(entity)
        except Exception as exc:  # noqa: BLE001 - any loader error is a finding to report
            failures.append(f"{label}: {short(exc)}")
            print(f"FAIL  {label:<52} {kind}\n      {short(exc)}")
            continue
        if problems:
            joined = "; ".join(problems)
            failures.append(f"{label}: {joined}")
            print(f"FAIL  {label:<52} {kind}\n      {joined}")
        else:
            print(f"OK    {label:<52} {kind} -> {type(entity).__name__}")
    return failures


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, DEMO / "sdk" / (f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_sdk_scripts(verbose: bool) -> list[str]:
    failures: list[str] = []
    for script in sorted((DEMO / "sdk").glob("*.py")):
        label = f"sdk/{script.name}"
        try:
            module = load_module(script.stem)
        except Exception as exc:  # noqa: BLE001 - any import error is a finding to report
            failures.append(f"{label}: import failed: {short(exc)}")
            print(f"FAIL  {label:<52} import failed\n      {short(exc)}")
            continue
        print(f"OK    {label:<52} imports")
        if script.stem != "run_pipeline":
            continue
        try:
            job = module.build_pipeline_job(
                "azureml:fleet-asset-day-features-reference:1", "azureml:fleet-champion-metrics:1", git_sha="abc123"
            )
            problems = local_validation_errors(job)
            steps = list(job.jobs)
        except Exception as exc:  # noqa: BLE001 - any build error is a finding to report
            failures.append(f"{label}: build_pipeline_job failed: {short(exc)}")
            print(f"FAIL  {label:<52} build_pipeline_job\n      {short(exc)}")
            continue
        if problems:
            joined = "; ".join(problems)
            failures.append(f"{label}: pipeline validation: {joined}")
            print(f"FAIL  {label:<52} pipeline validation\n      {joined}")
        else:
            print(f"OK    {label:<52} pipeline built: {len(steps)} steps {steps}, experiment {job.experiment_name}")
        yaml_experiment = yaml.safe_load((DEMO / "jobs" / "pipeline-train.yml").read_text(encoding="utf-8")).get("experiment_name")
        if job.experiment_name != yaml_experiment:
            failures.append(f"{label}: SDK pipeline experiment '{job.experiment_name}' differs from jobs/pipeline-train.yml '{yaml_experiment}'")
            print(f"FAIL  {label:<52} experiment differs from the YAML pipeline")
    return failures


REFERENCE = re.compile(r"azureml:([A-Za-z0-9_.-]+)(?::([A-Za-z0-9_.-]+)|@([A-Za-z0-9_.-]+))")
# Created at run time (by the register step and by the endpoint deployments), not by a YAML in this folder.
RUNTIME_ASSETS = {"fleet-failure-7d", "fleet-risk-online"}
DATASTORE_REFERENCE = re.compile(r"azureml://datastores/([A-Za-z0-9_-]+)/")
DATASTORE_TYPES = {"one_lake", "azure_blob", "azure_data_lake_gen2", "azure_file"}
# Datastores that every workspace creates by itself.
DEFAULT_DATASTORES = {"workspaceblobstore", "workspaceartifactstore", "workspacefilestore", "workspaceworkingdirectory"}


def check_asset_references() -> list[str]:
    """Every azureml: asset and datastore that a file points at must be created by a YAML in this folder."""
    defined: dict[tuple[str, str], str] = {}
    datastores: dict[str, str] = {}
    for path in sorted(DEMO.rglob("*.y*ml")):
        rel = path.relative_to(DEMO)
        if SKIP_DIRS & set(rel.parts[:-1]):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and str(doc.get("$schema", "")).startswith("https://") and "name" in doc and "version" in doc:
            defined[(str(doc["name"]), str(doc["version"]))] = rel.as_posix()
        if isinstance(doc, dict) and doc.get("type") in DATASTORE_TYPES and "name" in doc:
            datastores[str(doc["name"])] = rel.as_posix()
    used: dict[tuple[str, str, str], set[str]] = {}
    stores_used: dict[str, set[str]] = {}
    scanned = [*sorted((DEMO / "jobs").rglob("*.yml")), *sorted((DEMO / "endpoints").glob("*.yml")), *sorted((DEMO / "sdk").glob("*.py"))]
    for path in scanned:
        text = path.read_text(encoding="utf-8")
        for name, version, label in REFERENCE.findall(text):
            used.setdefault((name, version, label), set()).add(path.relative_to(DEMO).as_posix())
        for store in DATASTORE_REFERENCE.findall(text):
            stores_used.setdefault(store, set()).add(path.relative_to(DEMO).as_posix())
    failures: list[str] = []
    for (name, version, label), files in sorted(used.items()):
        ref = "azureml:{}{}".format(name, ":" + version if version else "@" + label)
        used_by = ", ".join(sorted(files))
        if name in RUNTIME_ASSETS:
            print(f"OK    {ref:<52} created at run time")
        elif (version and (name, version) in defined) or (label and any(n == name for n, _ in defined)):
            source = defined.get((name, version)) or next(p for (n, _), p in defined.items() if n == name)
            print(f"OK    {ref:<52} defined by {source}")
        else:
            failures.append(f"{ref} is used by {used_by} but no YAML in this folder creates it")
            print(f"FAIL  {ref:<52} not created by any YAML (used by {used_by})")
    for store, files in sorted(stores_used.items()):
        ref = f"azureml://datastores/{store}"
        used_by = ", ".join(sorted(files))
        if store in DEFAULT_DATASTORES:
            print(f"OK    {ref:<52} default datastore of every workspace")
        elif store in datastores:
            print(f"OK    {ref:<52} defined by {datastores[store]}")
        else:
            failures.append(f"{ref} is used by {used_by} but no datastore YAML in this folder creates it")
            print(f"FAIL  {ref:<52} not created by any YAML (used by {used_by})")
    return failures


def check_local_data_paths() -> list[str]:
    """A data asset with a local path must point at something that exists (the path is relative to the YAML)."""
    failures: list[str] = []
    for path in sorted((DEMO / "jobs").glob("data-*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        target = str(doc.get("path", ""))
        label = path.relative_to(DEMO).as_posix()
        if not target or "://" in target or target.startswith("azureml:"):
            print(f"SKIP  {label:<52} remote path {target or '-'}")
            continue
        resolved = (path.parent / target).resolve()
        if resolved.exists():
            print(f"OK    {label:<52} {resolved.name} exists")
        else:
            failures.append(f"{label}: local path {target} does not exist")
            print(f"FAIL  {label:<52} missing {target}")
    return failures


def check_experiment_names() -> list[str]:
    """train.py calls mlflow.set_experiment(); inside an AML job it must equal the job's experiment."""
    failures: list[str] = []
    pattern = re.compile(r"--experiment-name\s+(\S+)")
    for path in sorted((DEMO / "jobs").glob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        label = path.relative_to(DEMO).as_posix()
        job_type = doc.get("type")
        if job_type not in {"command", "sweep", "pipeline"}:
            continue
        job_experiment = doc.get("experiment_name")
        passed: list[str] = []
        if job_type == "command":
            passed = pattern.findall(str(doc.get("command", "")))
        elif job_type == "sweep":
            passed = pattern.findall(str(doc.get("trial", {}).get("command", "")))
        else:
            for step in (doc.get("jobs") or {}).values():
                value = (step.get("inputs") or {}).get("experiment_name")
                if value is not None:
                    passed.append(str(value))
        if not job_experiment:
            failures.append(f"{label}: no experiment_name (AML would use a default name, so set_experiment() would not match)")
        for value in passed:
            if value != job_experiment:
                failures.append(f"{label}: train step uses experiment '{value}' but the job experiment_name is '{job_experiment}'")
        status = "FAIL" if any(f.startswith(label) for f in failures) else "OK"
        print(f"{status:<5} {label:<52} experiment_name={job_experiment}, train step uses {passed or '-'}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    print("== 1. YAML files through the SDK loaders ==")
    failures = check_yaml_files(args.verbose)
    print("\n== 2. sdk/*.py scripts and the SDK pipeline builder ==")
    failures += check_sdk_scripts(args.verbose)
    print("\n== 3. MLflow experiment names vs job experiment names ==")
    failures += check_experiment_names()
    print("\n== 4. Every azureml: asset reference is created by a YAML in this folder ==")
    failures += check_asset_references()
    print("\n== 5. Every data asset with a local path points at an existing file ==")
    failures += check_local_data_paths()
    print()
    if failures:
        print(f"{len(failures)} problem(s):")
        for failure in failures:
            print(" -", failure)
        return 1
    print("All checks passed (offline; server-side validation still needs a real `az ml ... create`).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
