using './main.bicep'

param location = 'westeurope'
param environmentName = 'dev'
param prefix = 'fleet'
param workspaceName = 'mlw-fleet-dev'
param userObjectId = '00000000-0000-0000-0000-000000000000'
param userPrincipalName = 'presenter@example.com'
param deployContainerRegistry = true
param deployComputeInstance = false
param deployRegistry = false
param registryName = 'mlr-fleet-shared'
