param location string
param registryName string
param tags object = {}

resource registry 'Microsoft.MachineLearningServices/registries@2025-06-01' = {
  name: registryName
  location: location
  kind: 'Default'
  sku: {
    name: 'Premium'
    tier: 'Premium'
  }
  tags: tags
  properties: {
    publicNetworkAccess: 'Enabled'
    regionDetails: [
      {
        location: location
      }
    ]
  }
}

output registryId string = registry.id
