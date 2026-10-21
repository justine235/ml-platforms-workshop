# Verify before Friday: the short list

Nothing in this kit has been run in a real Fabric, Azure ML or Foundry tenant. It was checked offline and in GitHub Actions: Python, PySpark, MLflow and scikit-learn on a laptop, the azure-ai-ml SDK loaders for the Azure ML YAML, a static checker for the Fabric Git folders, and the Bicep templates of `infra\` (compiled, and previewed with `what-if` against one real subscription, never deployed). So **expect small surprises (labels, names, IDs, one or two rules of the platform) on your first tenant run.** That is normal. The point of this page is to find them on Tuesday and Wednesday, not on Friday at 11:00.

Every demo folder has its own `VERIFY-BEFORE-FRIDAY.md` with the full detail. This page puts the items in priority order and links to the detail. Next to each item, write **ok**, **changed the slide** or **dropped**.

## 1. Ask for these now (they take days, not hours)

- [ ] **Paid Fabric capacity (F2 or higher), assigned to your workspace.** The trial runs notebooks and pipelines but has no Copilot, no data agent and no AI functions, so Part 4 cannot run on it. F4 or F8 is a reasonable starting size for the ETL (not verified: time the notebooks on your capacity and watch the Capacity Metrics app). Details: `00-presenter-guide\04-prep-plan.md`, section 1.
- [ ] **Fabric tenant settings** (one email to a Fabric admin): create Fabric items; Git sync (and the GitHub variant); Copilot and Azure OpenAI features; capacities designated as Copilot capacities; the two cross-geography AI settings if the capacity is outside the EU data boundary and the US; ML model endpoints (preview, only if you show one); the service principal setting only if CI/CD runs as a service principal. List: `00-presenter-guide\04-prep-plan.md`, section 2.
- [ ] **Azure ML quota** for `Standard_DS3_v2` in the region you deploy to. France Central is the default of `infra\`, Sweden Central also passed a what-if, West Europe was refused on the presenter subscription (the kit assumes at least 24 vCPUs in the DSv2 family, a planning estimate). `05-demo-azureml-e2e\VERIFY-BEFORE-FRIDAY.md`.
- [ ] **Foundry project and one chat model deployment**, with enough tokens per minute. `infra\` creates both (`gpt-5.4`, GlobalStandard), but its `what-if` does not check quota: check it first (`infra\README.md`, "Before you start"). Choose a Data Zone EU deployment type if data residency matters (`chatModelSkuName`; ⚠ UNVERIFIED that the model offers it in your region). Same sign-in account for Fabric and Foundry. `06-demo-foundry-data-agent\VERIFY-BEFORE-FRIDAY.md`.
- [ ] **Access**: Contributor on the Fabric workspace and on the Azure resource group, write on the GitHub repository, and someone who can create an Entra app with a federated credential (only for the GitHub Actions step).

## 2. Rehearse once, end to end, in a scratch tenant (hard stop: Wednesday evening)

| # | What to run | What the offline checks already proved | What only the tenant can prove | Detail |
|---|---|---|---|---|
| 0 | **Azure infrastructure**: `az deployment sub what-if`, then `create`, from `infra\README.md` | The Bicep compiles in CI. On the presenter subscription the what-if passed in France Central and in Sweden Central (17 resources for Azure ML plus Foundry, 19 with the Fabric capacity), and `az deployment sub validate` succeeded. West Europe was refused (`RequestDisallowedByAzure`) | A real deployment: role propagation, the Foundry project identity role, the model deployment (quota), the Azure ML compute, `azd provision`, the Fabric capacity administrator given as a user principal name, prices | `infra\README.md`, "What was validated" |
| 1 | **Fabric ETL**: land the raw files, run `nb_00` to `nb_03`, then `pl_fleet_etl` | The notebooks run on local PySpark and match the reference pipeline on every checked count: 39 of 39 checks on Spark 4.1.1 with Delta 4.2.0, and on Spark 3.5.6 with Delta 3.2.1, on a laptop and in GitHub Actions (Linux) | Default lakehouse binding (attach `lh_fleet` to every notebook after an import, then restart the session), schema-enabled lakehouse, which runtime a new workspace really starts on (the default is Runtime 2.0, Spark 4.1: keep it, and fall back to Runtime 1.3 only if a notebook fails) and whether Fabric keeps the ANSI mode that Spark 4 turns on by default, the delay of about two minutes before an uploaded file is visible on the mounted path, capacity speed and sizing, the Git import of the folders | `04-demo-fabric-e2e\etl\VERIFY-BEFORE-FRIDAY.md` |
| 2 | **Fabric ML and MLOps**: `nb_04` to `nb_08`, then `pl_fleet_daily` | The notebooks run on pandas, scikit-learn and MLflow with a Fabric simulation, on a Runtime 2.0-like and a Runtime 1.3 library set (locally and in GitHub Actions on Linux); the Delta tables of the ETL, from Spark 3.5 and from Spark 4.1, feed them (14 checks); the Git folders pass the static checker | How the shared code is found from a Fabric notebook, pandas and Spark type conversions (the Spark calls to watch in `notebook_common.py` are listed in the kit's own page), what a fresh workspace raises when `ml.model_pointer` does not exist yet (`read_model_pointer` handles it in code, tested only against a fake exception), the exit-value expression of the drift branch, the Office 365 alert, the Variable Library read, that the model registered in the Fabric registry exposes its source-run metrics (the gate reads them) | `04-demo-fabric-e2e\ml-mlops\VERIFY-BEFORE-FRIDAY.md` |
| 3 | **Fabric Git sync**: connect a scratch workspace to a repository holding the two `fabric-git` folders | The structure follows the public `microsoft/fabric-cicd` sample (`04-demo-fabric-e2e\tools\check_fabric_git.py`) | That a real workspace accepts every item and binds each pipeline activity to its notebook; whether your Git provider is supported | `04-demo-fabric-e2e\README.md` |
| 4 | **Azure ML**: follow `rebuild-guide.md` once in a scratch resource group | Every YAML loads with the real SDK loaders; the pipeline builds; one offline run reproduces the gate decision | Server-side validation of each `az ml ... create`, the first image build (10 to 20 minutes) and first online deployment (10 to 15 minutes), the blue/green sequence on a real endpoint (green with no live traffic, then mirror 10 %, then clear the mirror, then a live 90/10 split), batch output shape, the experiment name inside a real job, the GitHub OIDC workflows | `05-demo-azureml-e2e\VERIFY-BEFORE-FRIDAY.md` |
| 5 | **Foundry and the data agent**: load the tables, build `da_fleet_recon`, publish, connect `fleet-recon-agent`, ask every question of `qa-script.md` | An offline harness grades the 30 expected answers against the reference tables; the Foundry code is dry-run-first; the tests, the example SQL, the harness and the dry run also run in GitHub Actions | Field limits in the Fabric UI, the Fabric IQ connection flow, the published MCP tool name, the trace path, throttling, and that the Spark-only notebooks `nb_10` and `nb_11` run in the tenant (they were only checked on local Spark 3.5 with Delta: they pass unchanged on 3.5.5, while on 3.5.6 a table overwrite fails unless Spark's write route is changed, and whether the Fabric runtime is affected is unverified; see `RESULTS.md` of the kit) | `06-demo-foundry-data-agent\VERIFY-BEFORE-FRIDAY.md` |
| 6 | **MLflow tour**: local run, one Fabric run, one Azure ML job | The registry behaviour (versions, aliases, stages) was probed on MLflow 2.12.2, 2.16.2, 2.22.0 and 3.17.0 locally; metrics reproduce | The `Files/` import path in Fabric, run-comparison button labels, nested runs, Azure ML compute-instance paths, registering an exported model into Fabric and Azure ML | `03-demo-mlflow-tour\VERIFY-BEFORE-FRIDAY.md` |

Four facts the room will test you on, so know them before Friday:

- **Registry semantics differ.** Open-source MLflow has versions, aliases and (deprecated) stages; the docs of the managed registries in Fabric and Azure ML describe them as version-first. The kit's slides say "check the platform" where the docs are silent. Do not promise stages or aliases in Fabric.
- **Fabric has no first-party drift monitoring.** The drift demo is a notebook plus a pipeline branch plus Activator. Say so.
- **The promotion gate in Fabric reads the metrics logged at training time** (the honest hold-out numbers). It does not re-score the registered model, because the shipped model is refit on all labelled history and would look perfect on its own test split.
- **Azure ML traffic: a deployment is live or mirrored, never both.** Mirroring copies a share of live traffic (at most 50 %, one mirrored deployment, not for Kubernetes endpoints) to a second deployment; clients only ever see the live deployment's answer. To go live you clear the mirror and then split the real traffic.

## 3. Labels, limits and wording to confirm in the portals (30 minutes each)

- [ ] **Fabric data agent**: tenant setting labels; character limits of the instruction, source-instruction and source-description fields; size of the example-query import; draft versus publish behaviour. (Slides P4.4 and P4.8.)
- [ ] **Foundry**: the Fabric IQ and OneLake Catalog connection flow, the published MCP tool name and settings labels, the Application Insights tracing path, content-recording defaults. (P4.9 and P4.15.)
- [ ] **Fabric ML**: run-comparison buttons, the ML model item's version comparison, the `Machine learning models` item in Git and in deployment pipelines (preview), the Monitor view label, the notebook import button label.
- [ ] **Azure ML Studio**: whether stages show in the UI (they are SDK-only in the docs), alias support, the registry and `az ml model share` flags if you demo cross-workspace promotion.
- [ ] **Azure ML CLI**: the exact syntax on your installed `ml` extension (version 2.4.0 or later is needed for mirroring): `--mirror-traffic "green=10"` on the endpoint update, then `--mirror-traffic "green=0"`, then `--traffic "blue=90 green=10"`. Quote the traffic strings, invoke the endpoint without naming a deployment (a call that names one is not mirrored) and read the mirrored deployment's logs with `az ml online-deployment get-logs`.
- [ ] **Pipeline**: the `IfDriftAlert` expression against a real notebook exit payload, and which alert channel (email, Teams or both) your shared connection supports.

## 4. Facts that move: previews, deprecations, dates

Re-read the portal banners on Thursday and again on Friday morning. If a date moved, change slide P4.16 and say so out loud.

| Item | State in this kit (checked 2026-10-18 and 19) |
|---|---|
| Legacy Microsoft Fabric data agent tool in Foundry | Preview, **deprecates 2026-11-06**; Fabric IQ is the replacement path (also preview) |
| Foundry visual workflow builder | **Retires 2026-12-01** |
| Prompt flow | **Retires 2027-04-20** |
| Azure ML CLI v1 and SDK v1 | Ended 2025-09-30 and 2026-06-30: use CLI and SDK v2 only |
| Azure ML model monitoring schedules, OneLake datastore | Preview or experimental: the schema moves |
| Fabric ML experiments and models in Git and deployment pipelines; ML model endpoints; Activator parameter passing | Preview |
| Fabric data agent SDK | Preview |
| Fabric Runtime | Runtime 2.0 (Spark 4.1, Delta 4.2, Java 21, Python 3.13, mlflow-skinny 2.22) is generally available, recommended and the default for new workspaces, supported until 2028-08-31. Runtime 1.3 (Spark 3.5, Python 3.11, mlflow-skinny 2.12.2) has its end of support announced (2026-09-30) and is in long-term support until March 2027 (Learn, runtime lifecycle page, read 2026-10-21). The ETL passes 39 of 39 checks on Spark 4.1.1 and 3.5.6 (on a laptop and in GitHub Actions on Linux), and the ML kit runs on a Runtime 2.0-like and a Runtime 1.3 library set, which are Linux approximations and not Fabric images. Nothing ran in Fabric: keep the default, rehearse once, and fall back to Runtime 1.3 only if a notebook fails |

## 5. Numbers: what is exact and what is not

| Kind | What | Rule |
|---|---|---|
| **Exact (must match, or stop and fix)** | Row counts, tier counts, duplicates, late rows, exceptions, episodes, feature rows, 264 scored assets, 47 drift combinations | The list is in `00-presenter-guide\04-prep-plan.md`, section 5, and in `02-demo-data\scenario-contract.md` |
| **Approximate (say "about")** | Model metrics: gradient boosting test PR-AUC about 0.385 (plus or minus 0.03), logistic about 0.29, rules about 0.07, prevalence about 0.045 | They move slightly with library versions |
| **Varies on a live run** | Risk bands: the frozen file used in Part 4 has exactly 9 High, 7 Medium and 248 Low; a live scoring run gives roughly 8 to 10 High and 7 to 13 Medium | Part 3 slides say "roughly"; never say "exactly" about a live run |
| **Not verified** | Euro prices for Fabric capacities and the capacity size the ETL really needs; the exact day total for Azure ML (planning estimate USD 3 to 10; the `Standard_DS3_v2` West Europe retail anchor was about USD 0.272 per hour on 2026-10-18) | Do not quote them as facts |

## 6. Slides

The deck is static. Every platform claim has a source in `00-presenter-guide\fact-sheets\` and a date. After your rehearsal, put the real labels and numbers you saw into the speaker notes (or tell me and I will update the deck). The appendix slide A9 (troubleshooting) is compiled from the kits' troubleshooting notes, not from a live tenant run, and says so on the slide.
