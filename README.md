# ML platforms on Microsoft: workshop kit

A one-day workshop for data scientists and data engineers: **Fabric vs Azure ML**, **MLflow** on both, **MLOps**, an **end-to-end demo on Fabric and on Azure ML**, and **Microsoft Foundry with a Fabric data agent**.

This repository holds everything needed to deliver the day and to rebuild every demo from scratch: the slides, the presenter guide, one synthetic dataset, and five demo kits. All text is in English. It is also set up to be pushed to your own GitHub account and deployed in your own subscription (`deploy\README.md`).

## The day at a glance

| Time | Part | Min | What the room sees | Kit |
|---|---|---:|---|---|
| 09:00 | Opening | 20 | Why this day, the shared scenario, how we work | slides |
| 09:20 | Part 1 | 90 | Fabric vs Azure ML, MLflow concepts side by side | `03-demo-mlflow-tour` |
| 10:50 | Break | 15 | | |
| 11:05 | Part 2 | 75 | MLOps concepts: lifecycle, gates, drift, CI/CD | slides |
| 12:20 | Lunch | 60 | | |
| 13:20 | Part 3 | 115 | End to end ETL + ML + MLOps: Fabric first (55 min), then Azure ML and the bridge between them (60 min) | `04-demo-fabric-e2e`, `05-demo-azureml-e2e` |
| 15:15 | Break | 15 | | |
| 15:30 | Part 4 | 75 | Foundry and a Fabric data agent over reconciled logs, with questions on top | `06-demo-foundry-data-agent` |
| 16:45 | Wrap-up | 15 | Decision guide, next steps | slides |
| 17:00 | End | | | |

The deck also has optional slides and a half-day version (core slides only). The day plan says what to cut when you are late.

## Start here

1. `00-presenter-guide\README.md`: reading order, day plan, prep plan by day, Q&A cheat sheet, glossary, research fact sheets.
2. `VERIFY-BEFORE-FRIDAY.md`: everything that could not be checked offline and must be looked at in the real tenants.
3. `01-slides\ml-platforms-workshop.pptx`: the full deck with speaker notes (the talk track). `ml-platforms-workshop-halfday.pptx` is the core-only version. See `01-slides\README.md`.
4. The `run-of-show.md` of each demo, then its `rebuild-guide.md` the first time you build it.
5. `deploy\README.md`: what deploys where in your own Azure and Fabric tenants, and how to tear it down. `AGENTS.md`: the rules and the validation commands for anyone, or any agent, who continues the work.

## Folder map

| Folder | What is inside |
|---|---|
| `00-presenter-guide` | For the presenter only: day plan, prep plan, slide timeline, Q&A, glossary, fact sheets with sources |
| `01-slides` | The decks (editable PowerPoint, native shapes and notes), the Python modules that generate them, the icon set |
| `02-demo-data` | **The shared scenario.** Deterministic data generator, reference pipeline, `scenario-contract.md` (schemas, injected problems, rules, expected numbers) and `reference_out` (expected results) |
| `03-demo-mlflow-tour` | Demo 1: the same MLflow concepts on a laptop, in Fabric and in Azure ML, plus a portability proof |
| `04-demo-fabric-e2e` | Demo 2a on Fabric: `etl` (bronze, silver, gold with reconciliation) and `ml-mlops` (features, MLflow, registry, scoring, drift, promotion gate, pipeline, CI/CD). See its README |
| `05-demo-azureml-e2e` | Demo 2b on Azure ML v2: pipeline, MLflow, registry, online and batch endpoints, monitoring, Bicep, GitHub Actions |
| `06-demo-foundry-data-agent` | Demo 3: reconciliation walk-through, a Fabric data agent built live, and a Foundry agent on top, with guardrails and an offline evaluation harness |
| `deploy` | How to deploy each module in your own Azure and Fabric tenants, and how to remove it again |
| `ci`, `.github` | Continuous integration (`ci.yml`), the manual-only deploy workflows, the Copilot cloud agent setup and the repository checks (`ci\static_checks.py`) |

Every demo kit follows the same pattern: `README.md` (what and why), `run-of-show.md` (the live script with a short and a full path), `rebuild-guide.md` (every step from an empty tenant), `troubleshooting.md`, `VERIFY-BEFORE-FRIDAY.md`, `RESULTS.md` (what was really run and what was not) and a `*-facts-for-slides.md` that backs the slide numbers.

## The shared scenario: Contoso Fleet

A construction-equipment fleet (excavators, wheel loaders, compactors, mobile cranes, pavers) where three systems disagree on purpose:

- **Telematics logs**: JSON lines, with asset references typed by the installer in several formats.
- **CMMS work orders**: CSV, tags typed by hand, some legacy tags, some typos.
- **ERP asset register**: the golden key (`EQ-00143` format).

The ETL reconciles the three into one lakehouse (bronze, silver, gold). The ML task predicts whether an asset will need a corrective work order within 7 days. MLOps wraps it in tracking, a registry, a champion/challenger gate and drift monitoring. Part 4 lets an agent answer questions about the reconciled data and refuse the ones it cannot answer.

Exact numbers (the data is deterministic, seed `20261023`): 208,900 raw telematics events, 316 assets, 12 sites, 2,345 work orders, 3,459 fault episodes, 50,876 asset-day feature rows with about 5.5 % positives. Model metrics are approximate (HGB test PR-AUC about 0.385, plus or minus 0.03, against a prevalence of about 0.045); everything else is exact. `02-demo-data\scenario-contract.md` has the full list.

## The demos

| Demo | Where | Live time, short path / full path | Kit |
|---|---|---|---|
| 1. MLflow tour | laptop, Fabric, Azure ML | 10 / 25 min | `03-demo-mlflow-tour` |
| 2a. Fabric ETL | Fabric | 15 / 25 min | `04-demo-fabric-e2e\etl` |
| 2a. Fabric ML and MLOps | Fabric | 18 / 30 min | `04-demo-fabric-e2e\ml-mlops` |
| 2b. Azure ML end to end | Azure ML | about 45 min | `05-demo-azureml-e2e` |
| 3a/3b/3c. Reconciliation walk-through, build the data agent, ask the agent | Fabric, Foundry | 15 + 20 + 15 min standard (25 + 20 + 20 extended) | `06-demo-foundry-data-agent` |

The Fabric block of Part 3 is 55 minutes including its intro slides, so plan on the short paths there (about 33 live minutes).

**Optional labs (homework).** Nobody needs a tenant on the day: participants watch the demos. Slide P3.24 offers three bounded labs for afterwards: Fabric bronze and silver (30 min), Azure ML train and track (20 min) and Azure ML deploy one endpoint (30 min). Their steps are in the "Lab variant" sections of `04-demo-fabric-e2e\etl\README.md` and `05-demo-azureml-e2e\README.md`. Two more variants are ready if someone asks: features and training in Fabric (`04-demo-fabric-e2e\ml-mlops\README.md`, 20 min) and building your own data agent (`06-demo-foundry-data-agent\README.md`, 30 min).

## Names used everywhere

| Thing | Name |
|---|---|
| Lakehouse | `lh_fleet` (schemas `bronze`, `silver`, `gold`, `ml`) |
| MLflow experiment and registered model | `fleet-failure-7d` |
| Champion pointer table (Fabric) | `ml.model_pointer` |
| Fabric notebooks | `nb_00` to `nb_08`, `nb_10_load_gold_break_glass`, `nb_11_recon_walkthrough` |
| Fabric pipelines | `pl_fleet_etl`, `pl_fleet_daily` |
| Fabric Variable Library | `fleet_mlops` |
| Fabric workspaces | `ws-fleet-dev`, `ws-fleet-test`, `ws-fleet-prod` |
| Fabric data agent | `da_fleet_recon` |
| Foundry agent | `fleet-recon-agent` |
| Azure ML workspace, registry | `mlw-fleet-dev` (`rg-fleet-aml-dev`), `mlw-fleet-prod` (`rg-fleet-aml-prod`), `mlr-fleet-shared` |
| Azure ML compute, environment, endpoints | `cpu-cluster`, `env-fleet-sklearn`, `fleet-risk-online`, `fleet-risk-batch` |

## What you need

- **Microsoft Fabric**: a workspace on a **paid capacity (F2 or higher)**. A trial capacity has no Copilot, data agent or AI functions, so it cannot run Part 4. Tenant settings are listed in each Fabric kit.
- **Azure subscription** for Azure ML, with quota for `Standard_DS3_v2` in an EU region (`05-demo-azureml-e2e\cost-and-cleanup.md` has the cost and the teardown).
- **Microsoft Foundry** project with one chat model deployed.
- **GitHub** repository and OIDC, only if you want to run the CI/CD workflows live.
- **Laptop**: Python 3.11, VS Code, Azure CLI with the `ml` extension. Each kit's README has its own pinned requirements.

## Deploy it in your own subscription

Push this repository to your own GitHub account (private) and follow `deploy\README.md`. It lists, per module, what deploys where, the commands, the one-time setup (capacity, tenant settings, GitHub OIDC) and the teardown. Today the Azure ML kit has infrastructure as code (Bicep). The Fabric and Foundry parts are guided by hand, and automating them is tracked in the open issues.

The workflows in `.github\workflows` check the repository on every push without any cloud access. The four deploy workflows stay switched off until you set the variable `ENABLE_AZURE_DEPLOY` and the OIDC variables.

## How far this has been tested

Be honest with the room and with yourself: **nothing in this kit has been run in a real Fabric, Azure ML or Foundry tenant.** It was built and checked offline against the same synthetic data:

- **Data and reference pipeline**: deterministic; the reference pipeline checks its own output against the hidden answer key.
- **Fabric ETL**: the notebooks ran locally on PySpark and match the reference pipeline on every checked count.
- **Fabric ML and MLOps**: the notebooks ran locally on pandas, scikit-learn and MLflow; the Git folders (notebooks, pipelines, Variable Library) are checked by `04-demo-fabric-e2e\tools\check_fabric_git.py` against the public `microsoft/fabric-cicd` sample.
- **Azure ML**: every YAML loads with the real `azure-ai-ml` SDK loaders, the pipeline builds, and one offline end-to-end run reproduces the gate decision.
- **MLflow tour**: the registry behaviour was probed on four MLflow versions (2.12.2, 2.16.2, 2.22.0, 3.17.0).
- **Foundry and data agent**: dry-run first; an offline harness grades the expected answers (30 questions) against the reference tables.
- **Repository checks** (`ci.yml`): lint, parsing of every YAML, JSON and notebook, a neutrality and secret scan, the strict deck build, and the tests of modules 03 and 05. The workflow is green on GitHub (four jobs: static checks, deck, module 03, module 05). The deck job runs on Windows because the builder measures text with Windows fonts. The Spark ETL, the Fabric ML kit, the ETL-to-ML integration and the Part 4 kit are checked locally for now (commands in `AGENTS.md`); adding them to the workflow is tracked in the open issues.

That is why every kit ends with `VERIFY-BEFORE-FRIDAY.md`, and why `VERIFY-BEFORE-FRIDAY.md` at this level puts the checks in priority order. Spend a rehearsal day on it.

## Rules

- **Synthetic data only.** Nothing here comes from a customer.
- **`02-demo-data\truth\` is the hidden answer key** (created when you run the generator). Never upload it to a lakehouse, a repository or an agent.
- The generated folders `02-demo-data\data`, `truth` and `out` are git-ignored: regenerate them (about 5 seconds and 30 seconds).
- Share only folders `02` to `06` with attendees. They are self-contained rebuild kits. Keep `00-presenter-guide` and the speaker notes for yourself.
- Keep the folder layout as it is: the Azure ML data assets and the Part 4 kit read `02-demo-data\reference_out` through relative paths.
- Part 4 reads the **frozen** `reference_out\ml_failure_risk_score.csv`, so the agent's answers are stable. A live scoring run gives a slightly different split of High, Medium and Low (for example 8 High and 13 Medium instead of 9 and 7); the count of 264 scored assets is exact.
