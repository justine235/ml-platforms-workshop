// Microsoft Foundry: AIServices account + project + chat model deployment + the roles the presenter needs.
// Resource-group scope. Called from ../main.bicep.
targetScope = 'resourceGroup'

@description('Region of the Foundry account. The chat model must be available in this region.')
param location string

@description('Name of the Foundry account. It is also the custom subdomain, so it must be globally unique (2-64 characters: letters, digits, hyphens).')
@minLength(2)
@maxLength(64)
param accountName string

@description('Name of the Foundry project created inside the account.')
@minLength(2)
@maxLength(64)
param projectName string

@description('Object id of the user who builds and runs agents in the project. It gets Foundry User and Foundry Project Manager on the account.')
param userObjectId string

@description('Name of the chat model deployment. This is the value of AZURE_OPENAI_MODEL_DEPLOYMENT in the 06 kit.')
param deploymentName string

@description('Model name, for example gpt-5.4.')
param modelName string

@description('Model version, for example 2026-03-05.')
param modelVersion string

@description('Deployment SKU, for example GlobalStandard.')
param modelSkuName string

@description('Capacity in units of 1,000 tokens per minute. Must not exceed the quota of the subscription in this region.')
param modelCapacity int

@description('Create the three role assignments below. Set to false if the deploying identity may not create role assignments; then assign the roles by hand (see infra/README.md).')
param assignRoles bool = true

param tags object = {}

// Built-in role ids (Microsoft Learn, "Azure built-in roles"; the roles were renamed from "Azure AI ..." and the ids did not change).
var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
var foundryProjectManagerRoleId = 'eadc314b-1a2d-4efa-be10-5d325db5065e'

resource account 'Microsoft.CognitiveServices/accounts@2026-09-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  parent: account
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: projectName
    description: 'Project for the workshop data agent demo (06).'
  }
}

// Created after the project so that the account is never modified by two operations at the same time.
resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-09-01' = {
  parent: account
  name: deploymentName
  sku: {
    name: modelSkuName
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
  dependsOn: [
    project
  ]
}

resource userFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  scope: account
  name: guid(account.id, userObjectId, foundryUserRoleId)
  properties: {
    principalId: userObjectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

// Needed to create the project connection to Fabric in the Foundry portal.
resource userProjectManager 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  scope: account
  name: guid(account.id, userObjectId, foundryProjectManagerRoleId)
  properties: {
    principalId: userObjectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryProjectManagerRoleId)
  }
}

// The project's managed identity also needs Foundry User on the account.
resource projectFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignRoles) {
  scope: account
  name: guid(account.id, project.id, foundryUserRoleId)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

output accountName string = account.name
output accountId string = account.id
output projectName string = project.name
output projectEndpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output deploymentName string = chatDeployment.name