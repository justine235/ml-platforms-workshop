# Rebuild guide

## 1. Create the resource group and deploy infrastructure

- **Goal:** create the Azure ML workspace and its dependencies with deterministic names.
- **Action:**

```powershell
az group create --name rg-fleet-aml-dev --location westeurope
az deployment group what-if `
  --resource-group rg-fleet-aml-dev `
  --template-file .\infra\main.bicep `
  --parameters .\infra\dev.bicepparam `
  --parameters userObjectId=<entra-object-id> userPrincipalName=<upn>

az deployment group create `
  --resource-group rg-fleet-aml-dev `
  --template-file .\infra\main.bicep `
  --parameters .\infra\dev.bicepparam `
  --parameters userObjectId=<entra-object-id> userPrincipalName=<upn>
```

- **Expected result:** workspace `mlw-fleet-dev`, compute cluster `cpu-cluster`, storage, Key Vault, Log Analytics, App Insights, and ACR exist. The cluster is `Standard_DS3_v2`, min nodes 0, max 2.
- **Duration:** 8-12 minutes.
- **What to say:** "The Fabric demo stopped at the lakehouse. Here we add the dedicated ML control plane: isolated compute, registry-ready promotion, serving, monitoring, and CI/CD."
- **What can go wrong / fix:** quota or SKU unavailable in the chosen region. Switch to France Central or Sweden Central after checking your subscription quota, or temporarily use a nearby CPU SKU and update the docs before Friday.
- **Fallback:** use a pre-created resource group and show the Bicep what-if output only.

## 2. Register the environment and data assets

- **Goal:** preload the AML environment and the data assets that the jobs reference by name.
- **Order matters:** every job and component points at `azureml:env-fleet-sklearn:1` and at `azureml:` data assets. Register all four items below **before** you create any job, component, endpoint or schedule, otherwise the create call fails with "asset not found".
- **Action:**

```powershell
az ml environment create --file .\environments\env-fleet-sklearn.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml data create --file .\jobs\data-reference-features.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml data create --file .\jobs\data-reference-dim-asset.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml data create --file .\jobs\data-champion-metrics.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
```

- **Expected result:** `env-fleet-sklearn:1`, `fleet-asset-day-features-reference:1`, `fleet-dim-asset-reference:1`, and `fleet-champion-metrics:1` appear in Studio.
- **What the champion file is:** the frozen metrics of the logistic-regression baseline on the reference run (`assets\champion-metrics.json`, test PR-AUC about 0.29). The gate compares the new challenger against it. In production the champion's metrics would come from the registry (tags on the production model version) instead of a file.
- **Duration:** 10-20 minutes for the first environment build; a few seconds later once cached.
- **What to say:** "This is the one step we pre-build. AML resolves Docker and Conda once, then reuses the image for jobs and deployments."
- **What can go wrong / fix:** environment solve failures usually come from MLflow/`azureml-mlflow` drift. Keep the exact `mlflow==2.16.2` pin.
- **Fallback:** use a curated environment for the live demo and keep the custom YAML in the repo for the rebuild story.

## 3. Submit the training pipeline

- **Goal:** validate the contract, train the model, evaluate it, apply the champion/challenger rule, and register it.
- **Action:**

```powershell
az ml job create `
  --file .\jobs\pipeline-train.yml `
  --set inputs.git_sha=$(git rev-parse HEAD) `
  --resource-group rg-fleet-aml-dev `
  --workspace-name mlw-fleet-dev
```

- **Expected result:** the pipeline shows five steps. `prep` writes the prepared bundle, `train` logs MLflow metrics, `evaluate` writes `evaluation.json`, `gate` decides promotion, and `register` creates a new `fleet-failure-7d` model version.
- **Duration:** 6-10 minutes after compute warm-up.
- **What to say:** "The point is not a miracle PR-AUC. The point is a repeatable MLOps path with traceability and a policy gate."
- **What can go wrong / fix:** a cold cluster adds 3-5 minutes. Warm the cluster before the audience arrives or temporarily set min nodes to 1 for the rehearsal window.
- **Fallback:** open a previously successful run in Studio and compare metrics there.

## 4. Verify the model metrics

- **Goal:** confirm the model still lands near the contract.
- **Action:** in Studio, open the `train` and `evaluate` outputs or run:

```powershell
az ml job show --name <pipeline-job-name> --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev --query services.Studio.endpoint
```

- **Expected result:** `test_pr_auc` lands around `0.385 ± 0.03`, `test_roc_auc` around `0.75 ± 0.02`.
- **Duration:** 2 minutes.
- **What to say:** "This is a realistic low-prevalence maintenance problem. A PR-AUC around 0.38 is useful once you operationalize it."
- **What can go wrong / fix:** tiny differences across libraries are expected; if the run drifts beyond tolerance, confirm the MLflow and scikit-learn pins.
- **Fallback:** use the local validation output or the contract table in `scenario-contract.md`.

## 5. Deploy the managed online endpoint

- **Goal:** expose the model behind `fleet-risk-online` with blue/green control.
- **Action:**

```powershell
az ml online-endpoint create --file .\endpoints\online-endpoint.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml online-deployment create --file .\endpoints\online-blue-deployment.yml --all-traffic --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml online-deployment create --file .\endpoints\online-green-deployment.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
```

- **Expected result:** blue handles 100% of live traffic; green is provisioned but dark.
- **Duration:** 10-15 minutes the first time, faster after cache warm-up.
- **What to say:** "Fabric can score in batch, but this is why Azure ML exists in the story: explicit serving, blue/green, mirroring, and endpoint observability."
- **What can go wrong / fix:** if deployment creation stalls, check ACR pull permissions, image build logs, and SKU quota.
- **Fallback:** show the YAML and a prebuilt endpoint in Studio.

## 6. Smoke-test the endpoint, shadow green, then shift traffic

- **Goal:** prove the model serves live and show safe rollout mechanics, in the order the Learn article uses: green dark, then mirrored, then a small live share.
- **Action:**

```powershell
az ml online-endpoint invoke `
  --name fleet-risk-online `
  --deployment-name blue `
  --request-file .\endpoints\sample-request.json `
  --resource-group rg-fleet-aml-dev `
  --workspace-name mlw-fleet-dev

# Shadow: blue still answers, about 10% of calls are copied to green
az ml online-endpoint update --name fleet-risk-online --mirror-traffic "green=10" --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
1..20 | ForEach-Object { az ml online-endpoint invoke --name fleet-risk-online --request-file .\endpoints\sample-request.json --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev | Out-Null }
az ml online-deployment get-logs --name green --endpoint-name fleet-risk-online --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml online-endpoint update --name fleet-risk-online --mirror-traffic "green=0" --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev

# Canary: now green gets a small LIVE share
az ml online-endpoint update --name fleet-risk-online --traffic "blue=90 green=10" --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
```

- **Expected result:** the request to blue returns probabilities for three real feature rows; the mirrored calls appear in green's logs while callers still get blue's answer; the endpoint then shows 90/10 blue/green live traffic.
- **Rule to say out loud:** a deployment is either live or mirrored, never both, so the mirror is cleared (`green=0`) before green gets live traffic. Mirroring is capped at 50% and works for one deployment at a time. Call the endpoint without `--deployment-name`: a call that names a deployment is not mirrored.
- **Duration:** 3 minutes.
- **What to say:** "The online story is not just deployment. It is controlled rollout, shadowing, and rollback."
- **What can go wrong / fix:** if the payload fails, confirm that the request uses AML's `input_data` wrapper and the exact feature signature.
- **Fallback:** use `invoke-online.py` with an Entra token or show the endpoint test pane in Studio.

## 7. Deploy and invoke the batch endpoint

- **Goal:** score a day of feature exports asynchronously.
- **Action:**

```powershell
az ml batch-endpoint create --file .\endpoints\batch-endpoint.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml batch-deployment create --file .\endpoints\batch-deployment.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml batch-endpoint invoke `
  --name fleet-risk-batch `
  --deployment-name default `
  --input azureml:fleet-asset-day-features-reference:1 `
  --resource-group rg-fleet-aml-dev `
  --workspace-name mlw-fleet-dev
```

- **Expected result:** a batch scoring job starts and writes predictions to `predictions.csv`.
- **Duration:** 3-5 minutes plus compute warm-up.
- **What to say:** "For lake-sized backfills or daily partitions, batch endpoints are the clean contract between Fabric orchestration and AML serving."
- **What can go wrong / fix:** batch input must match the MLflow model signature. If the deployment rejects the file, confirm the source is the same prepared schema used at training time.
- **Fallback:** run `src\score.py` locally and show the equivalent output contract.

## 8. Set up retraining and monitoring

- **Goal:** leave the audience with an operational pattern, not just a one-off run.
- **Action:**

```powershell
az ml schedule create --file .\jobs\schedule.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
az ml schedule create --file .\jobs\monitoring\model-monitoring.schedule.yml --resource-group rg-fleet-aml-dev --workspace-name mlw-fleet-dev
```

- **Expected result:** one retraining schedule exists, and the monitoring schedule is ready if the target tenant supports the preview schema.
- **Duration:** 2 minutes.
- **What to say:** "The guaranteed monitoring path is our PSI job. AML managed monitoring is useful, but still something I recheck in the tenant before promising it live."
- **What can go wrong / fix:** the preview monitoring schema can change. Keep `drift.py` as the guaranteed monitoring fallback.
- **Fallback:** show `local-validation\run_local.py` and `src\drift.py` instead of the preview schedule.

## 9. CI/CD wiring

- **Goal:** show how the repo becomes an auditable MLOps asset.
- **Action:** apply the OIDC guide in `mlops\docs\oidc-setup.md`, then place the templates in `.github\workflows\` or a template repo.
- **Expected result:** PRs lint and validate assets, merges can deploy infra, and approved promotions can shift traffic from blue to green in production.
- **Duration:** 5-10 minutes outside the live demo.
- **What to say:** "OIDC means no Azure secrets in GitHub. The deployment identity is issued just-in-time per workflow run."
- **What can go wrong / fix:** the most common failure is a mismatched federated-credential subject or missing `id-token: write` permission.
- **Fallback:** show the workflow YAML and the GitHub Environments approval model on slides.
