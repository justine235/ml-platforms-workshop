# Endpoint rollout commands

Order that follows the Learn article on safe rollout of online endpoints: green starts dark, is shadow-tested, then gets a small live share, then everything.

1. Green is created without `--all-traffic`, so it has 0% of live traffic. Call it directly:

```powershell
az ml online-endpoint invoke --name fleet-risk-online --deployment-name green --request-file .\endpoints\sample-request.json
```

2. Mirror (shadow) 10% of live traffic to green. Clients still get blue's answer. Call the endpoint WITHOUT a deployment name (a call that names a deployment is not mirrored), then read green's logs and switch the mirror off:

```powershell
az ml online-endpoint update --name fleet-risk-online --mirror-traffic "green=10"
1..20 | ForEach-Object { az ml online-endpoint invoke --name fleet-risk-online --request-file .\endpoints\sample-request.json | Out-Null }
az ml online-deployment get-logs --name green --endpoint-name fleet-risk-online
az ml online-endpoint update --name fleet-risk-online --mirror-traffic "green=0"
```

3. Give green a small share of live traffic, then everything. A deployment can be live OR mirrored, not both: clear the mirror first (step 2).

```powershell
az ml online-endpoint update --name fleet-risk-online --traffic "blue=90 green=10"
az ml online-endpoint update --name fleet-risk-online --traffic "blue=50 green=50"
az ml online-endpoint update --name fleet-risk-online --traffic "blue=0 green=100"
```

Mirroring limits (Learn): at most 50% of traffic, one shadow deployment per endpoint, not available for Kubernetes online endpoints, CLI 2.4.0+ or SDK 1.0.0+ (older clients drop the mirror setting when they update the endpoint).

Rollback:

```powershell
az ml online-endpoint update --name fleet-risk-online --traffic "blue=100 green=0"
az ml online-deployment delete --endpoint-name fleet-risk-online --name green --yes
```

Batch invoke example:

```powershell
az ml batch-endpoint invoke `
  --name fleet-risk-batch `
  --input azureml:fleet-asset-day-features-reference:1 `
  --deployment-name default
```

Use one instance for the workshop and scale out only when you rehearse the batch path. Online endpoints bill while deployments are provisioned; batch endpoints bill when jobs run.
