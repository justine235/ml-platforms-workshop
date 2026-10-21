// Microsoft Fabric capacity (paid F SKU). Resource-group scope. Called from ../main.bicep.
// A capacity bills from the moment it is created until it is paused or deleted.
targetScope = 'resourceGroup'

@description('Region of the capacity. It must be a region where Fabric capacities are offered.')
param location string

@description('Capacity name: lowercase letters and digits only, starting with a letter, 3-63 characters.')
@minLength(3)
@maxLength(63)
param capacityName string

@description('Capacity SKU. F2 is the smallest paid size. A trial capacity does not support the Fabric data agent.')
@allowed([
  'F2'
  'F4'
  'F8'
  'F16'
  'F32'
  'F64'
  'F128'
  'F256'
  'F512'
  'F1024'
  'F2048'
])
param skuName string = 'F2'

@description('Capacity administrators (user principal names).')
@minLength(1)
param adminMembers array

param tags object = {}

resource capacity 'Microsoft.Fabric/capacities@2023-11-01' = {
  name: capacityName
  location: location
  tags: tags
  sku: {
    name: skuName
    tier: 'Fabric'
  }
  properties: {
    administration: {
      members: adminMembers
    }
  }
}

output capacityName string = capacity.name
output capacityId string = capacity.id