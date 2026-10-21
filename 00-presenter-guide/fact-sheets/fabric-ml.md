# Microsoft Fabric Data Science (ML) and MLOps on Fabric — fact sheet
**As of:** 2026-10-18. **Scope:** Fabric Data Science / ML, scoring, notebooks/runtimes, CI/CD/MLOps, capacity/admin controls, and Fabric-vs-Azure ML positioning. **Notation:** if current official docs didn't clearly confirm a point, it is marked **UNVERIFIED**.

## A. MLflow in Fabric

### A1. Current state and runtime coupling
| Topic | Fact | Status | As-of | Source |
|---|---|---:|---|---|
| Runtime 2.0 | Fabric Runtime 2.0 is **GA** and is the current production runtime. Components: **Spark 4.1, Python 3.13, Delta Lake 4.2, Java 21, Scala 2.13, R 4.5.2**. | GA | runtime page updated 2026-09-19; lifecycle updated 2026-09-29 | https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 ; https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle |
| “Default runtime” in Oct 2026 | Docs are slightly inconsistent: Runtime 2.0 page says it was planned to become default in late Sep 2026; lifecycle says current production runtime is 2.0. Safest wording: **2.0 is the current recommended GA runtime; exact ‘default’ wording is not perfectly synchronized across docs**. | GA / wording ambiguity | 2026-10-18 read | same |
| Bundled MLflow in Runtime 2.0 | Runtime manifest shows **mlflow-skinny 2.22.0**. | Current runtime manifest | GitHub manifest | https://github.com/microsoft/synapse-spark-runtime |
| Bundled MLflow in Runtime 1.3 | Runtime manifest shows **mlflow-skinny 2.12.2**. | LTS runtime | GitHub manifest | same |
| MLflow 3 support | Fabric supports **MLflow 3 up to 3.1**; notebooks still ship MLflow 2.x by default, so MLflow 3 requires explicit install. | Current | 2026-09-02 | https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview |

### A2. What Fabric preconfigures
- In Fabric notebooks, MLflow tracking/auth is **preconfigured** for the current workspace. You typically just `import mlflow`; Fabric auto-enables tracking and autologging hooks. Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
- Fabric has first-class items:
  - **Experiment** item = container for runs, metrics, params, artifacts, comparison UI, search/filter. Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment
  - **ML model** item = registered model container with model versions, source run, params/metrics, files, signature/schema, endpoint activation. Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model
- Notebook UI supports **Run comparison** and **Save as a ML model** from a run. Source: experiment page above.

### A3. Autologging behavior
- **Yes: Fabric calls `mlflow.autolog()` automatically** when you open a Data Science notebook; configuration is applied when you run `import mlflow`. Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
- Default notebook hook documented by Microsoft:

```python
# Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
mlflow.autolog(
    log_input_examples=False,
    log_model_signatures=True,
    log_models=True,
    log_datasets=True,
    log_traces=True,
    disable=False,
    exclusive=True,
    disable_for_unsupported_versions=True,
    silent=True,
    extra_tags=None,
    exclude_flavors=None
)
```

- Supported frameworks called out by Fabric docs: **TensorFlow, PyTorch, scikit-learn, XGBoost**; Fabric defers framework-specific capture behavior to MLflow docs. Source: autologging page.
- To add manual logging to autologged runs, switch to `exclusive=False`.
- Workspace admins can disable it via **Workspace settings > Data Engineering/Science > Spark settings > Automatic log > Automatically track machine learning experiments and models**. Source: autologging page.

### A4. Supported/unsupported MLflow concepts in Fabric
- **Supported/documented**:
  - `set_experiment`, `start_run`, params/metrics/tags/artifacts, `search_runs`, autologging.
  - `log_model`, `infer_signature`, `register_model`, `load_model`.
  - MLflow 3 **LoggedModel** and **Traces** surfaces in Experiment UI.
  - Cross-workspace/platform logging by setting the tracking URI to a Fabric workspace endpoint.
- **Not clearly documented in current Fabric docs**:
  - MLflow **aliases** and **stages** as first-class Fabric model-item capabilities. Current docs emphasize model **versions** and endpoint/default-version semantics, not stage/alias workflows. Treat alias/stage support in Fabric as **UNVERIFIED / not a documented Fabric pattern**.
  - Hard platform-wide limits for number of experiments/models/runs per workspace were **not found** in current docs.

### A5. Cross-workspace and outside-Fabric logging
- Fabric tracking URI format for another workspace:
  - `sds://api.fabric.microsoft.com/v1/workspaces/<workspaceId>/mlflow`
- Auth patterns documented: `DefaultAzureCredential`, `DeviceCodeCredential`, `ClientSecretCredential` with `synapseml-mlflow` helpers.
- Logging from **outside Fabric to Fabric** is supported; reverse pattern (Fabric notebook logging to another Fabric workspace / other MLflow-compatible backends) is also supported by explicitly setting tracking URI.
- Microsoft’s documented dev→prod promotion pattern for workspace-scoped registries is **download artifact(s) + re-log/re-register into target workspace**.
- UI support for cross-workspace browsing is not the point; docs explicitly describe this as a **code-first** pattern. Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging

### A6. Signatures, versions, tags, limits
- **Signatures matter**: required for `PREDICT`, and model endpoints reject models without usable schema/signature. Sources: PREDICT + model endpoints pages.
- Run tag limits documented on Experiment page:
  - tag name not empty, max **250** chars
  - tag value not empty, max **5000** chars
  - prefixes **`synapseml`**, **`mlflow`**, **`trident`** are restricted
- Current docs emphasize **model versions**; they do **not** document Fabric-native “stages” like Staging/Production.

### A7. Verified minimal MLflow snippets
```python
# Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment
import mlflow
mlflow.set_experiment("equipment-failure-exp")
```

```python
# Source: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
import mlflow
mlflow.autolog(exclusive=False)
```

```python
# Adapted from Fabric experiment/model docs + MLflow 3 doc
import mlflow
from mlflow.models import infer_signature

with mlflow.start_run(tags={"scenario":"fleet-failure","owner":"workshop"}):
    mlflow.log_param("lookahead_days", 7)
    mlflow.log_metric("auc", 0.91)
    with open("metrics.json", "w", encoding="utf-8") as f:
        f.write('{"auc":0.91}')
    mlflow.log_artifact("metrics.json")
```

```python
# Source concept: Fabric model item + MLflow signature requirements
signature = infer_signature(X_train, model.predict(X_train))
mlflow.sklearn.log_model(
    sk_model=model,
    name="model",   # MLflow 3 style; Fabric also accepts legacy artifact_path pattern
    signature=signature
)
```

```python
# Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model
model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
registered = mlflow.register_model(model_uri=model_uri, name="fleet-failure-model")
```

```python
# Fabric/MLflow-compatible loading
loaded = mlflow.sklearn.load_model("models:/fleet-failure-model/1")
preds = loaded.predict(X_test)
```

```python
# Source: experiment page
runs_df = mlflow.search_runs(
    experiment_names=["equipment-failure-exp"],
    order_by=["start_time DESC"],
    max_results=20,
)
```

```python
# Cross-workspace / external-to-Fabric tracking
# Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging
mlflow.set_tracking_uri("sds://api.fabric.microsoft.com/v1/workspaces/<workspace-guid>/mlflow")
```

## B. Scoring

### B1. Batch scoring in Fabric
- Fabric supports batch predictions through:
  1. **`PREDICT()`** SQL/function-generated notebook flow
  2. **`MLFlowTransformer`** in SynapseML
  3. UDF scoring patterns from registered models
- `PREDICT` requirements:
  - model saved in **MLflow** format
  - model **signature populated**
  - **no multi-tensor** inputs/outputs
- Supported flavors for `PREDICT`: **CatBoost, Keras, LightGBM, ONNX, Prophet, PyTorch, Sklearn, Spark, Statsmodels, TensorFlow, XGBoost**. Source: https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict

```python
# Source: model-scoring-predict page
import mlflow
from synapse.ml.predict import MLFlowTransformer

df = spark.read.format("delta").load(<INPUT_TABLE>)
model = MLFlowTransformer(
    inputCols=<INPUT_COLS>,
    outputCol=<OUTPUT_COLS>,
    modelName=<MODEL_NAME>,
    modelVersion=<MODEL_VERSION>
)
df = model.transform(df)
df.write.format("delta").mode("overwrite").save(<OUTPUT_TABLE>)
```

### B2. “Apply this version” wizard
From the ML model version page, **Apply this version** can:
- create a new notebook with generated prediction code, or
- let you **Copy code to apply** and paste into an existing notebook.
Verified wizard details:
1. choose input table
2. map model input columns from the model signature
3. choose/create output table
4. map output columns
5. generate notebook / review-and-finish. Source: PREDICT page.

### B3. Real-time scoring: ML model endpoints
| Topic | Fact | Status | As-of | Source |
|---|---|---:|---|---|
| Feature | **ML model endpoints** for real-time scoring exist in Fabric. | Public preview | docs updated 2026-09-29 | https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints |
| Supported model flavors | **Keras, LightGBM, scikit-learn, XGBoost** | Preview | same | same |
| Schema/signature | Endpoints aren't available for models with no schema or tensor-based schema. | Preview | same | same |
| Scaling/limits | Up to **5 active version endpoints per model**; auto-sleep after **5 minutes** idle by default; up to **3 nodes** scale-out; **5 CU-seconds/sec/node** consumption. | Preview | same | same |
| Billing | Usage appears as **Model Endpoint** in metrics app and invoice line **ML Model Endpoint Capacity Usage CU**. | Preview | same | same |

**REST call shape (default version endpoint):**
```http
# Source: https://learn.microsoft.com/en-us/rest/api/fabric/mlmodel/endpoint/score-ml-model-endpoint
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/mlModels/{modelId}/endpoint/score
Authorization: Bearer <Entra token>
Content-Type: application/json

{
  "formatType": "dataframe",
  "orientation": "values",
  "inputs": [[1,2,3],[4,5,6]]
}
```
- Supported identities for scoring API: **user, service principal, managed identity**. Source: REST page above.
- Version-specific scoring exists too:
  - `POST .../mlmodels/{modelId}/endpoint/versions/{name}/score`

## C. Notebooks & runtimes

### C1. Default/current runtime package picture
**Runtime 2.0** (current GA production runtime) package versions verified from runtime manifest:
- Python **3.13**, Spark **4.1**, Delta **4.2**
- `mlflow-skinny` **2.22.0**
- `scikit-learn` **1.6.1**
- `lightgbm` **4.6.0**
- `xgboost` **2.1.4**
- `pandas` **2.3.3**
- `numpy` **2.4.1**
- `pyarrow` **24.0.0**
- `synapseml` **1.1.3+spark4.1**
- `synapseml-mlflow` **2.0.4**
- `flaml` **2.5.0.post6**
- `optuna` **3.6.1**
- `shap` **UNVERIFIED in Runtime 2.0 manifest pass**

Reference baseline: Runtime 1.3 manifest shows `mlflow-skinny 2.12.2`, `scikit-learn 1.2.2`, `lightgbm 4.3.0`, `xgboost 2.0.3`, `pandas 2.1.4`, `numpy 1.26.4`, `pyarrow 14.0.2`, `synapseml 1.1.3`, `synapseml-mlflow 1.0.31`, `flaml 2.5.0.post4`, `optuna 3.6.1`, `shap 0.42.1`. Source: https://github.com/microsoft/synapse-spark-runtime

### C2. Python notebook (no Spark)
- **Pure Python notebook** exists and is a separate experience for exploration/ML that doesn’t require distributed Spark.
- Built-in kernels: **Python 3.10, 3.11, 3.12**; default is **3.12**.
- Good fit for smaller-data exploration, visualization, scikit-learn-style work, and mixed Python/T-SQL without Spark-session overhead. Source: https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook

### C3. `%pip install` vs Environment item
- `%pip`/`%conda` are **session-scoped / notebook-scoped**, restart the Python interpreter, and are **not recommended for pipelines**.
- In pipeline runs, inline install is **disabled by default**; enable only by passing notebook activity parameter `_inlineInstallationEnabled=True`.
- Inline `%pip` is **not supported in High Concurrency mode** and not supported in notebook reference runs.
- For repeatable CI/CD/pipelines, Microsoft recommends **Environment** items instead. Sources: https://learn.microsoft.com/en-us/fabric/data-engineering/library-management ; https://learn.microsoft.com/en-us/fabric/data-engineering/environment-manage-library

### C4. NotebookUtils
- `mssparkutils` was renamed to **`notebookutils`**; backward compatibility remains, but future support is on `notebookutils`.
- Key modules relevant to DS/MLOps: `notebook`, `fs`, `credentials`, `runtime`, `session`, `variableLibrary`, `lakehouse`, `udf`.
- `notebookutils.notebook.run()` and `runMultiple()` are documented and supported. Sources: https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities ; https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-notebook-run

### C5. Parameter cells, scheduling, high concurrency, start time
- Parameterization: Fabric supports **parameter cells** and public API/pipeline parameter passing.
- Scheduling: notebooks can run interactively, via **Schedule** in notebook UI, via **Pipeline**, via **Job Scheduler API**, or via `notebookutils.notebook.run()` / `runMultiple()`.
- High concurrency in pipelines:
  - enable at **Workspace settings > Data Engineering/Science > Spark settings > High concurrency > For pipeline running multiple notebooks**
  - same-user boundary only
  - same workspace/default lakehouse/compute/libs required
  - up to **5 notebooks** per session tag before Fabric starts another session. Source: high-concurrency doc.
- Session startup: Microsoft now distinguishes environment publishing modes:
  - **Quick mode** environment publish ~5 sec; libraries install at session start
  - **Full mode** publish typically **3–6 min**, then session startup adds **1–3 min** for dependency deployment
  - custom live pool + full mode can give ~**5-second** starts. Source: library-management doc.

## D. MLOps on Fabric

### D1. Git integration
- Supported Git providers: **GitHub, GitHub Enterprise, Azure DevOps**. Source: Git integration overview.
- Explicit item support (requested list):
  - **Notebook, Lakehouse, Environment, DataPipeline/Pipeline, VariableLibrary, SparkJobDefinition, SemanticModel, Report, Eventhouse, KQLDatabase, Eventstream, DataAgent, Warehouse** = supported
  - **ML experiment** = supported in **preview**
  - **ML model** = supported in **preview**
- ML artifact caveat that matters most: for **ML experiments/models, Git sync includes metadata only**. **Runs** and **model versions** are **not** included in Git sync payloads. Source: https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-artifacts-git-deployment-pipelines
- Notebook source format in Git:
  - source-first (`notebook-content.py` / `.sql` etc.), not just `.ipynb`
  - `.platform` JSON (version 2) carries metadata incl. `logicalId`
  - outputs are not versioned. Source: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format
- Lakehouse in Git/deploy = **metadata only**; tables/files/views themselves are not promoted. Source: lakehouse Git/deployment doc.

### D2. Deployment pipelines
- Deployment pipelines support core DS assets like **notebooks, environments, lakehouses, pipelines**.
- **ML experiments and ML models** are in **preview** and, again, move **metadata only** — not experiment runs / model binaries / model versions. That rules out “click deploy to promote trained model artifact” as a complete MLOps story.
- Variable Library is the main built-in environment-specific parameterization mechanism.

### D3. `fabric-cicd`
- Latest PyPI version found: **1.4.0**. Source: https://pypi.org/pypi/fabric-cicd/json
- Auth examples use **`AzureCliCredential()`**; service principal / OIDC are standard Azure credential options for CI.
- Parameterization file: **`parameter.yml`**; documented transforms include string replacement, JSON key/value replacement, Spark pool remap, semantic-model binding.
- Important mismatch: current `fabric-cicd` docs list **`MLExperiment`** among supported item types, but **`MLModel`** was **not clearly listed** on the main supported-items page. Treat automated deploy support for ML model items as **UNVERIFIED / check latest docs before relying on it**.

```python
# Adapted from official fabric-cicd tutorial
# Source: https://microsoft.github.io/fabric-cicd/latest/how_to/tutorial/
from azure.identity import AzureCliCredential
from fabric_cicd import publish_all_items

publish_all_items(
    source_workspace_path="./fabric",
    target_workspace_id="<workspace-guid>",
    credential=AzureCliCredential(),
    parameter_file="./parameter.yml"
)
```

```yaml
# Minimal GitHub Actions OIDC pattern for fabric-cicd automation
# OIDC auth pattern from official azure/login docs; deploy shape from fabric-cicd docs
permissions:
  id-token: write
  contents: read
steps:
  - uses: actions/checkout@v4
  - uses: azure/login@v2
    with:
      client-id: ${{ secrets.AZURE_CLIENT_ID }}
      tenant-id: ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  - run: pip install fabric-cicd
  - run: python deploy.py
```

### D4. Fabric CLI (`fab`)
- Install: `pip install ms-fabric-cli`
- Login: `fab auth login`
- Verified examples:
```bash
# Sources: Fabric CLI docs + official examples pages
fab create ws1.Workspace -P capacityname=capac1
fab import ws2.Workspace -i C:\path\to\nb1.Notebook
fab job run ws1.Workspace/nb1.Notebook
```
Sources: https://learn.microsoft.com/en-us/rest/api/fabric/articles/fabric-command-line-interface ; https://microsoft.github.io/fabric-cli/examples/workspace_examples/ ; https://microsoft.github.io/fabric-cli/commands/fs/import/ ; https://microsoft.github.io/fabric-cli/commands/jobs/

### D5. REST APIs / service principals / tenant switches
- Notebook CRUD and execution are public:
  - create/get/update definition
  - run-on-demand through Job Scheduler API
- Notebook create/update definitions accept Fabric notebook definitions (`ipynb`, `fabricGitSource` on relevant APIs).
- Example run-on-demand route for notebook jobs is documented from notebook public API pages.
- Service principals / managed identities require the tenant setting **Service principals can use Fabric APIs** and workspace role assignment. Sources: REST identity support + notebook public API pages.

```http
# Notebook run-on-demand pattern (see notebook public API / Job Scheduler docs)
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{itemId}/jobs/instances?jobType=RunNotebook
Authorization: Bearer <token>
Content-Type: application/json
```

### D6. Variable libraries and env-specific config
- Variable Library is the native Fabric answer for environment-specific constants/secrets references across deploy stages.
- Limits documented: up to **1000 variables**, **1000 value sets**, **<10,000 cells**, **<1 MB item size**. Source: variable-library overview.
- Notebook consumption paths include NotebookUtils/`%%configure` patterns depending on workload.

### D7. Dev/test/prod model promotion when registry is workspace-scoped
- Fabric’s registry is effectively **workspace-scoped** for the operational patterns Microsoft documents.
- Since Git/deployment pipelines don’t move run artifacts/model versions, the practical promotion patterns are:
  1. **Code promotion + retrain in target workspace** (most reproducible)
  2. **Artifact copy + re-register** into target workspace using MLflow download/re-log pattern (documented by Microsoft)
- Feasibility: **yes**, using `mlflow.artifacts.download_artifacts(...)` from source and then `mlflow.<flavor>.log_model(...)` + `register_model(...)` against target tracking URI. Source: cross-workspace logging page.

### D8. Monitoring
- In the docs reviewed, Fabric has **no first-party equivalent of Azure ML managed data/model drift monitoring** for classical ML models.
- Native pieces you can combine: notebook jobs, experiment/model metadata, Monitor integration for experiment runs (preview), Power BI/Semantic Link reporting, and Activator/alerting on derived metrics.
- Common external pattern (community, not first-party managed feature): run scheduled notebook checks and publish metrics; optionally use external libraries such as **Evidently**. Treat external-monitoring guidance as implementation pattern, not managed Fabric capability.

### D9. Useful official references/samples
- **CI/CD overview:** architecture/options map across Git integration, deployment pipelines, REST, CLI, variable libraries.  
  https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview
- **microsoft/fabric-cicd:** packaging/deployment automation library and docs.  
  https://microsoft.github.io/fabric-cicd/latest/
- **microsoft/fabric-cli:** official CLI and examples.  
  https://microsoft.github.io/fabric-cli/
- **microsoft/synapse-spark-runtime:** authoritative runtime package manifests.  
  https://github.com/microsoft/synapse-spark-runtime

## E. Other Fabric DS features (status + one-line use)
| Feature | Status | Use | Source |
|---|---:|---|---|
| AutoML (FLAML) | Current / not marked preview | Low-code model selection + HPO for classification, regression, forecasting. | https://learn.microsoft.com/en-us/fabric/data-science/automated-ml-fabric |
| SynapseML | Current / preinstalled | Distributed ML + transformers/lightgbm/predict/MLFlowTransformer on Spark. | https://learn.microsoft.com/en-us/fabric/data-science/install-synapseml |
| Semantic Link (SemPy) | Current / in default runtime from Runtime 1.2+ | Bring Power BI semantic models/measures into DS workflows. | https://learn.microsoft.com/en-us/fabric/data-science/semantic-link-overview |
| Data Wrangler | Current / not marked preview | Visual data prep with generated pandas/PySpark code. | https://learn.microsoft.com/en-us/fabric/data-science/data-wrangler |
| AI Functions | **Preview** | SQL-native text AI functions in Warehouse / SQL analytics endpoint. | https://learn.microsoft.com/en-us/fabric/data-warehouse/ai-functions |
| Copilot for Data Engineering & Data Science | **Preview** | Notebook-aware AI assistant for code generation, explanation, optimization, debugging. | https://learn.microsoft.com/en-us/fabric/data-engineering/copilot-notebooks-overview |
| Fabric data agent | Out of scope here; tenant settings and Git/deployment support exist in current docs. | Agent over Fabric data sources. | https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings |

## F. Capacity, licensing, admin controls

### F1. Trial capacity and minimum SKUs
- Fabric trial lasts **60 days**.
- Trial is configured as **F4 or F64** depending on tenant/user eligibility; stores up to **1 TB** in OneLake.
- Trial **does support Data Science / notebooks / pipelines**, but **does not support Copilot, Fabric data agent, AI functions, AI services, or Trusted Workspace Access**. Source: https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial
- Smallest paid Fabric SKU is **F2**; paid F SKUs are billed **per second with one-minute minimum**. Source: licenses page.
- Notebooks / experiments: official prerequisites consistently say **Fabric capacity or trial**; for paid capacity that means **F2 or higher**.
- Model endpoints: current docs reviewed did **not** publish a higher minimum SKU than general supported Fabric capacity; treat **F2+ paid capacity** as the minimum paid entry point, but this specific point is **UNVERIFIED as an endpoint-only rule**.

### F2. Consumption, smoothing, pause/resume
- Capacity platform evaluates usage in **30-second windows**; e.g. F2=60 CU/30s, F4=120, F8=240. Source: plan-capacity page.
- Pausing capacity immediately stops throttling; on resume, billing resumes. Remaining smoothed operations/overages are summed into Azure bill when pausing. Source: pause-resume page.
- Azure F capacities support **pause/resume**; P capacities do not. Source: features-by-SKU + pause/resume pages.

### F3. Cost guidance for a one-day workshop demo
- Official docs confirm that Fabric capacity pricing is **regional**, **hourly/monthly**, and **per-second** billed for F SKUs. Source: Azure pricing page + licenses/plan-capacity docs.
- The public pricing page is not machine-readable enough in this research pass to verify exact **West Europe / France Central** F2/F4/F8 list prices; therefore exact one-day euro estimates are **UNVERIFIED** here.
- Practical guidance:
  - use **trial** if AI features are not required
  - use **paid F2+** if you need Copilot/AI features not available on trial
  - pause capacity outside the workshop window
  - if using model endpoints, add endpoint background cost even when idle-but-active (see model-endpoints cost table)

### F4. Exact admin/tenant/workspace settings to know
- **Users can create Fabric items** — required foundation for notebooks/experiments/models. Tenant-level and capacity-level. Source: fabric-switch + tenant settings index.
- **Automatically track machine learning experiments and models** — workspace setting for autologging. Source: autologging page.
- **ML models can serve real-time predictions from API endpoints (preview)** — tenant setting for model endpoints. Source: tenant settings index.
- **Service principals can use Fabric APIs** — required for SP/MI against supported Fabric REST APIs. Source: REST identity support.
- For Copilot / notebook AI experiences:
  - **Users can use Copilot and other features powered by Azure OpenAI**
  - **Capacities can be designated as Fabric Copilot capacities**
  - depending on geography, also the cross-geo processing/storage settings:
    - **Data sent to Azure OpenAI can be processed outside your capacity's geographic region, compliance boundary, or national cloud instance**
    - **Data sent to Azure OpenAI can be stored outside your capacity's geographic region, compliance boundary, or national cloud instance**
  Sources: copilot-enable-fabric + data-agent-tenant-settings.

## G. Official positioning: Fabric DS vs Azure Machine Learning
- Microsoft’s official docs position **integration**, not “winner takes all” replacement.
- Verified patterns:
  - **Azure ML can read OneLake `Files` directly** via OneLake datastore / ABFSS. Source: https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-machine-learning
  - **OneLake `Tables` to Azure ML** commonly requires **copy to ADLS Gen2** first (for the documented UI-linked pattern). Source: same.
  - Fabric can orchestrate **Azure Machine Learning activity** from Fabric pipelines. Source: https://learn.microsoft.com/en-us/fabric/data-factory/azure-machine-learning-activity
  - Fabric can call **Azure ML batch endpoints** through shared ADLS/shortcut patterns; this feature is **preview** and not recommended for production. Source: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-fabric?view=azureml-api-2
- Neutral takeaway for slide builders:
  - **Fabric Data Science** = strongest when your workflow is lake-centric, notebook-centric, Power BI/semantic-model-adjacent, and you want MLflow tracking/modeling inside the same Fabric workspace.
  - **Azure Machine Learning** = Microsoft’s richer dedicated ML platform for externalized production MLOps, managed serving options, and broader ML platform capabilities.
  - The official integration story is “**share data and connect workflows**,” not “one product eliminates the other.”

## Gotchas & limits
- Runtime docs are in transition: **Runtime 2.0 is GA/current**, but exact “default runtime” wording is not perfectly synchronized.
- Fabric notebooks ship with **MLflow 2.x**, even though Fabric supports **MLflow 3** — install MLflow 3 explicitly if you need LoggedModel/GenAI tracing APIs.
- Git/deployment for ML experiment/model items is **metadata-only**; **trained artifacts/model versions do not move**.
- `PREDICT` and endpoints depend on a valid **model signature**.
- **Model endpoints are preview**, limited to a short model-flavor list, and have idle/active consumption behavior you must budget for.
- `%pip install` is convenient but weak for repeatable pipelines; use **Environment** items instead.
- Trial capacity is great for notebooks/demos, but **AI features (Copilot, data agent, AI functions)** are not available there.
- Fabric docs reviewed do **not** document model registry **stages/aliases** as a primary Fabric pattern.

## Questions a skeptical data scientist / data engineer would ask
1. **Is Fabric MLflow “real MLflow” or a proprietary wrapper?**  
   Real MLflow APIs are supported for tracking/model logging; Fabric adds first-class workspace items and UI on top.
2. **Can I log from my laptop/CI agent into Fabric?**  
   Yes, with `synapseml-mlflow` and a Fabric tracking URI (`sds://.../mlflow`).
3. **Does Fabric autologging happen automatically?**  
   Yes in Data Science notebooks; Fabric documents the default `mlflow.autolog()` configuration.
4. **Can deployment pipelines promote a trained model artifact across workspaces?**  
   Not by themselves. They move ML item metadata, not run artifacts/model versions.
5. **Can I do real-time scoring in Fabric?**  
   Yes, but only through **preview** ML model endpoints with flavor/schema limits.
6. **If my model has no signature, can I still use PREDICT/endpoints?**  
   Batch/model-endpoint docs say signature/schema is required for those experiences.
7. **Can I avoid Spark for small scikit-learn work?**  
   Yes — use the pure Python notebook experience.
8. **Can I use service principals for notebook automation?**  
   Yes, for supported APIs, after enabling **Service principals can use Fabric APIs** and granting workspace permissions.
9. **Does Fabric have native model drift monitoring like Azure ML managed monitoring?**  
   Not in the current official docs reviewed. Build scheduled checks/alerts yourself.
10. **Should I use Fabric or Azure ML for production MLOps?**  
   Fabric is strong for integrated analytics + notebook ML inside OneLake; Azure ML remains the dedicated ML platform for broader production ML platform needs.

## Sources
- https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints (updated 2026-09-29)
- https://learn.microsoft.com/en-us/rest/api/fabric/mlmodel/endpoint (updated 2025-07-16)
- https://learn.microsoft.com/en-us/rest/api/fabric/mlmodel/endpoint/score-ml-model-endpoint (updated 2026-09-15)
- https://learn.microsoft.com/en-us/rest/api/fabric/mlmodel/endpoint/score-ml-model-endpoint-version (updated 2026-09-15)
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0 (updated 2026-09-19)
- https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle (updated 2026-09-29)
- https://github.com/microsoft/synapse-spark-runtime (runtime manifests read 2026-10-18)
- https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook (updated 2026-08-13)
- https://learn.microsoft.com/en-us/fabric/data-engineering/library-management (updated 2026-08-04)
- https://learn.microsoft.com/en-us/fabric/data-engineering/environment-manage-library (updated 2026-10-08)
- https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-notebook-run (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/data-engineering/configure-high-concurrency-session-notebooks-in-pipelines (updated 2026-10-02)
- https://learn.microsoft.com/en-us/fabric/cicd/cicd-overview (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-artifacts-git-deployment-pipelines (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-public-api (updated 2026-09-29)
- https://learn.microsoft.com/en-us/rest/api/fabric/notebook/items/create-notebook (updated 2026-09-15)
- https://learn.microsoft.com/en-us/rest/api/fabric/notebook/items/update-notebook-definition (updated 2026-09-15)
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/identity-support (updated 2026-09-15)
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/fabric-command-line-interface (updated 2026-09-15)
- https://microsoft.github.io/fabric-cli/examples/workspace_examples/ (read 2026-10-18)
- https://microsoft.github.io/fabric-cli/commands/fs/import/ (read 2026-10-18)
- https://microsoft.github.io/fabric-cli/commands/jobs/ (read 2026-10-18)
- https://microsoft.github.io/fabric-cicd/latest/ (read 2026-10-18)
- https://microsoft.github.io/fabric-cicd/latest/how_to/tutorial/ (read 2026-10-18)
- https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/ (read 2026-10-18)
- https://pypi.org/pypi/fabric-cicd/json (read 2026-10-18)
- https://learn.microsoft.com/en-us/fabric/data-science/automated-ml-fabric (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/install-synapseml (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/semantic-link-overview (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-science/data-wrangler (updated 2026-09-02)
- https://learn.microsoft.com/en-us/fabric/data-warehouse/ai-functions (updated 2026-09-15)
- https://learn.microsoft.com/en-us/fabric/data-engineering/copilot-notebooks-overview (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/enterprise/licenses (updated 2026-08-05)
- https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/enterprise/plan-capacity (updated 2026-08-18)
- https://learn.microsoft.com/en-us/fabric/enterprise/pause-resume (updated 2026-08-14)
- https://learn.microsoft.com/en-us/fabric/enterprise/fabric-features (updated 2026-06-30)
- https://learn.microsoft.com/en-us/fabric/admin/fabric-switch (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/admin/tenant-settings-index (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/fundamentals/copilot-enable-fabric (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings (updated 2026-09-29)
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-machine-learning (updated 2026-09-09)
- https://learn.microsoft.com/en-us/fabric/data-factory/azure-machine-learning-activity (updated 2026-09-10)
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-fabric?view=azureml-api-2 (updated 2026-09-01)
- https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/ (read 2026-10-18)
