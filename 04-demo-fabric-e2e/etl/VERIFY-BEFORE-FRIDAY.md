# Verify before Friday

## D-5 to D-0 checklist
| Day | Check |
|---|---|
| D-5 | Create `ws-fleet-dev`, attach paid capacity or confirm trial, pin Runtime 1.3 (`rebuild-guide.md` section 3), create `lh_fleet`, confirm schemas enabled. If 1.3 cannot be selected, say so immediately: the whole chain then has to be rehearsed on Runtime 2.0. |
| D-5 | Rehearse the raw-data landing method you will actually use on stage, and note how long the files take to become visible to `nb_00_setup` (plan for about 2 minutes). |
| D-4 | Import the four notebooks, attach `lh_fleet` as the DEFAULT lakehouse of each one, restart the session, and run them once end to end. |
| D-4 | Create `pl_fleet_etl` in the UI and run it once. |
| D-4 | If rehearsing the optional October drift batch (feeds the Part 4 ML drift-monitor demo only, not required for the ETL audience path), confirm `bronze.telematics_events_drift` and `silver.telemetry_drift` appear after `nb_01`/`nb_02`. |
| D-3 | Validate exact counts against the contract from notebook output and table previews. |
| D-3 | Confirm the slide screenshots or code callouts match the latest files in this folder. |
| D-2 | Rehearse the 25-minute path and the 15-minute short path with the presenter. |
| D-1 | Warm the workspace with one notebook run; confirm raw files and gold tables still exist. |
| D-0 | Open the workspace early, verify the runtime (`print(spark.version)` is `3.5.x`) and the default lakehouse of each notebook, open the fallback pre-run outputs, and keep the aggregate tables ready in another tab. |

## UNVERIFIED or rehearsal-only items
| Item | What to verify | Exact page or setting |
|---|---|---|
| Local run is not a Fabric run | The 39/39 result comes from local Spark 3.5.6 + delta-spark 3.2.1 on Windows (not a Fabric tenant). It runs the local branches only: the Fabric branches (`notebookutils.fs.exists`, the Spark read of `_manifest.json`, `saveAsTable("schema.table")`, `notebookutils.notebook.exit`) never ran. Run all four notebooks once in the workspace and compare with the counts in `rebuild-guide.md` section 6 | Target workspace, after the Runtime pin and the default-lakehouse step |
| Runtime 1.3 still selectable (⚠ UNVERIFIED) | Microsoft Learn (read 2026-10-21) lists Runtime 1.3 as end-of-support-announced: support ends 2026-09-30, then Long Term Support from 2026-10-01 for six months (through March 2027). Confirm the dropdown still offers **1.3 (Spark 3.5, Delta 3.2)**, save, and check `print(spark.version)` shows `3.5.x`. If it is gone, use Runtime 2.0 (Spark 4.1) and rehearse the whole chain: the notebooks were never run on Spark 4.1 | Workspace settings → Data Engineering/Science → Spark settings → Environment tab (Learn: Runtime 1.3 page, lifecycle page) |
| Runtime menu labels | Confirm the exact labels of the runtime dropdown and of the default-environment option in today's UI; the guide uses the Learn wording | Same settings page |
| Default runtime of a new workspace | Learn says Runtime 2.0 becomes the default for new workspaces in late September 2026 (a plan). Check what a new `ws-fleet-dev` starts on before you pin | Fresh workspace, same settings page |
| Why a different runtime matters | A different Spark major version can change SQL, ANSI and cast behaviour. Local proxy (2026-10-21): with `spark.sql.ansi.enabled=true` (the Spark 4.0 default per the Apache migration guide) on Spark 3.5.6, the chain raised no error and wrote the same 18 tables. Not covered, still ⚠ UNVERIFIED: Spark 4.1, Delta 4.2, Java 21, Python 3.13, and whether Fabric Runtime 2.0 keeps the ANSI default. Only the pin to 1.3 is the safe choice | Rehearsal on Runtime 2.0 only if 1.3 is unavailable. If a cell fails there on a cast or a date / timestamp parse, try `spark.conf.set("spark.sql.ansi.enabled", "false")` in the first cell (Apache's documented switch back; ⚠ UNVERIFIED in Fabric) |
| Default lakehouse and session restart | After attaching `lh_fleet` as default and restarting the session, `nb_00_setup` creates the four schemas and `nb_01_bronze_ingest` writes `bronze.*`. Note the real error text when no default lakehouse is attached (the guide only says "path not found / table not found", ⚠ UNVERIFIED) | Notebook Explorer pane (**Add lakehouse**, pin icon) |
| File-listing delay after upload (about 2 minutes) | Learn documents a default 120-second file cache for the default lakehouse mount; that a fresh upload looks missing in `nb_00_setup` for that long is ⚠ UNVERIFIED. Upload, run `nb_00_setup` at once, and see whether the readable "Could not list Files/raw" message appears | Rehearsal lakehouse |
| `CREATE SCHEMA IF NOT EXISTS` in a schema-enabled lakehouse | Confirm `bronze`, `silver`, `gold`, `ml` appear under `Tables` after `nb_00_setup` (the local run proves the logic only) | Lakehouse explorer |
| F64 as the workshop capacity | A workshop-comfort recommendation, not a documented requirement (⚠ UNVERIFIED sizing) | Capacity assigned to `ws-fleet-dev` |
| F4 or F8 being “enough” for this ETL-only segment | Run all four notebooks once on the target capacity and time them | Capacity used in `ws-fleet-dev`; no Learn page gives a notebook-by-notebook sizing rule |
| Notebook UI import button label | Confirm the exact import action text in today’s Fabric notebook UI | Notebook creation/import UI in the target workspace |
| Notebook run details label used in slide narration | Confirm the exact right-pane or run-history label | Notebook UI after a run |
| Monitor hub label used in slide narration | Confirm the exact monitoring entry name in the current Fabric UI | Workspace navigation / monitoring entry in target workspace |
| Git import rebinding for `pl_fleet_etl` notebook references | The pipeline JSON now ships with each notebook's real logicalId (zero-GUID workspaceId) instead of dummy placeholders, so Git sync should auto-resolve; confirm this actually happens and that no activity shows "unresolved notebook" after import | `pl_fleet_etl.DataPipeline\pipeline-content.json` import into a rehearsal workspace |
| Fabric CLI raw-file workflow | Confirm whether the installed CLI path is worth teaching | Presenter workstation with installed `fab` CLI |

## Preview items
| Item | Status | Page |
|---|---|---|
| Lakehouse schema enablement via REST `creationPayload.enableSchemas` | ⚠ PREVIEW | `https://learn.microsoft.com/en-us/rest/api/fabric/lakehouse/items/create-lakehouse` |
| Optional session-tag optimization for pipelines running multiple notebooks | Depends on workspace high concurrency mode; rehearse before using | `https://learn.microsoft.com/en-us/fabric/data-factory/notebook-activity` |

## Settings to confirm
| Setting | Where |
|---|---|
| `Users can create Fabric items` | OneLake catalog → Govern → Configurations → Tenant settings |
| `Users can synchronize workspace items with their Git repositories` | OneLake catalog → Govern → Configurations → Tenant settings |
| `Users can synchronize workspace items with GitHub repositories` | Same location, GitHub only |
| Workspace high concurrency mode for pipelines running multiple notebooks | Workspace settings if you plan to use session tags |
| Default lakehouse on each notebook is `lh_fleet`, and the session was restarted after attaching it | Notebook UI, before every live run |
| Workspace runtime is 1.3 (Spark 3.5) | Workspace settings → Data Engineering/Science → Spark settings → Environment tab |
