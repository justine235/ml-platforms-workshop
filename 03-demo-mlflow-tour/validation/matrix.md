# Validation matrix — OSS MLflow across 4 pinned versions

Last updated: 2026-10-19 (empirically run today; folder dates before this are stale).
All runs: local machine, sqlite-backed tracking+registry store, `code\train_fleet_model.py`
via `validation\registry_matrix.py` (not a copy of the script — same training path as the
demo), model kind `hist_gradient_boosting`, data file `ml_asset_day_features.csv.gz`
(sha256 `51384c56b0e52460c81dbda8ed4e8cb0c367f4220d5278fb89f9ad269bcb868d`).

Acceptance: metrics compared with `02-demo-data\reference_out\ground_truth.json`
(`ml.metrics_approximate.hist_gradient_boosting`, tolerance +-0.03 on AUCs; row/positive
counts must match exactly). **All 4 runs below meet this.**

## Why these 4 versions

- **2.12.2** — MLflow version shipped in Fabric Runtime 1.3 LTS.
- **2.16.2** — the version pinned for Azure ML curated environments at the time this
  workshop was built (AML-compatible pin).
- **2.22.0** — MLflow version shipped in Fabric Runtime 2.0.
- **3.17.0** (latest 3.x available today) — the current OSS release line.

## Training results (identical across all 4 — fully reproducible)

| MLflow | Python | pandas | numpy | scikit-learn | train_seconds (full script) | valid pr_auc / roc_auc | test pr_auc / roc_auc | vs ground truth |
|---|---|---|---|---|---|---|---|---|
| 2.12.2 | 3.11.9 | 2.2.3 | 2.4.6 | 1.6.1 | 35.8 | 0.3490 / 0.7037 | 0.3882 / 0.7551 | within tolerance |
| 2.16.2 | 3.11.9 | 2.2.3 | 2.4.6 | 1.6.1 | 105.4 | 0.3490 / 0.7037 | 0.3882 / 0.7551 | within tolerance |
| 2.22.0 | 3.13.15 | 2.2.3 | 2.5.4 | 1.6.1 | 62.3 | 0.3490 / 0.7037 | 0.3882 / 0.7551 | within tolerance |
| 3.17.0 | 3.13.15 | 2.2.3 | 2.5.4 | 1.6.1 | 84.6 | 0.3490 / 0.7037 | 0.3882 / 0.7551 | within tolerance |

Row/positive counts (train 28520/1639, valid 6591/353, test 6111/274) are byte-identical
in all 4 runs — the pipeline is fully deterministic given the fixed data file and params.
`train_seconds` is wall-clock for the whole script invocation (env import + data load +
train + log + score); it varies with machine load from sibling agents, not with MLflow
version — do not read it as a performance comparison. The actual model-fit time
(`durations.train_seconds` in each JSON) is 4.4s / 28.2s / 14.0s / 12.4s respectively and is
noisier for the same load-variance reason; do not present it as an MLflow-version effect either.

## THE KEY QUESTION — do OSS registry stages and aliases work? (empirical answer)

**Scope: OSS MLflow with a local sqlite backend store only.** This does NOT apply to
Fabric ML model registry or Azure ML's MLflow-compatible registry — those are separate,
managed implementations with their own documented support surface (see
`01-slides\content_p1.py` slide P1.12 and `00-presenter-guide\03-qa-cheatsheet.md` Q7,
both already correctly scoped and unchanged by this validation).

Tested end to end in every version: register v1 + v2 of a model, `set_registered_model_alias`
(champion -> v1), `get_model_version_by_alias`, `mlflow.pyfunc.load_model("models:/name@champion")`,
`transition_model_version_stage` (v1 -> Staging, v2 -> Production), then load by
`models:/name/Production`, `/Staging`, `/latest`.

| MLflow | Aliases work? | Stages work? | `transition_model_version_stage` warning | `get_latest_versions`/load-by-stage warning | MLflow-3 LoggedModel API present |
|---|---|---|---|---|---|
| 2.12.2 | Yes | Yes | deprecated since 2.9.0 | **yes**, warns | No |
| 2.16.2 | Yes | Yes | deprecated since 2.9.0 | **yes**, warns | No |
| 2.22.0 | Yes | Yes | deprecated since 2.9.0 | **no warning** | No |
| 3.17.0 | Yes | Yes | deprecated since 2.9.0 | **no warning** | **Yes** |

**Answer: in OSS MLflow with a sqlite registry backend, both stages and aliases work in
all 4 versions tested (2.12.2 through 3.17.0).** Stage APIs (`transition_model_version_stage`,
loading `models:/name/Production`, `/Staging`) are deprecated since MLflow 2.9.0 and still
present everywhere tested; no removal has happened in any version up to 3.17.0. Aliases are
the modern, non-deprecated mechanism and work identically across all 4. The one real
behavioral drift: 2.12.2/2.16.2 emit a deprecation warning when a model is loaded *by stage*
(via `get_latest_versions` internally); 2.22.0 and 3.17.0 no longer emit that specific
warning (the `transition_model_version_stage` call itself still warns in all 4).

MLflow 3.17.0 additionally exposes a `LoggedModel`/model-URI (`models:/m-<id>`) concept
alongside the classic registry; `has_logged_model_api` probe (checking for
`mlflow.client.MlflowClient.search_logged_models` or equivalent) is `true` only in 3.x. This
is additive — the classic `transition_model_version_stage`/alias registry calls still worked
unchanged in 3.17.0 in this test.

## API differences found, by version

- **sqlite registry backend store (ALL versions, 2.12.2 through 3.17.0)**: the sqlite-backed
  model registry requires `sqlalchemy>=1.4,<2.1` and `alembic<1.14` in the venv. The default
  resolved `sqlalchemy` (2.1.4 as pulled by pip today) breaks
  `mlflow.store.db.utils` import with
  `ImportError: cannot import name 'FallbackAsyncAdaptedQueuePool' from 'sqlalchemy.pool'`
  in every MLflow version tested, including 3.17.0. This is not an MLflow-version-specific
  issue — pin `sqlalchemy<2.1` and `alembic<1.14` whenever a sqlite (or any DB) backend store
  is used, regardless of MLflow version. File-store-only tracking (no registry) does not need
  this pin.
- **MLflow 3.x only — sklearn flavor defaults to `skops` serialization, not pickle.** This is
  a real, demo-breaking difference (not just a validation-script quirk): `mlflow.sklearn.log_model`
  on MLflow 3.x uses `skops` by default, and `skops` is not an MLflow dependency — the `skops`
  package must be installed separately, or `log_model` raises `ModuleNotFoundError: No module
  named 'skops'`. Once installed, loading a logged `HistGradientBoostingClassifier` (this
  workshop's default model kind) then fails with
  `skops.io.exceptions.UntrustedTypesFoundException: Untrusted types found in the file:
  ['sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor']` — skops' security
  scanner refuses to deserialize `TreePredictor`'s raw node-index arrays unless explicitly
  told they're trusted. **Fix applied in `code\mlflow_compat.py`**: `log_sklearn_model()` now
  calls a new `skops_trusted_types_for(model)` helper and passes
  `skops_trusted_types=["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]`
  to `log_model(...)` when running under MLflow 3.x and the model is (or contains, if a
  pipeline) a `HistGradientBoostingClassifier`/`Regressor`. This kwarg does not exist in
  MLflow 2.x and is only passed when `is_mlflow_3()`. Without this fix, the presenter's
  default run would crash live on MLflow 3.x at the "load the registered model back" step.
- **MLflow 3.x — registration path differs when there are no run-relative artifacts.** The
  3.17.0 run logged a warning not seen in 2.x: `Run ... has no artifacts at artifact path
  'model', registering model based on models:/m-<id> instead` — MLflow 3's `log_model` already
  registers a `LoggedModel` at log time (`model_uri` returned is `models:/m-<hash>`, not
  `runs:/<run_id>/model` as in 2.x), and `mlflow.register_model` on the run-relative path then
  falls back to the LoggedModel URI. Functionally harmless here (still produces a correct
  registry version) but worth mentioning if a presenter is asked why the `model_uri` format
  looks different in 3.x traces.
- **Signature/schema warning (all versions, pre-existing, not new)**: every run emits
  `UserWarning: Hint: Inferred schema contains integer column(s)...` from
  `mlflow.types.utils` — expected given this dataset's integer columns; not an error, and not
  version-specific.

## Portability check (export under one MLflow version, import under another)

Ran `portability\export_model_zip.py` under MLflow 2.12.2 (`.venv-mlflow2122`), then
`portability\import_check.py` under MLflow 3.17.0 (`.venv-mlflow3`) — the oldest and
newest versions tested, to stress the widest possible gap. Both the exported model folder
and its zip archive were loaded, and predictions on 20 sample rows were compared against
the reference predictions captured at export time.

Result: **PASS.** `folder_matches_reference: true`, `zip_matches_folder: true` (byte-identical
predictions). MLflow 3.17.0 printed non-fatal warnings (dependency-version mismatch:
`mlflow==2.12.2` vs installed `3.17.0`; `numpy` mismatch; Python 3.11.9 vs 3.13.15) but loaded
and predicted correctly regardless.

Why this worked despite the MLflow-3 skops finding above: the model was *exported* by
MLflow 2.12.2, which serializes with pickle/cloudpickle, not skops. MLflow's pyfunc loader
reads the serialization format from the model's own `MLmodel`/flavor metadata, not from the
currently-installed MLflow version, so a pickle-serialized model loads fine under MLflow 3.x.
The skops/`UntrustedTypesFoundException` issue found above only happens when a model is both
*logged and reloaded* under MLflow 3.x's own default (skops) serialization — it is not a
portability regression for models already trained under 2.x. **Caveat (not tested today,
would need the reverse direction)**: exporting a `HistGradientBoostingClassifier` *under*
MLflow 3.x (skops format) and importing it under an MLflow 2.x venv would likely fail outright
— MLflow 2.x's sklearn flavor loader does not know about skops at all. This directionality
(2.x -> 3.x pickle import: fine; 3.x skops export -> 2.x import: expected to fail, not
exercised) should be called out to presenters as a one-way portability result, ⚠ UNVERIFIED
for the reverse direction.
