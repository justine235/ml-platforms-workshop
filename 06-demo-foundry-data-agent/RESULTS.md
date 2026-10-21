# Validation results - 2026-10-21

Re-run on 2026-10-21; replaces the 2026-10-19 results. The notebooks are Spark-only now, so the old "notebook local mode" row (a DuckDB run) is replaced by a real local Spark + Delta run of both notebooks.

## Commands executed

| Check | Command | Result |
| --- | --- | --- |
| Python compile | `python -m py_compile` over all 20 `.py` files under this folder | **PASS** |
| Ruff | `ruff check .` | **PASS** |
| Pytest | `pytest tests -q` | **PASS - 14 passed** (includes the notebook drift guard) |
| Example-query validator | `python data-agent\validate_examples.py` | **PASS - 30 of 30** |
| Eval harness - oracle | `python foundry-agent\eval_harness.py --agent oracle` | **PASS - 30/30, pass rate 1.0** |
| Eval harness - naive | `python foundry-agent\eval_harness.py --agent naive` | **EXPECTED FAIL PROFILE - 0/30, pass rate 0.0** |
| JSON / JSONL / YAML parse | Python parse sweep across this folder | **PASS** (3 JSON files; this folder holds no JSONL or YAML) |
| Notebook validation | `nbformat.validate` for both `.ipynb` files | **PASS - 2 of 2** |
| Notebook run | `nb_10` then `nb_11`, unchanged, in one local Spark + Delta session | **PASS** (details below) |

## Notebook run: `nb_10` then `nb_11` on a local Spark + Delta session

**What ran.** The percent-Python sources of both notebooks, unchanged (the `.ipynb` files are generated from them and a test fails if they drift), in that order, in one fresh Python process and one fresh Spark session. Spark read the CSV files of `02-demo-data\reference_out` from a staged `Files\reference_out` folder (no `truth\` folder) and wrote each table with `saveAsTable`. A small harness outside this kit drove the run.

**Environment.** Windows, Python 3.11.9, PySpark 3.5.6, delta-spark 3.2.1, pandas 2.2.3, Java 17, `local[2]`, in-memory catalog, local file system. This is close to Fabric Runtime 1.3 (Spark 3.5, Delta 3.2, Python 3.11), not identical.

**Results** (`nb_10` took 120 s, `nb_11` took 15 s):

- 11 of 11 tables loaded and every row count equals the contract: `gold.dim_asset` 316, `gold.dim_site` 12, `gold.fact_telemetry_daily` 51,353, `gold.fact_fault_episode` 3,459, `gold.fact_work_order` 2,345, `gold.fact_recon_match` 468, `gold.fact_recon_exception` 211, `gold.agg_recon_monthly` 72, `ml.asset_day_features` 50,876, `ml.failure_risk_score` 264, `ml.drift_report` 47.
- Column level, outside the notebooks: for all 172 columns of the 11 tables the Delta table equals the reference CSV on the null count and on the sum (numbers), the true-count (booleans), the min / max (dates, timestamps) or the distinct count (text). Column names and order equal the CSV header, and every table is a managed Delta table.
- `nb_10` prints the `ml.failure_risk_score` risk bands on 2026-09-30: High 9 / Medium 7 / Low 248 (264 rows).
- `nb_11` prints, and its last cell asserts, the scorecard: significant episodes MATCHED / UNMATCHED / PENDING = 455 / 91 / 11 (557) and CRIT episodes 367 / 30 / 2 (399). 326 of the 367 matched CRIT episodes got their work order within 24 hours and 17 took more than 72 hours.
- Exceptions by type (211): ACTIVE_ASSET_SILENT 12, DUPLICATE_WO 6, FAULT_WITHOUT_WO 91, RETIRED_ASSET_REPORTING 6, UNRESOLVED_ASSET_CMMS 3, UNRESOLVED_ASSET_TELEMATICS 6, WO_TIME_ANOMALY 8, WO_WITHOUT_FAULT 79. The EQ-00619 drill-down returns its ACTIVE_ASSET_SILENT row ("no telemetry for 43 days").
- The precision / recall panel of `nb_11` (0.933 / 0.778) is a literal from the frozen ground truth, guarded by a drift test. It is displayed, not recomputed from the loaded tables.

**Defect found and fixed.** An earlier run of this check loaded all 11 tables with the right row counts, but the column-level comparison showed that `ml.asset_day_features.warn_cnt_7d`, `crit_cnt_7d` and `warn_cnt_14d` were NULL in all 50,876 rows. The CSV stores them as decimals ("2.0"), the notebook declared them INT, and Spark's CSV reader turns values it cannot parse under the declared type into NULL without an error. The three columns are DOUBLE now in `nb_10`, in `b4_fleet_demo\reference_data.py` and in `fabric-setup\schema-descriptions.md`. Two drift tests keep it that way: every CSV value must parse under its declared type, and the `schema-descriptions.md` types must equal the table specs.

**Not covered** (each unverified item is listed in `VERIFY-BEFORE-FRIDAY.md`, item 8):

- A Fabric tenant or the Fabric Spark runtime. Runtime 2.0 (Spark 4.1, Delta 4.2, Python 3.13) was not tried (**UNVERIFIED**).
- The default-lakehouse binding: the run emulated it with the working directory (the relative `Files/reference_out` path) and a local warehouse. `CREATE SCHEMA` and `saveAsTable("schema.table")` on a schema-enabled lakehouse are **UNVERIFIED**.
- The file-listing delay after an upload and the SQL analytics endpoint sync delay (both **UNVERIFIED**).
- `saveAsTable` overwrite onto tables that already exist in a lakehouse: every local run started from an empty warehouse.
- The write route. With delta-spark 3.2.1 on Spark 3.5.6, Spark's default write route failed every table write ("does not support truncate in batch mode"), so the harness makes Spark use its V1 write route for Delta (`spark.sql.sources.useV1SourceList`). The notebooks do not set it. Whether the Fabric runtime needs it is **UNVERIFIED**.

## SDK / documentation re-check

- Learn pages re-fetched on **2026-10-19** for Fabric data-agent prerequisites, limits, tenant settings, MCP behavior, Fabric IQ preview status, legacy-tool deprecation, Foundry prompt-agent/Responses patterns, and the two retirement dates.
- Learn "Apache Spark runtime in Fabric" re-read on **2026-10-21**: Runtime 1.3 is in the end-of-support-announced stage (Spark 3.5.5, Delta 3.2, Python 3.11, Java 11); Runtime 2.0 is GA (Spark 4.1, Delta 4.2, Python 3.13, Java 21).
- PyPI versions rechecked on **2026-10-19**:
  - `azure-ai-projects` **2.9.0**
  - `openai` **3.35.1**
  - `fabric-data-agent-sdk` **0.1.33a0**

## Notes

- The first validation sweep revealed that the requested top-level `tests\` entry point was missing even though `foundry-agent\tests\` already existed. A small top-level `tests\` bundle was added so `pytest tests -q` now works as requested.
- Anything still not settled by Learn is explicitly marked `UNVERIFIED` in the relevant docs and mirrored in `VERIFY-BEFORE-FRIDAY.md`.
