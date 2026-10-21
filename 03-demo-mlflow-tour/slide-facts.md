# 24 verified slide facts for Part 1

1. **Fabric Runtime 2.0 documents Python 3.13, Spark 4.1, and Delta Lake 4.2.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
2. **Fabric Runtime 1.3 LTS ships `mlflow-skinny 2.12.2`.**  
   Source: https://github.com/microsoft/synapse-spark-runtime
3. **Fabric Runtime 2.0 ships `mlflow-skinny 2.22.0`.**  
   Source: https://github.com/microsoft/synapse-spark-runtime
4. **Fabric supports MLflow 3 up to 3.1, but notebooks still ship MLflow 2.x by default.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview
5. **Fabric Data Science notebooks enable MLflow autologging by default.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
6. **Fabric cross-workspace tracking uses `sds://api.fabric.microsoft.com/v1/workspaces/<workspace-id>/mlflow`.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging
7. **Fabric exposes experiments as first-class Experiment items.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment
8. **Fabric exposes registered models as ML model items.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model
9. **Fabric documentation emphasizes model versions; it does not present stages and aliases as the main model-item pattern.**  
   Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model
10. **Fabric `PREDICT` and `MLFlowTransformer` require an MLflow-format model with a signature.**  
    Source: https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict
11. **Fabric ML model endpoints are available, but still in preview.**  
    Source: https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints
12. **AML documentation pins compatible MLflow usage to version 2.16.x or earlier.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
13. **AML docs explicitly recommend `pip install "mlflow<=2.16.2" azureml-mlflow "xgboost<=2.1.1" scikit-learn`.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
14. **AML jobs and AML notebooks configure MLflow tracking automatically inside AML compute.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
15. **External AML clients can fetch the workspace `mlflow_tracking_uri` and point MLflow at it.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
16. **AML supports MLflow model registration from a run URI and from a local MLflow model folder.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
17. **AML stages exist only through the MLflow SDK, not as first-class Studio / CLI / SDK-v2 features.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
18. **AML does not support deployment from a model stage.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
19. **AML managed online endpoints can deploy MLflow-format models without a custom scoring script.**  
    Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-mlflow-models-online-endpoints?view=azureml-api-2
20. **The safest cross-platform claim is that the MLflow model folder is portable, while platform lineage and registry semantics are not identical.**  
    Sources: https://mlflow.org/docs/latest/ml/model-registry/ ; https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model ; https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
21. **OSS MLflow registry stages and aliases both work today, local sqlite backend, across every version this workshop touches (2.12.2, 2.16.2, 2.22.0, 3.17.0).** Stage APIs (`transition_model_version_stage`, loading `models:/name/Production`) are deprecated since MLflow 2.9.0 but not removed through 3.17.0; aliases are the current, non-deprecated mechanism. This is OSS behavior only — it does not apply to Fabric or AML managed registries (see facts 9, 17, 18).  
    Source: empirical validation, this workshop, 2026-10-19 — `validation\matrix.md`.
22. **MLflow 3.x's sklearn flavor serializes with `skops` by default, not pickle, and `skops` is not an MLflow dependency — it must be installed separately.** `skops` additionally refuses to reload `HistGradientBoostingClassifier`/`Regressor` internals unless the type is explicitly marked trusted via `log_model(..., skops_trusted_types=[...])`; without this, this workshop's default model crashes on reload under MLflow 3.x.  
    Source: empirical validation, this workshop, 2026-10-19 — `validation\matrix.md`; fix applied in `code\mlflow_compat.py`.
23. **A sqlite-backed MLflow tracking/registry store requires `sqlalchemy>=1.4,<2.1` and `alembic<1.14`, independent of MLflow version (2.12.2 through 3.17.0 all hit the same import error otherwise).**  
    Source: empirical validation, this workshop, 2026-10-19 — `validation\matrix.md`.
24. **A model folder exported under MLflow 2.12.2 (pickle-serialized) loads and predicts correctly under MLflow 3.17.0, both from the folder and from a zip archive, byte-identical predictions — only non-fatal dependency-mismatch warnings appear. The reverse direction (export under MLflow 3.x skops format, import under MLflow 2.x) was not tested and is expected to fail.**  
    Source: empirical validation, this workshop, 2026-10-19 — `validation\matrix.md` (portability check section).