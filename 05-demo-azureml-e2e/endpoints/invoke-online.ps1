param(
  [string]$ResourceGroup,
  [string]$Workspace,
  [string]$Deployment = "blue"
)

az ml online-endpoint invoke `
  --name fleet-risk-online `
  --deployment-name $Deployment `
  --resource-group $ResourceGroup `
  --workspace-name $Workspace `
  --request-file .\sample-request.json
