# Demo 2a ETL facts for slides

## Data flow
- `nb_00_setup` creates the `bronze`, `silver`, `gold`, and `ml` schemas and fails fast if the 12 required raw files are not present.
- Raw files live under `Files/raw/` with five subtrees: `reference`, `erp`, `cmms`, `telematics`, and optional `telematics_drift`.
- `nb_01_bronze_ingest` lands six raw sources into bronze Delta tables with explicit schemas and `_source_file`, `_ingest_ts`, `_batch_id`.
- Telematics keeps the original mixed-format `ts` as a string in bronze; flattening happens without changing the source semantics.
- `nb_02_silver_clean_resolve` deduplicates telematics on `event_id`, nulls out-of-range spikes, converts timestamps to UTC, and resolves ERP asset identity in four tiers.
- Optional drift batch: when `Files/raw/telematics_drift/` exists, `nb_01` ingests it into `bronze.telematics_events_drift` and `nb_02` runs the exact same silver function on it into `silver.telemetry_drift` (same columns as `silver.telemetry`), feeding `nb_07_drift_monitor` in `ml-mlops`. A missing folder is not an error.
- `silver.work_orders` keeps all CMMS rows but flags duplicates and swapped timestamps; `gold.fact_work_order` drops duplicate corrective work orders.
- `nb_03_gold_reconcile` explodes fault codes into episodes, matches significant episodes to corrective work orders in `[-24 h, +7 d]`, and assigns `MATCHED` / `UNMATCHED` / `PENDING`.
- Gold outputs end with dimensional tables, daily telemetry, work orders, matches, exceptions, and a monthly reconciliation aggregate.

## Bronze, silver, gold tables
| Table | Grain | Expected rows |
|---|---|---:|
| `bronze.telematics_events` | one raw telematics event | 208,900 |
| `bronze.cmms_work_orders` | one raw CMMS work order | 2,359 |
| `bronze.erp_assets` | one ERP asset | 316 |
| `bronze.site_master` | one site | 12 |
| `bronze.fault_code_catalog` | one fault code | 20 |
| `bronze.asset_crosswalk` | one legacy crosswalk row | 9 |
| `bronze.telematics_events_drift` | one raw October telematics event (optional) | 15,367 |
| `silver.telemetry` | one in-window deduplicated telematics event | 207,691 |
| `silver.work_orders` | one CMMS work order with flags | 2,359 |
| `silver.telemetry_drift` | one October telematics event, same columns as `silver.telemetry` (optional) | 15,288 |
| `gold.dim_asset` | one ERP asset | 316 |
| `gold.dim_site` | one site | 12 |
| `gold.fact_telemetry_daily` | one asset-day | 51,353 |
| `gold.fact_fault_episode` | one asset x fault-code episode | 3,459 |
| `gold.fact_work_order` | one resolved non-duplicate work order | 2,345 |
| `gold.fact_recon_match` | one episode-to-work-order match candidate | 468 |
| `gold.fact_recon_exception` | one surfaced reconciliation exception | 211 |
| `gold.agg_recon_monthly` | one month x site aggregate | 72 |

## Notebook facts

### `nb_00_setup`
| Field | Fact |
|---|---|
| Purpose | Create lakehouse schemas and validate that the raw landing structure is ready before ingestion. |
| Audience sees | Schemas created, a printed list of landing options, and a fast pass/fail on raw files under `Files/raw`. |
| Key code lines | `nb_00_setup.py:78  LANDING_OPTIONS = [`<br>`nb_00_setup.py:82              "Upload fleet_data_generator.py into Files/workshop-src/, open a Python or PySpark notebook, "`<br>`nb_00_setup.py:83              "and run: !python /lakehouse/default/Files/workshop-src/fleet_data_generator.py "`<br>`nb_00_setup.py:84              "--out /lakehouse/default/Files/raw --with-drift"`<br>`nb_00_setup.py:106 for schema_name in ("bronze", "silver", "gold", "ml"):`<br>`nb_00_setup.py:107     spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")`<br>`nb_00_setup.py:115 expected_files = [`<br>`nb_00_setup.py:141     files_root = "Files/raw"`<br>`nb_00_setup.py:143         present_required = [rel for rel in expected_files if notebookutils.fs.exists(f"{files_root}/{rel}")]`<br>`nb_00_setup.py:150         raise RuntimeError(`<br>`nb_00_setup.py:178     "status": "ok" if not missing_required else "failed",`<br>`nb_00_setup.py:191     raise AssertionError(f"Missing required raw files: {missing_required}")` |
| Tables written | none |
| Aha outputs | 4 schemas created; 12 required files found; optional drift file present when rehearsal data includes October. |
| Fabric UI places worth showing | Lakehouse explorer → `Tables` with `bronze`, `silver`, `gold`, `ml` schemas; Lakehouse explorer → `Files/raw`; notebook parameter cell; notebook result pane. |
| Timing | 3-5 min live; 2 min on short path. |
| Most common failure | Default lakehouse not attached (or the session not restarted after attaching it), so `Files/raw` resolves to the wrong place or not at all. Right after an upload the file listing can also lag by about 2 minutes (the documented cache is 120 s; the exact symptom is ⚠ UNVERIFIED, see `VERIFY-BEFORE-FRIDAY.md`). |

### `nb_01_bronze_ingest`
| Field | Fact |
|---|---|
| Purpose | Load raw JSONL and CSV sources into bronze tables with explicit schemas and landing metadata, without fixing the data. |
| Audience sees | Six bronze tables appear in the Lakehouse; counts match the contract exactly; mixed telematics timestamps are preserved. |
| Key code lines | `nb_01_bronze_ingest.py:73 def write_table(df: DataFrame, full_name: str, save_mode: str = "overwrite") -> None:`<br>`nb_01_bronze_ingest.py:79         writer.saveAsTable(full_name)`<br>`nb_01_bronze_ingest.py:237     raw_text = spark.read.text(raw_path(glob_relative_path))`<br>`nb_01_bronze_ingest.py:238     parsed_str = F.from_json("value", telematics_schema_str)`<br>`nb_01_bronze_ingest.py:239     parsed_num = F.from_json("value", telematics_schema_num)`<br>`nb_01_bronze_ingest.py:247             F.coalesce(parsed_str["ts"], parsed_num["ts"].cast("long").cast("string")).alias("ts"),`<br>`nb_01_bronze_ingest.py:262             parsed_str["payload"]["coolant_level_pct"].alias("coolant_level_pct"),`<br>`nb_01_bronze_ingest.py:268 bronze_telematics = read_bronze_telematics("telematics/*.jsonl")`<br>`nb_01_bronze_ingest.py:271     spark.read.option("header", True).schema(cmms_schema).csv(raw_path("cmms/cmms_work_orders.csv"))`<br>`nb_01_bronze_ingest.py:311 expected_counts = {`<br>`nb_01_bronze_ingest.py:325 if mixed_ts_rows != bronze_counts["telematics_events"]:`<br>`nb_01_bronze_ingest.py:342 drift_present = (files_root / drift_folder_rel).exists()`<br>`nb_01_bronze_ingest.py:346     bronze_telematics_drift = read_bronze_telematics(drift_glob_rel)` |
| Tables written | `bronze.telematics_events` 208,900; `bronze.cmms_work_orders` 2,359; `bronze.erp_assets` 316; `bronze.site_master` 12; `bronze.fault_code_catalog` 20; `bronze.asset_crosswalk` 9; `bronze.telematics_events_drift` ~15,367 (optional, only when `Files/raw/telematics_drift/` exists). |
| Aha outputs | Bronze proves “land as-is”: 208,900 telematics rows with mixed `ts` formats and the evolved `coolant_level_pct` column preserved. |
| Fabric UI places worth showing | Lakehouse explorer → `bronze` schema; table preview for `bronze.telematics_events`; notebook run output; ⚠ UNVERIFIED exact label: notebook run details pane after completion. |
| Timing | 4-5 min live; 3 min on short path. |
| Most common failure | Bad relative path or missing raw month file under `Files/raw/telematics`, causing incomplete bronze counts. |

### `nb_02_silver_clean_resolve`
| Field | Fact |
|---|---|
| Purpose | Convert raw events and work orders into cleaned silver tables with UTC timestamps, deterministic identity resolution, and data-quality flags. |
| Audience sees | Deduped silver telemetry, flagged late rows, corrected CMMS timestamps, and the four-way identity resolution split with exact counts. |
| Key code lines | `nb_02_silver_clean_resolve.py:108 def apply_resolution(df: DataFrame, ref_col: str, serial_col: str, erp: DataFrame, crosswalk: DataFrame) -> DataFrame:`<br>`nb_02_silver_clean_resolve.py:123     digits = F.regexp_extract(F.coalesce(F.col(ref_col), F.lit("")), NORM_REGEX, 1)`<br>`nb_02_silver_clean_resolve.py:124     candidate = F.when(digits != "", F.format_string("EQ-%05d", digits.cast("int")))`<br>`nb_02_silver_clean_resolve.py:132         .join(erp_ids.withColumnRenamed("erp_asset_id", "_exact_erp_asset_id"), F.col("_candidate_exact_id") == F.col("_exact_erp_asset_id"), "left")`<br>`nb_02_silver_clean_resolve.py:164 def parse_ts_to_epoch(col_name: str) -> F.Column:`<br>`nb_02_silver_clean_resolve.py:166         F.col(col_name).rlike(r"^[0-9]+$"),`<br>`nb_02_silver_clean_resolve.py:167         F.col(col_name).cast("double") / F.lit(1000.0),`<br>`nb_02_silver_clean_resolve.py:171 def build_silver_telemetry(bronze_telematics: DataFrame, erp: DataFrame, crosswalk: DataFrame) -> tuple[DataFrame, int]:`<br>`nb_02_silver_clean_resolve.py:203         apply_resolution(telemetry, "asset_ref", "serial_no", erp, crosswalk)`<br>`nb_02_silver_clean_resolve.py:204         .withColumn("is_late", (F.col("ingest_epoch") - F.col("ts_epoch")) > F.lit(3600.0))`<br>`nb_02_silver_clean_resolve.py:233     .withColumn("opened_epoch", F.unix_timestamp(F.to_utc_timestamp(F.col("opened_local_ts"), F.col("timezone"))).cast("double"))`<br>`nb_02_silver_clean_resolve.py:236     .withColumn("is_time_anomaly", F.col("closed_epoch") < F.col("opened_epoch"))`<br>`nb_02_silver_clean_resolve.py:297 expected_resolution_telematics = {`<br>`nb_02_silver_clean_resolve.py:352     telemetry_drift, _ = build_silver_telemetry(bronze_telematics_drift, bronze_erp, bronze_crosswalk)` |
| Tables written | `silver.telemetry` 207,691 at event grain; `silver.work_orders` 2,359 at work-order grain. Resolution counts: telematics `EXACT_NORM` 196,810 / `SERIAL` 4,350 / `CROSSWALK` 2,180 / `UNRESOLVED` 4,351; CMMS `EXACT_NORM` 2,305 / `SERIAL` 28 / `CROSSWALK` 18 / `UNRESOLVED` 8. Optional: `silver.telemetry_drift` ~15,288 rows (same columns, built by the same `build_silver_telemetry` function), resolution ~`EXACT_NORM` 14,457 / `SERIAL` 333 / `CROSSWALK` 167 / `UNRESOLVED` 331 (cross-checked live against the pandas reference pipeline in `compare_ground_truth.py`, not a static ground-truth entry). |
| Aha outputs | 1,209 duplicates removed; 217 spike values nulled; 2,066 late rows retained and flagged; 8 swapped CMMS timestamps corrected. |
| Fabric UI places worth showing | Lakehouse explorer → `silver` schema; table preview for `silver.telemetry`; notebook output showing resolution counts; ⚠ UNVERIFIED exact label: schema filter in table preview. |
| Timing | 7-8 min live; 5 min on short path. |
| Most common failure | Site time zone conversion or regex normalization changed, which breaks the exact resolution counts immediately. |

### `nb_03_gold_reconcile`
| Field | Fact |
|---|---|
| Purpose | Build gold dimensions, daily telemetry, fault episodes, work-order matches, surfaced exceptions, and month/site reconciliation KPIs. |
| Audience sees | Business tables appear, episode-to-work-order matching becomes tangible, and the “money” finding surfaces: 91 significant episodes with no corrective work order. |
| Key code lines | `nb_03_gold_reconcile.py:268 cm_work_orders = fact_work_order.where(F.col("wo_type") == "CM")`<br>`nb_03_gold_reconcile.py:270     episodes.where(F.col("is_significant"))`<br>`nb_03_gold_reconcile.py:274         (F.col("opened_fix") >= (F.col("start") - F.lit(MATCH_BEFORE_SECONDS)))`<br>`nb_03_gold_reconcile.py:275         & (F.col("opened_fix") <= (F.col("end") + F.lit(MATCH_AFTER_SECONDS)))`<br>`nb_03_gold_reconcile.py:277     .withColumn("delta_hours", F.round((F.col("opened_fix") - F.col("start")) / F.lit(3600.0), 2))`<br>`nb_03_gold_reconcile.py:281 best_match_window = Window.partitionBy("episode_id").orderBy(F.abs(F.col("delta_hours")).asc(), F.col("wo_number").asc())`<br>`nb_03_gold_reconcile.py:299         "recon_status",`<br>`nb_03_gold_reconcile.py:302         .when(F.col("end") <= F.lit(CUTOFF_EPOCH - MATCH_AFTER_SECONDS), F.lit("UNMATCHED"))`<br>`nb_03_gold_reconcile.py:569 fact_recon_exception = (`<br>`nb_03_gold_reconcile.py:639 agg_recon_monthly = (`<br>`nb_03_gold_reconcile.py:656         "crit_match_rate",`<br>`nb_03_gold_reconcile.py:742 expected_gold_counts = {` |
| Tables written | `gold.dim_asset` 316; `gold.dim_site` 12; `gold.fact_telemetry_daily` 51,353; `gold.fact_fault_episode` 3,459; `gold.fact_work_order` 2,345; `gold.fact_recon_match` 468; `gold.fact_recon_exception` 211; `gold.agg_recon_monthly` 72. |
| Aha outputs | Severity split `CRIT` 399 / `WARN` 1,406 / `INFO` 1,654; significant episodes `MATCHED` 455 / `UNMATCHED` 91 / `PENDING` 11; CRIT `MATCHED` 367 / `UNMATCHED` 30 / `PENDING` 2; `crit_match_rate` 92.44%; median CRIT fault-to-work-order delay 5.58 h; exceptions: `FAULT_WITHOUT_WO` 91 and `WO_WITHOUT_FAULT` 79. |
| Fabric UI places worth showing | Lakehouse explorer → `gold` schema; table preview for `gold.fact_fault_episode`; table preview for `gold.fact_recon_exception`; notebook run output; Monitor hub ⚠ UNVERIFIED label; notebook run details ⚠ UNVERIFIED label. |
| Timing | 6-7 min live; 5 min on short path. |
| Most common failure | SQL endpoint or preview pane lag makes a just-written gold table look missing even though the Spark write succeeded. |

## Slide-ready totals
| Topic | Number |
|---|---:|
| Bronze telematics rows | 208,900 |
| Silver telematics rows | 207,691 |
| Duplicates removed | 1,209 |
| Out-of-range values nulled | 217 |
| Late rows kept and flagged | 2,066 |
| Significant episodes | 557 |
| Significant matched / unmatched / pending | 455 / 91 / 11 |
| CRIT matched / unmatched / pending | 367 / 30 / 2 |
| Match candidates | 468 |
| Exceptions | 211 |
| Assets with telemetry / active with telemetry | 284 / 274 |
