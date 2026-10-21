# Azure ML facts for slides

1. Azure ML v2 is the current AML platform; CLI v1 support ended 2025-09-30 and Python SDK v1 support ended 2026-06-30. Source: AML fact sheet / Microsoft Learn AML v2 status.
2. AML's MLflow integration is pinned to MLflow 2.16.x and earlier; MLflow 2.17+ and MLflow 3 LoggedModels are not supported by `azureml-mlflow`. Source: `how-to-log-mlflow-models`.
3. AML workspaces are MLflow-compatible tracking servers and expose an `azureml://...` tracking URI. Source: `how-to-use-mlflow-configure-tracking`.
4. Managed online endpoints support key auth, AML token auth, and Entra token auth. Source: `concept-endpoints-online`.
5. Managed online endpoints support traffic split and mirrored traffic for safe rollout. Mirroring is capped at 50% of traffic, covers one shadow deployment, is not available for Kubernetes endpoints, and a deployment is either live or mirrored, never both (clear the mirror before it gets live traffic). A call that names a deployment is not mirrored. Source: `how-to-safely-rollout-online-endpoints`.
6. AML supports no-code deployment of MLflow models to managed online endpoints. Source: `how-to-log-mlflow-models` and AML endpoint docs.
7. AML also supports no-code deployment of MLflow models to batch endpoints. Source: `how-to-use-batch-model-deployments`.
8. Registries are Microsoft's recommended way to share models, components, and environments across AML workspaces. Source: AML fact sheet / registry docs.
9. GitHub Actions with `azure/login@v2` and OIDC is the recommended GitHub authentication pattern for AML. Source: `how-to-github-actions-machine-learning`.
10. AML model monitoring is current, but some related experiences such as the Responsible AI dashboard and managed feature store remain preview. Source: AML fact sheet.
11. OneLake `/Files` is directly usable from AML, including ABFSS paths and AML datastores. Source: `Integrate OneLake with Azure Machine Learning`.
12. The easy documented `/Tables` path from Fabric to AML still commonly involves a copy to ADLS Gen2 first. Source: `Integrate OneLake with Azure Machine Learning`.
13. Fabric Data Factory can orchestrate AML through the Azure Machine Learning activity. Source: `Azure Machine Learning activity - Microsoft Fabric`.
14. Azure ML remains the dedicated Microsoft platform for classic ML training, endpoints, and MLOps, while Foundry is positioned around GenAI and agents. Source: AML fact sheet.
15. For this workshop, the strongest hybrid pattern is Fabric ETL -> OneLake Files -> Azure ML training and serving. Source: Fabric and AML fact sheets plus the OneLake integration doc.

## Local validation run (static checks + one offline run, no cloud) - 2026-10-19

These facts come from running `local-validation/run_local.py` once end to end. No Azure subscription was used; this is a local rehearsal of the same `src/*.py` scripts that the AML pipeline YAML wraps.

16. Local pipeline exit line: `Local pipeline OK`, `test_pr_auc=0.3882`, `scored_rows=264`, `major_drift_pairs=4`, `gate_approved=True`. Full numbers and the real gate decision JSON are in `RESULTS.md`.
17. Step names and what each one does, for narrating the demo: `prep` (build `prepared_features` from the reference export), `train` (fit the challenger HistGradientBoosting model and a champion logistic-regression baseline, log both to MLflow), `evaluate` (score the challenger on the frozen test split and build `evaluation.json`), `gate` (compare challenger vs champion metrics, write `approved: true/false`), `register` (register a new MLflow model version only if the gate approved), `score` (batch-score the frozen 2026-09-30 asset list), `drift` (compute PSI between the reference months and the extra `telematics_drift` month).
18. Pipeline-stage durations observed on a laptop CPU with no cloud compute (informational only, not a timing rehearsal): `prep` about 10 s, `train` (champion plus challenger) about 15 s combined, `evaluate`+`gate`+`register` about 5 s, synthetic drift-month data regeneration about 21 s, drift computation 1-2 min. ⚠ UNVERIFIED for real AML managed compute: cold `cpu-cluster` start-up, environment image pull, and job orchestration overhead are not simulated locally and will dominate the live timing.
19. What must be pre-baked before the live demo so the 45-minute P3.15 slot is realistic: the AML workspace, `cpu-cluster`, and the `env-fleet-sklearn` environment image must already exist and be warmed by one prior successful pipeline run; the managed online endpoint `fleet-risk-online` should already have a blue deployment live before the session starts. ⚠ UNVERIFIED (planning estimate, not measured in a live tenant, consistent with `VERIFY-BEFORE-FRIDAY.md`): the **first** online deployment of a brand-new environment image can take roughly 10 to 20 minutes end to end (image build plus container provisioning), so it must be pre-baked and never attempted live for the first time.
20. The gate rule is identical, word for word, in `src/gate.py`, `tests/test_gate.py`, and every doc that quotes it: `challenger test_pr_auc >= champion + 0.01 AND challenger precision@top5% >= champion - 0.02`.