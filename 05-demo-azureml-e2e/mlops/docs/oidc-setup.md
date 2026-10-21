# GitHub OIDC setup

1. Create or reuse an Entra app registration that will represent GitHub Actions.
2. Add a **federated credential** for the repo and branch or GitHub Environment you want to trust.
3. Use the subject format that matches your policy:
   - branch-scoped: `repo:<owner>/<repo>:ref:refs/heads/main`
   - environment-scoped: `repo:<owner>/<repo>:environment:prod`
4. Grant the app the minimum Azure roles:
   - workspace deployment path: Contributor on the resource group or a tighter custom role
   - AML job path: Contributor or Azure ML Data Scientist on the workspace
   - endpoint promotion path: permissions for AML online endpoints and registry writes
5. Store only these repo or environment variables:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
6. In GitHub workflow YAML, set:

```yaml
permissions:
  id-token: write
  contents: read
```

7. Sign in from the workflow:

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ vars.AZURE_CLIENT_ID }}
    tenant-id: ${{ vars.AZURE_TENANT_ID }}
    subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
```

No client secret is needed. If login fails, the usual issue is a mismatched federated-credential subject or a missing `id-token: write` permission.
