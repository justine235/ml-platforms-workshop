# Deploy the kit in your own subscription

This repository is the whole workshop kit. This page says, module by module, what you can deploy in **your** Azure subscription and **your** Fabric tenant, how, and how to remove it again.

> **Status.** Nothing has been deployed in a real tenant yet. Every script and template was validated offline and in CI (`README.md`, "How far this has been tested"). Expect a few fixes on the first real run. The `rebuild-guide.md` of each kit is the manual fallback, and each kit has a `VERIFY-BEFORE-FRIDAY.md`.

## What each module deploys

| Module | Lands in | Deploy path | Today |
|---|---|---|---|
| `02-demo-data` | your laptop or CI | `python 02-demo-data/fleet_data_generator.py --out 02-demo-data/data --truth-dir 02-demo-data/truth --with-drift` (about 5 seconds) | Ready |
| `03-demo-mlflow-tour` | laptop, then one Fabric and one Azure ML workspace | Run it locally, then import its notebook in Fabric and in Azure ML (its README) | Ready |
| `04-demo-fabric-e2e` (ETL, then ML and MLOps) | Fabric workspace | Capacity, workspace, runtime pin, `lh_fleet`, raw data, then Git sync or `cicd/deploy.py` (`04-demo-fabric-e2e/README.md`, "Before you start") | Guided by hand. The item deploy script has not run in a tenant |
| `05-demo-azureml-e2e` | Azure subscription | `infra/main.bicep`, then the `az ml` steps of `rebuild-guide.md`, or the `aml-*` workflows | The Bicep compiles in CI. Never deployed |
| `06-demo-foundry-data-agent` | Fabric lakehouse and a Foundry project | `fabric-setup/nb_10` and `nb_11` in the Fabric lakehouse, the data agent in the Fabric UI, then `foundry-agent/create_agent.py` | Guided by hand |

**Not in the repository yet** (open issues labelled `module:deploy`): infrastructure as code for the Fabric capacity and the Foundry project (`azd up`), and a Fabric bootstrap script (workspace, lakehouse, data upload, item publish). Until they exist, those steps are manual.

## Prerequisites (once)

| You need | For | Notes |
|---|---|---|
| Azure subscription and rights to create role assignments on one resource group (Owner, or Contributor plus User Access Administrator) | 05 | `infra/modules/roles.bicep` assigns roles |
| Azure CLI with the `ml` extension, and Bicep (`az bicep install`) | 05 | `az extension add -n ml` |
| Fabric capacity **F2 or higher** in West Europe, France Central, Germany West Central or Sweden Central | 04, 06 | A trial capacity runs Part 3 but has no data agent, so it cannot run Part 4 |
| Fabric tenant settings (create Fabric items, Git integration, Copilot and data agent for Part 4) | 04, 06 | `04-demo-fabric-e2e/etl/rebuild-guide.md` section 2 and `06-demo-foundry-data-agent/README.md`, "Presenter prerequisites" |
| A Foundry project with one chat model deployed | 06 | Put the values in `06-demo-foundry-data-agent/foundry-agent/.env` (copy `.env.example`) |
| Python 3.11 or 3.13 | all | Each kit lists its pinned requirements |
| A GitHub repository, only for the workflows | optional | See "GitHub workflows" below |

## Azure ML (module 05)

1. Edit `05-demo-azureml-e2e/infra/dev.bicepparam`: set `userObjectId` (`az ad signed-in-user show --query id -o tsv`) and `userPrincipalName`. The file ships with placeholders and a deployment with the all-zero object id fails.
2. Deploy the infrastructure (from `05-demo-azureml-e2e`):

```powershell
az group create --name rg-fleet-aml-dev --location westeurope
az deployment group what-if --resource-group rg-fleet-aml-dev --template-file .\infra\main.bicep --parameters .\infra\dev.bicepparam
az deployment group create  --resource-group rg-fleet-aml-dev --template-file .\infra\main.bicep --parameters .\infra\dev.bicepparam
```

3. Register the environment and the data assets, submit the training pipeline, deploy the endpoints, set up monitoring: steps 2 to the end of `05-demo-azureml-e2e/rebuild-guide.md`. Register the assets **before** any job, or the create calls fail with "asset not found".
4. Check the result against `05-demo-azureml-e2e/VERIFY-BEFORE-FRIDAY.md` and `RESULTS.md`.

On bash, use `/` in paths and a backslash instead of the PowerShell backtick for line continuation.

## Fabric (module 04, then 06)

Follow `04-demo-fabric-e2e/README.md`, "Before you start (once per workspace)". The short version:

1. A workspace on your paid capacity, pinned to a Fabric Runtime that `VERIFY-BEFORE-FRIDAY.md` says you rehearsed.
2. A schema-enabled lakehouse `lh_fleet`, and the raw files under `Files/raw` (generate them with module 02, or let `nb_00_setup` guide you).
3. The items, in one of two ways:
   - **Git integration**: the two `fabric-git` folders (`etl` and `ml-mlops`) must be merged into one repository folder, because a workspace syncs one folder. The `logicalId` values already match.
   - **`fabric-cicd`**: `04-demo-fabric-e2e/ml-mlops/cicd/deploy.py` publishes notebooks, pipelines and the Variable Library into an existing workspace (`cicd/README.md`).
4. `lh_fleet` as the default lakehouse of every notebook, then run `nb_00` to `nb_08` in the order of the run table.
5. Module 06: run `fabric-setup/nb_10` and `nb_11` in the same lakehouse, build the data agent `da_fleet_recon` in the Fabric UI, then create the Foundry agent with `python foundry-agent/create_agent.py` once `.env` is filled.

Check: `python 04-demo-fabric-e2e/tools/check_fabric_git.py --list` must report 0 errors and 0 warnings before you sync.

## GitHub workflows (optional)

| Workflow | Runs | Purpose |
|---|---|---|
| `ci.yml` | on every push and pull request | Lint, parse every YAML, JSON and notebook, neutrality and secret scan, strict deck build, module tests. No cloud access needed |
| `copilot-setup-steps.yml` | for the Copilot cloud agent | Prepares its environment (Java, Python, linters) |
| `aml-infra.yml`, `aml-train-pipeline.yml`, `aml-promote-model.yml`, `fabric-mlops-deploy.yml` | **manual or on a path change, and only when switched on** | Deploy to your tenants with GitHub OIDC, no stored secret |

The four deploy workflows stay skipped until you set, in **Settings, Secrets and variables, Actions, Variables**: `ENABLE_AZURE_DEPLOY` = `true`, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` and, for Fabric, `FABRIC_WORKSPACE_ID` (per GitHub environment `dev`, `test`, `prod`). The federated credential setup is in `05-demo-azureml-e2e/mlops/docs/oidc-setup.md`. Commit your own values in `infra/dev.bicepparam` first.

## Teardown and cost

- **Azure ML**: delete the endpoints, then `az group delete --name rg-fleet-aml-dev --yes --no-wait` (`05-demo-azureml-e2e/cost-and-cleanup.md`). The cluster scales to zero when idle, but the storage, the registry and Log Analytics keep costing.
- **Fabric**: pause or delete the capacity in the Azure portal, then delete the workspaces `ws-fleet-*`. A capacity bills while it runs, even when nothing is queued.
- **Foundry**: delete the agent, the model deployment and the project.

Cost and sizing figures in the kits are estimates that nobody has checked against a bill (`⚠ UNVERIFIED`).

## Work that continues from GitHub

`AGENTS.md` at the root holds the rules and the validation commands for each module. The open issues, labelled `module:*`, are the work queue. They can be picked up by the Copilot cloud agent while your laptop is off.
