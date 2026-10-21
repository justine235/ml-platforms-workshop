# Results: local validation of the Azure ML end-to-end demo

**Scope.** Nothing in this folder was run against a real Azure subscription or Azure ML workspace. `az login` was never called, no deployment happened, no secrets were used. All checks below are static (no execution), SDK-loader checks (no network) or a single offline run of the plain Python scripts under `src/` and `local-validation/run_local.py`, in a Python 3.11.9 virtual environment (packages as pinned in `requirements-local.txt`).

## Static validation (all passed)

- Every `.py` file in this folder (22) compiles.
- `ruff check src tests sdk local-validation --config ruff.toml` (the CI command, ruff 0.17.0) - all checks passed.
- Every `.yml` / `.yaml` / `.json` asset (28 YAML, 8 JSON: jobs, components, environments, endpoints, schedule, monitoring, GitHub workflows) parses with `yaml.safe_load` / `json.load`. This proved much weaker than it sounds: see the next section.
- `az bicep build --file <f> --stdout` on all 7 `.bicep` files compiled. Only non-blocking `BCP081` warnings appeared: the local Bicep CLI v0.31.92 has no cached type definition for `Microsoft.MachineLearningServices/*@2025-06-01`. That is a limitation of this offline CLI version, not a template error, and must not be "fixed" by installing a newer Bicep CLI (no installs allowed).
- `pytest tests -q`: 3 passed (`test_gate.py` x2, `test_contract_scripts.py` x1).
- Name consistency checked across docs, YAML, SDK scripts, Bicep, and GitHub workflows for `mlw-fleet-dev`, `cpu-cluster`, `env-fleet-sklearn`, `fleet-risk-online`, `fleet-risk-batch`, `fleet-failure-7d`, and the `mlflow==2.16.2` + `azureml-mlflow` pin - all consistent, no mismatches found.

## Validation with the real azure-ai-ml SDK (azure-ai-ml 1.35.2)

`local-validation/validate_with_sdk_loaders.py` runs five checks, all passing. It is the authoritative offline check because it uses the same loaders as the `az ml` CLI v2.

1. All 23 YAML files that start with a `$schema:` line load with their SDK loader (jobs, components, environment, data assets, OneLake datastore, endpoints, deployments, schedules) and the SDK's local validation passes.
2. Every `sdk/*.py` script imports, and the SDK pipeline of `sdk/run_pipeline.py` builds (5 steps).
3. Each job's `experiment_name` equals the `--experiment-name` that `train.py` passes to `mlflow.set_experiment()`.
4. Every `azureml:name:version` asset and every `azureml://datastores/<name>/` reference is created by a YAML in this folder, at run time, or by the workspace itself.
5. Every data asset with a local path points at a file that exists.

### Defects found by the SDK loaders (all fixed)

Every one of these passed `yaml.safe_load`, the public JSON schemas and `py_compile`:

- `environment:` held a bare relative path. The SDK wants `azureml:name:version` (or `file:` or an inline object), and the environment must be registered before any job, so `rebuild-guide.md` step 2 now registers it first.
- The pipeline job declared `git_sha` as a typed input. A pipeline job takes literals or `{type, path}` entries only.
- `sweep-job.yml` had its inputs and outputs where the SDK does not accept them. They belong at the top level of the job.
- `schedule.yml` used capitalised weekday names; the SDK wants lowercase `week_days`.
- `sdk/run_pipeline.py` used `from __future__ import annotations`, which breaks the `@pipeline` DSL (it reads `__annotations__`).
- `azureml:fleet-champion-metrics:1` was referenced but nothing created it. It is now `assets/champion-metrics.json` plus `jobs/data-champion-metrics.yml`, registered in step 2.

Found by reading MLflow's code rather than by a loader, and not reproduced here because it needs a workspace: when `MLFLOW_RUN_ID` is set (Azure ML sets it inside jobs), `mlflow.start_run()` raises "active run ID does not match environment run ID" if `mlflow.set_experiment(name)` names another experiment than the job's. Both job experiment names are therefore pinned (`fleet-failure-7d`, `fleet-failure-7d-sweep`) and check 3 guards them. See `VERIFY-BEFORE-FRIDAY.md`.

Also fixed by review, not by a loader: the GitHub workflow templates (working directories, a dead step that pointed at a scratch file, a `what-if` job that never ran `what-if`, an incomplete `az ml model share` and registry deployment). They are only parse-checked, never run.

## One offline end-to-end run

`local-validation/run_local.py` was executed once, end to end. It trains two models from the reference feature export (`02-demo-data/reference_out`), logs them to a local MLflow SQLite store, gates the real HGB challenger against a real champion, registers the model, regenerates one extra month of synthetic telematics for drift, scores the frozen asset list, and computes PSI drift.

### Bug found and fixed: fabricated champion crashed the pipeline

The version left by the previous agent fabricated a champion with `test_precision_at_top5pct = 0.56` - a value never reached by any model in `ground_truth.json` (max about 0.36). That impossible champion made the real gate correctly reject the real HGB challenger, which made `register.py` raise `SystemExit`, which killed the whole script right after `prep` ran. That is why only `local-validation/out/prep` had output before this session. Fix: `run_local.py` now trains a real logistic-regression champion first (matching the contract's documented baseline model), and its own `metrics.json` is passed to `evaluate.py --champion-json` and `gate.py` for a real HGB-vs-logistic-regression comparison, instead of a fabricated JSON.

### Secondary bug found and fixed: MLflow / SQLAlchemy incompatibility

`mlflow==2.16.2`'s SQLite tracking store imports `FallbackAsyncAdaptedQueuePool` from `sqlalchemy.pool`, which does not exist in SQLAlchemy 2.1.x. `environments/conda-fleet-sklearn.yml` already pinned `sqlalchemy<2.1` (the previous agent had already anticipated this - good), but the validation venv had picked up a newer SQLAlchemy from its generic setup. Installing `SQLAlchemy>=1.4,<2.1` fixed it, and that pin is now in `requirements-local.txt`. No demo file needed to change.

### Real gate decision (from this run)

```json
{
  "approved": true,
  "challenger_metrics": {
    "test_pr_auc": 0.3882,
    "test_precision_at_top5pct": 0.3758,
    "test_recall_at_top5pct": 0.4197,
    "test_roc_auc": 0.7551,
    "valid_pr_auc": 0.349,
    "valid_roc_auc": 0.7037
  },
  "champion_metrics": {
    "test_pr_auc": 0.2924,
    "test_precision_at_top5pct": 0.3072,
    "test_recall_at_top5pct": 0.3431,
    "test_roc_auc": 0.741,
    "valid_pr_auc": 0.2923,
    "valid_roc_auc": 0.7301
  },
  "deltas": {
    "test_pr_auc": 0.0958,
    "test_precision_at_top5pct": 0.0686
  },
  "reason": "Approved: challenger cleared the +0.01 PR-AUC threshold and stayed within the precision guardrail.",
  "rule": "challenger test_pr_auc >= champion + 0.01 and precision@top5% not worse by more than 0.02"
}
```

The full file is copied to `results/gate-decision.json` (from `local-validation/out/train/evaluation.json`).

### Comparison with `ground_truth.json` (reference, generated with pandas 2.2 / scikit-learn 1.9.1)

| Metric | This run (scikit-learn 1.6.1) | `ground_truth.json` | Within tolerance? |
|---|---|---|---|
| Champion (logistic regression) test PR-AUC | 0.2924 | 0.2924 | yes, identical - contract says LR is stable across sklearn 1.6/1.9 |
| Champion test precision@top5% | 0.3072 | 0.3072 | yes, identical |
| Challenger (HGB) test PR-AUC | 0.3882 | 0.3847 | yes, +-0.0035, contract allows +-0.02 version drift for gradient boosting |
| Challenger test precision@top5% | 0.3758 | 0.3595 | yes, +0.0163 |
| Challenger test ROC-AUC | 0.7551 | 0.749 | yes |
| Scored rows | 264 | 264 | exact match |
| Risk bands (High / Medium / Low) | 8 / 13 / 243 | 9 / 7 / 248 | differs - expected, see note below |
| Drift combinations | 47 total: 4 major / 3 moderate / 40 stable | 47 total: 4 major / 3 moderate / 40 stable | exact match |
| Gate decision | approved = true | approved = true (implied by the HGB row beating the LR row) | consistent |

**Risk-band note.** `scenario-contract.md` states explicitly: "Risk bands depend on library versions (the pandas 2.2 / scikit-learn 1.6 run gives different bands)" and "Parts 1-3 train and score live; their numbers are expected to be close, not identical." The validation venv uses scikit-learn 1.6.1 (the contract's documented minimum), so the 8/13/243 split instead of the frozen 9/7/248 is the documented, expected outcome of retraining live rather than loading the frozen CSV - not a bug to fix. The same three highest-risk assets (`EQ-07040`, `EQ-02893`, `EQ-07412`) are at the top of both this run and the frozen reference.

## What is NOT validated and why

- Nothing ran against a real AML workspace, managed online/batch endpoint, Azure Container Registry, or GitHub Actions runner - no cloud credentials were used, per the hard rules.
- **No server-side validation.** The SDK loaders check the shape of each YAML on the client. A real `az ml ... create` (asset existence, quota, RBAC, region, preview features) was never done: rehearse the whole kit once in a scratch resource group.
- Bicep templates are syntax-checked only (`az bicep build`); they were never deployed or `what-if`-evaluated against a resource group.
- The monitoring schedule YAML (`jobs/monitoring/model-monitoring.schedule.yml`, preview) loads through the SDK as a `MonitorSchedule`, but the SDK has no local `_validate()` for it, so only its shape was loaded, not its content.
- The MLflow experiment-name behaviour inside a real job (`MLFLOW_RUN_ID`) is reasoned from MLflow's code, not observed; the kit pins `experiment_name` to stay clear of it.
- The OneLake datastore (`jobs/datastore-onelake.yml`, preview) loads through the SDK, but nothing created it in a real tenant. It is optional.
- Online-endpoint first-deployment timing (about 10 to 20 minutes) is a planning estimate, not a measurement; see `VERIFY-BEFORE-FRIDAY.md` and `aml-facts-for-slides.md` item 19.
- The four GitHub Actions workflow templates were parse-checked as YAML only; no workflow ran, the `az ml model share` flags and registry deployment reference are unverified, and OIDC federation (`azure/login@v2`) was reviewed on paper.

## Files kept in `results/` and `assets/`

- `results/gate-decision.json` - the real gate decision JSON quoted above (copy of `local-validation/out/train/evaluation.json`).
- `results/champion-metrics.json` and `results/challenger-metrics.json` - the two models' metrics from the same run. `assets/champion-metrics.json` is the champion file that step 2 of `rebuild-guide.md` registers as data asset `fleet-champion-metrics:1`.
- `results/registration.json` - the model registration record of the run.
- `results/drift-summary.json` - copy of `local-validation/out/drift/drift_summary.json` (47 combinations, 4 major).
- `results/score-summary.json` - copy of `local-validation/out/score/score_summary.json` (264 rows, risk bands 8/13/243, top-5 list).
- `results/pytest-output.txt` - the `pytest tests -q` console output (3 passed).

All bulk generated data under `local-validation/out/` (prepared features, synthetic telematics, MLflow run artifacts, models) was deleted after these small JSON/text summaries were copied out, per the final-cleanup rule.