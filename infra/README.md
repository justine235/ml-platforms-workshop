# Workshop infrastructure (`infra/`)

One deployment that creates the Azure resources used by the demos `05-demo-azureml-e2e` and `06-demo-foundry-data-agent`:

- an Azure Machine Learning workspace with its storage account, key vault, container registry and monitoring (the unchanged Bicep of `05-demo-azureml-e2e/infra`),
- a Microsoft Foundry account with one project and one chat model deployment,
- optionally a paid Microsoft Fabric capacity (off by default, because it bills from the moment it exists).

The template is `infra/main.bicep` (subscription scope). `azure.yaml` at the repository root lets `azd` use the same files. Keep the folder `05-demo-azureml-e2e` where it is: `infra/main.bicep` calls its template with a relative path.

Nothing was deployed while this kit was written. It was only compiled and checked with `az bicep build`, `az deployment sub what-if` and `az deployment sub validate` (see [What was validated](#what-was-validated-2026-10-21)). Items that could not be checked are marked `⚠ UNVERIFIED`.

## What it creates

| Resource group | Resources | Switch (default) |
|---|---|---|
| `rg-fleet-aml-<env>` | Azure ML workspace `mlw-fleet-<env>`, storage account, key vault, Log Analytics workspace, Application Insights, container registry (Basic), compute cluster `cpu-cluster` (0 to 2 nodes, scales to zero). Optional: compute instance, shared registry. | `deployAml` (true) |
| `rg-fleet-foundry-<env>` | Foundry account `aif-fleet-<env>-<suffix>` (kind AIServices), project `proj-fleet-<env>`, chat model deployment (`gpt-5.4`, GlobalStandard, 50 K tokens per minute), 3 role assignments | `deployFoundry` (true) |
| `rg-fleet-fabric-<env>` | Fabric capacity `fcfleet<env><suffix>` (F2) | `deployFabricCapacity` (**false**) |

`<env>` is `environmentName` (default `dev`). `<suffix>` is derived from the subscription id and `environmentName`, so the global names do not collide between subscriptions.

Role assignments:

| Where | Who | Role |
|---|---|---|
| Foundry account | presenter (`userObjectId`) | Foundry User, Foundry Project Manager |
| Foundry account | managed identity of the project | Foundry User |
| Azure ML workspace, storage, key vault, registry | workspace identity and presenter | created by the 05 module (see `05-demo-azureml-e2e/infra/modules/roles.bicep`) |

Foundry Project Manager is there for the project connection to Fabric (see [After the deployment](#after-the-deployment)). Learn asks for the permission `Microsoft.CognitiveServices/accounts/projects/connections/write` on the project to create it, and this role contains `Microsoft.CognitiveServices/accounts/projects/*` (read with `az role definition list`).

## Cost

Prices come from the Azure Retail Prices API (EUR, West Europe meters), queried on 2026-10-21. `⚠ UNVERIFIED`: they are not from Microsoft Learn, the base Fabric F-SKU meter was not isolated (the CU-hour rate of about 0.1936 EUR was taken from several Fabric meters), and prices change.

| Item | How it bills | Rough price |
|---|---|---|
| Fabric capacity F2 (2 capacity units) | per hour while it is running, also when idle | about 0.39 EUR per hour, 9.3 EUR per day, 283 EUR per month (730 h) |
| Container registry (Basic) | per day | about 0.15 EUR per day |
| Foundry model `gpt-5.4` GlobalStandard | per token used; an idle deployment costs nothing (`⚠ UNVERIFIED`, token price not researched) | depends on use |
| Azure ML | workspace is free; the cluster has 0 minimum nodes, so it bills only while a job runs; the compute instance (off by default) bills while it runs | depends on the VM size |
| Storage, Log Analytics, Application Insights, Key Vault | consumption | small |

Stop the billing:

- Fabric: pause the capacity (Azure portal, capacity, Pause) or delete it. Learn states that resuming a paused capacity also resumes billing ([pause and resume](https://learn.microsoft.com/en-us/fabric/enterprise/pause-resume)). Command line, `⚠ UNVERIFIED` (the REST operation `suspend` is documented on Learn, this command was not run):

  ```powershell
  az rest --method post --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/rg-fleet-fabric-dev/providers/Microsoft.Fabric/capacities/<capacity-name>/suspend?api-version=2023-11-01"
  ```

- Everything: delete the resource groups (see [Teardown](#teardown)).

## Before you start

1. **Tools.** Azure CLI with the Bicep CLI (`az bicep version`). Checked with Azure CLI 2.91.0 and Bicep CLI 0.31.92. This Bicep version is old and has no type definitions for some newer resource types, so it prints warnings BCP081 ([list](#bicep-warnings)). They do not block the deployment. The commands below put a `.bicepparam` file and inline `name=value` pairs in one `--parameters` list; that is what was tested. `⚠ UNVERIFIED`: older Azure CLI versions.
2. **Permissions on the subscription.** Owner, or Contributor plus User Access Administrator (or Role Based Access Control Administrator). The deployment creates role assignments (05 module and Foundry roles). With Contributor alone, `create` fails with `Authorization failed ... roleAssignments/write`, and so does a plain `what-if` (seen on the presenter subscription). Two ways out:
   - preview only: add `--validation-level ProviderNoRbac` to `what-if`,
   - Foundry without the role assignments: `deployAml=false assignFoundryRoles=false` (Contributor is enough; an admin then assigns the roles, see [Assign the Foundry roles by hand](#assign-the-foundry-roles-by-hand)). The Azure ML part cannot skip its role assignments.
3. **Resource providers** registered in the subscription:

   ```powershell
   foreach ($p in 'Microsoft.CognitiveServices','Microsoft.MachineLearningServices','Microsoft.Fabric','Microsoft.Storage','Microsoft.KeyVault','Microsoft.ContainerRegistry','Microsoft.Insights','Microsoft.OperationalInsights') {
     "$p " + (az provider show --namespace $p --query registrationState -o tsv)
   }
   # register a missing one: az provider register --namespace <name>
   ```

4. **Model and quota.** The deployment needs quota for `gpt-5.4` GlobalStandard in the Foundry region (default 50, in units of 1,000 tokens per minute). Check with `az cognitiveservices usage list --location <region>` and `az cognitiveservices model list --location <region>`. `what-if` and `validate` do not check quota or model availability.
5. **Fabric** (only for `deployFabricCapacity=true` and the 06 demo): a paid capacity (F2 or larger; a trial capacity is not enough for the data agent) and the tenant settings enabled by a Fabric admin: "Create workspaces" and the data agent settings. See [Sources](#sources).

## Deploy with az

Run the commands from the repository root (the folder that contains `infra/` and `05-demo-azureml-e2e/`).

```powershell
$oid = az ad signed-in-user show --query id -o tsv
$upn = az ad signed-in-user show --query userPrincipalName -o tsv

# 1. Preview, changes nothing
az deployment sub what-if --name fleet-ml-workshop --location francecentral `
  --template-file infra/main.bicep --parameters infra/main.bicepparam `
  userObjectId=$oid userPrincipalName=$upn location=francecentral `
  --no-prompt true --result-format ResourceIdOnly

# 2. Deploy
az deployment sub create --name fleet-ml-workshop --location francecentral `
  --template-file infra/main.bicep --parameters infra/main.bicepparam `
  userObjectId=$oid userPrincipalName=$upn location=francecentral
```

Bash: use `oid=$(az ad signed-in-user show --query id -o tsv)` and `\` instead of the backtick.

- `--location` is only where Azure stores the deployment record. The parameter `location=` is the region of the resources.
- Never write your object id or user principal name into a file; pass them on the command line as above. `infra/main.bicepparam` holds placeholders only.
- Add `deployFabricCapacity=true` to also create the Fabric capacity (billed). Other switches are in the [parameter table](#parameters).
- **Choose the region with the what-if.** The template default is `francecentral`. On the presenter subscription Azure refused `westeurope` (`RequestDisallowedByAzure`, "The selected region is currently not accepting new customers") for Log Analytics, Application Insights, the container registry, the Foundry project and the Fabric capacity, while `francecentral` and `swedencentral` (everything in one region) and `northeurope` for Azure ML with `foundryLocation=swedencentral` passed. Your subscription may behave differently; the what-if tells you before anything is created.
- A what-if is not a guarantee: it does not check quota, model availability or name collisions, and it cannot evaluate 3 role assignments of the Azure ML module (their names are computed at run time; reported as "unsupported").

## Deploy with azd

```powershell
azd env new dev
azd env set AZURE_LOCATION francecentral
azd env set AZURE_PRINCIPAL_UPN <your user principal name>
azd provision
```

- `azure.yaml` has no services, so `azd provision` (or `azd up`) only creates the infrastructure.
- azd uses the name of its environment as `environmentName`: use 2 to 8 lowercase letters or digits (`dev`), not `fleet-dev`.
- azd sets `AZURE_ENV_NAME` and `AZURE_PRINCIPAL_ID` itself and asks for the subscription if none is selected. Set the others with `azd env set`: `AZURE_LOCATION` and `AZURE_PRINCIPAL_UPN` (both required; azd has no variable for the user principal name), `AZURE_FOUNDRY_LOCATION` (optional), `DEPLOY_FABRIC_CAPACITY=true` (optional).
- azd prefers `infra/main.bicepparam` to `infra/main.parameters.json` (read in the azd source, `bicep_provider.go`, 2026-10-21). `main.parameters.json` is only a fallback with the same four values.
- `⚠ UNVERIFIED`: `azd provision` was not run (it would create resources). The behaviour above comes from the azd documentation and source, not from a run.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `environmentName` | `dev` | 2 to 8 lowercase letters or digits; part of every name |
| `location` | `francecentral` | region of Azure ML and Fabric, and of Foundry unless `foundryLocation` is set |
| `foundryLocation` | empty (= `location`) | region of the Foundry account and the model (models are not in every region) |
| `userObjectId` | required | object id of the presenter |
| `userPrincipalName` | required | user principal name of the presenter; default Fabric administrator |
| `tags` | `{ workload: 'fleet-ml-workshop' }` | tags on the resource groups, Foundry and Fabric resources |
| `deployAml` | `true` | Azure ML stack |
| `deployFoundry` | `true` | Foundry account, project, model deployment |
| `deployFabricCapacity` | `false` | paid Fabric capacity |
| `amlPrefix` | empty | prefix of the global names of the 05 module (`st<prefix><env>`, `kv-<prefix>-<env>`, `acr<prefix><env>`). Empty = `fleet` + 4 characters from the subscription id. Max 12 lowercase letters or digits |
| `deployContainerRegistry` | `true` | container registry of Azure ML |
| `deployComputeInstance` | `false` | Azure ML compute instance (a billed VM) |
| `deployRegistry` | `false` | shared Azure ML registry |
| `assignFoundryRoles` | `true` | the 3 Foundry role assignments; `false` if you may not create role assignments |
| `chatModelName` / `chatModelVersion` | `gpt-5.4` / `2026-03-05` | GA, GlobalStandard in westeurope, swedencentral and francecentral when checked on 2026-10-21 |
| `chatModelSkuName` | `GlobalStandard` | deployment SKU |
| `chatModelCapacity` | `50` | units of 1,000 tokens per minute; lower it on `InsufficientQuota` |
| `chatDeploymentName` | empty (= model name) | name of the deployment |
| `fabricCapacitySku` | `F2` | F2 to F2048 |
| `fabricAdminMembers` | empty (= `userPrincipalName`) | Fabric capacity administrators (user principal names) |

Environment variables read by `main.bicepparam` (azd and `az`): `AZURE_ENV_NAME`, `AZURE_LOCATION`, `AZURE_FOUNDRY_LOCATION`, `AZURE_PRINCIPAL_ID`, `AZURE_PRINCIPAL_UPN`, `DEPLOY_FABRIC_CAPACITY`. Values on the `az` command line win over the file.

## Outputs and the 06 `.env`

```powershell
az deployment sub show --name fleet-ml-workshop --query properties.outputs -o json
```

| Output | Use |
|---|---|
| `AZURE_AI_PROJECT_ENDPOINT` | `AZURE_AI_PROJECT_ENDPOINT` in `06-demo-foundry-data-agent/foundry-agent/.env` (form `https://<account>.services.ai.azure.com/api/projects/<project>`; the host is the account name) |
| `AZURE_OPENAI_MODEL_DEPLOYMENT` | `AZURE_OPENAI_MODEL_DEPLOYMENT` in the same `.env` |
| `FOUNDRY_RESOURCE_GROUP`, `FOUNDRY_ACCOUNT_NAME`, `FOUNDRY_PROJECT_NAME` | Foundry resource names |
| `AML_RESOURCE_GROUP`, `AML_WORKSPACE_NAME` | workspace for the 05 demo |
| `FABRIC_RESOURCE_GROUP`, `FABRIC_CAPACITY_NAME` | Fabric capacity (empty if not deployed) |

The outputs contain no secrets. Disabled parts return empty strings. With azd the outputs are saved in the azd environment: `azd env get-values` (`⚠ UNVERIFIED`, azd was not run).

## After the deployment

Bicep cannot create these; do them by hand (the 06 README has the detailed steps):

1. Copy the two Foundry outputs into the 06 `.env`.
2. Fabric: create the workspace, assign it to the capacity, create the lakehouse and load the data, create and publish the data agent. There is no ARM resource type for a Fabric workspace, lakehouse or data agent.
3. Foundry portal: connect the published Fabric data agent to the project (Foundry Project Manager, assigned by this template, covers the permission needed). `⚠ PREVIEW`: Learn marks the Fabric data agent tool in Foundry and the Fabric IQ connection as preview (read 2026-10-21), so menus and names may change. Put the connection id in `FABRIC_IQ_PROJECT_CONNECTION_ID`. Check the format: Learn shows `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>/connections/<name>`, while `06-demo-foundry-data-agent/foundry-agent/.env.example` shows a `Microsoft.MachineLearningServices/workspaces/...` form. `⚠ UNVERIFIED`: which one the 06 code accepts (06 was not run).

## Assign the Foundry roles by hand

Only if you deployed with `assignFoundryRoles=false`. An Owner or User Access Administrator runs this. `⚠ UNVERIFIED`: not run (it creates role assignments).

```powershell
$account = az cognitiveservices account show --name <FOUNDRY_ACCOUNT_NAME> --resource-group <FOUNDRY_RESOURCE_GROUP> --query id -o tsv
$project = az resource show --ids "$account/projects/<FOUNDRY_PROJECT_NAME>" --api-version 2026-09-01 --query identity.principalId -o tsv
az role assignment create --assignee-object-id <presenter object id> --assignee-principal-type User --role "Foundry User" --scope $account
az role assignment create --assignee-object-id <presenter object id> --assignee-principal-type User --role "Foundry Project Manager" --scope $account
az role assignment create --assignee-object-id $project --assignee-principal-type ServicePrincipal --role "Foundry User" --scope $account
```

## Teardown

```powershell
az group delete --name rg-fleet-aml-dev --yes --no-wait
az group delete --name rg-fleet-foundry-dev --yes --no-wait
az group delete --name rg-fleet-fabric-dev --yes --no-wait
```

Deleting does not free every name at once:

- **Key vault of the 05 module** has purge protection and the default 90-day retention ([Learn](https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview)). A vault with the same name cannot be created in the same region until the retention ends, and it cannot be purged earlier. To deploy again after a teardown, use another `environmentName` or `amlPrefix`.
- **Foundry account** is soft-deleted for 48 hours. The same name cannot be reused before that unless it is purged ([Learn](https://learn.microsoft.com/en-us/azure/ai-services/recover-purge-resources)). `⚠ UNVERIFIED` (not run): `az cognitiveservices account purge --name <account> --resource-group <rg> --location <region>`.

## Troubleshooting

| Message or symptom | Cause and fix |
|---|---|
| `RequestDisallowedByAzure ... not accepting new customers` | The subscription may not create that resource type in that region. Use another `location` (and `foundryLocation`) and run the what-if again. |
| `Authorization failed ... roleAssignments/write` (deployment or what-if) | You cannot create role assignments. Ask for Owner or User Access Administrator, preview with `--validation-level ProviderNoRbac`, or deploy Foundry only with `deployAml=false assignFoundryRoles=false`. |
| `InsufficientQuota`, `SkuNotSupported`, model not found | Lower `chatModelCapacity`, choose another `foundryLocation`, or another model version. Check `az cognitiveservices usage list` and `model list`. |
| `MissingSubscriptionRegistration`, `NoRegisteredProviderFound` | Register the provider (see Before you start). |
| Storage account, key vault, registry or Foundry name already taken | Set `amlPrefix` or `environmentName` to another value. For soft-deleted names see Teardown. |
| `InvalidResourceGroupLocation` | A resource group cannot change region. Delete it or use another `environmentName`. |
| azd: `PrincipalNotFound` or role assignment fails | `AZURE_PRINCIPAL_ID` was not set, so the object id is all zeros. Pass the real one. |
| Fabric capacity: administrator rejected | Use user principal names in `fabricAdminMembers`. `⚠ UNVERIFIED`: whether object ids are accepted. |

## What was validated (2026-10-21)

Read-only checks against the presenter subscription. Nothing was created, deleted or registered. All what-if runs used `--validation-level ProviderNoRbac` unless stated, because the signed-in user is Contributor only.

| Check | Exit | Result |
|---|---|---|
| `az bicep build` of `infra/main.bicep`, and of each file in `infra/modules` alone | 0 | 0 errors. Warnings, all BCP081: 9 for `main.bicep`, 3 for `foundry.bicep`, none for `fabric-capacity.bicep` |
| `az bicep build-params infra/main.bicepparam` (without and with `AZURE_*` environment variables) | 0 | placeholders and environment values evaluated as expected |
| `infra/main.parameters.json` and `azure.yaml` parsed (Python `json`, PyYAML) | 0 | both valid |
| `az provider show` for the 8 namespaces of [Before you start](#before-you-start) | 0 | all `Registered` |
| what-if, `location=westeurope` | 1 | `RequestDisallowedByAzure` for 4 resources: Log Analytics, Application Insights, registry, Foundry project |
| what-if, `deployFabricCapacity=true` (westeurope) | 1 | same 4 plus the Fabric capacity |
| what-if, `deployAml=false` (westeurope) | 1 | the Foundry project |
| what-if, `location=francecentral` | 0 | 17 to create, 3 unsupported |
| what-if, `location=francecentral deployFabricCapacity=true` | 0 | 19 to create, 3 unsupported |
| what-if, `location=francecentral deployAml=false` | 0 | 7 to create |
| what-if, `location=francecentral deployFoundry=false` (Azure ML only) | 0 | 10 to create, 3 unsupported |
| what-if, `location=francecentral deployAml=false deployFoundry=false deployFabricCapacity=true` (Fabric only) | 0 | 2 to create (resource group and capacity) |
| what-if, `location=swedencentral` | 0 | 17 to create, 3 unsupported |
| what-if, `location=northeurope foundryLocation=swedencentral` (also with `deployFabricCapacity=true`) | 0 | 17 (19 with Fabric) to create, 3 unsupported |
| what-if without `--validation-level`, Foundry only, `deployAml=false assignFoundryRoles=false` | 0 | 4 to create |
| what-if without `--validation-level`, defaults | 1 | `Authorization failed ... roleAssignments/write` |
| `az deployment sub validate` (`ProviderNoRbac`; `location=francecentral`, and `location=northeurope foundryLocation=swedencentral`) | 0 | `Succeeded`, no error, 20 validated resources (nested deployments included) |

"Unsupported" = the 3 role assignments of the 05 module for the workspace identity (storage, key vault, registry).

Not validated (`⚠ UNVERIFIED`):

- A real deployment. So role propagation, the Foundry project identity role, the model deployment (quota) and the Azure ML compute were not exercised.
- `azd provision` end to end.
- The Fabric capacity administrator as user principal name, and the Fabric `suspend` command.
- Prices and the quota in the target subscription.
- The Foundry portal and Fabric portal steps (workspace, data agent, project connection), the Fabric tenant settings, and the 06 demo itself.
- The property names of the Foundry resources (API `2026-09-01`) were not checked by the local compiler, because Bicep CLI 0.31.92 has no type definitions for them (BCP081). They were compared by hand with the published type definitions (see [Sources](#sources)), and the Resource Manager preflight accepted them. `⚠ UNVERIFIED`: a compile with a newer Bicep CLI.

### Bicep warnings

`az bicep build` ends with exit 0 and 9 warnings, all BCP081 ("does not have types available"). `az deployment` prints each one twice. They come from the old Bicep CLI, not from errors in the templates.

- In `05-demo-azureml-e2e/infra` (unchanged): `Microsoft.MachineLearningServices/workspaces@2025-06-01` (3), `.../registries@2025-06-01` (1), `.../workspaces/computes@2025-06-01` (2).
- In `infra/modules/foundry.bicep`: `Microsoft.CognitiveServices/accounts`, `accounts/projects`, `accounts/deployments`, all `@2026-09-01` (3).

## Sources

All read on 2026-10-21.

- Foundry account, project, deployment (Bicep reference): <https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts?pivots=deployment-language-bicep>, <https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/projects?pivots=deployment-language-bicep>, <https://learn.microsoft.com/en-us/azure/templates/microsoft.cognitiveservices/accounts/deployments?pivots=deployment-language-bicep>
- Bicep type definitions of the Foundry resources, used to compare the property names: <https://raw.githubusercontent.com/Azure/bicep-types-az/main/generated/cognitiveservices/microsoft.cognitiveservices/2026-09-01/types.md>
- Fabric capacity (Bicep reference; 2023-11-01 is the only non-preview version): <https://learn.microsoft.com/en-us/azure/templates/microsoft.fabric/capacities?pivots=deployment-language-bicep>
- Fabric capacity suspend operation: <https://learn.microsoft.com/en-us/rest/api/microsoftfabric/fabric-capacities/suspend?view=rest-microsoftfabric-2023-11-01>
- Pause and resume, billing: <https://learn.microsoft.com/en-us/fabric/enterprise/pause-resume>
- Buy and manage a capacity: <https://learn.microsoft.com/en-us/fabric/enterprise/buy-subscription>
- Fabric tenant setting "Create workspaces": <https://learn.microsoft.com/en-us/fabric/admin/portal-workspace>
- Fabric data agent tenant settings: <https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings>
- Fabric data agent with Foundry (Fabric IQ): <https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq>
- Foundry Fabric tool (connection id format): <https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric>
- Foundry roles: <https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry> and built-in roles <https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles>
- Model availability: <https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure>; quota: <https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/quota>
- Soft delete and purge of Foundry resources: <https://learn.microsoft.com/en-us/azure/ai-services/recover-purge-resources>
- Key Vault soft delete: <https://learn.microsoft.com/en-us/azure/key-vault/general/soft-delete-overview>
- What-if: <https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/deploy-what-if> and `az deployment sub` <https://learn.microsoft.com/en-us/cli/azure/deployment/sub>
- azd environment variables: <https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/manage-environment-variables>; azd source (parameter file precedence): <https://github.com/Azure/azure-dev/blob/main/cli/azd/pkg/infra/provisioning/bicep/bicep_provider.go>
- Prices: Azure Retail Prices API <https://prices.azure.com/api/retail/prices> (`⚠ UNVERIFIED`, see Cost)
- Region refusal: <https://aka.ms/locationineligible> (link given in the Azure error message)
