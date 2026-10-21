# Azure DevOps equivalence note

The same pattern works in Azure DevOps:

- GitHub OIDC -> Azure DevOps service connection with workload identity federation.
- GitHub Actions workflow -> Azure Pipelines YAML stage.
- GitHub Environments approval -> Azure DevOps environment approval or manual validation check.
- `azure/login@v2` -> AzureCLI task or AzurePowerShell task bound to the service connection.

Use GitHub in this repo because it is the cleaner workshop story, not because Azure DevOps is missing any critical AML capability.
