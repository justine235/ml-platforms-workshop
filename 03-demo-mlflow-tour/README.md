# MLflow tour: local, Fabric, and Azure ML

## What this folder is

This folder is Part 1 of the workshop: a **25-minute live MLflow tour inside a 90-minute platform block**. It is built for an audience that already knows MLflow. The point is not to teach MLflow from zero. The point is to show, quickly and honestly, that the same MLflow concepts exist in:

- open-source MLflow on a laptop
- Microsoft Fabric
- Azure Machine Learning

And to show exactly where the operational wrappers differ: version pins, registry semantics, tracking URI shape, artifact movement, and what is unsupported.

## Architecture of the tour

1. **One shared data contract:** `02-demo-data\reference_out\ml_asset_day_features.csv.gz`
2. **One shared model core:** `code\fleet_ml_core.py` copied unchanged from `02-demo-data`
3. **One shared training script:** `code\train_fleet_model.py`
4. **Three notebook experiences:** local, Fabric, AML
5. **One portability proof:** export an MLflow model folder, zip it, reload it, and compare predictions

## Preconditions

### Local laptop

- Python 3.11 and/or 3.13
- Virtual environments created next to the kit: `.venv-mlflow2122`, `.venv-mlflow2162`, `.venv-mlflow2222`, `.venv-mlflow3`
- No cloud access required
- To run the local notebook: add `ipykernel` to the venv you choose, open `code\mlflow_tour_local.ipynb` in VS Code and select that venv as the kernel. The notebook finds its files from its own folder, so open it from `code\`
- Expected local reference metrics from the contract:
  - HGB test PR-AUC about **0.385**
  - HGB test ROC-AUC about **0.75**
  - tolerance **+/- 0.03**

### Fabric

- Fabric workspace with notebook access
- Runtime 1.3 or 2.0
- If you want MLflow 3 features, notebook-scoped `%pip install`
- If you want the data agent later in the day, the workshop needs a paid F-SKU; trial is not enough for the data-agent part

### Azure ML

- AML workspace and a CPU compute target named `cpu-cluster`
- AML-compatible environment pinned to `mlflow<=2.16.2` and `azureml-mlflow`
- Input data asset for the feature table

## File index

| File | Purpose |
|---|---|
| `concept-map.md` | Reference comparison table: OSS MLflow vs Fabric vs AML |
| `code\train_fleet_model.py` | Shared CLI training script used everywhere |
| `code\mlflow_compat.py` | MLflow 2.x / 3.x compatibility layer |
| `code\mlflow_tour_local.py` + `.ipynb` | Local rehearsal notebook |
| `fabric\nb_mlflow_tour_fabric.py` + `.ipynb` | Fabric notebook tour |
| `azureml\aml_mlflow_tour.py` + `.ipynb` | AML notebook tour |
| `azureml\job-train-fleet.yml` | AML command job using the shared script |
| `azureml\conda-train-fleet.yml` | AML-compatible environment pin |
| `portability\export_model_zip.py` | Export the MLflow model folder and zip it |
| `portability\import_check.py` | Reload folder and zip; compare predictions |
| `portability\portability.md` | Portable artifact story and limits |
| `tests\` | Compat and smoke tests |
| `validation\matrix.md` | Actual version-by-version run results |
| `rebuild-guide.md` | Rebuild steps from empty laptop / Fabric / AML |
| `run-of-show.md` | 25-minute live script + 10-minute short version |
| `troubleshooting.md` | Real failure modes and fixes |
| `VERIFY-BEFORE-FRIDAY.md` | Checklist for every unverified or preview claim |
| `slide-facts.md` | 24 one-line slide-ready facts with sources |
| `RESULTS.md` | Validated facts, commands, metrics, and the stages/aliases table (2026-10-19) |
| `CHANGES-for-slides.md` | Per-slide-id changes given the measured validation results |
| `STATUS.md` | Build status / resume note |

## Suggested time plan

| Segment | Minutes | What happens |
|---|---:|---|
| Local MLflow baseline | 7 | Show experiment, runs, nested runs, params/metrics/artifacts, model package |
| Fabric mapping | 7 | Show same concepts in Experiment + ML model items, call out defaults and differences |
| Azure ML mapping | 7 | Show same script in AML, tracking URI, registration, no-code deployment story |
| Portability + summary | 4 | Show model-folder portability and honest limits |

## What to say in one sentence

"Fabric and Azure ML both speak real MLflow; the **model artifact is portable**, but the **operational wrappers are not identical**."
