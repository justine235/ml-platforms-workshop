# Troubleshooting

| Symptom | Where | Likely cause | Fix | Break-glass fallback |
|---|---|---|---|---|
| HGB test PR-AUC is far from 0.385 | Local / Fabric / AML | Wrong input file, wrong split usage, or accidental reshuffle | Use `02-demo-data\reference_out\ml_asset_day_features.csv.gz` and do not re-split | Show the saved validation matrix |
| `mlflow.register_model` fails on local file tracking | Local | Registry backend is not database-backed | Use the notebook's SQLite backend, not a plain `file://` tracking store | Skip registry and focus on run artifacts |
| Signature error during scoring | Local / Fabric / AML | Missing or incorrect signature | Re-log the model with `infer_signature(...)` and `input_example=` | Use the prebuilt logged model |
| Fabric notebook imports fail | Fabric | Wrong `Files/` path or repo mirror path | Fix `CODE_DIR` and `FEATURES_PATH` in the notebook before Friday | Use a copied notebook cell instead of importing the script |
| Fabric `%pip` cell breaks the session | Fabric | Session restart not completed or package conflict | Restart the notebook kernel after `%pip` and rerun from the top | Stay on runtime MLflow 2.22.0 and skip MLflow 3 |
| `PREDICT` or `MLFlowTransformer` refuses the model | Fabric | Model has no usable signature | Re-log the model with signature and input example | Point to B2b's prebuilt scoring notebook |
| AML job logs no MLflow run | AML | Environment missing `azureml-mlflow` or bad pin | Rebuild the environment from `conda-train-fleet.yml` | Run the AML notebook path on a compute instance |
| AML job cannot resolve `azureml:fleet-features-ref:1` | AML | Data asset missing or wrong version | Recreate the asset or update `job-train-fleet.yml` to the real asset version | Use a direct path for rehearsal only |
| AML registration works but stage workflow is confusing | AML | Stages are MLflow-SDK-only in AML | Demo explicit version loading instead of stage-based deployment | Skip stages in the live flow |
| Model-folder portability check fails | Local | Folder or zip was modified after export | Rerun `export_model_zip.py` and repeat the import check | Load the folder directly instead of the zip |

## Platform-specific truths worth saying out loud

- **Fabric:** model endpoints are `⚠ PREVIEW`, and Git/deployment promotion for ML items is metadata-only.
- **AML:** `azureml-mlflow` is pinned to `mlflow<=2.16.2`, so do not promise MLflow 3 features there.
- **Everywhere:** the model package is portable, not the full experiment lineage.
