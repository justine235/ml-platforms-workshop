# Demo 2a ETL run of show

## Checkpoints
| Checkpoint | What must exist |
|---|---|
| CP1 | `Files/raw` tree present with 12 required files |
| CP2 | `bronze.*` tables loaded and counts validated |
| CP3 | `silver.telemetry` and `silver.work_orders` written with exact quality counts |
| CP4 | `gold.dim_*`, `gold.fact_*`, `gold.agg_recon_monthly` written |
| CP5 | Gold exception and match counts shown from notebook output or table preview |

## Pre-flight (before the audience arrives, ideally the day before)
1. Runtime: the workspace is pinned to Fabric Runtime 1.3 (Spark 3.5, Python 3.11) and `print(spark.version)` shows `3.5.x`. Runtime 2.0 (Spark 4.1) was not rehearsed with these notebooks (`rebuild-guide.md` section 3).
2. Default lakehouse: in each of the four notebooks `lh_fleet` is attached as the DEFAULT lakehouse (pin icon) and the session was restarted after attaching it. Imports and Git syncs do not carry that binding into a new workspace.
3. Raw files: `Files/raw` was uploaded at least 2 minutes before `nb_00_setup` runs (file-listing cache, ⚠ UNVERIFIED duration). If `nb_00_setup` stops with "Could not list Files/raw in the attached lakehouse", wait a minute and re-run the cell.
4. Warm session: start one notebook session early, and run the whole chain once the day before so the outputs can serve as the fallback.

## 25-minute live path
| Min | Screen / click path | What to say | Checkpoint | Fallback if live step fails |
|---:|---|---|---|---|
| 0:00-1:30 | Lakehouse `lh_fleet` → `Files/raw` | “This ETL starts from files already landed in OneLake. I will not hide the raw data shape: JSONL for telematics, CSV for CMMS and ERP.” | CP1 | Open `Files/raw` and `_manifest.json` from the preloaded rehearsal lakehouse. |
| 1:30-3:30 | Open `nb_00_setup` → show parameter cell → Run | “Setup only does two things: create the medallion schemas and fail fast if raw landing is incomplete. The notebook is safe to rerun.” | CP1 | Open the saved output of `nb_00_setup` in the results pane. |
| 3:30-5:00 | Lakehouse explorer → `Tables` | “The presenter-friendly detail is schema-enabled lakehouse naming: bronze, silver, gold, ml. That keeps the whole path visible in one item.” | CP1 | Expand the already-created schemas. |
| 5:00-7:30 | Open `nb_01_bronze_ingest` → Run | “Bronze is intentionally boring. We flatten the payload enough to query it, but we do not fix duplicates, typos, or timestamps here.” | CP2 | Open `bronze.telematics_events` preview and the pre-run notebook output. |
| 7:30-10:00 | Lakehouse explorer → `bronze` → preview `bronze.telematics_events` | “The raw event time is still a string because the source mixes `Z`, offsets, and epoch milliseconds. Bronze preserves that reality.” | CP2 | Show the existing table preview and the 208,900 row count in notebook output. |
| 10:00-13:30 | Open `nb_02_silver_clean_resolve` → Run | “Silver is where the real engineering starts: dedupe, UTC conversion, identity resolution, and quality flags. We keep late rows; we do not erase operational problems. The optional October batch goes through the same silver function, into its own table.” | CP3 | Open saved notebook output with the resolution counts. |
| 13:30-16:00 | Notebook output for `nb_02_silver_clean_resolve` | “The four-tier identity cascade is deterministic: normalize the ERP id, then serial number, then crosswalk, else unresolved. These counts are the acceptance test.” | CP3 | Open `silver.telemetry` preview and point to `resolution_method`, `is_late`, `erp_asset_id`. |
| 16:00-18:30 | Open `nb_03_gold_reconcile` → Run | “Gold translates telemetry and work orders into business tables. The core rule is simple: match significant fault episodes to corrective work orders from 24 hours before to 7 days after.” | CP4 | Open pre-run notebook output from `nb_03_gold_reconcile`. |
| 18:30-21:30 | Lakehouse explorer → preview `gold.fact_fault_episode` and `gold.fact_recon_match` | “This is where the medallion becomes useful. We can show fault episodes, best matches, and the exact delay in hours.” | CP4 | Open `gold.fact_fault_episode` and filter on `recon_status`. |
| 21:30-23:30 | Preview `gold.fact_recon_exception` | “The business finding is not ‘we built a table’. It is ‘we surfaced 91 significant episodes without a corrective work order, including 30 CRIT episodes’.” | CP5 | Open `gold.fact_recon_exception` and the notebook output line with 211 exceptions. |
| 23:30-25:00 | Preview `gold.agg_recon_monthly` or notebook output | “At the end we have both detail facts and a month-by-site KPI table. That becomes the bridge to ML features and then to the agent demo.” | CP5 | Open `gold.agg_recon_monthly` from the rehearsal lakehouse. |

## 15-minute short path
| Min | Screen / click path | What to say | Checkpoint | Fallback |
|---:|---|---|---|---|
| 0:00-2:00 | `Files/raw` + `nb_00_setup` already open | “The raw landing is ready and schema-enabled lakehouse naming is already in place.” | CP1 | Use the rehearsal output only. |
| 2:00-5:00 | `nb_01_bronze_ingest` output + `bronze.telematics_events` preview | “Bronze lands 208,900 telematics rows and keeps the mixed timestamps intact.” | CP2 | Show output only. |
| 5:00-9:00 | `nb_02_silver_clean_resolve` output | “Silver removes 1,209 duplicates, nulls 217 spikes, keeps 2,066 late rows, and resolves identities in four tiers.” | CP3 | Show `silver.telemetry` preview if output pane is slow. |
| 9:00-13:00 | `nb_03_gold_reconcile` output + `gold.fact_recon_exception` preview | “Gold turns telemetry into 3,459 fault episodes and surfaces 211 exceptions, including 91 significant faults without a work order.” | CP5 | Use pre-run notebook output screenshot-free, directly in Fabric. |
| 13:00-15:00 | `gold.agg_recon_monthly` | “This closes the ETL story and hands clean daily facts to the ML notebooks.” | CP5 | Open the aggregate table from the rehearsal run. |
