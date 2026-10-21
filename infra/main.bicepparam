using './main.bicep'

// Placeholders only. With az, pass the real values on the command line (see README.md).
// With azd, the values come from the azd environment: azd sets AZURE_ENV_NAME, AZURE_LOCATION and
// AZURE_PRINCIPAL_ID; set the others with "azd env set" (AZURE_PRINCIPAL_UPN, AZURE_FOUNDRY_LOCATION, DEPLOY_FABRIC_CAPACITY).
// An empty foundryLocation means "same region as location".
param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'dev')
param location = readEnvironmentVariable('AZURE_LOCATION', 'francecentral')
param foundryLocation = readEnvironmentVariable('AZURE_FOUNDRY_LOCATION', '')
param userObjectId = readEnvironmentVariable('AZURE_PRINCIPAL_ID', '00000000-0000-0000-0000-000000000000')
param userPrincipalName = readEnvironmentVariable('AZURE_PRINCIPAL_UPN', 'presenter@example.com')
param deployFabricCapacity = toLower(readEnvironmentVariable('DEPLOY_FABRIC_CAPACITY', 'false')) == 'true'
