param location string
param workspaceName string
param computeClusterName string
param deployComputeInstance bool
param computeInstanceName string
param computeInstanceUserObjectId string

resource workspace 'Microsoft.MachineLearningServices/workspaces@2025-06-01' existing = {
  name: workspaceName
}

resource cpuCluster 'Microsoft.MachineLearningServices/workspaces/computes@2025-06-01' = {
  name: computeClusterName
  location: location
  parent: workspace
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: 'Standard_DS3_v2'
      minNodeCount: 0
      maxNodeCount: 2
      idleSecondsBeforeScaleDown: 900
      enableNodePublicIp: false
      scaleSettings: {
        maxNodeCount: 2
        minNodeCount: 0
        nodeIdleTimeBeforeScaleDown: 'PT15M'
      }
    }
  }
}

resource computeInstance 'Microsoft.MachineLearningServices/workspaces/computes@2025-06-01' = if (deployComputeInstance) {
  name: computeInstanceName
  location: location
  parent: workspace
  properties: {
    computeType: 'ComputeInstance'
    properties: {
      vmSize: 'STANDARD_DS3_V2'
      personalComputeInstanceSettings: {
        assignedUser: {
          objectId: computeInstanceUserObjectId
          tenantId: subscription().tenantId
        }
      }
    }
  }
}
