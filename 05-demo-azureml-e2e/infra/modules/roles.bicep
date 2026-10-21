param workspaceName string
param storageAccountName string
param keyVaultName string
param containerRegistryName string
param deployContainerRegistry bool
param userObjectId string
param workspacePrincipalId string

var contributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
var blobContributorRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var keyVaultSecretsUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var acrPushRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8311e382-0749-4cb8-b61a-304f252e45ec')

resource workspace 'Microsoft.MachineLearningServices/workspaces@2025-06-01' existing = {
  name: workspaceName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = if (deployContainerRegistry) {
  name: containerRegistryName
}

resource workspaceIdentityStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, workspacePrincipalId, blobContributorRole)
  scope: storage
  properties: {
    principalId: workspacePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: blobContributorRole
  }
}

resource workspaceIdentityKeyVault 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, workspacePrincipalId, keyVaultSecretsUserRole)
  scope: keyVault
  properties: {
    principalId: workspacePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsUserRole
  }
}

resource workspaceIdentityAcr 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployContainerRegistry) {
  name: guid(acr.id, workspacePrincipalId, acrPushRole)
  scope: acr
  properties: {
    principalId: workspacePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrPushRole
  }
}

resource userWorkspace 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(workspace.id, userObjectId, contributorRole)
  scope: workspace
  properties: {
    principalId: userObjectId
    principalType: 'User'
    roleDefinitionId: contributorRole
  }
}

resource userStorage 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, userObjectId, blobContributorRole)
  scope: storage
  properties: {
    principalId: userObjectId
    principalType: 'User'
    roleDefinitionId: blobContributorRole
  }
}
