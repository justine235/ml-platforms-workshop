# RESULTS — empirically validated facts (2026-10-19)

## THE KEY QUESTION — OSS MLflow registry stages and aliases

**Scope: OSS MLflow, local sqlite registry backend only — does not apply to Fabric or AML
managed registries (see `slide-facts.md` #9, #17, #18).**

| MLflow | Aliases | Stages | stage-transition warning | load-by-stage warning | MLflow-3 LoggedModel API |
|---|---|---|---|---|---|
| 2.12.2 | works | works | deprecated since 2.9.0 | yes | no |
| 2.16.2 | works | works | deprecated since 2.9.0 | yes | no |
| 2.22.0 | works | works | deprecated since 2.9.0 | no | no |
| 3.17.0 | works | works | deprecated since 2.9.0 | no | yes |

Full detail and raw JSON references: `validation\matrix.md`.

## Training/metrics validation

Ran `code\train_fleet_model.py` (model kind `hist_gradient_boosting`) through
`validation\registry_matrix.py` in 4 separate venvs, through the shared heavy-lock, on
2026-10-19:

- `.venv-mlflow2122` — MLflow 2.12.2, Python 3.11.9 (Fabric Runtime 1.3 LTS pin)
- `.venv-mlflow2162` — MLflow 2.16.2, Python 3.11.9 (Azure ML compatible pin)
- `.venv-mlflow2222` — MLflow 2.22.0, Python 3.13.15 (Fabric Runtime 2.0 pin)
- `.venv-mlflow3` — MLflow 3.17.0, Python 3.13.15 (latest 3.x)

All 4 runs produced **byte-identical** metrics: valid pr_auc 0.3490 / roc_auc 0.7037, test
pr_auc 0.3882 / roc_auc 0.7551, row/positive counts exactly matching
`02-demo-data\reference_out\ground_truth.json` within the contract's +-0.03 tolerance
(counts exact). Commands used (one per venv, via the shared `heavy.ps1` lock):

```powershell
& "<venv>\Scripts\python.exe" validation\registry_matrix.py --label <2122|2162|2222|3x> \
    --tracking-dir <scratch dir> --out-json <scratch json>
```

## Registry-ops probe (9 operations, all 4 versions)

register v2 -> set alias champion->v1 -> get_model_version_by_alias -> load by alias ->
transition v1->Staging -> transition v2->Production -> load by Production -> load by
Staging -> load by latest -> has_logged_model_api probe. **All 9 operations succeeded in
all 4 versions.** Raw JSON: `results\validation-2122.json`, `results\validation-2162.json`, `results\validation-2222.json`, `results\validation-3x.json`.

## A real bug found and fixed (not just a validation quirk)

MLflow 3.x's sklearn flavor defaults to `skops` serialization. `skops` is not an MLflow
dependency (must `pip install skops` separately) and its security scanner rejects
`HistGradientBoostingClassifier`'s internal `TreePredictor` type unless explicitly marked
trusted. **This would have crashed the presenter's live demo** the first time someone
re-loaded the registered model under MLflow 3.x. Fixed in `code\mlflow_compat.py`:
`skops_trusted_types_for()` + `log_sklearn_model()` now pass
`skops_trusted_types=["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"]`
only when `is_mlflow_3()` and the model needs it — no effect on MLflow 2.x calls. Covered by
3 new unit tests in `tests\test_mlflow_compat.py` (7/7 tests pass).

## Portability check

`portability\export_model_zip.py` run under MLflow 2.12.2, `portability\import_check.py`
run under MLflow 3.17.0 (oldest -> newest, widest gap tested): **PASS**, folder and zip both
reload with byte-identical predictions on 20 sample rows. Only non-fatal dependency-mismatch
warnings appear (expected — different mlflow/numpy/Python versions). The reverse direction
(MLflow-3-skops-exported model imported under MLflow 2.x) was NOT tested and is expected to
fail — `⚠ UNVERIFIED`, flagged as such in `validation\matrix.md`.

## Environment fact needed for any rebuild

A sqlite-backed MLflow tracking/registry store requires `sqlalchemy>=1.4,<2.1` and
`alembic<1.14` in every tested MLflow version (2.12.2 through 3.17.0) — the default pip
resolution of `sqlalchemy` (2.1.4 at the time of this build) breaks
`mlflow.store.db.utils` import with a missing `FallbackAsyncAdaptedQueuePool` symbol. Added
to `rebuild-guide.md` step A.2.

## Static checks

`py_compile`, `ruff` (via `.venv-mlflow2122`), `nbformat.validate` on
`code\mlflow_tour_local.ipynb` — all clean. `pytest tests\` — 7/7 passed (2026-10-19,
116s, `.venv-mlflow2122`).

## Local notebook: real NameError bug found and fixed, then executed end to end (2026-10-19)

`mlflow_tour_local.py`/`.ipynb` used `Path(__file__).resolve()...` to locate the code
folder and the shared feature table. `__file__` is not defined inside a Jupyter/VS Code
notebook kernel, so opening the notebook (the "Local notebook" path in `run-of-show.md`)
crashed with `NameError` on the very first code cell — before any MLflow concept was
shown. Static checks (`py_compile`, `ruff`, `nbformat.validate`) cannot catch this because
they do not execute the code; only running the notebook surfaces it.

Fix in `code\mlflow_tour_local.py` (regenerated `.ipynb` from it): `CODE_DIR` now tries
`Path(__file__).resolve().parent` and falls back to `Path.cwd().resolve()` on `NameError`,
then raises a readable `FileNotFoundError` naming the expected open-from folder if
`fleet_ml_core.py` is not next to it. `ROOT` is derived from `CODE_DIR`, so `python
mlflow_tour_local.py` keeps working unchanged.

While exercising the notebook for the first time end to end, a second real bug surfaced:
the registry demo cell (section 8) registered **both** `hist_gradient_boosting` and
`logistic_regression` as model versions, but only the HGB run ever logged an actual model
artifact. Loading `models:/<name>/latest` (section 9) then resolved to the
unlogged-model version and crashed with `OSError: No such file or directory`. Fixed by
also logging a signed sklearn model for the `logistic_regression` run (same
`log_sklearn_model` helper, same signature pattern) so every registered version has a
real model backing it.

Execution method: regenerated the fixed `.ipynb`, copied it plus `fleet_ml_core.py`,
`mlflow_compat.py`, and the feature table into a scratch mirror (same two-level relative
layout as the kit, so the `Path.cwd()` fallback and the `ROOT`/data lookup are exercised
exactly as a presenter would hit them — nothing was written back into the kit), then
executed headlessly with `nbclient` (`NotebookClient(..., kernel_name="python3")`) in
`.venv-mlflow2122` (installed `nbclient`/`ipykernel` there), through the heavy lock.

Result: **PASS.** All 23 notebook cells (11 code cells) executed with zero error outputs.
Confirmed values match the training validation above: HGB test PR-AUC **0.3882**, test
ROC-AUC **0.7551** (contract target ~0.385/~0.75, well inside +/-0.03). Registry/alias/stage
cells ran end to end: `{'alias_supported': True, 'stage_supported': True}`, alias-loaded
prediction sample printed successfully, `search_runs` leaderboard and the `MLmodel`
line-by-line explainer cell both rendered correctly.

## Fabric and AML notebooks checked for the same pitfall class

Reviewed `fabric\nb_mlflow_tour_fabric.py`/`.ipynb` and `azureml\aml_mlflow_tour.py`/`.ipynb`
for `__file__` usage, bare `argparse.parse_args()`/`sys.argv` reads, and
`if __name__ == "__main__"` blocks holding the real work. **Neither file has any of these.**
Both already use `train_script.parse_args([...])` with an explicit argument list (never
bare `sys.argv`), and both already mark their workspace-specific path assumptions as
`⚠ UNVERIFIED` with a one-line rehearsal note (Fabric: lakehouse `Files/` path; AML:
`../code`/`../data` relative paths assuming a specific checkout layout). No code change was
needed or made in either file.

## NOT validated, and why

- Fabric and AML cloud behavior (real workspace model registration, endpoint deployment,
  Studio UI visibility of stages) — out of scope for this folder's rules (no cloud calls
  allowed); remains `⚠ UNVERIFIED`, rehearsal items #11/#12 in `VERIFY-BEFORE-FRIDAY.md`.
- Reverse-direction portability (MLflow-3 skops export -> MLflow-2.x import) — not
  exercised; expected to fail based on code inspection, not empirically confirmed.
- `fabric\nb_mlflow_tour_fabric.py` and `azureml\aml_mlflow_tour.py` execution — cannot run
  without a live workspace; validated only via `py_compile`/`ruff` static checks.

## Slide/doc accuracy — no corrections needed

`content_p1.py` slide P1.12 and `00-presenter-guide\03-qa-cheatsheet.md` Q7 were re-checked
against these empirical results: both are already correctly scoped to Fabric/AML managed
registries (not OSS), already carry `⚠` flags, and make no claim contradicted by this
validation. `concept-map.md`'s stage/alias rows likewise need no correction. See
`CHANGES-for-slides.md` for the one wording fix applied (`run-of-show.md`) and the new
empirical facts added (`slide-facts.md` #21-24).