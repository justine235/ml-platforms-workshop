# Glossary: plain-English definitions

Use these when someone asks "what does that word mean?". Each entry is one or two sentences you can say out loud. The last column says where the word first matters in the day.

| Term | Plain English | Part |
|---|---|---|
| **Activator** (Fabric) | No-code alerting. It watches data or events and runs an action (an email, a Teams message, a pipeline) when a condition is met. | 3A |
| **Alias** (MLflow registry) | A movable name such as `champion` that points to one model version, so code can say "load the champion" without knowing the version number. | 1, 2 |
| **Application Insights** | Azure's monitoring service. It collects logs, metrics and traces from endpoints and agents. | 3B, 4 |
| **Asset** (our scenario) | One machine: an excavator, a loader, a generator. Three systems spell its identifier three ways. | All |
| **Asset** (Azure ML) | Anything you register in an Azure ML workspace and can reuse: data, a model, an environment, a component. | 3B |
| **Baseline** | A deliberately simple predictor you must beat, such as "predict the average rate for everyone" or one hand-written rule. If the model cannot beat it, stop. | 2 |
| **Batch endpoint** (Azure ML) | Scores a whole dataset as a job, on demand or on a schedule. You pay mainly while the job runs. | 3B |
| **Blue/green deployment** | Two versions of a model run behind one endpoint name. You send a small share of traffic to the new one (green), watch it, then switch or roll back. | 3B |
| **Bronze, silver, gold** (medallion) | Three layers of tables. Bronze is the raw data as received; silver is cleaned and matched; gold is ready for business questions. | 3A |
| **Capacity** (Fabric) | The pool of compute you buy (an F SKU such as F2, F4, F8) that all Fabric items in assigned workspaces share. | 3A |
| **Champion / challenger** | The model in production (champion) and the new candidate (challenger). The challenger replaces the champion only if it passes the gate. | 2, 3 |
| **CI/CD** | Automatic checks on every change (continuous integration) and an automatic, controlled release (continuous delivery or deployment). | 2, 3 |
| **CMMS** | Computerized maintenance management system: the tool where work orders live. | All |
| **Compute cluster** (Azure ML) | A pool of virtual machines that scales between a minimum and a maximum, used for training. Ours is `cpu-cluster`: 0 to 2 nodes. | 3B |
| **Data agent** (Fabric) | An AI assistant you configure on a few data sources (up to five). It turns a question into a read-only query, runs it and answers from the result. | 4 |
| **Data drift** | The live data stops looking like the training data, for example a sensor reads higher after a software change. | 2, 3 |
| **Data leakage** | The model sees information it would not have at prediction time. Test scores look great, production fails. | 2 |
| **Delta table** | A table format on top of Parquet files that adds transactions and history. Every table in a Fabric lakehouse is Delta. | 3A |
| **Deployment** (Azure ML) | One version of a model plus the compute that serves it, living behind an endpoint. | 3B |
| **Deployment pipeline** (Fabric) | Moves workspace items through development, test and production stages. | 3A |
| **Deployment type** (Foundry) | How a model deployment is hosted: global, data zone (stays inside a zone such as the EU) or regional. Choose a data zone type when residency matters. | 4 |
| **Endpoint** (Azure ML) | A stable HTTPS address in front of one or more deployments. "Online" answers one request at a time; "batch" scores a dataset. | 3B |
| **Entra ID** | Microsoft's identity service. Users, apps (service principals) and managed identities live there. | 3B |
| **Environment** (Azure ML) | The Docker image and Conda packages a job or a deployment runs in. Build once, reuse many times. | 3B |
| **Episode** (fault episode) | Consecutive fault events on one machine grouped into one incident. We have 3,459. | 3A |
| **ERP** | Enterprise resource planning: here, the official asset register. | All |
| **Experiment** (MLflow) | A named folder of runs that answer the same question. Ours is `fleet-failure-7d`. | 1 |
| **Feature** | One input column of the model, for example "critical faults in the last 7 days". | 3 |
| **Federated credential / OIDC** | Lets GitHub Actions sign in to Azure with a short-lived token instead of a stored password. | 3B |
| **Flavor** (MLflow) | How a model is packaged so tools can load it: `sklearn`, `pyfunc` and so on. `pyfunc` is the generic one. | 1 |
| **Foundry** | Microsoft's platform to build and run AI applications and agents: models, agents, tools, tracing and evaluation. | 4 |
| **Gate** (promotion gate) | A rule in code that decides whether a new model may be promoted. Ours: challenger test PR-AUC at least champion + 0.01, and challenger precision at the top 5 % at least champion − 0.02. | 2, 3 |
| **Grounding** | Making an answer depend on retrieved data instead of on what the model remembers. | 4 |
| **Guardrail** | A check around an AI app that blocks or limits unsafe inputs or outputs. | 4 |
| **Hallucination** | A fluent answer that the data does not support. | 4 |
| **HGB** (histogram gradient boosting) | scikit-learn's gradient-boosted trees. Our best model: test PR-AUC about 0.38. | 3 |
| **Instructions** (data agent) | Plain-language rules you give the agent: what the tables mean, how to join them, what to refuse. | 4 |
| **Job** (Azure ML) | One execution of code on compute, defined in YAML. A pipeline is a job made of steps. | 3B |
| **Label** | What you try to predict. Ours: a corrective work order within the next 7 days. | 3 |
| **Lakehouse** (Fabric) | An item that holds files and Delta tables in OneLake. Ours is `lh_fleet`. | 3A |
| **Lineage** | The record of which data, code and settings produced which model. | 1, 2 |
| **MCP** (Model Context Protocol) | An open standard that lets agents call tools and data sources. A published data agent can be offered as an MCP tool. | 4 |
| **Model registry** | A catalog of model names and versions with their metadata. | 1, 2 |
| **Model signature** | The declared input and output columns and types of a model. Fabric `PREDICT` and endpoints need it. | 1 |
| **Model version** | Each registration under the same model name creates version 1, 2, 3 and so on. | 1 |
| **Monitoring** | Watching data and predictions after launch: drift, quality, errors, cost. | 2 |
| **MLflow** | Open-source tool to track experiments, package models and register versions. The common language of the day. | 1 |
| **Nested run** (MLflow) | A child run inside a parent run, for example one child per candidate model. | 1, 3 |
| **Notebook** | An interactive document with code cells and results. | All |
| **OneLake** | Fabric's single logical data lake, one per tenant. | 1, 3A |
| **Parquet** | A columnar file format. Delta tables store their data as Parquet. | 3A |
| **PR-AUC** | Precision-recall area under the curve: one number for the trade-off between precision and recall. The right headline metric when positives are rare; a random model scores about the positive rate. | 2, 3 |
| **Precision at top k %** | Of the k % of items with the highest scores, the share that are real positives. Good for "who do we inspect first". | 3 |
| **PREDICT** (Fabric) | A function that scores a Spark table with a registered model, inside a notebook. | 1, 3 |
| **Prevalence** | The share of positive cases. Here 5.47 % of labelled asset-days; a "prevalence baseline" predicts that share for everyone. | 2 |
| **Prompt injection** | Text that tries to make an agent ignore its instructions. | 4 |
| **Prompt Shields** | An Azure AI Content Safety feature that detects prompt-injection attacks. By default user-prompt attacks are checked and document attacks are not. | 4 |
| **PSI** (population stability index) | A number for how far a feature's current distribution moved from the reference. Ours: below 0.10 stable, 0.10 to 0.25 moderate, above 0.25 major. | 3 |
| **Purge gap** | Days left out between the training and the validation period so that 7-day-ahead labels do not overlap. | 2 |
| **Quota** | The maximum of a resource (for example vCPUs of one VM family) your subscription may use in a region. | Prep |
| **Reconciliation** | Deciding that records in different systems describe the same real-world thing, and listing the ones that do not match. | 3A, 4 |
| **Run** (MLflow) | One execution of training with its parameters, metrics and files. | 1 |
| **Service principal** | An app identity in Entra ID that automation uses instead of a person. | 3B |
| **Shadow (mirror) traffic** | A copy of live requests sent to a new deployment. Its answers are recorded but never returned to callers. | 3B |
| **SKU** | A size or tier you buy: Fabric F2, F4, F8; the VM size `Standard_DS3_v2`. | Prep |
| **Spark / PySpark** | A distributed engine and its Python API. Fabric notebooks use it for ETL. | 3A |
| **Stage** (MLflow registry) | An older label on a model version (None, Staging, Production, Archived) that MLflow is moving away from in favor of aliases. Support differs by platform: see Q7 in the cheat sheet. | 1 |
| **Telematics** | Data that machines send from on-board sensors: engine hours, temperatures, fault codes. | All |
| **Tenant** | Your organization's Microsoft cloud account boundary. **Tenant settings** are the admin-controlled switches. | Prep |
| **Time-based split** | Train on the past, validate and test on later periods, never the reverse. | 2 |
| **Tracking URI** (MLflow) | Where MLflow stores runs: a local folder, a Fabric workspace or an Azure ML workspace. | 1 |
| **Trace** | The record of the steps of one agent run: which tool was called, with what, how long it took. | 4 |
| **Variable library** (Fabric) | An item that holds named values per environment (dev, test, prod) for pipelines and notebooks. | 3A |
| **Work order** | The maintenance request in the CMMS that records a repair. | All |
| **Workspace** | In Fabric, a container for items (lakehouse, notebooks, models). In Azure ML, the top-level resource that holds jobs, models and endpoints. | 1 |
