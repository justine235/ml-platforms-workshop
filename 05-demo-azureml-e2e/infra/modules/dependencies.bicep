param location string
param storageAccountName string
param keyVaultName string
param logAnalyticsName string
param appInsightsName string
param containerRegistryName string
param deployContainerRegistry bool
param tags object = {}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: tags
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    accessTier: 'Hot'
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
    features: {
      searchVersion: 1
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    enablePurgeProtection: true
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = if (deployContainerRegistry) {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  tags: tags
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

output storageAccountId string = storage.id
output keyVaultId string = keyVault.id
output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsId string = appInsights.id
output containerRegistryId string = deployContainerRegistry ? acr.id : ''
