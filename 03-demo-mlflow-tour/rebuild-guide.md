# Rebuild guide

This guide is written so a competent data engineer can rebuild the MLflow tour from scratch on a laptop, then map it to Fabric and Azure ML.

Run every command from the workshop folder, the one that contains `02-demo-data` and `03-demo-mlflow-tour`. The `.venv-mlflow*` folders and the `work\` folder are created there too.

## A. Empty laptop rebuild

### 1. Create the versioned environments

- **Goal:** create the exact local environments used for the compatibility tour.
- **Action:**

  ```powershell
  py -3.11 -m venv .venv-mlflow2122
  py -3.11 -m venv .venv-mlflow2162
  py -3.13 -m venv .venv-mlflow2222
  py -3.13 -m venv .venv-mlflow3
  ```

- **Expected result:** four venv folders exist next to the kit (`.venv-mlflow2122`, `.venv-mlflow2162`, `.venv-mlflow2222`, `.venv-mlflow3`).
- **Duration:** 2-4 minutes.
- **What to say:** "We are not changing the ML problem. We are changing only the MLflow runtime around it."
- **What can go wrong + fix:** if `py -3.11` is missing, install Python 3.11 first or adjust to the nearest supported interpreter.
- **Fallback:** keep one prebuilt working venv zipped in `work\`.

### 2. Install the required packages

- **Goal:** create platform-aligned package sets.
- **Action:** install the exact package pins listed in `validation\matrix.md`.
- **Required for every version (empirically confirmed, not optional):** pin `sqlalchemy>=1.4,<2.1` and `alembic<1.14` before using a sqlite-backed registry store, or `mlflow.store.db.utils` import fails. On `.venv-mlflow3` specifically, also install the `skops` package (MLflow 3's default sklearn serializer).
- **Expected result:** each venv imports `mlflow`, `pandas`, `sklearn`, `nbformat`, `pytest`, and `ruff`. The venv you will open the local notebook with (`.venv-mlflow2222` is a good default) also needs `ipykernel`, so that VS Code or Jupyter can use it as a kernel without downloading anything in the room.
- **Duration:** 10-20 minutes depending on network and wheel cache.
- **What to say:** "This is one of the real-world differences: AML is pinned to an older MLflow line, while Fabric runtime 2.0 already ships a newer one."
- **What can go wrong + fix:** if `azureml-mlflow` refuses a newer MLflow, do not fight it; pin `mlflow<=2.16.2`.
- **Fallback:** skip the 2.12.2 run if it is not installable in the rehearsal environment and record that clearly.

### 3. Run the shared training script locally

- **Goal:** prove the common MLflow workflow on a laptop.
- **Action:**

  ```powershell
  .venv-mlflow2222\Scripts\python.exe `
    03-demo-mlflow-tour\code\train_fleet_model.py `
    --features 02-demo-data\reference_out\ml_asset_day_features.csv.gz `
    --experiment fleet-failure-7d `
    --model-kind hist_gradient_boosting `
    --run-name local-hgb `
    --summary-json work\local-hgb-summary.json
  ```

- **Expected result:** the JSON summary includes the six workshop metric names and test PR-AUC about **0.385** and test ROC-AUC about **0.75** within **+/- 0.03** of the contract.
- **Duration:** about 1-2 minutes once the environment is warm.
- **What to say:** "Same experiment, run, params, metrics, artifacts, and model package you already know from open-source MLflow."
- **What can go wrong + fix:** if the metric is far outside tolerance, verify you used the shared feature table and did not reshuffle the splits.
- **Fallback:** keep a saved `summary.json` from a known-good rehearsal run.

### 4. Rebuild the local notebook

- **Goal:** regenerate the `.ipynb` from the percent-format source.
- **Action:**

  ```powershell
  .venv-mlflow2222\Scripts\python.exe `
    03-demo-mlflow-tour\code\percent_to_notebook.py `
    03-demo-mlflow-tour\code\mlflow_tour_local.py `
    03-demo-mlflow-tour\code\mlflow_tour_local.ipynb
  ```

- **Expected result:** `mlflow_tour_local.ipynb` exists and validates with `nbformat`.
- **Duration:** under 30 seconds.
- **What to say:** "The `.py` percent notebook is the source of truth; the `.ipynb` is a build artifact."
- **What can go wrong + fix:** if validation fails, check that every cell marker starts with `# %%`.
- **Fallback:** keep the already-built `.ipynb` in the folder.

### 5. Rebuild the portability demo

- **Goal:** prove the model package itself is portable.
- **Action:** run `portability\export_model_zip.py`, then `portability\import_check.py`.
- **Expected result:** the folder and zip predict identically on the sample input.
- **Duration:** 1-2 minutes.
- **What to say:** "The model folder is portable. The experiment history is not."
- **What can go wrong + fix:** if the zip check fails, recreate the zip from the exported folder.
- **Fallback:** show the already-created `out\model-folder` instead of rebuilding live.

## B. Empty Fabric workspace rebuild

### 6. Create the Fabric notebook context

- **Goal:** prepare a workspace that can demonstrate MLflow in Fabric.
- **Action:** upload or Git-sync the workshop folder; create/open a notebook using Runtime 2.0 or 1.3.
- **Expected result:** notebook starts; `import mlflow` works; `mlflow.__version__` matches the runtime line you chose.
- **Duration:** 3-5 minutes if the workspace already exists.
- **What to say:** "Fabric already wraps MLflow inside the workspace. That is why the tracking URI feels invisible in the default notebook path."
- **What can go wrong + fix:** if the runtime version is wrong, switch the notebook environment or workspace Spark setting.
- **Fallback:** show the local notebook first, then a prebuilt Fabric Experiment item.

### 7. Optionally upgrade to MLflow 3 in Fabric

- **Goal:** show LoggedModel and Traces only if you want the GenAI extension.
- **Action:** run the `%pip install` cell in `fabric\nb_mlflow_tour_fabric.py`, then restart the session.
- **Expected result:** `mlflow.__version__` shows the MLflow 3 pin you chose.
- **Duration:** 2-6 minutes depending on wheel download and restart.
- **What to say:** "Fabric supports MLflow 3, but it does not ship it by default in the runtime today."
- **What can go wrong + fix:** if the session does not restart cleanly, reopen the notebook session before continuing.
- **Fallback:** skip the MLflow 3 cell and keep the comparison on classic tracking/model concepts.

### 8. Run the shared training script from Fabric

- **Goal:** prove the same training script works in Fabric.
- **Action:** set the `CODE_DIR` and `FEATURES_PATH` in `fabric\nb_mlflow_tour_fabric.py`, then run the training cell.
- **Expected result:** a new run appears in the Fabric Experiment item, with params/metrics/artifacts and a logged model.
- **Duration:** 2-4 minutes.
- **What to say:** "Same script. Same run semantics. Different tracking backend."
- **What can go wrong + fix:** if the notebook cannot import the code folder, fix the lakehouse Files path before the live demo.
- **Fallback:** show a prebuilt Fabric run and focus on the Experiment/ML model UI.

## C. Empty Azure ML workspace rebuild

### 9. Build the AML-compatible environment

- **Goal:** create the AML-safe package pin.
- **Action:** use `azureml\conda-train-fleet.yml` as the environment definition.
- **Expected result:** environment resolves with `mlflow==2.16.2` and `azureml-mlflow`.
- **Duration:** 5-15 minutes depending on image build and cache state.
- **What to say:** "This pin is a real platform constraint, not a workshop preference."
- **What can go wrong + fix:** if someone upgrades MLflow, revert to `<=2.16.2`.
- **Fallback:** keep a prebuilt environment named `env-fleet-sklearn`.

### 10. Register the feature file as a data asset

- **Goal:** give the AML job a stable input asset.
- **Action:** create or upload a `uri_file` data asset named `fleet-features-ref` from `02-demo-data\reference_out\ml_asset_day_features.csv.gz`.
- **Expected result:** AML can resolve `azureml:fleet-features-ref:1`.
- **Duration:** 2-5 minutes.
- **What to say:** "Same file, different wrapper: Fabric points at lakehouse Files, AML points at a data asset."
- **What can go wrong + fix:** if the job cannot resolve the asset, check the asset name and version in the YAML.
- **Fallback:** replace the YAML asset reference with a direct path during rehearsal only.

### 11. Submit the AML command job

- **Goal:** run the shared script as an AML command job.
- **Action:** use `azureml\job-train-fleet.yml`.
- **Expected result:** the job runs on `cpu-cluster`, logs metrics into the AML tracking store, and registers `fleet-failure-7d`.
- **Duration:** 5-15 minutes depending on cluster warm-up.
- **What to say:** "Inside AML jobs, tracking is configured for us automatically."
- **What can go wrong + fix:** if the job starts but tracking is empty, verify the environment really includes `azureml-mlflow`.
- **Fallback:** run the AML notebook path on a compute instance and set the tracking URI explicitly.

## D. Pre-flight before the audience arrives

1. Rebuild the notebooks from the percent sources.
2. Run the shared training script once per supported MLflow version and refresh `validation\matrix.md`.
3. Precreate at least one successful local run, one successful Fabric run, and one successful AML run.
4. Warm the AML compute cluster and verify the Fabric notebook environment.
5. Keep the portability `out\` folder and a prebuilt `summary.json` as break-glass assets.
