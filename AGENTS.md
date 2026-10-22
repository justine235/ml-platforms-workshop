# AGENTS.md: instructions for any coding agent working in this repository

This repository is a workshop kit: ML platforms on Microsoft (Fabric vs Azure ML, MLflow, MLOps, Foundry and a Fabric data agent).
The audience is data scientists and data engineers. Everything is in English, written in a simple, natural style.
Read `README.md` first, then the README of the module you work on.

## Hard rules

1. **Customer-neutral.** Never write the name of any customer, company or person in files, commit messages or PR text. The scenario is the fictional "Contoso Fleet".
2. **Synthetic data only.** The data comes from `02-demo-data/fleet_data_generator.py` (seed 20261023). Never commit `02-demo-data/data/` or `02-demo-data/truth/` (the hidden answer key). They are in `.gitignore`.
3. **No secrets and no environment identifiers.** No keys, tokens, tenant IDs, subscription IDs, object IDs, absolute local paths (`C:\...`, `/home/...`) or e-mail addresses. Use placeholders such as `<subscription-id>`.
4. **Do not invent platform facts.** Check Microsoft Learn and date the claim. Mark anything you could not verify with `⚠ UNVERIFIED`, and preview features with `⚠ PREVIEW`. Never claim something was "tested" unless a command in this repository ran it.
5. **Counts are exact, metrics are approximate.** Row counts and match counts come from `02-demo-data/scenario-contract.md` and must not change. Model metrics (for example PR-AUC about 0.385) vary by plus or minus 0.03.
6. **Fabric Git items.** Keep every `logicalId` in `.platform` files stable, keep notebook sources LF, and run `python 04-demo-fabric-e2e/tools/check_fabric_git.py --list` after any change under a `fabric-git` folder (expected: 0 errors, 0 warnings).
7. **One module per pull request.** Do not edit another module's folder. If you find a defect there, describe it in the PR body.
8. **Say what you could not do.** A partial result with an honest note is better than a green claim you did not check. Put exact commands and results in the PR body.

## Modules

| Module | Folder | What it is | How to validate on Linux |
|---|---|---|---|
| Data | `02-demo-data/` | Deterministic generator, reference pipeline and contract: the single source of truth | `python 02-demo-data/fleet_data_generator.py --out 02-demo-data/data --truth-dir 02-demo-data/truth --with-drift` |
| MLflow tour | `03-demo-mlflow-tour/` | MLflow concepts: local, Fabric and Azure ML notebooks, portability proof | `pytest 03-demo-mlflow-tour/tests`; see its `rebuild-guide.md` |
| Fabric ETL | `04-demo-fabric-e2e/etl/` | Bronze, silver, gold and reconciliation notebooks plus `pl_fleet_etl` | `etl/local-validation/run_local.py` then `compare_ground_truth.py` (JDK 17 or 21 and PySpark; 39 checks must be ok). CI: the `etl` job of `ci-data-ml.yml` (Spark 3.5 with Java 17, Spark 4.1 with Java 21), then `ci/assert_etl_results.py` |
| Fabric ML and MLOps | `04-demo-fabric-e2e/ml-mlops/` | Features, MLflow training, registration, scoring, drift, promotion gate, `pl_fleet_daily`, CI/CD | From `ml-mlops/`: `python -m pytest -q`, `local-validation/run_local.py`, `compare_ground_truth.py`, `fabric_sim.py`, and `integration_etl_to_ml.py` once the ETL has produced `lh_fleet`; `tools/build_notebooks.py` must leave the `fabric-git` folders unchanged. CI: the `ml-mlops` and `integration` jobs of `ci-data-ml.yml`, on `ci/requirements/ml-mlops.txt` (Python 3.13) and `ml-mlops-rt13.txt` (Python 3.11) |
| Azure ML | `05-demo-azureml-e2e/` | Bicep infrastructure, jobs, pipelines, endpoints, CI/CD workflow templates | The `aml` job of `.github/workflows/ci.yml` (pytest, SDK loaders, `az bicep build`, `local-validation/run_local.py`) |
| Foundry data agent | `06-demo-foundry-data-agent/` | Fabric data agent plus a Foundry agent over reconciled logs | The `foundry` job of `ci.yml`: `pytest 06-demo-foundry-data-agent/tests`, `data-agent/validate_examples.py`, `foundry-agent/eval_harness.py --agent oracle` and `create_agent.py --dry-run` |
| Slides | `01-slides/` | python-pptx deck builder (105 slides, 51 core for a half day). `ml-platforms-workshop-W1.pptx` is the presenter's 68-slide edition, built once by `build_w1.py` from the presenter's edited copy; CI does not rebuild it | `cd 01-slides && python build_deck.py --out out/strict` must print `RESULT: clean`. It measures text with Windows fonts, so run it on Windows (the `deck` job of `ci.yml` uses `windows-latest`) |
| Presenter guide | `00-presenter-guide/` | Day plan, slide timeline, Q&A, prep plan, glossary | none |
| Infra | `infra/`, `azure.yaml` | Subscription-scope Bicep: the Azure ML workspace (module 05), a Foundry account with project and chat model, an optional Fabric capacity. Default region `francecentral` | `az bicep build --file infra/main.bicep` (the `infra` job of `ci.yml`). A what-if needs a subscription: `infra/README.md` |
| Deploy | `deploy/`, `.github/workflows/` | How to deploy each module in a subscription, plus `ci.yml`, `ci-data-ml.yml` and the manual-only deploy workflows | `python ci/static_checks.py`, `ruff check .`, `actionlint` on the workflows, and `az bicep build --file <file>` for every Bicep file |

## Runtime facts to keep consistent (Microsoft Learn, lifecycle page, checked 2026-10-21)

- Fabric Runtime 2.0 (Spark 4.1) is GA and the recommended runtime.
- Fabric Runtime 1.3 (Spark 3.5) is end-of-support-announced (2026-09-30) and in long-term support until March 2027.
- The Python code must run on both stacks. `ci-data-ml.yml` tests both: the ETL on Spark 3.5 (Runtime 1.3) and Spark 4.1 (Runtime 2.0), and the Fabric ML kit on a Runtime 2.0-like and a Runtime 1.3 library set. These are Linux approximations built from Microsoft's public package lists, not Fabric images. Do not change a pin or a runtime statement without checking Learn again.
- The files in `ci/requirements/` pin each CI job. MLflow 2.x needs SQLAlchemy 2.0.x, and an unpinned install resolves SQLAlchemy 2.1, which fails on import: keep the pins.

## What has not been verified

Nothing in this repository has run in a real Fabric, Azure ML or Foundry tenant. The code is checked locally and in CI (GitHub-hosted Linux runners, plus Windows for the deck). The first run in a tenant is a test: expect small fixes (labels, names, IDs, permissions). Every `VERIFY-BEFORE-FRIDAY.md` lists what to confirm live.

## Working without the author

Open work is tracked as GitHub issues labelled `module:*`. Issues labelled `needs-tenant` can only be finished in a real Azure or Fabric tenant; the others can be done offline and checked by CI. Pick one, work on a branch, open a pull request, and make sure the `ci` workflow is green or explain exactly why a job cannot be green.

The deploy workflows (`aml-*.yml`, `fabric-mlops-deploy.yml`) need a real tenant and stay skipped unless the repository variable `ENABLE_AZURE_DEPLOY` is `true`. Never turn them on, and never add a cloud credential, from an agent session. Anything that must be checked in a tenant goes into a `VERIFY-BEFORE-FRIDAY.md` and into the pull request body.
