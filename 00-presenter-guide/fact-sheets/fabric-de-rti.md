# Microsoft Fabric Data Engineering + RTI + Admin/Automation fact sheet (verified as of 2026-10-18)

Scope: workshop build notes for Fabric lakehouse/RTI/admin/automation. Sources are official Microsoft Learn or Microsoft GitHub unless explicitly marked otherwise. Anything not confirmed on an official/current source is marked **UNVERIFIED**.

---

## A. Lakehouse + medallion

### A1. Schema-enabled lakehouse
- **Status:** **Preview** for the REST `creationPayload.enableSchemas` property (the create-Lakehouse API still labels `LakehouseCreationPayload` preview); portal creation has **Lakehouse schemas** checked by default. **As of:** 2026-10-18. **Sources:**  
  - https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas  
  - https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/create-lakehouse
- Default schema is **`dbo`** and can’t be renamed or removed.
- Schema names: letters, numbers, underscore only.
- Features that **require** schema-enabled lakehouses include **Materialized Lake Views**.
- Cross-workspace Spark naming is `workspace.lakehouse.schema.table`.

### A2. Notebook pathing and default lakehouse rules
- **Relative Spark paths** work only against the **default lakehouse** attached to the notebook. `Files/...` and `Tables/...` are resolved relative to that default lakehouse. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data
- **Pandas mount** for the default lakehouse is `/lakehouse/default/Files/...`; this mount exists in notebooks, **not** Spark job definitions. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data
- If multiple lakehouses are attached, the pinned one is the runtime root for relative paths. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-explore
- For non-default lakehouses or cross-item access, use **ABFSS** copied from the UI.

```python
# official path patterns adapted from Learn
# Source: https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data

# Spark, default lakehouse
spark.read.parquet("Files/bronze/telematics")

# Pandas, default lakehouse
import pandas as pd
pd.read_parquet("/lakehouse/default/Files/bronze/telematics.parquet")

# Cross-lakehouse / explicit OneLake path
spark.read.format("delta").load(
    "abfss://MyWorkspace@onelake.dfs.fabric.microsoft.com/FleetDemo.Lakehouse/Tables/silver/faults"
)
```

### A3. Delta write/upsert patterns that are safe for the demo
- `saveAsTable("schema.table")` is the right write target for schema-enabled lakehouses; omitting schema lands in `dbo`. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas
- `mergeSchema=true` = additive schema evolution only; `overwriteSchema=true` = replace table schema and is disruptive. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/delta-lake-schema-evolution
- `MERGE WITH SCHEMA EVOLUTION` is documented in Fabric and is the cleanest upsert + new-column pattern. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/delta-lake-schema-evolution

```python
# Sources:
# https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas
# https://learn.microsoft.com/en-us/fabric/data-engineering/delta-lake-schema-evolution

df.write.format("delta").mode("overwrite").saveAsTable("bronze.telematics_raw")

df2.write.format("delta").option("mergeSchema", "true").mode("append").saveAsTable("silver.telematics")

new_df.write.format("delta").option("overwriteSchema", "true").mode("overwrite").saveAsTable("silver.telematics")

spark.sql("""
MERGE WITH SCHEMA EVOLUTION INTO silver.assets AS target
USING staged_assets AS source
ON target.asset_id_norm = source.asset_id_norm
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
""")
```

### A4. V-Order, OPTIMIZE, VACUUM, partitioning
- **Important 2026 change:** in **new Fabric workspaces, V-Order is disabled by default** for Spark writes (`spark.sql.parquet.vorder.default=false`) to favor write-heavy engineering workloads. Enable it deliberately for read-heavy/Direct Lake serving layers. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order
- `OPTIMIZE` is the main compaction tool; `VACUUM` is for storage cleanup, not performance. **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization
- For Spark-written tables, Microsoft guidance is: keep adaptive file sizing, deletion vectors, file-level compaction targets, and prefer **auto compaction**; avoid arbitrary max row counts per file. **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization
- For small/medium demo data, **don’t partition by default**. Microsoft now explicitly says avoid partitioning by default; use it only for clear operational reasons (for example, concurrent updates on disjoint partitions). **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization

```sql
-- Read-heavy serving layer only if measured need exists
-- Source: https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order
SET spark.sql.parquet.vorder.default=TRUE;
```

### A5. Materialized Lake Views (MLVs)
- **Status:** feature documented and production-oriented; **PySpark authoring is explicitly Preview** and currently **full refresh only**. **As of:** 2026-10-18. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view
- MLVs require **schema-enabled lakehouses**.
- Best fit: SQL-defined bronze→silver→gold transformations, built-in lineage, dependency ordering, and scheduled refresh.
- Data-quality constraints are first-class: `CONSTRAINT ... CHECK (...) ON MISMATCH DROP|FAIL`.
- `REFRESH_HINT ... UNIQUE (...)` is explicitly **Preview**. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view
- Recommendation for this workshop: keep **bronze/silver/gold ETL in PySpark** for teaching medallion mechanics, but mention MLVs as Fabric’s newer declarative option.

```sql
-- Source: https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view
CREATE MATERIALIZED LAKE VIEW silver.valid_orders
(
    CONSTRAINT positive_amount CHECK (order_amount > 0) ON MISMATCH DROP
)
AS SELECT * FROM bronze.raw_orders;
```

### A6. Shortcuts and SQL endpoint sync gotchas
- Lakehouse shortcuts support **OneLake, ADLS Gen2, Azure Blob, Amazon S3, S3-compatible, Google Cloud Storage, Dataverse, OneDrive/SharePoint** in the public definition. **Source:** https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/lakehouse-definition
- SQL analytics endpoint metadata sync is automatic, but still a real demo gotcha.
- **New metadata sync** is explicitly **Preview**, only applies to **new** SQL analytics endpoints created after enablement, and **can’t be enabled if the workspace uses workspace private link**. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/sql-analytics-endpoint-metadata-sync
- Force refresh options: portal **Refresh**, REST API, or `sys.sp_dw_refresh_ext_table` for per-table refresh on the new sync architecture.

### A7. Direct Lake basics
- Direct Lake is the semantic-model storage mode optimized to load from **Delta tables in OneLake** with low-cost “framing” instead of full import. **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview
- For this workshop, the clean story is: **gold Delta tables in Lakehouse -> Direct Lake semantic model**.
- Direct Lake on OneLake supports Lakehouse, Warehouse, SQL DB in Fabric, mirrored sources, and **KQL database only when OneLake availability is enabled**. **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview

---

## B. Orchestration (Pipelines, notebooks, Dataflow Gen2)

### B1. Notebook activity facts
- Pipeline notebook activity type is **`TridentNotebook`** in the definition schema. **Source:** https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition
- Documented notebook activity properties: `notebookId`, `workspaceId`, optional `parameters`, optional `sessionTag`.
- `notebookutils.notebook.exit("...")` surfaces to orchestration; Fabric notebook public API and notebook activity both treat the returned string as the run exit value. **Sources:**  
  - https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-public-api  
  - https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-activity
- `NotebookUtils` is the current namespace; `mssparkutils` remains for backward compatibility, but don’t teach the old name first.
- `sessionTag` reuse requires workspace high concurrency support.
- Known limitation: notebook activity doesn’t support **cross-region notebook calls**.

### B2. `notebookutils.notebook.run` and `runMultiple`
- Use `notebookutils.notebook.run(path, timeout, args)` for simple chaining.
- Use `runMultiple()` for DAG-style fan-out/fan-in orchestration inside notebooks; use pipelines when you want monitoring/governance/UI scheduling.
- For this workshop, show pipelines for top-level orchestration and `runMultiple()` only as an advanced notebook-local DAG pattern.

### B3. Copy / Web / ForEach / triggers / Dataflow Gen2
- Pipeline definitions document `Copy`, `WebActivity`, `ForEach`, and notification activities. **Source:** https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition
- Copy from **HTTP** into **Lakehouse Files** is supported through pipeline connectors/datasets; practical use: ingest raw synthetic files from a GitHub raw URL for a no-local-tool demo.
- `ForEach` is the right pattern for iterating over a list of raw file URLs or entity names.
- `WebActivity` is useful for lightweight web calls (for example, ping, webhook, signed URL call) but not for moving bulk data.
- **Dataflow Gen2:** use it when you want GUI-first shaping for tabular data; not the best primary vehicle for this workshop’s PySpark medallion/ML demo, because Spark notebooks are more reproducible and closer to Azure ML/Fabric code parity.

### B4. Failure alerts
- Use **MicrosoftTeams/Teams** or **Email/Office365Email** activities in pipelines for deterministic post-failure notification. **Source:** https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition
- For near-real-time/event-driven alerting, use **Activator**; it can trigger Teams/email/pipelines/notebooks/dataflows/copy jobs/UDFs. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction

### B5. Verified minimal pipeline definition (Git/REST format) with a Notebook activity
```json
{
  "properties": {
    "description": "Minimal notebook pipeline",
    "activities": [
      {
        "name": "RunBronzeNotebook",
        "type": "TridentNotebook",
        "typeProperties": {
          "notebookId": "11111111-1111-1111-1111-111111111111",
          "workspaceId": "22222222-2222-2222-2222-222222222222",
          "parameters": {
            "run_date": {
              "value": "2026-10-23",
              "type": "string"
            }
          },
          "sessionTag": "fleet-demo"
        }
      }
    ]
  }
}
```
Source schema: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition

---

## C. Git item formats / item definitions

### C1. Notebook
- Git folder shape is official:  
  `<name>.Notebook/` -> `.platform`, `notebook-content.py|sql|scala|r`, optional `Resources/`, `fs-settings.json`, `notebook-settings.json`. **Source:** https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-source-control-deployment
- REST definition supports `FabricGitSource` and `ipynb`. **Source:** https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition
- Default lakehouse metadata fields verified from the official **microsoft/fabric-cli** examples: `default_lakehouse`, `default_lakehouse_name`, `default_lakehouse_workspace_id` under `metadata.dependencies.lakehouse`. **Source:** https://raw.githubusercontent.com/microsoft/fabric-cli/main/docs/examples/item_examples.md

```text
Notebook_1.Notebook/
  .platform
  notebook-content.py
  fs-settings.json              # optional
  notebook-settings.json        # optional
  Resources/builtin/...         # optional
```

```python
# minimal FabricGitSource notebook metadata shape (adapted from official docs/examples)
# Sources:
# https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition
# https://raw.githubusercontent.com/microsoft/fabric-cli/main/docs/examples/item_examples.md
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "00000000-0000-0000-0000-000000000001",
# META       "default_lakehouse_name": "FleetDemo",
# META       "default_lakehouse_workspace_id": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }
```

### C2. Lakehouse / DataPipeline / Environment / VariableLibrary / Eventhouse / Eventstream
```text
LakehouseName.Lakehouse/
  lakehouse.metadata.json
  shortcuts.metadata.json       # optional
  data-access-roles.json        # optional
  alm.settings.json             # optional
  .platform                     # optional

PipelineName.DataPipeline/
  pipeline-content.json
  .platform                     # optional

EnvName.Environment/
  Libraries/PublicLibraries/environment.yml   # optional
  Setting/Sparkcompute.yml                    # optional
  .platform                                   # optional

Vars.VariableLibrary/
  variables.json
  settings.json
  valueSets/<name>.json                       # optional
  .platform                                   # optional

Rt.Eventhouse/
  EventhouseProperties.json
  .platform                                   # optional

Stream.Eventstream/
  eventstream.json
  eventstreamProperties.json                  # optional
  .platform                                   # optional
```
Sources:  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/lakehouse-definition  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/environment-definition  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/variable-library-definition  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventhouse-definition  
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventstream-definition

### C3. `fabric-cicd` parameterization
- Official docs/tutorials confirm `parameter.yml` for environment-specific replacement and official GitHub examples show notebook/lakehouse ID rewriting. **Sources:**  
  - https://learn.microsoft.com/en-us/fabric/cicd/tutorial-fabric-cicd-azure-devops  
  - https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-deploy-fabric-cicd  
  - https://github.com/microsoft/fabric-cicd
- Practical use in this demo: replace workspace IDs, lakehouse IDs, SQL endpoint IDs, and notebook-attached lakehouse metadata.

```yaml
# minimal example, adapted from official fabric-cicd docs
find_replace:
  - find_value: "11111111-1111-1111-1111-111111111111"
    replace_value:
      dev: "11111111-1111-1111-1111-111111111111"
      prod: "22222222-2222-2222-2222-222222222222"
```

---

## D. Real-Time Intelligence for logs / reconciliation

### D1. Eventstream -> Eventhouse/KQL DB
- Eventstream source coverage is broad and current: **custom endpoint**, **Azure Event Hubs**, **Kafka/Confluent/MSK**, **sample data**, **HTTP (preview)**, many CDC sources, and Fabric/Azure events. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview
- **Schema-aware eventstream** is explicitly **Preview**. Use the existing eventstream experience for the least demo risk.
- Eventhouse is Fabric’s preferred engine for **semistructured and free-text** event/log analysis. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/eventhouse

### D2. KQL patterns that fit this reconciliation demo
```kusto
// normalize asset IDs from multiple sources
let norm = (s:string) {
    toupper(replace_regex(@"[^A-Z0-9]", "", s))
};
telematics_raw
| extend asset_id_norm = norm(asset_id)
| extend fault_code = tostring(parse_json(payload).fault_code)
| project ts, asset_id_norm, fault_code, src="telematics"
```

```kusto
// recent work order match within 7 days
let wo = workorders
| extend asset_id_norm = toupper(replace_regex(@"[^A-Z0-9]", "", asset_id));
let faults = faults_gold
| extend asset_id_norm = toupper(replace_regex(@"[^A-Z0-9]", "", asset_id));
faults
| join kind=leftouter wo on asset_id_norm
| where wo_time between (ts .. ts + 7d)
```

```kusto
// anti-join = assets seen in logs but missing in ERP
faults_gold
| join kind=leftanti erp_assets on asset_id_norm
```

Other useful operators for the workshop: `extract()`, `parse`, `replace_regex()`, `lookup`, `arg_max()`, `take_any()`, materialized views, update policies.

### D3. Eventhouse OneLake availability
- **Status:** generally documented/available feature, but with important restrictions. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-house-onelake-availability
- Turning on **OneLake availability** exposes KQL database data as Delta in OneLake, enabling notebooks, lakehouse/warehouse shortcuts, SQL analytics endpoint (with schema sync), and Direct Lake.
- Restrictions while enabled: no table rename, no column type alteration, no row-level security, no delete/truncate/purge.
- **Major live-demo gotcha:** default write latency can be **up to 3 hours** or until optimal Parquet files are formed; `TargetLatencyInMinutes` can be lowered to **5..180** minutes, but shorter windows create small-file risks and the Delta copy is read-only / can’t be optimized later.

```kusto
// Source: https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-house-onelake-availability
.alter-merge table Faults policy mirroring dataformat=parquet with (IsEnabled=true, TargetLatencyInMinutes=5);
```

### D4. Spark connector for Kusto/Eventhouse
- Official guidance is still the **Azure Kusto Spark connector** (open source). Versions earlier than **2.5.1** are called out as no longer working for ingest into existing tables. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/get-data-spark
- Good for batch ETL/ML over eventhouse data; KQL is still better for interactive reconciliation and time-window log joins.

### D5. PySpark vs KQL guidance for this demo
- **Use KQL** for: parsing logs, regex cleanup, windowed joins over event time, anti-joins for “missing in ERP/work orders”, fast dedupe and low-latency dashboards.
- **Use PySpark** for: medallion ETL, feature engineering for the failure model, large multi-step data prep, training/inference.
- Best workshop story: **raw log ingress -> Eventhouse/KQL for interactive reconciliation; curated historical gold + ML features -> Lakehouse/Spark**.

### D6. Real-Time Dashboard + Activator
- Real-Time Dashboard supports live monitoring, cross-filter/drillthrough, Copilot authoring, and Activator integration. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/real-time-dashboards-overview
- Activator is subsecond for stateless rules on streaming data and can trigger Teams/email/Power Automate/**pipelines/notebooks/dataflows/copy jobs**. **Source:** https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction

---

## E. Admin / enterprise readiness / prerequisites

### E1. Exact tenant settings you almost certainly need
- **Service principals can call Fabric public APIs** — for unattended REST automation. **Default:** enabled for new customers. **Source:** https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-developer
- **Service principals can create workspaces, connections, and deployment pipelines** — needed if automation creates workspaces. **Default:** disabled for new customers. **Source:** same as above.
- **Users can use Copilot and other features powered by Azure OpenAI** — required for Copilot/AI experiences; enabled by default. **Source:** https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-copilot
- **Capacities can be designated as Copilot in Fabric capacities** — enabled by default. **Source:** same.
- For data agents specifically: enable the above plus, outside EU/US data boundaries, the cross-region processing/storage settings below. **Source:** https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings
- Cross-boundary settings with exact names:  
  - **Data sent to Azure OpenAI can be processed outside your capacity's geographic region, compliance boundary, or national cloud instance**  
  - **Data sent to Azure OpenAI can be stored outside your capacity's geographic region, compliance boundary, or national cloud instance**

### E2. Capacity / trial / roles / region
- Fabric uses **F SKUs**; **Trial** is listed as 64 CU equivalent but isn’t acceptable for some enterprise features (for example trusted workspace access, CMK). **Source:** https://learn.microsoft.com/en-us/fabric/enterprise/licenses
- For Power BI viewing with free users, **F64+** is the important threshold. Below F64, viewers need Pro/PPU/trial. **Source:** same.
- Regions: **West Europe, North Europe, France Central, Germany West Central, Italy North, Spain Central, Sweden Central, Switzerland North/West, UK South/West** all show all Fabric workloads. **Source:** https://learn.microsoft.com/en-us/fabric/admin/region-availability
- **Sweden Central** has a specific BCDR note: Power BI supported there but not in its paired region by default. **Source:** same.

### E3. Security/networking distinctions that large enterprises ask about
- **Private Link** = inbound/private access to Fabric; it does **not** secure Fabric outbound traffic to your external sources. **Source:** https://learn.microsoft.com/en-us/fabric/security/security-private-links-overview
- **Managed private endpoints** = Fabric-managed outbound private connectivity to supported resources; supported for Data Engineering and Eventstream, region-limited to where Data Engineering exists. **Source:** https://learn.microsoft.com/en-us/fabric/security/security-managed-private-endpoints-overview
- **Trusted workspace access** = allow specific Fabric workspaces through Azure Storage firewall resource-instance rules; **GA**, F SKU only, not Trial. **Source:** https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access
- **Workspace outbound access protection** = default-deny outbound at workspace level + allowlist via managed private endpoints or data connection rules. **Source:** https://learn.microsoft.com/en-us/fabric/security/workspace-outbound-access-protection-overview

### E4. Governance / compliance / audit / CMK / BCDR
- **Purview:** use Fabric-native governance for basics, Purview when you need enterprise scanning, lineage beyond Fabric, DLP, broader classification/compliance. **Source:** https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric
- **Sensitivity labels:** supported through Microsoft Purview Information Protection; apply at item level and propagate downstream depending on item flow. **Source:** https://learn.microsoft.com/en-us/fabric/fundamentals/apply-sensitivity-labels
- **Audit logs:** accessed through **Microsoft Purview audit**; Fabric audit entries are documented. **Source:** https://learn.microsoft.com/en-us/fabric/admin/track-user-activities
- **Workspace CMK:** supported for Lakehouse, Warehouse, Notebook, Environment, Spark Job Definition, Pipeline, Dataflow, Copy Job, SQL DB, Mirrored DB, Graph, and **Eventhouse (preview)**. Not supported for Spark temp/shuffle/cache or some metadata/transient areas. **Source:** https://learn.microsoft.com/en-us/fabric/security/workspace-customer-managed-keys
- **BCDR:** shared-responsibility model; OneLake geo-replication is capacity-level opt-in, asynchronous, and only where Azure paired-region + Fabric support exist. **Sources:**  
  - https://learn.microsoft.com/en-us/fabric/security/reliability-fabric  
  - https://learn.microsoft.com/en-us/fabric/onelake/onelake-disaster-recovery

### E5. One-page enterprise readiness FAQ
- **Can Fabric stay inside EU data boundary?** Yes, if you place capacity in EU-supported regions; Multi-Geo in EU keeps data within EU boundary, but AI cross-region settings must remain off unless you accept that exception. **Sources:** region availability + copilot settings docs.
- **Is OneLake data residency guaranteed by workspace region?** Data items live in the workspace/capacity region; home-region and Multi-Geo still matter for some service metadata/control-plane behaviors. **Source:** reliability + region docs.
- **Can we lock outbound access?** Yes, with workspace outbound access protection; but support is workload-specific and unsupported artifacts can block enablement. **Source:** outbound protection doc.
- **Can we use private network for inbound and storage firewalls for external ADLS?** Yes: Private Link for Fabric inbound + trusted workspace access or MPE for storage/outbound scenarios.

---

## F. Automation: rebuild from repo

### F1. What is publicly automatable today?
| Item / action | REST API public docs | `fab` evidence | `fabric-cicd` evidence | Notes |
|---|---|---|---|---|
| Workspace create | Yes | Yes | N/A | Requires SP admin setting |
| Lakehouse create/definition | Yes | Yes | Yes | `enableSchemas=true` supported |
| Notebook create/update definition | Yes | Yes | Yes | Public docs strong |
| DataPipeline definition | Yes | Yes | Yes | Public docs strong |
| Environment definition | Yes | Yes | Yes | Public docs strong |
| VariableLibrary definition | Yes | Yes | Yes | Public docs strong |
| Eventhouse definition | Yes | Yes | Yes | Public docs strong |
| Eventstream definition | Yes | Yes | Yes | Public docs strong |
| Run notebook job + poll | Yes | Yes (`fab` via item ops/api) | N/A | Use REST for deterministic docs |
| Data agent create/definition | **UNVERIFIED** | **UNVERIFIED** | **UNVERIFIED** | No official public item-definition doc found in this research |

### F2. Verified minimal REST script pattern
```powershell
# Verified endpoints from Learn; adapt IDs/names.
# Sources:
# https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace
# https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/create-lakehouse
# https://learn.microsoft.com/en-us/rest/api/fabric/notebook/background-jobs/run-on-demand-notebook

$token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }

# 1) Create workspace
$ws = Invoke-RestMethod -Method POST -Uri "https://api.fabric.microsoft.com/v1/workspaces" -Headers $headers -Body (@{
  displayName = "Fleet Demo WS"
  capacityId  = "<capacity-guid>"
} | ConvertTo-Json)

# 2) Create schema-enabled lakehouse
$lh = Invoke-RestMethod -Method POST -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($ws.id)/lakehouses" -Headers $headers -Body (@{
  displayName = "FleetDemo"
  creationPayload = @{ enableSchemas = $true }
} | ConvertTo-Json -Depth 5)

# 3) Upload notebook definition
# Use Items create/update definition APIs or fab import/export workflow. Exact body omitted here because the notebook payload is large,
# but the supported parts/paths are verified in Notebook definition docs.

# 4) Run notebook on demand
$runHeaders = $headers
$run = Invoke-WebRequest -Method POST -Uri "https://api.fabric.microsoft.com/v1/workspaces/$($ws.id)/notebooks/<notebook-guid>/jobs/execute/instances?beta=false" -Headers $runHeaders
$jobUrl = $run.Headers.Location
$retryAfter = [int]$run.Headers["Retry-After"]
Start-Sleep -Seconds $retryAfter
$status = Invoke-RestMethod -Method GET -Uri $jobUrl -Headers $headers
$status
```

### F3. Data upload options for repo -> Lakehouse Files
- **AzCopy:** officially documented and strong for bulk/large files; requires local tool/auth and `--trusted-microsoft-suffixes "fabric.microsoft.com"`. **Source:** https://learn.microsoft.com/en-us/fabric/onelake/onelake-azcopy
- **`fab`**: official Microsoft CLI exists and the official examples show `fab cp`, `fab export`, `fab import`, `fab create`, etc. **Source:** https://raw.githubusercontent.com/microsoft/fabric-cli/main/docs/examples/item_examples.md
- **Notebook download from raw GitHub URL:** operationally simple for small synthetic files; good for live demo; exact raw-URL code pattern is common Python, but not documented by Fabric docs, so treat the convenience wrapper as **UNVERIFIED** from a Fabric-doc perspective.
- **Pipeline Copy from HTTP:** good no-local-tool option; reliable if outbound web access is allowed.

### F4. Best recommendation
- **Best “rebuild everything” path:** use **REST + Git definitions** (or `fabric-cicd`) for items, and **AzCopy** or **pipeline HTTP copy** for files.
- **Best live-demo path for small synthetic files:** keep the files in the repo and ingest them from **pipeline HTTP** or a **notebook** rather than depending on local drag/drop.

---

## G. Getting synthetic demo files into the Lakehouse

| Method | Pros | Cons | Live demo verdict |
|---|---|---|---|
| UI upload | simplest to explain | manual, clicky, easiest to fat-finger | OK backup only |
| OneLake File Explorer | Windows-friendly | client dependency/sync behavior | Not my first choice live |
| `fab cp` | scriptable, official CLI | newer toolchain; team must preinstall/auth | Good for rehearsed automation |
| AzCopy | fastest + most robust for bulk | local tool/auth; command-line dependency | Best for bulk preload |
| Notebook download from raw GitHub | self-contained inside Fabric, no local client | depends on outbound web access to GitHub raw | **Best live-demo choice for small/medium synthetic files** |
| Pipeline Copy from HTTP | no local client, monitorable, repeatable | more setup than notebook | Best no-code live option |

Recommendation: for Friday’s live session, **pre-generate the files in repo and ingest via notebook or HTTP Copy activity**. Use **AzCopy** for rehearsal/bulk loading, not as the primary on-stage move.

---

## H. Notebook conventions to avoid live-demo failures
- Attach the **correct default lakehouse** before running Spark SQL; schema-enabled notebook behavior depends on it.
- Use **relative `Files/...`** only for the default lakehouse; use ABFSS for everything else.
- In schema-enabled lakehouses, always write `schema.table`, not bare table names.
- Set session-level configs deliberately; don’t assume V-Order defaults are read-optimized anymore.
- Prefer explicit schema on CSV/JSON log ingestion; don’t demo accidental inference drift unless you’re teaching drift.
- If you need additive evolution, set `mergeSchema=true`; if you need upsert + new columns, use `MERGE WITH SCHEMA EVOLUTION`.
- Refresh or manually force SQL endpoint sync before switching from Spark to SQL/semantic-model demos.
- For KQL -> OneLake demos, don’t promise immediate visibility unless you adjusted `TargetLatencyInMinutes` and verified latency.
- Treat timestamps/time zones explicitly (UTC end-to-end for logs/features).
- Keep notebook exits machine-readable (`notebookutils.notebook.exit('{\"status\":\"ok\"}')`) when orchestrated.

---

## Gotchas & limits
- **Lakehouse schemas via REST still ride a preview payload property** even though schemas are normal in the portal.
- **V-Order is no longer the default write posture in new workspaces.**
- **New SQL metadata sync is preview-only, new-endpoint-only, and incompatible with workspace private link.**
- **Eventhouse OneLake availability is not “instant lakehouse sync”; default batching can be hours.**
- **Private Link is inbound; it does not solve outbound-to-source security by itself.**
- **Trusted workspace access is GA but not supported on Trial capacities.**
- **Workspace outbound access protection** can block you from adding unsupported artifacts.
- **CMK doesn’t cover Spark temp/shuffle/cache data.**
- **Copilot/data-agent cross-boundary settings matter** for compliance, and data-agent use from non-Fabric services can leave Fabric’s compliance boundary.

---

## Questions a skeptical data engineer would ask — with factual answers

1. **“Can I rely on `Files/...` paths in every notebook?”**  
   Only for the default lakehouse in notebooks. For other lakehouses or Spark job definitions, use ABFSS.

2. **“Are schema-enabled lakehouses just cosmetic folders?”**  
   No. They change naming, enable schema-level organization/security behaviors, enable four-part names, and are required for MLVs.

3. **“Is MLV the replacement for PySpark medallion?”**  
   Not universally. It is strong for declarative SQL medallion pipelines, but not for ML inference/API logic; PySpark authoring is still preview/full-refresh-only.

4. **“Will SQL endpoint always see my Spark schema change immediately?”**  
   No. Background sync exists; manual refresh options are documented; the new faster sync is preview-only and has constraints.

5. **“Can Direct Lake sit directly on RTI/KQL data?”**  
   Yes, but for KQL DB/Eventhouse it depends on **OneLake availability** exposing Delta tables.

6. **“Is Eventhouse OneLake availability free of tradeoffs?”**  
   No. It forbids rename/type-change/RLS/delete-truncate-purge while enabled, and latency/file-shape tradeoffs are explicit.

7. **“Can I automate the whole environment with service principals?”**  
   Yes for public REST APIs, but only if the exact tenant settings for service principals are enabled and the SP has workspace/capacity rights.

8. **“Does Private Link solve storage-firewall access to ADLS?”**  
   Not alone. For that, use managed private endpoints or trusted workspace access depending on the scenario.

9. **“Is Trial capacity acceptable for enterprise rehearsal?”**  
   Fine for learning, not for several enterprise controls (for example trusted workspace access, CMK).

10. **“Can we keep AI/chat history forever inside region?”**  
    No by default. For Copilot in notebooks/data agents, history can persist up to 28 days unless users clear it; cross-region processing/storage settings are separate controls.

---

## Sources
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-schemas — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/create-lakehouse — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-explore — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-science/read-write-pandas — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/delta-lake-schema-evolution — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/sql-analytics-endpoint-metadata-sync — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-public-api — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/notebook/background-jobs/run-on-demand-notebook — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-source-control-deployment — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/lakehouse-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/environment-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/variable-library-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventhouse-definition — checked 2026-10-18
- https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/eventstream-definition — checked 2026-10-18
- https://raw.githubusercontent.com/microsoft/fabric-cli/main/docs/examples/item_examples.md — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/cicd/tutorial-fabric-cicd-azure-devops — checked 2026-10-18
- https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-deploy-fabric-cicd — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/eventhouse — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-house-onelake-availability — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/get-data-spark — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/real-time-intelligence/real-time-dashboards-overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-developer — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-copilot — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/admin/region-availability — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/enterprise/licenses — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/security-private-links-overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/security-managed-private-endpoints-overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/workspace-outbound-access-protection-overview — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/governance/microsoft-purview-fabric — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/fundamentals/apply-sensitivity-labels — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/admin/track-user-activities — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/workspace-customer-managed-keys — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/security/reliability-fabric — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-disaster-recovery — checked 2026-10-18
- https://learn.microsoft.com/en-us/fabric/onelake/onelake-azcopy — checked 2026-10-18
