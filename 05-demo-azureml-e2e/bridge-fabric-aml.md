# Fabric and Azure ML together

## The short answer

Use **Fabric** for lakehouse ETL, lake-native notebooks, shortcuts, and Power BI-adjacent analytics. Use **Azure ML** for explicit ML platforms concerns: managed online endpoints, batch endpoints, champion/challenger promotion, dedicated ML RBAC, AML schedules, and registry-based sharing.

## Today’s practical hybrid pattern

1. Fabric data engineering produces `ml.asset_day_features`.
2. Publish the feature export to OneLake `/Files` or to shared ADLS Gen2.
3. Register that path in AML as a data asset or reference it directly from a datastore.
4. Train, evaluate, register, and deploy in AML.
5. Write scores back to OneLake `/Files` or to a landing table for Power BI and the data agent.

## Reading OneLake from Azure ML

- **Verified:** AML can read OneLake `/Files` through direct `abfss://` paths or an AML OneLake datastore.
- **Verified:** AML's CLI/SDK support OneLake datastore definitions even though the AML Studio UI doesn't list OneLake as a datastore type.
- **⚠ PREVIEW / care point:** the OneLake datastore support is still described as CLI/SDK-focused and the `OneLakeDatastore` Python entity is experimental.
- **Verified:** the easy no-copy story is for `/Files`. The documented `/Tables` UI-linked pattern copies data into ADLS Gen2 first.

Example ABFSS path:

```text
abfss://<fabric-workspace-guid>@onelake.dfs.fabric.microsoft.com/<lakehouse-name>.Lakehouse/Files/fleet/ml/asset_day_features/
```

## Create the OneLake datastore (optional, ⚠ preview)

The kit does not create this datastore. The default demo path uses the three data assets of `rebuild-guide.md` step 2, which read the reference files and need no Fabric. Use the datastore only for the hybrid demo, where Azure ML reads the features straight from the Fabric lakehouse (`jobs\data-onelake-features.yml`).

1. In Fabric, open the lakehouse. Its URL contains both ids: `.../groups/<workspace-guid>/lakehouses/<lakehouse-guid>`.
2. Put them in `jobs\datastore-onelake.yml` (`one_lake_workspace_name` and `artifact.name`; the SDK documents names as well as GUIDs).
3. Export the table once to the folder the data asset points at (any export works; from a Fabric notebook with `lh_fleet` as the default lakehouse):

   ```python
   spark.table("ml.asset_day_features").write.mode("overwrite").parquet("Files/fleet/ml/asset_day_features")
   ```

4. Create the datastore, then the data asset that uses it:

   ```powershell
   az ml datastore create --file jobs/datastore-onelake.yml
   az ml data create --file jobs/data-onelake-features.yml
   ```

Python SDK equivalent (the class is marked experimental):

```python
from azure.ai.ml.entities import OneLakeArtifact, OneLakeDatastore

ml_client.datastores.create_or_update(
    OneLakeDatastore(
        name="fleet_onelake",
        artifact=OneLakeArtifact(name="<lakehouse-name-or-guid>", type="lake_house"),
        one_lake_workspace_name="<fabric-workspace-name-or-guid>",
        endpoint="https://onelake.dfs.fabric.microsoft.com",
    )
)
```

Care points, all to check in the target tenant before Friday:

- The credential is either a service principal or none (identity-based access). The identity that reads the data needs access to the Fabric workspace; confirm the minimum workspace role.
- The Fabric tenant setting that lets apps outside Fabric read OneLake must be on for the users or principals involved.
- The YAML shape comes from the azure-ai-ml schema (the offline validator loads it). There is no public JSON schema for it, so `az ml datastore create` is the real test.

## Writing scores back to Fabric

- For the workshop, the cleanest pattern is `ml.failure_risk_score` written as CSV or Parquet to a shared folder, then surfaced in Fabric through OneLake Files or a shortcut-backed lakehouse folder.
- If you need a managed table, let Fabric load the scored files into a Delta table after the AML batch job finishes.

## Calling AML from Fabric

- **Fabric pipelines:** the Azure Machine Learning activity can run AML jobs and currently exposes **Batch Endpoint** and **Pipeline (v1)** endpoint types.
- **Fabric notebooks:** there is no special AML client surface. Call the AML online endpoint as a normal HTTPS service or use the AML SDK as an external Python client.
- **Batch endpoint from Fabric:** Microsoft documents this as a **preview** integration pattern and recommends shared storage paths rather than OneLake-only assumptions.

## Identity and permissions

- The human operator needs access to both the Fabric workspace and the AML workspace.
- The AML compute identity needs access to the storage that holds the shared features or batch inputs.
- If you use AAD-authenticated online endpoints, the Fabric or notebook caller needs an Entra token for the AML endpoint audience.

## Network considerations

- The workshop files assume public network access because it keeps the live setup simpler.
- If you later lock down AML with managed networking or Private Link, rehearse the storage, ACR, endpoint, and Fabric access paths again. Those are the first places where live demos slow down.

## Fabric ML vs Azure ML decision guide

Choose **Fabric ML** when:

- the primary persona lives in the lakehouse and notebook,
- the model stays close to Fabric data products,
- MLflow tracking inside the Fabric workspace is enough,
- you do not need AML-style endpoint rollout or registry promotion.

Choose **Azure ML** when:

- you need managed online endpoints or batch endpoints,
- you need blue/green rollout, mirroring, or registry-driven promotion,
- you want the ML workflow separated from the analytics workspace,
- you need AML schedules, explicit compute management, or richer endpoint monitoring,
- you want a classic MLOps control plane around the model.
