param location string
param workspaceName string
param storageAccountId string
param keyVaultId string
param appInsightsId string
param containerRegistryId string
param tags object = {}

resource workspace 'Microsoft.MachineLearningServices/workspaces@2025-06-01' = {
  name: workspaceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  tags: tags
  properties: {
    applicationInsights: appInsightsId
    description: 'Fleet failure-prediction AML workspace for the workshop.'
    friendlyName: workspaceName
    keyVault: keyVaultId
    publicNetworkAccess: 'Enabled'
    storageAccount: storageAccountId
    hbiWorkspace: false
    containerRegistry: empty(containerRegistryId) ? null : containerRegistryId
  }
}

output workspaceId string = workspace.id
output principalId string = workspace.identity.principalId
