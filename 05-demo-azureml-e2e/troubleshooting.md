# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `az ml job create` waits several minutes before starting | `cpu-cluster` is cold | Warm the cluster before the workshop or temporarily set min nodes to 1 during rehearsal |
| Environment build fails on MLflow packages | MLflow or `azureml-mlflow` drift | Keep `mlflow==2.16.2` and do not upgrade to MLflow 2.17+ or MLflow 3 |
| Managed online deployment fails during image pull | Workspace identity lacks ACR permissions | Recheck the ACR role assignment for the AML workspace identity |
| Endpoint provisioning times out | SKU quota too low, or the first image build is still running | Verify DS3_v2 quota, then prebuild the image and retry |
| `invoke` fails with schema or payload errors | Request format does not match the MLflow model signature | Use `sample-request.json` and AML's `input_data` wrapper; keep the 42 feature columns only |
| Batch endpoint run starts then fails on input parsing | Input file has ID or label columns that were not in the model signature | Score the prepared feature contract, not a raw export |
| Gate rejects a new model | PR-AUC gain is below +0.01 or precision@top5% drops by more than 0.02 | Inspect `evaluation.json`, compare with the champion metrics, and keep the current model |
| PSI job shows unexpected classes or too many alerts | Reference/current windows are wrong or raw telemetry was not filtered to `RUN` | Use September 2026 as the reference window and October 1-14 drift data as the current window |
| Fabric cannot call the AML batch path | The Fabric AML activity is pointed at the wrong endpoint type or storage path | Use a batch endpoint, not an online endpoint, and keep the input/output on shared ADLS or a supported shortcut path |
| No-code MLflow endpoint returns different output shape than expected | MLflow serving wrapped the sklearn classifier in the standard scoring server | Test the exact output contract before Friday and update the demo narration if the service returns class probabilities rather than a single scalar |
| `az ml ... create` says an asset, environment or data version was not found | Step 2 of `rebuild-guide.md` was skipped, or the CLI points at another workspace | Register the environment and the three data assets first; check `az configure -l` for the default group and workspace |
| `Cannot start run with ID ... because active run ID does not match environment run ID` | `mlflow.set_experiment()` in `train.py` names another experiment than the job's `experiment_name` | Keep `experiment_name: fleet-failure-7d` in the job YAML (the sweep uses `fleet-failure-7d-sweep`); if it persists, remove or guard `set_experiment` in `train.py` line 46 |
| `Environment schema data cannot be a string` or similar environment error on a job | `environment:` holds a bare path | Use `azureml:env-fleet-sklearn:1` (or `file:...` or an inline definition), after registering the environment |
| `Unsupported annotation type` while building the SDK pipeline | `from __future__ import annotations` in a script that uses `@pipeline` | Remove that import from the script (`sdk\run_pipeline.py` has none) |
| `validate_yaml_schemas.py` reports errors that `validate_with_sdk_loaders.py` does not | The published JSON schemas lag the SDK and the CLI (for example a schedule flagged for a root `create_job` key) | Trust the SDK-loader check, and a real `az ml ... create` over both |

## Extra checks

- **Quota:** verify the DS3_v2 family in the chosen region.
- **RBAC:** the presenter needs workspace access and storage access; the workspace identity needs storage, Key Vault, and ACR access.
- **Preview drift:** recheck the preview monitoring schedule schema in the tenant before using it live.
