# Registry promotion

## Recommended path

1. Train and register in the dev AML workspace.
2. Share the winning model to a shared AML registry.
3. Deploy from the registry into test and prod workspaces.
4. Keep environments and reusable components in the same registry so the serving stack is versioned with the model.

## CLI examples

Run these from your machine or from the promotion workflow (`mlops/github-workflows/promote-model.yml`). The source workspace flags are required because the command copies an asset **out of** a workspace.

```powershell
az ml model share `
  --name fleet-failure-7d `
  --version 12 `
  --share-with-name fleet-failure-7d `
  --share-with-version 12 `
  --registry-name mlr-fleet-shared `
  --resource-group rg-fleet-aml-dev `
  --workspace-name mlw-fleet-dev

az ml environment share `
  --name env-fleet-sklearn `
  --version 1 `
  --share-with-name env-fleet-sklearn `
  --share-with-version 1 `
  --registry-name mlr-fleet-shared `
  --resource-group rg-fleet-aml-dev `
  --workspace-name mlw-fleet-dev
```

Deploy from the registry into test or prod. The model lives in the registry, not in the target workspace, so override the model reference of the deployment YAML:

```powershell
az ml online-deployment create `
  --file .\endpoints\online-green-deployment.yml `
  --set model=azureml://registries/mlr-fleet-shared/models/fleet-failure-7d/versions/12 `
  --resource-group rg-fleet-aml-prod `
  --workspace-name mlw-fleet-prod
```

> ⚠ Verify once in the target tenant: the `share` flags (the share-with flags are optional and default to the source name and version), the registry reference format, and the RBAC on the registry.

## Why the registry matters

- Promotion is explicit and auditable.
- Dev/test/prod workspaces stay isolated.
- The same model and environment versions are deployable in each workspace.
- You avoid re-creating environments and components by hand in every workspace.

## Notes

- Recheck the target registry region and RBAC before the live demo.
- If the registry path is unavailable in the tenant, fall back to workspace-local deployment and explain that registry-based promotion is the production pattern.
