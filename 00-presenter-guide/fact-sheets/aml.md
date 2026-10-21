# Azure Machine Learning + MLflow + MLOps fact sheet (verified for workshop prep)

**Scope/date:** Verified against Microsoft Learn / Azure Architecture Center / Azure samples / PyPI / Azure Retail Prices API on **2026-10-18**. Audience: engineers building a **classic ML + MLOps** demo in Azure Machine Learning (AML), with Fabric/Foundry interplay.

## 0) Executive snapshot

| Topic | Current position |
|---|---|
| AML + MLflow compatibility | **Critical:** AML docs now explicitly pin compatibility to **MLflow 2.16.x and earlier**; **MLflow 2.17+ / MLflow 3 LoggedModels changes are not supported by `azureml-mlflow`**. (Current, doc 2026-02-10, S1) |
| AML v2 platform | **Current production platform** for jobs, pipelines, endpoints, registries, schedules, AutoML, monitoring. CLI/SDK v1 are past support end. (Current, doc 2026-09-09; retirement dates from Learn, S2/S3) |
| Foundry vs AML | Microsoft positions **Foundry** for agents/models/tools/GenAI; **AML** remains the Microsoft service for training, classical/deep ML, endpoints, and MLOps. (Current, docs 2026-09-24 and 2026-09-09, S4/S2) |
| Fabric vs AML MLflow | **Fabric supports MLflow 3.x/LoggedModel/Traces; AML does not.** Do not design a cross-platform demo around MLflow 3 entities if AML is the deployment target. (Current, docs 2026-09-02 and 2026-02-10, S5/S1) |
| OneLake from AML | `/Files` access is documented; `/Tables` direct no-copy is **not** the easy path and often requires copy/workaround. AML `OneLakeDatastore` Python class is **experimental**. (Current, docs 2026-09-02 / 2026-09-09, S6/S7) |
| Managed online endpoints | Support **key / `aml_token` / `aad_token`**, traffic split, mirrored traffic, autoscale, App Insights/logs. Watch the **20% extra quota reservation** on some SKUs. (Current, docs 2026-03 to 2026-09, S8/S9/S10) |
| Prompt flow | Still documented in AML, but **retired 2027-04-20** and not recommended for new development. (Current, doc 2026-09-09, S2) |
| Managed feature store / Responsible AI dashboard | Feature store and Responsible AI dashboard/scorecard remain **preview** items you should avoid depending on for a live customer demo unless already proven in your tenant. (Current, docs 2025-10 to 2026-01, S11/S12) |

## 1) Versions / packages to pin

| Package / tool | Verified state |
|---|---|
| `mlflow` for AML | **Use `<=2.16.2`**. AML doc explicitly recommends `pip install "mlflow<=2.16.2" azureml-mlflow "xgboost<=2.1.1" scikit-learn`. (Current, doc 2026-02-10, S1) |
| `azureml-mlflow` | Latest PyPI seen during research: **1.62.0.post6** (release 2026-09-02). Treat plugin compatibility, not PyPI latest MLflow, as source of truth. (PyPI release page, 2026-09-02, S13) |
| `mlflow-skinny` | Latest PyPI seen: **3.17.1** (release 2026-10-13), but that does **not** mean AML supports it end-to-end. AML compatibility remains tied to MLflow 2.16.x. (PyPI + AML doc, S14/S1) |
| `azure-ai-ml` | Latest PyPI seen: **1.35.2** (release 2026-10-12). (PyPI, S15) |
| `az ml` CLI extension | Azure CLI availability query on 2026-10-18 returned **2.45.2**; Learn docs refer to **v2 (current)**. (Local CLI query + Learn, S16/S17) |

## A. MLflow in AML

### A1. What is supported vs not

| MLflow area | Status in AML |
|---|---|
| Tracking (params/metrics/artifacts/runs) | **Supported**. AML workspaces are MLflow-compatible servers. (Current, doc 2026-02-24, S18) |
| Registry / workspace model registry | **Supported with caveats**: workspace-local only; no cross-workspace MLflow ops; no rename; no delete of whole model container; no org registries via MLflow; deployment from stage not supported. (Current, doc 2025-11-19, S19) |
| `models:/` URIs | **Supported for loading** models from AML workspace registry via MLflow SDK. (Current, S19) |
| Model stages | **Supported only through MLflow SDK**, not visible in AML studio / CLI / SDK v2; deploying "stage=Staging" is not supported. (Current, S19) |
| Model version tags | **Supported** (`set_model_version_tag`, `remove_model_version_tag`). (Current, S19) |
| Model aliases | **UNVERIFIED in AML docs**. Do not make aliases a workshop dependency. |
| MLflow Projects | **UNVERIFIED / not documented as an AML feature area** in current AML MLflow docs. Avoid for demo architecture. |
| MLflow Evaluate / Tracing / LoggedModel (MLflow 3-era features) | **Effectively not supported in AML integration** because AML docs explicitly state support only for MLflow 2.16 and earlier and call out 2.17+ LoggedModels API changes as unsupported. (Current, S1) |

### A2. Tracking URI + auth patterns

- **Inside AML jobs / AML notebooks / compute instances / AML clusters:** no extra tracking URI setup required; AML configures it automatically. (Current, S18)
- **From a laptop / VS Code / local Jupyter:** get workspace `mlflow_tracking_uri`, then `mlflow.set_tracking_uri(...)`; auth chain is environment vars -> managed identity -> Azure CLI -> browser interactive. (Current, S18)
- **From Azure Databricks / Synapse / any external cluster:** same pattern as any external environment; Microsoft specifically calls out shared clusters as a case where setting `MLFLOW_TRACKING_URI` at cluster level is useful. (Current, S18)
- **From Fabric notebooks:** no AML-specific Fabric tracking doc found. **Feasible as a normal external Python environment**, but treat as **code-first / external MLflow client**, not as a native Fabric-AML integration feature. Use service principal or interactive auth; do not promise a Fabric-specific AML tracking wizard. (Derived conservatively from S18 + S20)

```python
# Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
import mlflow

ml_client = MLClient.from_config(credential=DefaultAzureCredential())
mlflow_tracking_uri = ml_client.workspaces.get(ml_client.workspace_name).mlflow_tracking_uri
mlflow.set_tracking_uri(mlflow_tracking_uri)
```

### A3. Autologging and model logging

- `mlflow.autolog()` is supported; AML docs explicitly show XGBoost + autolog. (Current, S1)
- For deployability and lineage, **log as an MLflow model, not just generic artifacts**. Benefits documented by Microsoft: no-code deployment, auto Swagger in endpoints, and Responsible AI dashboard compatibility. (Current, S1)
- Prefer adding **signature** + `input_example`; it improves serving contract quality. (Current, S1)

```python
# Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
import mlflow
from mlflow.models import infer_signature

mlflow.autolog(log_models=False)
with mlflow.start_run():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    signature = infer_signature(X_test, y_pred)
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        signature=signature,
        input_example=X_train.head(1),
    )
```

### A4. `mlflow.register_model(...)` vs `ml_client.models.create_or_update(type=mlflow_model)`

| Method | Use when | Practical consequence |
|---|---|---|
| `mlflow.register_model("runs:/...", name)` | Model was logged in an MLflow run and you want AML's MLflow registry semantics + lineage. (S19) | Best for experiment-first workflow; keeps run lineage. |
| `ml_client.models.create_or_update(Model(..., type=AssetTypes.MLFLOW_MODEL))` | You already have an MLflow model folder on disk / in repo and want a registered AML model asset. (S8/S21) | Best for SDK-v2 asset-centric workflows and promotion scripts. |

### A5. No-code deployment of MLflow models

- **Managed online endpoint:** supported. You do **not** specify scoring script or environment; AML installs packages from `conda.yaml` at runtime and uses an MLflow base image with `azureml-inference-server-http` and `mlflow-skinny`. (Current, S8)
- **Batch endpoint:** supported. AML creates a batch scoring pipeline for you. (Current, S21)
- **Alternative when you need custom behavior:** use a custom scoring script / `code_configuration`, or log a custom `pyfunc` model. (Current, S1/S8)

```yaml
# Sources:
# https://raw.githubusercontent.com/Azure/azureml-examples/main/cli/endpoints/online/managed/sample/endpoint.yml
# https://raw.githubusercontent.com/Azure/azureml-examples/main/cli/endpoints/online/managed/sample/blue-deployment.yml
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineEndpoint.schema.json
name: my-endpoint
auth_mode: key
---
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineDeployment.schema.json
name: blue
endpoint_name: my-endpoint
model:
  path: ../../model-1/model/
code_configuration:
  code: ../../model-1/onlinescoring/
  scoring_script: score.py
environment:
  conda_file: ../../model-1/environment/conda.yaml
  image: mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu22.04:latest
instance_type: Standard_DS3_v2
instance_count: 1
```

### A6. Registry URI rules and limits

- `models:/<name>/latest`, `models:/<name>/<version>`, `models:/<name>/<stage>`: MLflow registry access. (Current, S19)
- `azureml://...`: AML workspace MLflow tracking URI or AML datastore URI; **not** an MLflow model-registry URI. (Current, S18/S6)
- **Artifact / metric hard limits:** I did **not** find a current Microsoft page that publishes AML-specific MLflow run caps as a concise table. Treat exact MLflow artifact-count / metric-count limits as **UNVERIFIED**; design the demo to log only modest artifacts and summary metrics.

## B. AML v2 platform status + working patterns

### B1. v2 status and retirements

| Item | Status |
|---|---|
| CLI v2 / SDK v2 / REST / studio | **Current** AML control/data plane. (S2) |
| CLI v1 support | **Ended 2025-09-30**. (Learn retirement guidance, S3) |
| Python SDK v1 support | **Ended 2026-06-30**. (S3) |
| Prompt flow in AML | **Retires 2027-04-20**; not recommended for new development. (S2) |

### B2. Command jobs / pipelines / sweep / schedules

- **Command jobs:** current and standard. (S2/S17)
- **Serverless training:** current; omitting `compute` uses serverless. Same AML compute quota; supports user identity and managed identity. (Current, S22)
- **Pipeline jobs with components:** current. (S17 + official samples S23/S24)
- **Sweep jobs:** current in v2 platform (doc set present; not reprinted here). Suitable for hyperparameter tuning.
- **Schedules:** current; recurrence schedule YAML is used across jobs/monitoring. (S25/S26)

```yaml
# Source: https://raw.githubusercontent.com/Azure/azureml-examples/main/cli/jobs/pipelines-with-components/basics/3a_basic_pipeline/pipeline.yml
$schema: https://azuremlschemas.azureedge.net/latest/pipelineJob.schema.json
type: pipeline
settings:
  default_datastore: azureml:workspaceblobstore
  default_compute: azureml:cpu-cluster
jobs:
  component_a:
    type: command
    component: ./componentA.yml
  component_b:
    type: command
    component: ./componentB.yml
  component_c:
    type: command
    component: ./componentC.yml
```

```python
# Adapted from official sample:
# https://raw.githubusercontent.com/Azure/azureml-examples/main/sdk/python/jobs/pipelines/1b_pipeline_with_python_function_components/src/components.py
from azure.ai.ml.dsl import pipeline

@pipeline(default_compute="cpu-cluster")
def train_score_eval(training_data, test_data):
    train_step = train_model(training_data=training_data, max_epochs=5)
    score_step = score_data(model_input=train_step.outputs.model_output, test_data=test_data)
    eval_step = eval_model(scoring_result=score_step.outputs.score_output)
    return {"evaluation": eval_step.outputs.eval_output}
```

### B3. Environments

- **Curated environments** remain the easiest workshop path (`azureml://registries/azureml/environments/...`). (S22)
- **Custom** environment = Docker image + conda/pip, fully supported. (S1/S8/S17)
- Best demo advice: **prebuild** the environment or use curated to avoid live image-build waits.

### B4. Data assets / datastores

| Area | Status / reality |
|---|---|
| `uri_file`, `uri_folder`, `mltable` | Current AML v2 data types for jobs/assets. `mltable` is the best fit for tabular training/inference inputs and monitoring reference data. |
| Azure Blob / ADLS datastores | Current / standard AML storage integration. |
| OneLake datastore in AML | **Python SDK `OneLakeDatastore` is experimental**; only LakeHouse artifacts are supported. (S7) |
| OneLake connection YAML | Microsoft has a YAML doc, but it explicitly says the **OneLake connection is specific to Foundry**, not general AML datastore semantics. Do **not** confuse this with AML datastore GA. (S27) |

```python
# Source: https://learn.microsoft.com/en-us/python/api/azure-ai-ml/azure.ai.ml.entities.onelakedatastore?view=azure-python
from azure.ai.ml.entities import OneLakeDatastore, OneLakeArtifact

ds = OneLakeDatastore(
    name="fleet_onelake",
    artifact=OneLakeArtifact(name="MyLakehouse", type="lake_house"),
    one_lake_workspace_name="<fabric-workspace-guid>",
    endpoint="https://onelake.dfs.fabric.microsoft.com",
)
```

### B5. Spark / AutoML / monitoring / RAI / feature store / prompt flow / registries

| Capability | Status |
|---|---|
| Serverless Spark in AML | **UNVERIFIED for GA in fetched docs**. Current docs exist, but I did not verify an explicit GA badge; treat carefully for workshop promises. |
| AutoML in AML v2 | Current / documented in v2 platform; safe to mention, but not needed for this demo. |
| Model monitoring | Current and actively documented; supports data drift, prediction drift, data quality, feature attribution drift, model performance; alerts can go through AML and Event Grid. (Current, S26) |
| Responsible AI dashboard / scorecard | **Public preview** in current AML doc set; do not make it a core live-demo dependency. (Current, S12) |
| Managed feature store | **Public preview** in current AML docs / preview features guidance. (Current, S11) |
| Prompt flow in AML | Current docs still exist, but **retired 2027-04-20**. Avoid in a Nov-2026 design. (S2) |
| Registries | Current; recommended for promotion/sharing of models/components/environments across workspaces. (S28/S29) |

```yaml
# Source: https://raw.githubusercontent.com/Azure/azureml-examples/main/cli/monitoring/advanced-model-monitoring.yaml
$schema: http://azureml/sdk-2-0/Schedule.json
name: fraud_detection_model_monitoring
trigger:
  type: recurrence
  frequency: day
  interval: 1
  schedule:
    hours: 3
    minutes: 15
create_monitor:
  compute:
    instance_type: standard_e4s_v3
    runtime_version: "3.4"
  monitoring_target:
    ml_task: classification
    endpoint_deployment_id: azureml:credit-default:main
```

## C. Endpoints

### C1. Managed online endpoints

- **Auth modes:** `key`, `aml_token`, `aad_token` (managed online only). (Current, S9)
- **Testing:** `az ml online-endpoint invoke` is the normal CLI path. (Current, S17)
- **Rollout:** blue/green, traffic split, mirrored traffic are documented. (Current, S10)
- **Observability:** container logs + deployment logs + App Insights metrics. (Current, S30/S31)
- **Cost:** billed while deployment instances exist. Microsoft's own guidance recommends **>3 instances for production**, so a workshop/demo can use 1 instance, but that is a demo-only posture. (Current, S31)
- **Common failures:** quota, image build/pull, bad conda/pip dependencies, scoring script path/signature mismatches, private networking/DNS, insufficient RBAC, missing model files. (Current, S30)

### C2. Batch endpoints

- **Two deployment styles:** model deployment and pipeline-component deployment. (Current, S21/S32)
- **Batch MLflow no-code:** supported. AML generates the scoring pipeline/runtime. (Current, S21)
- **Billing pattern:** endpoint itself is not the main cost; compute is charged when jobs run. (Current, S21)
- **Fabric hook:** using Fabric to consume AML **batch** endpoints is **public preview** and uses shared ADLS Gen2 rather than OneLake-native execution. (Current, S33)

### C3. Quota facts that matter

- Microsoft docs **do not publish stable default per-subscription quotas by region/SKU**; quotas are **subscription/offer-specific** and not a capacity guarantee. So "default DS3_v2 quota in West Europe / France Central / Sweden Central" must be checked in **your** subscription. (Current, S34)
- Some managed online endpoint SKUs require **20% extra reserved quota** for upgrades; the SKU list indicates which SKUs skip that reservation. This surprises many teams. (Current, S35)
- **Low-priority VMs** for batch endpoints were retired; use **Spot VMs** terminology and behavior instead. (Current, S36)

### C4. Typical endpoint timing

- Microsoft docs do **not** publish a deterministic create/deploy SLA for managed endpoints.
- **Workshop planning estimate (UNVERIFIED operational estimate):** create the endpoint shell ahead of time; allow **10-20 min** for a first online deployment if a fresh environment build/image pull is needed; faster when model, environment, and image are already cached.

## D. MLOps with AML

### D1. What Microsoft recommends

- The **Azure/mlops-v2** accelerator remains the reference architecture/repo for CI/CD + retraining patterns. It covers classical ML, CV, and NLP, and uses AML as the service substrate. (Current, S37/S38)
- The MLOps v2 architecture phases are: **Data estate**, **Administration and setup**, **Model development (inner loop)**, **Model deployment (outer loop)**. (Current, S38)
- Infra examples use **Bicep or Terraform** in the architecture guidance. (Current, S38)

### D2. GitHub Actions pattern (recommended)

- Learn now explicitly recommends **OIDC** with `azure/login` over service-principal secret auth. (Current, S17)
- Store only `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`; protect production via **GitHub Environments** approval gates. (Current, S17)
- Minimal RBAC: for job submission you need workspace role such as **Contributor** or **Azure ML Data Scientist**; for online endpoints/batch endpoints you need the corresponding `.../onlineEndpoints/*` or `.../batchEndpoints/*` permissions; for registry writes/promotion you need access to the registry asset scopes. (Current, S8/S21/S17/S29)

```yaml
# Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-github-actions-machine-learning?view=azureml-api-2
name: aml-train-and-register
on:
  workflow_dispatch:
permissions:
  id-token: write
  contents: read
jobs:
  train:
    runs-on: ubuntu-latest
    environment: prod
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - run: az extension add -n ml --upgrade
      - run: az ml job create --file cli/jobs/pipelines-with-components/basics/3a_basic_pipeline/pipeline.yml
```

### D3. Promotion, validation gates, retraining

- **Recommended promotion primitive:** AML **registries** for models/components/environments shared across dev/test/prod workspaces. (Current, S28/S29)
- **Model-validation gate pattern:** compare candidate vs champion metric in CI, then register/promote only if candidate wins. This is an architectural best practice; Microsoft's MLOps v2 repo is the place to borrow concrete implementation patterns. (Current, S37/S38)
- **Scheduled retraining:** use AML schedules. (Current, S25)
- **Event-driven retraining:** Event Grid is explicitly mentioned in monitoring and MLOps maturity guidance. (Current, S26/S39)
- **What-if infra deploy:** use Bicep/Terraform in CI/CD with preview/what-if before apply. (Architecture guidance, S38)
- **Secrets:** use GitHub secrets / environment secrets for nonsecret IDs, and Key Vault / managed identity for runtime secrets. (S17 + standard Azure practice)
- **Managed identity for compute:** supported for serverless jobs and AML compute access to storage. (Current, S22/S33)

### D4. Learn MLOps maturity model (quote safely)

| Level | Official name | One-line description |
|---|---|---|
| 0 | **No MLOps** | Manual builds, releases, training, and testing; little feedback or traceability. (Current, S39) |
| 1 | **DevOps but no MLOps** | App CI/CD exists, but model deployment/feedback still rely heavily on data teams. (S39) |
| 2 | **Automated training** | Reproducible, managed training with centralized tracking and scheduled/event-driven retraining jobs. (S39) |
| 3 | **Automated model deployment** | Releases become automatic with full traceability and registry-based promotion. (S39) |
| 4 | **Full MLOps automated operations** | Monitoring, retraining, promotion, and improvement are largely automated and policy-driven. (S39) |

## E. AML <-> Fabric interplay

### E1. What is actually good today

- **Best-supported shared-data path:** keep data in **ADLS Gen2** and let Fabric use a **OneLake shortcut** while AML uses a datastore against the same underlying storage. That is the cleanest Microsoft-documented interop pattern today for batch scenarios. (Public preview for the Fabric+AML batch-endpoint article, S33)
- **Fabric can trigger AML work** via **Fabric Data Factory Azure Machine Learning activity**; doc currently exposes **Batch Endpoint** or **Pipeline (v1)** endpoint type. That v1 pipeline wording is a reminder that not every Fabric surface is fully modernized. (Current, S40)

### E2. OneLake from AML

- **Direct `/Files` access:** documented. Example path pattern: `abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/...` or GUID-based equivalents. (Current, S6)
- **`/Tables` access:** not the same story. Microsoft documents a **copy** workflow to ADLS/AML UI instead of treating lakehouse tables as a first-class AML datastore path. For Delta tables, code-based readers may work on ABFSS paths, but the simple no-copy AML UI path is **not** the documented easy route. (Current, S6/S41)
- **Permissions:** both the caller and, where relevant, the AML compute identity need storage permissions; Microsoft explicitly calls this out for Fabric-to-batch-endpoint scenarios on shared storage. (Current, S33)

### E3. Calling AML endpoints from Fabric notebooks

- I did **not** find a dedicated "Fabric notebook -> AML online endpoint" how-to page.
- **Factual answer:** it is just an HTTPS call from Python using AML online endpoint auth (`key`, `aml_token`, or Entra token). Official auth semantics are documented by AML; Fabric notebooks are simply a Python host. For batch orchestration, Fabric Data Factory has a native AML activity. (S9/S40)

### E4. Moving MLflow models between Fabric and AML

- **Fabric -> AML:** feasible if you export/download a **classic MLflow model folder** (`MLModel` + artifacts) and register it in AML as `mlflow_model`. **Pitfall:** Fabric's MLflow 3 **LoggedModel/Traces** concepts do not map to AML's current MLflow integration. Export the model artifact, not the Fabric MLflow 3 entity semantics. (S5/S1/S21)
- **AML -> Fabric:** Fabric docs explicitly support bringing existing MLflow assets from AML, Databricks, local, etc. into Fabric using `synapseml-mlflow`. (Current, S20)
- **Practical rule for this workshop:** if the same model must appear in both platforms, package and move the **MLflow model folder**, not "MLflow 3 LoggedModel" metadata.

## F. AML <-> Microsoft Foundry positioning (Oct 2026)

| Question | Factual answer |
|---|---|
| What is Foundry now? | Microsoft positions Foundry as the platform that **unifies agents, models, and tools** with enterprise readiness, observability, governance, and a single control plane. (Current, S4) |
| What is AML now? | Microsoft positions AML as the cloud service to **train and deploy models and manage MLOps**. It still explicitly covers classical ML workflows. (Current, S2) |
| Where do classic ML jobs/pipelines/endpoints/registries live? | **AML**. Those capabilities are still current in AML docs and architecture guidance. (S2/S38/S28) |
| What happened to hubs / hub-based projects? | They are now **Foundry (classic)** / hub-based projects; docs say **new investments are focused on Foundry projects in the new portal**. Existing classic docs remain for legacy support. (Current, S4/S42) |
| Is there a published retirement date for hub-based projects? | **No official date found** in the docs fetched here. Message is "legacy, migrate, no new investments." |
| What about Prompt flow? | **Retires 2027-04-20** in both Foundry and AML. (S2) |
| AML Studio classic / classic designer? | AML Studio (classic) is already retired. AML still has a modern **Designer** experience in the current studio. (Current, S43/S2) |

**Simple positioning for slides:**
- **AML:** classical ML / deep ML / training jobs / pipelines / endpoints / registries / MLOps.
- **Foundry:** GenAI / agents / model catalog / agent observability / enterprise AI platforming.
- **Fabric:** lakehouse + analytics + ML within Fabric, plus growing interoperability with AML.

## G. Demo cost / quota / prewarm guidance

### G1. Cost estimate (workshop-day order of magnitude, not quote)

- Microsoft's public docs do **not** give a single "demo-day cost" calculator for AML; use Azure pricing and your subscription's quota.
- **Retail-price anchor (official Azure Retail Prices API, 2026-10-18):** West Europe **Linux Standard_DS3_v2 ~ USD 0.272/hour**. (S44)
- If you run:
  - one small training cluster node for ~4 hours,
  - one online endpoint instance for ~4 hours,
  - plus a short batch run,
  - plus storage / ACR / App Insights,
  then a **reasonable demo-day estimate is roughly USD 3-10 for compute plus small overhead**, assuming no accidental scale-out. **UNVERIFIED for your exact subscription/currency/region.**
- France Central / Sweden Central exact figures were **not verified here**; check the Retail Prices API or pricing calculator for the actual workshop subscription.

### G2. What to pre-provision / pre-warm

1. **Create AML workspace / compute / RBAC ahead of time.**
2. **Build the environment ahead of time** (or use curated envs only).
3. **Warm the training compute**: set cluster `min_instances` to **1** shortly before the workshop if you want to avoid cold start.
4. **Create the online endpoint and deployment before the live session**; do not rely on live first-time deployment.
5. **Run one scoring call before the workshop** to validate auth, swagger/test payload, and logs.
6. **Verify quota headroom** for both training and endpoint SKUs, including the online-endpoint reservation behavior.
7. **Prestage data** in ADLS/OneLake/AML datastore and run one successful pipeline + one successful endpoint invoke + one successful batch job.

## Gotchas & limits

1. **Biggest 2026 gotcha:** AML is still **not** the place to demo MLflow 3 LoggedModels/Traces; Fabric is.
2. Do **not** assume model aliases are an AML-safe registry feature; I did not verify them in AML docs.
3. AML MLflow **stages exist only in MLflow SDK** and are not a deployment primitive in AML.
4. The OneLake YAML doc many people find is a **Foundry connection** doc, not proof of AML datastore GA.
5. Fabric **lakehouse `/Tables`** are not the same as easy AML datastore file paths.
6. Endpoint quota failures are common because of **20% extra reservation** and per-subscription quotas.
7. Prompt flow is a **retiring** technology; don't put it in a future-state recommendation.
8. Fabric Data Factory AML activity still mentions **Pipeline (v1)** in current docs; do not assume every Fabric surface is v2-native.
9. Batch endpoint + shared storage access requires both **invoker identity** and **compute identity** to have the right storage access.
10. For a live workshop, avoid first-time Docker/conda resolution live on stage.

## Questions a skeptical data scientist / data engineer would ask - with factual answers

**1. "Can AML be my MLflow server?"**  
Yes. AML workspaces are MLflow-compatible tracking servers; each workspace exposes an `azureml://...` MLflow tracking URI. (S18)

**2. "Can I use MLflow 3 LoggedModel in AML?"**  
Not safely. AML docs explicitly pin support to MLflow 2.16 and earlier, and say MLflow 2.17+ LoggedModels API changes are unsupported by `azureml-mlflow`. (S1)

**3. "If Fabric supports MLflow 3, why not just move that straight into AML?"**  
Because AML's MLflow integration lags MLflow 3 semantics. Move the **model artifact folder** instead of relying on MLflow 3 entity semantics. (S5/S1/S20)

**4. "Does AML support model registry stages like vanilla MLflow?"**  
Partly: MLflow stages exist, but only through the MLflow SDK, aren't visible in AML studio/CLI/SDK v2, and stage-based deployment isn't supported. (S19)

**5. "Why should I log a model instead of just dumping a pickle?"**  
Because AML's MLflow model contract enables no-code deploy, auto scoring stack, better lineage, and Responsible AI dashboard compatibility. (S1/S8)

**6. "Can Fabric read/write the same data as AML without copies?"**  
Yes for the best-documented path when both point to the same **ADLS Gen2** data (Fabric shortcut + AML datastore). For OneLake native `/Files`, AML access is documented; `/Tables` are trickier. (S33/S6)

**7. "Can I call AML endpoints from Fabric?"**  
Yes, as ordinary HTTPS calls with AML endpoint auth. Fabric Data Factory also has a native AML activity for orchestration, especially batch scenarios. (S9/S40)

**8. "Are AML online endpoints production ready?"**  
Yes, but your workshop should still treat them carefully: use prebuilt envs, validate quota, and know the auth/logging story. Microsoft documents rollout controls, logs, and App Insights integration. (S8/S10/S30/S31)

**9. "Should we build new MLOps on Prompt flow?"**  
No. Microsoft explicitly says Prompt flow in Foundry and AML retires on **2027-04-20** and is not recommended for new development. (S2)

**10. "What is Microsoft's official split between AML and Foundry now?"**  
AML = model training/deployment/MLOps; Foundry = agents/models/tools/GenAI platform. Both exist, but for different first-class scenarios. (S2/S4)

## Sources

- **S1** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2 - updated 2026-02-10
- **S2** https://learn.microsoft.com/en-us/azure/machine-learning/overview-what-is-azure-machine-learning?view=azureml-api-2 - updated 2026-09-09
- **S3** AML v1 migration/retirement guidance on Microsoft Learn - CLI v1 support ended 2025-09-30; SDK v1 support ended 2026-06-30
- **S4** https://learn.microsoft.com/en-us/azure/foundry/what-is-foundry - updated 2026-09-24
- **S5** https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview - updated 2026-09-02
- **S6** https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-machine-learning - updated 2026-09-02
- **S7** https://learn.microsoft.com/en-us/python/api/azure-ai-ml/azure.ai.ml.entities.onelakedatastore?view=azure-python - updated 2026-09-09
- **S8** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-mlflow-models-online-endpoints?view=azureml-api-2 - updated 2026-03-25
- **S9** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-authenticate-online-endpoint?view=azureml-api-2 - current Learn doc used in research
- **S10** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints?view=azureml-api-2 - current Learn doc used in research
- **S11** https://learn.microsoft.com/en-us/azure/machine-learning/concept-what-is-managed-feature-store?view=azureml-api-2 - updated 2025-12-31 (plus preview-features guidance during research)
- **S12** https://learn.microsoft.com/en-us/azure/machine-learning/concept-responsible-ai-dashboard?view=azureml-api-2 and https://learn.microsoft.com/en-us/azure/machine-learning/how-to-responsible-ai-dashboard?view=azureml-api-2 - updated 2025-10-16 / 2026-01-23
- **S13** https://pypi.org/project/azureml-mlflow/ - release seen 1.62.0.post6, 2026-09-02
- **S14** https://pypi.org/project/mlflow-skinny/ - release seen 3.17.1, 2026-10-13
- **S15** https://pypi.org/project/azure-ai-ml/ - release seen 1.35.2, 2026-10-12
- **S16** `az extension list-available` on 2026-10-18 - `ml` extension version 2.45.2
- **S17** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-github-actions-machine-learning?view=azureml-api-2 - updated 2026-03-20
- **S18** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2 - updated 2026-02-24
- **S19** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2 - updated 2025-11-19
- **S20** https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging - updated 2026-09-02
- **S21** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-mlflow-batch?view=azureml-api-2 - updated 2026-07-29
- **S22** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-serverless-compute?view=azureml-api-2 - updated 2026-03-27
- **S23** https://raw.githubusercontent.com/Azure/azureml-examples/main/cli/jobs/pipelines-with-components/basics/3a_basic_pipeline/pipeline.yml - Azure official sample
- **S24** https://raw.githubusercontent.com/Azure/azureml-examples/main/sdk/python/jobs/pipelines/1b_pipeline_with_python_function_components/src/components.py - Azure official sample
- **S25** AML schedule docs for pipeline/jobs in Learn v2 doc set - used in research
- **S26** https://learn.microsoft.com/en-us/azure/machine-learning/concept-model-monitoring?view=azureml-api-2 - updated 2026-01-28
- **S27** https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-connection-onelake?view=azureml-api-2 - updated 2025-11-18
- **S28** https://learn.microsoft.com/en-us/azure/machine-learning/concept-machine-learning-registries-mlops?view=azureml-api-2 - current Learn doc used in research
- **S29** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-registries?view=azureml-api-2 - current Learn doc used in research
- **S30** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-troubleshoot-online-endpoints?view=azureml-api-2 - current Learn doc used in research
- **S31** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-view-online-endpoints-costs?view=azureml-api-2 - current Learn doc used in research
- **S32** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-pipeline-deployments?view=azureml-api-2 - current Learn doc used in research
- **S33** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-fabric?view=azureml-api-2 - updated 2026-09-01, public preview
- **S34** https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-quotas?view=azureml-api-2 - current Learn doc used in research
- **S35** https://learn.microsoft.com/en-us/azure/machine-learning/reference-managed-online-endpoints-vm-sku-list?view=azureml-api-2 - current Learn doc used in research
- **S36** Batch endpoint retirement note for low-priority VMs in current Learn docs (research set)
- **S37** https://github.com/Azure/mlops-v2 - Microsoft reference accelerator repo
- **S38** https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/machine-learning-operations-v2 - updated 2026-05-04
- **S39** https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/mlops-maturity-model - updated 2026-06-03
- **S40** https://learn.microsoft.com/en-us/fabric/data-factory/azure-machine-learning-activity - updated 2026-09-10
- **S41** https://learn.microsoft.com/en-us/azure/machine-learning/create-datastore-with-user-interface?view=azureml-api-2 - current Learn doc used in research
- **S42** https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic and Foundry classic docs used in research
- **S43** https://learn.microsoft.com/en-us/azure/machine-learning/concept-designer?view=azureml-api-2 and AML Studio classic retirement guidance used in research
- **S44** https://prices.azure.com/api/retail/prices - queried 2026-10-18 for West Europe `Standard_DS3_v2`
