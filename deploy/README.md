# Deploy the kit in your own subscription

This repository is the whole workshop kit. This page says, module by module, what you can deploy in **your** Azure subscription and **your** Fabric tenant, how, and how to remove it again.

> **Status.** Nothing has been deployed in a real tenant yet. Every script and template was validated offline and in CI (`README.md`, "How far this has been tested"). Expect a few fixes on the first real run. The `rebuild-guide.md` of each kit is the manual fallback, and each kit has a `VERIFY-BEFORE-FRIDAY.md`.

## What each module deploys

| Module | Lands in | Deploy path | Today |
|---|---|---|---|
| `02-demo-data` | your laptop or CI | `python 02-demo-data/fleet_data_generator.py --out 02-demo-data/data --truth-dir 02-demo-data/truth --with-drift` (about 5 seconds) | Ready |
| `03-demo-mlflow-tour` | laptop, then one Fabric and one Azure ML workspace | Run it locally, then import its notebook in Fabric and in Azure ML (its README) | Ready |
| `04-demo-fabric-e2e` (ETL, then ML and MLOps) | Fabric workspace | Capacity, workspace, runtime check, `lh_fleet`, raw data, then Git sync or `cicd/deploy.py` (`04-demo-fabric-e2e/README.md`, "Before you start") | Guided by hand. The item deploy script has not run in a tenant |
| `infra` (repository root) | Azure subscription | One deployment, `az deployment sub create` with `infra/main.bicep` or `azd provision`: the Azure ML resources of module 05, a Foundry account with a project and a chat model, and an optional paid Fabric capacity. The default region is `francecentral`; a subscription policy can refuse a region (West Europe was refused on the presenter's), so run the what-if first (`infra/README.md`) | The Bicep compiles in CI. What-if and validate passed on one subscription. Never deployed |
| `05-demo-azureml-e2e` | Azure subscription | The resources come from `infra/` above, or from `05-demo-azureml-e2e/infra/main.bicep` alone; then the `az ml` steps of `rebuild-guide.md`, or the `aml-*` workflows | The Bicep compiles in CI. Never deployed |
| `06-demo-foundry-data-agent` | Fabric lakehouse and the Foundry project of `infra/` | `fabric-setup/nb_10` and `nb_11` in the Fabric lakehouse, the data agent in the Fabric UI, then `foundry-agent/create_agent.py` | Guided by hand |

**Not in the repository yet** (open issues labelled `module:deploy`): a Fabric bootstrap script (workspace, capacity assignment, lakehouse, data upload, item publish) and a tool that merges the two `fabric-git` folders into one. Azure has no resource type for a Fabric workspace or a lakehouse, so `infra/` creates only the capacity. The Fabric steps below are manual, or use `cicd/deploy.py`.

## Prerequisites (once)

| You need | For | Notes |
|---|---|---|
| Azure subscription with Owner, or Contributor plus User Access Administrator | infra, 05 | The templates create role assignments. With Contributor only, preview with `--validation-level ProviderNoRbac` (`infra/README.md`) |
| Azure CLI with Bicep (`az bicep install`), and the `ml` extension for the 05 steps | infra, 05 | `az extension add -n ml`. `azd` is optional |
| Fabric capacity **F2 or higher** in West Europe, France Central, Germany West Central or Sweden Central | 04, 06 | `infra/` can create it (`deployFabricCapacity=true`). A trial capacity runs Part 3 but has no data agent, so it cannot run Part 4 |
| Fabric tenant settings (create Fabric items, Git integration, Copilot and data agent for Part 4) | 04, 06 | `04-demo-fabric-e2e/etl/rebuild-guide.md` section 2 and `06-demo-foundry-data-agent/README.md`, "Presenter prerequisites" |
| A Foundry project with one chat model deployed | 06 | `infra/` creates them. Put its two outputs in `06-demo-foundry-data-agent/foundry-agent/.env` (copy `.env.example`) |
| Python 3.11 or 3.13 | all | Each kit lists its pinned requirements |
| A GitHub repository, only for the workflows | optional | See "GitHub workflows" below |

## Azure: `infra/` (Azure ML, Foundry, optional Fabric capacity), then module 05

1. Deploy `infra/`. `infra/README.md` has the parameters, the cost, the teardown and the checks that were run. The short version, from the repository root:

```powershell
$oid = az ad signed-in-user show --query id -o tsv
$upn = az ad signed-in-user show --query userPrincipalName -o tsv
az deployment sub what-if --name fleet-ml-workshop --location francecentral --template-file infra/main.bicep --parameters infra/main.bicepparam userObjectId=$oid userPrincipalName=$upn location=francecentral --no-prompt true --result-format ResourceIdOnly
az deployment sub create  --name fleet-ml-workshop --location francecentral --template-file infra/main.bicep --parameters infra/main.bicepparam userObjectId=$oid userPrincipalName=$upn location=francecentral
```

   `RequestDisallowedByAzure` in the what-if means your subscription may not create that resource type in that region: pass another `location=`. Add `deployFabricCapacity=true` for a paid Fabric capacity (it bills per hour until you pause or delete it).
2. Copy the two Foundry outputs into the 06 `.env` (`infra/README.md`, "Outputs and the 06 `.env`").
3. Register the environment and the data assets, submit the training pipeline, deploy the endpoints, set up monitoring: steps 2 to the end of `05-demo-azureml-e2e/rebuild-guide.md` (its step 1, the resource group and the template, is what `infra/` just did). Register the assets **before** any job, or the create calls fail with "asset not found".
4. Check the result against `05-demo-azureml-e2e/VERIFY-BEFORE-FRIDAY.md` and `RESULTS.md`.

Module 05 alone, without `infra/`: edit `05-demo-azureml-e2e/infra/dev.bicepparam` (set `userObjectId`, `userPrincipalName` and, if you change the region, `location`; the file ships with placeholders and a deployment with the all-zero object id fails), then, from `05-demo-azureml-e2e`:

```powershell
az group create --name rg-fleet-aml-dev --location francecentral
az deployment group what-if --resource-group rg-fleet-aml-dev --template-file .\infra\main.bicep --parameters .\infra\dev.bicepparam
az deployment group create  --resource-group rg-fleet-aml-dev --template-file .\infra\main.bicep --parameters .\infra\dev.bicepparam
```

On bash, use `/` in paths and a backslash instead of the PowerShell backtick for line continuation.

## Fabric (module 04, then 06)

Follow `04-demo-fabric-e2e/README.md`, "Before you start (once per workspace)". The short version:

1. A workspace on your paid capacity, on the workspace default runtime (Runtime 2.0). Runtime 1.3 (long-term support until March 2027) is the fallback if a notebook fails; `VERIFY-BEFORE-FRIDAY.md` says what was checked locally and what only a rehearsal can show.
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
| `ci.yml` | on every push and pull request | Lint, parse every YAML, JSON and notebook, neutrality and secret scan, strict deck build, the tests of modules 03, 05 and 06, Bicep compile of `infra/`. No cloud access needed |
| `ci-data-ml.yml` | when `02-demo-data`, `04-demo-fabric-e2e` or `ci/requirements` change, and by hand | The Spark ETL on Spark 3.5 and 4.1, the Fabric ML kit on two library sets, and the ETL-to-ML integration. About an hour of runner time per run. No cloud access needed |
| `copilot-setup-steps.yml` | for the Copilot cloud agent | Prepares its environment (Java, Python, linters) |
| `aml-infra.yml`, `aml-train-pipeline.yml`, `aml-promote-model.yml`, `fabric-mlops-deploy.yml` | **manual or on a path change, and only when switched on** | Deploy to your tenants with GitHub OIDC, no stored secret |

The four deploy workflows stay skipped until you set, in **Settings, Secrets and variables, Actions, Variables**: `ENABLE_AZURE_DEPLOY` = `true`, `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` and, for Fabric, `FABRIC_WORKSPACE_ID` (per GitHub environment `dev`, `test`, `prod`). The federated credential setup is in `05-demo-azureml-e2e/mlops/docs/oidc-setup.md`. Commit your own values in `infra/dev.bicepparam` first.

## Teardown and cost

- **Everything created by `infra/`**: delete the resource groups `rg-fleet-aml-dev`, `rg-fleet-foundry-dev` and `rg-fleet-fabric-dev` (`infra/README.md`, "Teardown"). The key vault of the Azure ML module is purge-protected for 90 days, so a redeploy after a teardown needs another `environmentName` or `amlPrefix`.
- **Azure ML**: delete the endpoints, then `az group delete --name rg-fleet-aml-dev --yes --no-wait` (`05-demo-azureml-e2e/cost-and-cleanup.md`). The cluster scales to zero when idle, but the storage, the registry and Log Analytics keep costing.
- **Fabric**: pause or delete the capacity in the Azure portal, then delete the workspaces `ws-fleet-*`. A capacity bills while it runs, even when nothing is queued.
- **Foundry**: delete the agent, the model deployment and the project.

Cost and sizing figures in the kits are estimates that nobody has checked against a bill (`⚠ UNVERIFIED`).

## Work that continues from GitHub

`AGENTS.md` at the root holds the rules and the validation commands for each module. The open issues, labelled `module:*`, are the work queue. A Copilot cloud agent can pick them up while your laptop is off, but only if the repository owner has a Copilot plan with the cloud agent and GitHub-hosted runners are allowed (check **Settings, Actions** and **Settings, Copilot**; managed enterprise accounts often disable hosted runners). Otherwise open a Copilot CLI session in a clone and ask it to follow `AGENTS.md` for one issue.
