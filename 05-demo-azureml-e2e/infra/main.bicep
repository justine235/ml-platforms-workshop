targetScope = 'resourceGroup'

@description('Primary Azure region. Keep this in the EU for the workshop.')
param location string = resourceGroup().location

@description('Short environment name used in resource names and tags.')
param environmentName string = 'dev'

@description('Resource name prefix. Final resources become mlw-fleet-dev, stfleetdev, and so on.')
param prefix string = 'fleet'

@description('Azure ML workspace name.')
param workspaceName string = 'mlw-fleet-dev'

@description('Existing Entra object ID of the presenter or demo operator.')
param userObjectId string

@description('Optional human-readable user principal name tag.')
param userPrincipalName string = 'presenter@example.com'

@description('Deploy a dedicated ACR for deterministic image builds. When false, AML creates one on first build.')
param deployContainerRegistry bool = true

@description('Deploy an optional personal compute instance for notebook troubleshooting.')
param deployComputeInstance bool = false

@description('Object ID of the compute-instance owner. Defaults to the presenter user object ID.')
param computeInstanceUserObjectId string = userObjectId

@description('Optional shared AML registry for dev/test/prod promotion.')
param deployRegistry bool = false

@description('AML registry name. Used only when deployRegistry=true.')
param registryName string = 'mlr-fleet-shared'

var nameSuffix = toLower(replace('${prefix}${environmentName}', '-', ''))
var storageAccountName = take('st${nameSuffix}', 24)
var keyVaultName = take('kv-${prefix}-${environmentName}', 24)
var logAnalyticsName = 'log-${prefix}-${environmentName}'
var appInsightsName = 'appi-${prefix}-${environmentName}'
var containerRegistryName = take('acr${nameSuffix}', 50)
var computeClusterName = 'cpu-cluster'
var computeInstanceName = 'ci-fleet-dev'

module dependencies './modules/dependencies.bicep' = {
  name: 'dependencies'
  params: {
    location: location
    storageAccountName: storageAccountName
    keyVaultName: keyVaultName
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    containerRegistryName: containerRegistryName
    deployContainerRegistry: deployContainerRegistry
    tags: {
      environment: environmentName
      workload: 'fleet-workshop'
    }
  }
}

module workspace './modules/workspace.bicep' = {
  name: 'workspace'
  params: {
    location: location
    workspaceName: workspaceName
    storageAccountId: dependencies.outputs.storageAccountId
    keyVaultId: dependencies.outputs.keyVaultId
    appInsightsId: dependencies.outputs.appInsightsId
    containerRegistryId: dependencies.outputs.containerRegistryId
    tags: {
      environment: environmentName
      workload: 'fleet-workshop'
      owner: userPrincipalName
    }
  }
}

module compute './modules/compute.bicep' = {
  name: 'compute'
  params: {
    location: location
    workspaceName: workspaceName
    computeClusterName: computeClusterName
    deployComputeInstance: deployComputeInstance
    computeInstanceName: computeInstanceName
    computeInstanceUserObjectId: computeInstanceUserObjectId
  }
}

module roles './modules/roles.bicep' = {
  name: 'roles'
  params: {
    workspaceName: workspaceName
    storageAccountName: storageAccountName
    keyVaultName: keyVaultName
    containerRegistryName: containerRegistryName
    deployContainerRegistry: deployContainerRegistry
    userObjectId: userObjectId
    workspacePrincipalId: workspace.outputs.principalId
  }
}

module registry './modules/registry.bicep' = if (deployRegistry) {
  name: 'registry'
  params: {
    location: location
    registryName: registryName
    tags: {
      environment: environmentName
      workload: 'fleet-workshop'
    }
  }
}

output workspaceId string = workspace.outputs.workspaceId
output workspacePrincipalId string = workspace.outputs.principalId
output storageAccountId string = dependencies.outputs.storageAccountId
output keyVaultId string = dependencies.outputs.keyVaultId
output logAnalyticsWorkspaceId string = dependencies.outputs.logAnalyticsWorkspaceId
output applicationInsightsId string = dependencies.outputs.appInsightsId
output containerRegistryId string = dependencies.outputs.containerRegistryId
output registryId string = deployRegistry ? registry.outputs.registryId : ''
