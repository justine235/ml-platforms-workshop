# Rebuild guide

## 1. Scope
1. Rebuild only the ETL half of the Fabric end-to-end demo in this folder.
2. Create one workspace: `ws-fleet-dev`.
3. Create one schema-enabled lakehouse: `lh_fleet`.
4. Import four notebooks: `nb_00_setup`, `nb_01_bronze_ingest`, `nb_02_silver_clean_resolve`, `nb_03_gold_reconcile`.
5. Run them in order, then optionally add the `pl_fleet_etl` pipeline.

## 2. Capacity and prerequisites
1. Required Fabric capability from Learn:
   - Fabric capacity or Fabric trial for notebooks and pipelines.
   - Trial is 60 days and includes notebooks and pipelines, but not Copilot, Fabric data agent, AI functions, AI services, or Trusted Workspace Access.
   - Paid Fabric starts at F2.
2. Practical sizing for this ETL-only demo:
   - F2 paid capacity is the lowest documented paid entry point.
   - F4 or F8 is likely enough for these four small sequential notebooks. ⚠ UNVERIFIED sizing recommendation; rehearse on the target tenant.
   - F64 is comfortable for the whole workshop day because free viewers and other Fabric parts often use that threshold; this is a workshop-comfort recommendation, not an ETL requirement and not a documented minimum. ⚠ UNVERIFIED sizing.
3. Region:
   - Prefer West Europe, France Central, Germany West Central, or Sweden Central.
   - All four regions show all Fabric workloads on the current Learn region-availability page.
4. Tenant and workspace prerequisites:
   - `Users can create Fabric items`
   - If using Git integration: `Users can synchronize workspace items with their Git repositories` and, for GitHub, `Users can synchronize workspace items with GitHub repositories`
5. Presenter workstation prerequisites:
   - Browser access to Fabric.
   - This folder available locally.
   - Optional: OneLake File Explorer or AzCopy for bulk file upload.
6. Two settings that are easy to forget and break the first run:
   - Check which Spark runtime the workspace uses before any notebook runs: keep the default (Runtime 2.0) and know the fallback (Runtime 1.3, LTS) in case a notebook fails in Fabric (section 3, step 2).
   - Attach `lh_fleet` as the DEFAULT lakehouse of every notebook and restart its session (section 5).

## 3. Create the workspace, check the runtime, create the lakehouse
1. In Fabric, create workspace `ws-fleet-dev` on the chosen capacity.
2. Check the Spark runtime now, before you create or import any notebook:
   - Keep the workspace default. Microsoft Learn (runtime lifecycle page, updated 2026-09-18, checked 2026-10-21) lists Runtime 2.0 (Spark 4.1, Delta 4.2, Java 21, Python 3.13) as generally available and as the recommended runtime, and says it is the default for new workspaces (announced for late September 2026), so a new `ws-fleet-dev` should start on 2.0. There is nothing to pin; confirm it with the check below.
   - Local evidence, not a Fabric run: the four notebooks passed 39/39 metrics against the ground truth on local Spark 4.1.1 + Delta 4.2.0 (Java 17, Python 3.13, ANSI on, which is the Spark 4 default) and on local Spark 3.5.6 + Delta 3.2.1, and wrote identical tables on both; Java 21 (the Runtime 2.0 JDK) also ran the four notebooks on Spark 4.1.1 (`run_local.py` exit 0, no mismatches, the same tables; the ground-truth compare was not re-run on Java 21) (`RESULTS.md`, "Round 5, follow-up T5"; exact pins in `local-validation\requirements-spark4.txt` and `requirements-spark35.txt`). What no local run shows: that Fabric Runtime 2.0 behaves like that stack, including whether it keeps Apache Spark 4's ANSI-on default, and every Fabric-only code path (⚠ UNVERIFIED until the rehearsal).
   - Fallback: Runtime 1.3 (Spark 3.5, Delta 3.2) is in the end-of-support-announced (EOSA) stage. Its end of support is 2026-09-30, followed by a six-month Long Term Support (LTS) period from 2026-10-01 through March 2027 (Microsoft Learn, lifecycle page). Switch to it only if a notebook fails in Fabric on 2.0 (for example on a cast or a date / timestamp parse): set the workspace to 1.3, restart the session and re-run.
   - Where to switch (Microsoft Learn, Runtime 1.3 page, read 2026-10-21): **Workspace settings** → **Data Engineering/Science** → **Spark settings** → **Environment** tab → open the **Runtime Versions** dropdown → select **1.3 (Spark 3.5, Delta 3.2)** → save. This sets 1.3 as the default runtime of the workspace. Learn adds that the runtime dropdown is offered when the option to have a default environment is turned off; with a default Environment set, the runtime comes from that Environment.
   - Alternative, per notebook: create an **Environment** item, pick runtime 1.3 in its **Runtime** dropdown, **Save**, **Publish**, then select that Environment in each notebook. Learn describes this flow on the Runtime 2.0 page; the exact label of the 1.3 entry there is ⚠ UNVERIFIED.
   - Check: run `print(spark.version)` in any notebook. Expect `4.1.x` on the default (Runtime 2.0) or `3.5.x` on Runtime 1.3.
   - ⚠ UNVERIFIED that Runtime 1.3 can still be selected in the target tenant on the day: it is the fallback, so check it on Thursday (`VERIFY-BEFORE-FRIDAY.md`). If a notebook fails on 2.0 with an ANSI error and 1.3 is gone, try `spark.conf.set("spark.sql.ansi.enabled", "false")` in the first cell (Apache's documented switch back; ⚠ UNVERIFIED in Fabric).
3. In the workspace, create a lakehouse named `lh_fleet`.
4. Keep **Lakehouse schemas** checked when creating the lakehouse. Microsoft Learn (lakehouse schemas page, read 2026-10-21): schemas are on by default for a lakehouse created in the portal, a lakehouse created through the REST API must enable them explicitly, and to use schemas in notebook code the notebook's default lakehouse must be schema-enabled (or there must be no default lakehouse).
5. You do not have to create the schemas by hand: `nb_00_setup` runs `CREATE SCHEMA IF NOT EXISTS` for `bronze`, `silver`, `gold`, and `ml` (a no-op when a schema already exists, so creating them under `Tables` first is harmless). The local run proves this logic only; that Fabric accepts the statement in a schema-enabled lakehouse is ⚠ UNVERIFIED until the rehearsal. If `nb_00_setup` fails there, create the four schemas by hand under `Tables` and re-run it.
6. The default `dbo` schema also exists; it cannot be removed.
7. `lh_fleet` must be the default lakehouse of every notebook (section 5).

## 4. Get the raw data into `lh_fleet\Files\raw`
### Main path: generate inside Fabric from `nb_00_setup` guidance
1. Upload `02-demo-data\fleet_data_generator.py` (from the workshop folder) to `lh_fleet` → `Files` → create folder `workshop-src` → upload the file there.
2. Create folder `Files/raw`.
3. Open a Fabric notebook that has `lh_fleet` attached as its default lakehouse (section 5); the `/lakehouse/default/...` paths below point at that default lakehouse.
4. Run this exact command in a cell:

```python
!python /lakehouse/default/Files/workshop-src/fleet_data_generator.py --out /lakehouse/default/Files/raw --with-drift
```

5. Expected result:
   - `_manifest.json`
   - `reference/site_master.csv`
   - `reference/fault_code_catalog.csv`
   - `reference/asset_crosswalk.csv`
   - `erp/erp_assets.csv`
   - `cmms/cmms_work_orders.csv`
   - `telematics/telematics_2026-04.jsonl` through `telematics_2026-09.jsonl`
   - `telematics_drift/telematics_2026-10.jsonl`

### Option B: Lakehouse upload UI
1. Generate the files locally: `cd 02-demo-data` then
   `python fleet_data_generator.py --out data --truth-dir truth --with-drift`.
   The ETL local-validation scripts (`local-validation\run_local.py` and
   `compare_ground_truth.py`) default to `02-demo-data\data` and
   `02-demo-data\truth` next to this kit; set the environment variables
   `FLEET_RAW_ROOT` and `FLEET_TRUTH_ROOT` to point elsewhere if you generated
   the data in a different folder.
2. In `lh_fleet`, go to `Files`.
3. Create folder `raw`.
4. Upload `_manifest.json` and the folders `reference`, `erp`, `cmms`, `telematics`, and `telematics_drift`.

### Option C: OneLake File Explorer
1. Install OneLake File Explorer on Windows if it is not already installed.
2. Let the workspace and lakehouse sync into Windows File Explorer.
3. Copy the locally generated `raw` subtree into `lh_fleet\Files\raw`.
4. If the new files do not appear in Fabric, right-click the lakehouse folder in File Explorer and select **OneLake** → **Sync from OneLake**.

### Option D: AzCopy
1. Create the lakehouse first; AzCopy cannot create Fabric items for you.
2. Authenticate with AzCopy.
3. Use `--trusted-microsoft-suffixes "fabric.microsoft.com"`.
4. Copy into `https://onelake.dfs.fabric.microsoft.com/<workspace-name>/<item-name>/Files/raw/...`.
5. Use this for preloading, not as the primary live-demo move.

### Option E: Fabric CLI
1. ⚠ UNVERIFIED exact item/file copy recipe for this workshop path; official `fab` examples confirm import/export and copy capabilities, but this specific raw-folder workflow was not rehearsed here.
2. Use only if the presenter already knows the installed CLI flow.

### Before you run `nb_00_setup`: wait about 2 minutes
1. After the files are uploaded (any option above), wait about 2 minutes before you run `nb_00_setup`.
2. Why: Microsoft Learn (NotebookUtils file system utilities, read 2026-10-21) documents a default file cache timeout of 120 seconds for the default lakehouse file paths mounted in a notebook. That a freshly uploaded file can look missing for that long in this demo is ⚠ UNVERIFIED; the 2-minute wait is the cautious reading.
3. `nb_00_setup` checks `Files/raw` with `notebookutils.fs` and reads `_manifest.json` through Spark, not through the `/lakehouse/default` mount. If the listing fails it stops with a readable message ("Could not list Files/raw in the attached lakehouse ..."). Wait a minute and re-run the cell.

## 5. Import the notebooks
### Default lakehouse (every notebook, every time)
1. Notebooks imported from `.ipynb` or synced from Git carry no binding to a lakehouse of the new workspace (the shipped notebooks have an empty `dependencies` block in their metadata, because the lakehouse only exists once you create it).
2. In each notebook, open the lakehouse list in the Explorer pane, select **Add lakehouse**, add the existing `lh_fleet`, and make it the default lakehouse (the pin icon marks the default; Learn: to switch the default, move the pin icon).
3. Stop the notebook session and start it again, then run.
4. Why it matters: relative `Files/...` and `Tables/...` paths resolve against the default lakehouse, and the default lakehouse decides which metastore Spark SQL uses. That is where `spark.sql("CREATE SCHEMA ...")` and `saveAsTable("bronze.<table>")` act.
5. Symptom when it is missing: a "path not found" or "table or schema not found" error in `nb_00_setup` or `nb_01_bronze_ingest`. ⚠ UNVERIFIED exact message.
### Path A: UI import of `.ipynb`
1. In `ws-fleet-dev`, create or open a notebook.
2. Use the notebook import action to import each file from `etl\notebooks\`:
   - `nb_00_setup.ipynb`
   - `nb_01_bronze_ingest.ipynb`
   - `nb_02_silver_clean_resolve.ipynb`
   - `nb_03_gold_reconcile.ipynb`
3. After each import, attach `lh_fleet` as the default lakehouse and restart the session (see "Default lakehouse" above).
4. Verify the parameter cell is still tagged as a parameter cell.
5. ⚠ UNVERIFIED exact current button label for the import action; confirm in the target Fabric UI during rehearsal.

### Path B: Git integration with the Fabric Git folders
1. Connect `ws-fleet-dev` to a Git repository and branch.
2. Copy these folders into the repo root that Fabric syncs:
   - `nb_00_setup.Notebook`
   - `nb_01_bronze_ingest.Notebook`
   - `nb_02_silver_clean_resolve.Notebook`
   - `nb_03_gold_reconcile.Notebook`
   - optional `pl_fleet_etl.DataPipeline`
3. Sync from Git into the workspace.
4. Verify the four notebook items appear in the workspace.
5. Open each notebook once, attach `lh_fleet` as the default lakehouse and restart the session. A Git sync does not bind a lakehouse of the new workspace (see "Default lakehouse" above).
6. The notebook Git shape is `<name>.Notebook\.platform` plus `notebook-content.py`.

## 6. Run order and expected results
1. `nb_00_setup`
   - Goal: create schemas and validate the raw landing.
   - Expected: status ok; 12 required files found; optional drift file present.
2. `nb_01_bronze_ingest`
   - Goal: land raw data into bronze tables.
   - Expected rows:
     - `bronze.telematics_events` 208,900
     - `bronze.telematics_events_drift` 15,367 (optional, only when the drift folder is present)
     - `bronze.cmms_work_orders` 2,359
     - `bronze.erp_assets` 316
     - `bronze.site_master` 12
     - `bronze.fault_code_catalog` 20
     - `bronze.asset_crosswalk` 9
3. `nb_02_silver_clean_resolve`
   - Goal: dedupe, normalize time, resolve identity, flag quality issues.
   - Expected:
     - `silver.telemetry` 207,691
     - `silver.work_orders` 2,359
     - late rows 2,066
     - duplicate work orders 6
     - time anomalies 8
     - telematics resolution `196,810 / 4,350 / 2,180 / 4,351`
     - drift (optional): `silver.telemetry_drift` 15,288, resolution `14,457 / 333 / 167 / 331`
4. `nb_03_gold_reconcile`
   - Goal: create dimensional, fact, exception, and monthly summary tables.
   - Expected:
     - `gold.dim_asset` 316
     - `gold.dim_site` 12
     - `gold.fact_telemetry_daily` 51,353
     - `gold.fact_fault_episode` 3,459
     - `gold.fact_work_order` 2,345
     - `gold.fact_recon_match` 468
     - `gold.fact_recon_exception` 211
     - `gold.agg_recon_monthly` 72
     - significant episodes `455 matched / 91 unmatched / 11 pending`
     - CRIT match rate `92.44%`
     - median CRIT delay `5.58 h`

## 7. Build the pipeline in the Fabric UI
1. In the workspace, create a new pipeline named `pl_fleet_etl`.
2. Add four **Notebook** activities to the canvas.
3. Configure them in this order:
   - `RunSetup` → notebook `nb_00_setup`
   - `RunBronzeIngest` → notebook `nb_01_bronze_ingest`
   - `RunSilverCleanResolve` → notebook `nb_02_silver_clean_resolve`
   - `RunGoldReconcile` → notebook `nb_03_gold_reconcile`
4. For each activity, open **Settings** and set base parameters:
   - `batch_id = fleet-demo-live`
   - `data_cutoff_utc = 2026-10-01T00:00:00Z`
   - `mode = full`
5. Add success dependencies:
   - `RunSetup` → `RunBronzeIngest`
   - `RunBronzeIngest` → `RunSilverCleanResolve`
   - `RunSilverCleanResolve` → `RunGoldReconcile`
6. Save the pipeline and run it once.
7. Monitor from the output pane below the canvas; after the run, also check run history. The docs call out notebook activity output there.
8. Optional: if rehearse-time is tight, configure a session tag only after verifying that workspace high concurrency mode for pipelines running multiple notebooks is enabled.

## 8. Use the provided Fabric Git pipeline item
1. The folder `etl\fabric-git\pl_fleet_etl.DataPipeline\` contains:
   - `.platform`
   - `pipeline-content.json`
2. The JSON shape is aligned with the Learn DataPipeline definition:
   - activity type `TridentNotebook`
   - `dependsOn`
   - `typeProperties.notebookId`
   - `typeProperties.workspaceId`
   - `typeProperties.parameters`
3. The notebook IDs in `pipeline-content.json` are the real `logicalId` values from each notebook's own `.platform` file (auto-generated by `tools\build_notebooks.py` from a neutral `contoso-fleet-workshop/<name>` seed), and `workspaceId` is the all-zero GUID `00000000-0000-0000-0000-000000000000`, which Fabric resolves to the importing workspace at Git sync time. If an activity still shows an unresolved notebook after import, open the activity and re-pick the notebook once; this is a one-time binding, not a sign that the JSON is wrong.

## 9. Live-demo checkpoints
1. CP1: `Files/raw` visible.
2. CP2: bronze counts validated.
3. CP3: silver resolution counts validated.
4. CP4: gold tables written.
5. CP5: exception and match counts visible.

## 10. Break-glass fallback
1. Keep a rehearsal workspace with all notebooks already run once.
2. If a live run stalls:
   - open the pre-run notebook output,
   - open the corresponding table preview in the Lakehouse,
   - continue the story from the materialized result.
