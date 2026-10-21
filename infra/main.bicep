// Root deployment of the workshop kit (subscription scope).
// Creates: resource groups, the Azure ML stack (module of 05-demo-azureml-e2e, unchanged),
// a Foundry account + project + chat model deployment, and optionally a paid Fabric capacity.
// See infra/README.md for the commands.
targetScope = 'subscription'

// ---------------------------------------------------------------- general
@description('Short environment name: 2-8 lowercase letters or digits. It is part of the resource group and resource names.')
@minLength(2)
@maxLength(8)
param environmentName string = 'dev'

@description('Region of the Azure ML and Fabric resource groups and resources.')
param location string = 'francecentral'

@description('Region of the Foundry account and the model deployment. Empty = same as location. It is a separate parameter because models are not available in every region.')
param foundryLocation string = ''

@description('Object id of the presenter (az ad signed-in-user show --query id -o tsv). Receives the data-plane roles. Pass it on the command line; never commit it.')
@minLength(36)
@maxLength(36)
param userObjectId string

@description('User principal name of the presenter (az ad signed-in-user show --query userPrincipalName -o tsv). Default Fabric capacity administrator.')
@minLength(3)
param userPrincipalName string

@description('Tags added to the resource groups and to the Foundry and Fabric resources.')
param tags object = {
  workload: 'fleet-ml-workshop'
}

// ---------------------------------------------------------------- what to deploy
@description('Deploy the Azure ML workspace stack (module of 05-demo-azureml-e2e).')
param deployAml bool = true

@description('Deploy the Foundry account, project and chat model deployment.')
param deployFoundry bool = true

@description('Deploy a paid Fabric capacity. Off by default because it bills from the moment it is created.')
param deployFabricCapacity bool = false

// ---------------------------------------------------------------- Azure ML
@description('Prefix of the storage account, key vault and container registry names of the Azure ML module. These names are global. Empty = "fleet" + 4 characters derived from the subscription id. Max 12 lowercase letters or digits.')
@maxLength(12)
param amlPrefix string = ''

@description('Create the Azure Container Registry used by Azure ML.')
param deployContainerRegistry bool = true

@description('Create an Azure ML compute instance for the presenter (a billed VM). The cluster scales to zero by itself.')
param deployComputeInstance bool = false

@description('Create the shared Azure ML registry.')
param deployRegistry bool = false

// ---------------------------------------------------------------- Foundry chat model
@description('Create the Foundry role assignments (Foundry User and Foundry Project Manager for the presenter, Foundry User for the project identity). Set to false if you may not create role assignments, then assign them by hand.')
param assignFoundryRoles bool = true

@description('Chat model name. gpt-5.4 version 2026-03-05 is GA with GlobalStandard in westeurope, swedencentral and francecentral (checked 2026-10-21).')
param chatModelName string = 'gpt-5.4'

@description('Chat model version.')
param chatModelVersion string = '2026-03-05'

@description('Deployment SKU of the chat model.')
param chatModelSkuName string = 'GlobalStandard'

@description('Capacity in units of 1,000 tokens per minute. It must not exceed the subscription quota in the Foundry region; lower it if the deployment fails with InsufficientQuota.')
param chatModelCapacity int = 50

@description('Name of the model deployment (value of AZURE_OPENAI_MODEL_DEPLOYMENT in the 06 kit). Empty = the model name.')
param chatDeploymentName string = ''

// ---------------------------------------------------------------- Fabric capacity
@description('Fabric capacity SKU. F2 is the smallest paid size.')
param fabricCapacitySku string = 'F2'

@description('Fabric capacity administrators (user principal names). Empty = userPrincipalName.')
param fabricAdminMembers array = []

// ---------------------------------------------------------------- names
var workload = 'fleet'
var nameSuffix = uniqueString(subscription().id, environmentName)

var amlRgName = 'rg-${workload}-aml-${environmentName}'
var foundryRgName = 'rg-${workload}-foundry-${environmentName}'
var fabricRgName = 'rg-${workload}-fabric-${environmentName}'

var amlWorkspaceName = 'mlw-${workload}-${environmentName}'
var amlResolvedPrefix = empty(amlPrefix) ? '${workload}${take(nameSuffix, 4)}' : amlPrefix
var foundryAccountName = 'aif-${workload}-${environmentName}-${nameSuffix}'
var foundryProjectName = 'proj-${workload}-${environmentName}'
var fabricCapacityName = 'fc${workload}${environmentName}${take(nameSuffix, 8)}'

var resolvedFoundryLocation = empty(foundryLocation) ? location : foundryLocation
var resolvedDeploymentName = empty(chatDeploymentName) ? chatModelName : chatDeploymentName
var resolvedFabricAdmins = empty(fabricAdminMembers) ? [userPrincipalName] : fabricAdminMembers
var resourceTags = union(tags, {
  environment: environmentName
})

// ---------------------------------------------------------------- resource groups
resource amlRg 'Microsoft.Resources/resourceGroups@2024-03-01' = if (deployAml) {
  name: amlRgName
  location: location
  tags: resourceTags
}

resource foundryRg 'Microsoft.Resources/resourceGroups@2024-03-01' = if (deployFoundry) {
  name: foundryRgName
  location: resolvedFoundryLocation
  tags: resourceTags
}

resource fabricRg 'Microsoft.Resources/resourceGroups@2024-03-01' = if (deployFabricCapacity) {
  name: fabricRgName
  location: location
  tags: resourceTags
}

// ---------------------------------------------------------------- modules
// The 05 module is called as it is; only its parameters are set here.
module aml '../05-demo-azureml-e2e/infra/main.bicep' = if (deployAml) {
  name: 'aml-${environmentName}'
  scope: amlRg
  params: {
    location: location
    environmentName: environmentName
    prefix: amlResolvedPrefix
    workspaceName: amlWorkspaceName
    userObjectId: userObjectId
    userPrincipalName: userPrincipalName
    deployContainerRegistry: deployContainerRegistry
    deployComputeInstance: deployComputeInstance
    deployRegistry: deployRegistry
  }
}

module foundry 'modules/foundry.bicep' = if (deployFoundry) {
  name: 'foundry-${environmentName}'
  scope: foundryRg
  params: {
    location: resolvedFoundryLocation
    accountName: foundryAccountName
    projectName: foundryProjectName
    userObjectId: userObjectId
    deploymentName: resolvedDeploymentName
    modelName: chatModelName
    modelVersion: chatModelVersion
    modelSkuName: chatModelSkuName
    modelCapacity: chatModelCapacity
    assignRoles: assignFoundryRoles
    tags: resourceTags
  }
}

module fabricCapacity 'modules/fabric-capacity.bicep' = if (deployFabricCapacity) {
  name: 'fabric-${environmentName}'
  scope: fabricRg
  params: {
    location: location
    capacityName: fabricCapacityName
    skuName: fabricCapacitySku
    adminMembers: resolvedFabricAdmins
    tags: resourceTags
  }
}

// ---------------------------------------------------------------- outputs (no secrets)
output AML_RESOURCE_GROUP string = deployAml ? amlRgName : ''
output AML_WORKSPACE_NAME string = deployAml ? amlWorkspaceName : ''
output FOUNDRY_RESOURCE_GROUP string = deployFoundry ? foundryRgName : ''
output FOUNDRY_ACCOUNT_NAME string = deployFoundry ? foundry!.outputs.accountName : ''
output FOUNDRY_PROJECT_NAME string = deployFoundry ? foundry!.outputs.projectName : ''
output AZURE_AI_PROJECT_ENDPOINT string = deployFoundry ? foundry!.outputs.projectEndpoint : ''
output AZURE_OPENAI_MODEL_DEPLOYMENT string = deployFoundry ? foundry!.outputs.deploymentName : ''
output FABRIC_RESOURCE_GROUP string = deployFabricCapacity ? fabricRgName : ''
output FABRIC_CAPACITY_NAME string = deployFabricCapacity ? fabricCapacity!.outputs.capacityName : ''