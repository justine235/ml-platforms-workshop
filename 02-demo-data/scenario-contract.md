# Contoso Fleet — scenario contract

This document is the single source of truth for every demo in the workshop (MLflow tour, Fabric end-to-end,
Azure ML end-to-end, Foundry + data agent). All demos use the **same synthetic data** and must reproduce the
**same ground-truth numbers** (section 10). If a demo disagrees with this contract, the demo is wrong.

* Data generator: `fleet_data_generator.py` (deterministic, seed 20261023).
* Reference implementation of every transformation: `fleet_reference_pipeline.py` (plain pandas, ~30 s).
* Expected results: `reference_out/ground_truth.json` and `reference_out/agent_eval.jsonl`.
* All data is synthetic. "Contoso Fleet", the manufacturers and the sites are fictional.

---

## 1. The story

**Contoso Fleet** owns about 300 heavy machines (excavators, wheel loaders, bulldozers, dump trucks, mobile cranes,
compactors, pavers, generators) working on **12 construction sites in 8 European countries**.

Three systems describe the same machines and none of them agrees with the others:

| System | What it holds | Format | Time zone | Asset key |
|---|---|---|---|---|
| **Telematics** (IoT platform) | One reading every 6 h per machine: engine state, temperatures, pressures, vibration, fuel, fault codes | JSON lines, one event per line | UTC, local offset or epoch ms (mixed) | `asset_ref` written by the installer (6 different spellings) |
| **CMMS** (maintenance system) | Work orders: preventive (PM), inspection (INSP), corrective (CM) | CSV | Site-local wall clock, no zone | `asset_tag` (legacy tags, typos, serial numbers) |
| **ERP** (asset register) | The master list: class, model, serial number, cost, site, status | CSV | n/a | `erp_asset_id` = `EQ-NNNNN` (the golden key) |

Three business problems, one dataset:

1. **Reconcile** the three sources. Which machines exist in which system? Which critical faults were never followed by a
   work order? Which work orders have no fault behind them? Which retired machines still talk?
2. **Predict** which machine will need a corrective work order in the next 7 days (binary classification, ~5 % positives).
3. **Ask** questions in natural language on top of the reconciled data (Fabric data agent, called from a Foundry agent).

Observation window: **2026-04-01 → 2026-09-30** (183 days). The "present" for all demos is **2026-10-01 00:00 UTC**
(`cutoff_utc`). A drift batch for **2026-10-01 → 2026-10-14** is generated separately for the monitoring demo.

---

## 2. Reproduce the data

Requirements: Python ≥ 3.11, `numpy`, `pandas` ≥ 2.2, `scikit-learn` ≥ 1.6 (ML part only), `tzdata` (Windows only).

```bash
# 1) raw data (≈ 5 s, ≈ 95 MB; add --gzip to cut the telematics folder to ≈ 15 MB)
python fleet_data_generator.py --out data --truth-dir truth --with-drift

# 2) reference pipeline: silver -> gold -> features -> model -> ground truth (≈ 30 s)
python fleet_reference_pipeline.py --data data --out out --truth truth --with-drift
#    --skip-ml           : stop after the reconciliation tables (no scikit-learn needed)
#    --no-features-csv   : do not write the 13 MB feature table
```

Generator options: `--assets 300 --start 2026-04-01 --days 183 --seed 20261023 --with-drift --gzip --truth-dir DIR`.
Two runs with the same options produce **byte-identical files** (verified across numpy 2.1/2.5 and pandas 2.2/3.0).

`truth/` holds the *hidden* answer key (true asset behind every id, injected anomalies, true failure times).
**Never upload `truth/` to a lakehouse or hand it to the agent** — it is only used to grade the pipeline.

`reference_out/` (committed, ≈ 6 MB) holds the expected results of the canonical run
(`--with-drift`, seed 20261023): every gold table, the frozen risk scores, `drift_report.csv`,
`ground_truth.json` and `agent_eval.jsonl`. The two big tables are gzipped (`*.csv.gz`).

---

## 3. Raw sources (bronze)

Layout produced by the generator (identical under `Files/raw/` in a lakehouse or in a blob container):

```
data/
  _manifest.json                       parameters, counts of every injected problem, sha256 per file
  reference/site_master.csv            12 sites
  reference/fault_code_catalog.csv     20 fault codes
  reference/asset_crosswalk.csv        9 legacy-reference -> EQ-id mappings
  erp/erp_assets.csv                   316 rows
  cmms/cmms_work_orders.csv            2,359 rows
  telematics/telematics_2026-04.jsonl  ... one file per month, 6 files, 208,900 events in total
  telematics_drift/telematics_2026-10.jsonl   15,367 events (Oct 1-14, only with --with-drift)
```

### 3.1 Telematics event (JSON line)

```json
{"event_id":"eda5e643-2057-4202-879b-59c97c110a59","device_id":"TLM-107AFB","asset_ref":"EQ-07538",
 "ts":"2026-04-01T00:00:00Z","ingest_ts":"2026-04-01T00:02:18Z","firmware":"2.4.0",
 "payload":{"engine_state":"RUN","engine_hours":5099.8,"engine_temp_c":84.5,"oil_pressure_kpa":352.5,
            "hydraulic_pressure_bar":null,"vibration_mm_s":1.22,"fuel_rate_lph":11.1,"load_pct":45.1,
            "idle_pct":13.1,"fault_codes":[],"lat":43.30704,"lon":5.38115}}
```

| Field | Notes |
|---|---|
| `event_id` | UUID. **Not unique**: 1,209 events are delivered twice (keep the earliest `ingest_ts`). |
| `device_id` | `TLM-XXXXXX`, one per physical device (290 devices). |
| `asset_ref` | The asset as typed by the installer. Spellings: `EQ-00143`, `eq00143`, `EQ_00143`, `00143`, `EQ-143` (unpadded), ` EQ-00143 ` (blanks); also legacy `FLT-nnnn`, rental `RNT-nnnn`, typos — and **JSON `null` or `""`** (6 devices, which only send `serial_no`). |
| `serial_no` | Top-level field, present only on those 6 devices (ERP serial number such as `SN-IRO-19-313115`). |
| `ts` | Event time. Three styles: ISO UTC `Z` (≈ 81 %), ISO with local offset such as `+02:00` (≈ 13 %, DST aware), epoch **milliseconds** as a number (≈ 6 %). |
| `ingest_ts` | When the platform received the event (ISO UTC). 2,066 events arrive more than 1 h late. |
| `firmware` | `2.1.4`, `2.2.0`, `2.3.1`, `2.4.0`, `2.4.2`. |
| `payload.engine_state` | `RUN`, `IDLE` or `OFF`. OFF readings have null sensors. |
| `payload.*` | `engine_hours`, `engine_temp_c`, `oil_pressure_kpa`, `hydraulic_pressure_bar`, `vibration_mm_s`, `fuel_rate_lph`, `load_pct`, `idle_pct`, `fault_codes` (array of catalog codes), `lat`, `lon`. Not every class has every sensor (a generator has no hydraulics). |
| `payload.coolant_level_pct` | **Schema evolution**: appears only for firmware ≥ 2.4.0 and `ts` ≥ 2026-07-01. Not used by the ML model. |

Sampling is 4 readings per day (00, 06, 12, 18 UTC). Real telematics would be seconds apart; the demo compresses it.

### 3.2 CMMS work order (`cmms/cmms_work_orders.csv`)

`wo_number` (`WO-2026-NNNNNN`), `asset_tag`, `serial_number`, `site_code`, `wo_type` (`PM`/`CM`/`INSP`), `priority` (`P1`..`P4`),
`status` (`Closed`/`Open`), `failure_code`, `failure_system`, `description`, `opened_local`, `closed_local`
(both `YYYY-MM-DD HH:MM`, **site-local wall clock**, convert with the site time zone), `labor_hours`, `parts_cost_eur`,
`technician_id`, `reported_by`.

`asset_tag` spellings: `E05596` (≈ 48 %), `EQ05596` (≈ 28 %), `EQ 05596` (≈ 13 %), `EQ-05596` (≈ 9 %), or a legacy tag `LEG-nnnn` (54 work orders; 28 of them also carry
the ERP `serial_number`). `failure_code` / `failure_system` are filled for corrective (CM) work orders only; `reported_by` is filled for some of them.

### 3.3 ERP asset register (`erp/erp_assets.csv`)

`erp_asset_id` (`EQ-NNNNN`, unique key), `asset_name`, `equipment_class`, `manufacturer`, `model`,
`serial_number` (`SN-<MFR3>-<YY>-<6 digits>`), `acquisition_date`, `acquisition_cost_eur`, `site_code`, `cost_center`,
`status` (`Active` 300 / `Retired` 10 / `Disposed` 6), `retirement_date`, `telematics_device_installed` (`Y`/`N`).

Equipment classes (316 assets): Excavator 65, Generator 58, DumpTruck 44, Compactor 34, WheelLoader 32, MobileCrane 31, Bulldozer 26, Paver 26.

### 3.4 Reference tables

* `site_master.csv`: `site_code, site_name, country, timezone, utc_offset_standard_h, latitude, longitude, project_type`
  (FR-PAR-01 Paris, FR-LYS-01 Lyon, FR-MRS-01 Marseille, DE-MUC-01 Munich, DE-HAM-01 Hamburg, BE-ANR-01 Antwerp,
  GB-MAN-01 Manchester, GB-BHM-01 Birmingham, ES-MAD-01 Madrid, NL-RTM-01 Rotterdam, CH-ZRH-01 Zurich, PT-LIS-01 Lisbon).
* `fault_code_catalog.csv`: `fault_code, system, severity, description, recommended_action`.
  Systems: ENG, HYD, ELEC, COOL, TRN, UND, STR, GEN. Severity: `INFO`, `WARN`, `CRIT` (e.g. `P0218` engine over-temperature protection = CRIT, `H1210` hydraulic pressure loss = CRIT).
* `asset_crosswalk.csv`: `legacy_ref, erp_asset_id, source_system, note` (telematics `FLT-nnnn` fleet numbers and CMMS `LEG-nnnn` tags).

---

## 4. What is wrong with the data (injected on purpose)

Every number below is in `data/_manifest.json`. The hidden `truth/` files say which record carries which problem.

| # | Problem | Source | Count | How a correct pipeline handles it |
|---|---|---|---|---|
| 1 | Same asset written in many spellings | Telematics, CMMS | 275 devices fine after normalising; 6 by serial; 3 by crosswalk | Identity cascade (section 6.1) |
| 2 | Typos that match no asset (`EQ-09257`, `EQ-09536`) | Telematics | 2 devices | Cannot be resolved → exception `UNRESOLVED_ASSET_TELEMATICS` |
| 3 | Rental machines that are not in ERP (`RNT-nnnn`) | Telematics | 4 devices | Same exception |
| 4 | Unknown legacy tags | CMMS | 3 tags (8 work orders) | Exception `UNRESOLVED_ASSET_CMMS` |
| 5 | Duplicate events | Telematics | 1,209 | Deduplicate on `event_id`, keep earliest ingest |
| 6 | Late-arriving events | Telematics | 2,066 (> 1 h) | Keep, flag `is_late`; do not change event time |
| 7 | Mixed timestamp styles (Z / offset / epoch ms) | Telematics | 100 % | Convert everything to UTC |
| 8 | Local wall-clock times with DST | CMMS | 100 % | Convert with the site time zone |
| 9 | Sensor spikes (value 999) | Telematics | 217 | Out-of-range → null |
| 10 | Missing readings and null sensors | Telematics | 2,113 missing readings, 1,121 null values | Keep nulls, never impute silently |
| 11 | Duplicate corrective work orders (same asset + code within 60 min) | CMMS | 6 pairs | Keep the earliest, flag the other (`DUPLICATE_WO`) |
| 12 | Closed before opened (timestamps swapped) | CMMS | 8 | Swap back, flag `WO_TIME_ANOMALY` |
| 13 | Retired / disposed machines that still report | Telematics | 6 "zombie" assets | Exception `RETIRED_ASSET_REPORTING` |
| 14 | Active machines whose device went quiet or was never linked | Telematics | 10 stopped + 2 never linked | Exception `ACTIVE_ASSET_SILENT` |
| 15 | Real failures nobody wrote a work order for | CMMS | 43 of 495 failures | Appear as `FAULT_WITHOUT_WO` (the demo's "money" finding) |
| 16 | Work orders opened 3-6 days after the fault | CMMS | 24 | Still matched (7-day window) |
| 17 | Schema evolution (`coolant_level_pct`) | Telematics | from 2026-07-01 | Must not break ingestion (`mergeSchema`) |
| 18 | Distribution shift in Oct 1-14 | Drift batch | Excavator + WheelLoader | Detect with PSI (section 9) |

Population facts: 316 ERP assets (300 Active, 10 Retired, 6 Disposed), 290 devices (284 linked to an ERP asset after the cascade,
6 unresolvable), 24 active assets without a device, 2,359 work orders (PM 642, INSP 1,266, CM 451),
495 real failures on 226 assets (420 with a sensor precursor, 426 with a CRIT code at failure time).
---

## 5. Medallion design and naming (all demos use these names)

```
Files/raw/...                 bronze files exactly as generated          (Fabric: lakehouse Files, AML: data asset / blob)
bronze.*                      raw tables, one per file group, nothing fixed (add _source_file, _ingested_at)
silver.*                      cleaned + conformed + identity resolved
gold.*                        business tables used by BI, the data agent and the ML features
ml.*                          feature table, risk scores, drift report
```

| Layer | Delta table | Built from | Row count (canonical run) |
|---|---|---|---|
| bronze | `bronze.telematics_events` (payload flattened, `fault_codes` array, original `ts` as string) | `telematics/*.jsonl` | 208,900 |
| bronze | `bronze.cmms_work_orders`, `bronze.erp_assets`, `bronze.site_master`, `bronze.fault_code_catalog`, `bronze.asset_crosswalk` | CSV files | 2,359 / 316 / 12 / 20 / 9 |
| silver | `silver.telemetry` | bronze telematics | 207,691 |
| silver | `silver.work_orders` | bronze CMMS | 2,359 (flags, nothing dropped) |
| gold | `gold.dim_asset`, `gold.dim_site` | ERP + telemetry + site master | 316 / 12 |
| gold | `gold.fact_telemetry_daily` | silver telemetry | 51,353 |
| gold | `gold.fact_fault_episode` | silver telemetry + catalog | 3,459 |
| gold | `gold.fact_work_order` | silver work orders (resolved, non-duplicate) | 2,345 |
| gold | `gold.fact_recon_match` | episodes x corrective work orders | 468 |
| gold | `gold.fact_recon_exception` | all of the above | 211 |
| gold | `gold.agg_recon_monthly` | month x site summary | 72 |
| ml | `ml.asset_day_features` | daily + work orders + faults | 50,876 |
| ml | `ml.failure_risk_score` | model output (see section 8 "frozen scores") | 264 |
| ml | `ml.drift_report` | PSI per class x sensor | 47 |

The CSV files in `reference_out/` carry the same names as the gold/ml tables (without the schema prefix).
`fact_telemetry_daily` and `ml_asset_day_features` are shipped as `.csv.gz`.

Other shared names: lakehouse `lh_fleet` (schema enabled), MLflow experiment and registered model `fleet-failure-7d`,
metrics `valid_pr_auc`, `valid_roc_auc`, `test_pr_auc`, `test_roc_auc`, `test_precision_at_top5pct`, `test_recall_at_top5pct`,
data agent `da_fleet_recon`, Foundry agent `fleet-recon-agent`, AML endpoints `fleet-risk-online` / `fleet-risk-batch`.

---

## 6. Reconciliation rules (the business logic every implementation must follow)

Constants: `DAY = 86400 s`, episode gap 24 h, match window `[start − 24 h, end + 7 d]`, duplicate window 60 min, silent threshold 14 days,
cutoff `2026-10-01T00:00:00Z`.

### 6.1 Identity resolution — first hit wins

Applied to telematics (`asset_ref`, `serial_no`) and to CMMS (`asset_tag`, `serial_number`). The result is stored as
`erp_asset_id` + `resolution_method`.

1. **EXACT_NORM** — normalise the reference with the regex `^\s*(?:EQ|E)?[\s_\-]*0*(\d{1,5})\s*$` (case-insensitive) and format it as
   `EQ-%05d`. Accept it **only if that id exists in ERP** (`EQ-09257` normalises fine but does not exist, so it falls through).
2. **SERIAL** — normalise the serial (upper case, keep `[A-Z0-9]`) and look it up in the ERP serial numbers.
3. **CROSSWALK** — upper-case and strip the reference, look it up in `asset_crosswalk.legacy_ref`.
4. **UNRESOLVED** — keep the row, `erp_asset_id` is null, raise an exception (6.8).

Expected counts (events / work orders): telematics EXACT_NORM 196,810, SERIAL 4,350, CROSSWALK 2,180, UNRESOLVED 4,351;
CMMS EXACT_NORM 2,305, SERIAL 28, CROSSWALK 18, UNRESOLVED 8.

### 6.2 Time

* Telematics `ts`: ISO with `Z` or offset → UTC; a JSON number → epoch **milliseconds** → UTC. `ingest_ts` is ISO UTC.
* CMMS `opened_local` / `closed_local`: parse as wall-clock in the **site's** time zone (`site_master.timezone`, DST aware) → UTC.
* If `closed < opened` the two stamps were swapped: swap them back and flag `is_time_anomaly` (8 work orders).
* `is_in_window` = event time < cutoff. The drift batch is **never** part of the base tables.

### 6.3 Silver telemetry

1. Drop duplicate `event_id`s, keeping the earliest `ingest_ts` (1,209 removed → 207,691 rows).
2. Null out-of-range sensor values (217): `engine_temp_c` 0-150, `oil_pressure_kpa` 0-800, `hydraulic_pressure_bar` 0-450,
   `vibration_mm_s` 0-30, `fuel_rate_lph` 0-200, `load_pct` 0-100, `idle_pct` 0-100.
3. Resolve the asset (6.1). Flag `is_late` = `ingest − event > 3600 s`.

### 6.4 Silver work orders

Convert times (6.2), resolve the asset (6.1). **Duplicate**: among corrective (`CM`) work orders with a resolved asset, sort by
(asset, `failure_code`, opened time, `wo_number`); a work order opened ≤ 60 min after the previous one with the same asset and failure code
is a duplicate of it (`is_duplicate`, `duplicate_of` = the earlier `wo_number`). Nothing is deleted in silver.
`gold.fact_work_order` keeps resolved, non-duplicate work orders only (2,359 − 6 − 8 = 2,345) and uses the **ERP site** of the asset.

### 6.5 Fault episodes (`gold.fact_fault_episode`)

Explode `fault_codes` of every resolved, in-window telemetry record. An **episode** is a run of records with the same asset + fault code in which
consecutive records are ≤ 24 h apart (a larger gap starts a new episode). `episode_id` = `EP-nnnnnn`, numbered after sorting by
(start, asset, code). `severity` and `system` come from the catalog.
`is_significant` = `CRIT`, or `WARN` with `n_records ≥ 3`. `INFO` and short WARN episodes are never reconciled.

### 6.6 Matching (`gold.fact_recon_match`)

An episode matches every **corrective** work order of the same asset opened in `[episode.start − 24 h, episode.end + 7 d]`.
`delta_hours` = WO opened − episode start (negative = the WO came first). `same_system` = episode system equals `failure_system`.
`is_best_for_episode` marks the match with the smallest `|delta_hours|` (ties: lowest `wo_number`).

### 6.7 Reconciliation status (on episodes)

`NOT_APPLICABLE` (not significant) · `MATCHED` (has a match) · `UNMATCHED` (no match and `end ≤ cutoff − 7 d`, i.e. the window is closed) ·
`PENDING` (no match yet but the window is still open). `matched_wo_number` = the best match.

### 6.8 Exceptions (`gold.fact_recon_exception`, 211 rows)

`exception_id` = `EXC-nnnnn` after sorting by type order (the order of the table below), `event_epoch`, `reference_id`.

| Type | Subtype | Severity | `reference_id` | `n_records` | Rule | Count |
|---|---|---|---|---|---|---|
| `UNRESOLVED_ASSET_TELEMATICS` | – | MEDIUM | device id | events | device whose `asset_ref`/serial resolve to nothing | 6 |
| `UNRESOLVED_ASSET_CMMS` | – | MEDIUM | asset tag | work orders | CMMS tag that resolves to nothing | 3 (8 WOs) |
| `RETIRED_ASSET_REPORTING` | – | MEDIUM | asset id | events after retirement | ERP `Retired`/`Disposed` but telemetry on/after `retirement_date` | 6 |
| `ACTIVE_ASSET_SILENT` | `NO_LINKED_TELEMETRY` | MEDIUM | asset id | 0 | Active, device installed = `Y`, no telemetry resolves to it | 2 |
| `ACTIVE_ASSET_SILENT` | `STOPPED_REPORTING` | MEDIUM | asset id | 0 | Active, device installed, last telemetry > 14 days before cutoff | 10 |
| `FAULT_WITHOUT_WO` | `CRIT` / `WARN` | HIGH / MEDIUM | episode id | records | significant, closed, `UNMATCHED` episode | 91 (30 CRIT, 61 WARN) |
| `WO_WITHOUT_FAULT` | `NO_FAULT_SIGNAL` | LOW | wo number | 1 | CM work order matched by no episode; the asset has telemetry | 40 |
| `WO_WITHOUT_FAULT` | `NO_TELEMETRY` | LOW | wo number | 1 | … and the asset never had telemetry | 37 |
| `WO_WITHOUT_FAULT` | `TELEMETRY_STOPPED` | LOW | wo number | 1 | … and telemetry stopped > 1 day before the WO | 2 |
| `WO_TIME_ANOMALY` | – | LOW | wo number | 1 | closed before opened in CMMS | 8 |
| `DUPLICATE_WO` | – | LOW | wo number | 1 | duplicate corrective WO (6.4) | 6 |

Total 211. `event_utc` is the first event time (empty for `NO_LINKED_TELEMETRY`). `detail` is a human readable sentence.

### 6.9 Daily and monthly aggregates

* `fact_telemetry_daily`: one row per asset-day with resolved, in-window telemetry. `n_readings`, `n_run`, `engine_hours` (max of the day).
  Sensor aggregates (`*_mean`, `*_min`, `*_max`) use **RUN readings only**; `run_share = n_run / n_readings`.
  `is_after_retirement` marks days on/after the ERP retirement date (477 rows); they stay in the fact table but are excluded from ML.
* `agg_recon_monthly`: one row per month x site (72 rows). `crit_match_rate = crit_matched / (crit_matched + crit_unmatched)` (PENDING excluded).
  `cm_repair_hours` = sum of work-order duration (hours) of corrective work orders opened in the month.

---

## 7. Gold and ml table schemas

| Table | Columns |
|---|---|
| `gold.dim_asset` | `erp_asset_id` PK, `asset_name`, `equipment_class`, `equipment_class_code` (1-8), `manufacturer`, `model`, `serial_number`, `acquisition_date`, `acquisition_cost_eur`, `site_code`, `cost_center`, `status`, `retirement_date`, `telematics_device_installed`, `device_id`, `has_telemetry` (bool), `telemetry_rows`, `first_telemetry_utc`, `last_telemetry_utc`, `last_engine_hours`, `asset_age_years` |
| `gold.dim_site` | `site_code` PK, `site_name`, `country`, `timezone`, `latitude`, `longitude`, `project_type` |
| `gold.fact_telemetry_daily` | `erp_asset_id`, `site_code`, `obs_date`, `n_readings`, `n_run`, `engine_hours`, `temp_mean`, `temp_max`, `oil_mean`, `oil_min`, `hyd_mean`, `hyd_min`, `vib_mean`, `vib_max`, `fuel_mean`, `load_mean`, `idle_mean`, `run_share`, `is_after_retirement` |
| `gold.fact_fault_episode` | `episode_id` PK, `erp_asset_id`, `site_code`, `fault_code`, `system`, `severity`, `start_utc`, `end_utc`, `n_records`, `is_significant`, `recon_status`, `matched_wo_number`, `month` (`YYYY-MM` of the start) |
| `gold.fact_work_order` | `wo_number` PK, `erp_asset_id`, `site_code`, `wo_type`, `priority`, `status`, `failure_code`, `failure_system`, `description`, `opened_utc`, `closed_utc`, `duration_hours`, `labor_hours`, `parts_cost_eur`, `technician_id`, `reported_by`, `id_resolution`, `times_corrected` (bool) |
| `gold.fact_recon_match` | `episode_id`, `wo_number`, `erp_asset_id`, `delta_hours`, `same_system`, `is_best_for_episode` |
| `gold.fact_recon_exception` | `exception_id` PK, `exception_type`, `subtype`, `severity`, `erp_asset_id`, `site_code`, `reference_id`, `event_utc`, `n_records`, `detail` |
| `gold.agg_recon_monthly` | `month`, `site_code`, `crit_episodes`, `crit_matched`, `crit_unmatched`, `crit_pending`, `crit_match_rate`, `warn_episodes_3plus`, `warn_matched`, `warn_unmatched`, `cm_work_orders`, `cm_wo_with_fault_signal`, `cm_wo_without_fault_signal`, `avg_crit_fault_to_wo_hours`, `cm_repair_hours` |
| `ml.asset_day_features` | `erp_asset_id`, `obs_date`, 42 features (section 8), `fail_next_7d` (0/1, null when unknown), `split` |
| `ml.failure_risk_score` | `score_date`, `erp_asset_id`, `site_code`, `equipment_class`, `risk_score`, `risk_band` (`High` ≥ 0.30, `Medium` ≥ 0.10, else `Low`), `risk_rank`, `top_drivers` (`;`-joined reason codes), `model_version` |
| `ml.drift_report` | `equipment_class`, `sensor`, `psi`, `ref_mean`, `new_mean`, `ref_rows`, `new_rows`, `status` (`stable` / `moderate` / `major`) |

Note on semantics: **gold tables are rebuilt from scratch on every run** (idempotent, deterministic). The ids `EP-nnnnnn` and `EXC-nnnnn`
are stable only for the same input data; a production design would use hashed business keys.
---

## 8. ML specification (identical on laptop, Fabric and Azure ML)

**Task**: for every asset-day with telemetry, predict `fail_next_7d` = 1 if a (non-duplicate, resolved) **corrective work order is opened
in the next 7 calendar days (UTC days d+1 … d+7)**. Labelled rows: 49,028, positive rate 5.47 %.
Labels are valid up to 2026-09-23 (the last day with a complete 7-day look-ahead before the cutoff).

**Label noise (a teaching point, not a bug)**: 43 real failures never produced a work order, 24 work orders were opened 3-6 days late,
work orders can be opened without any fault. A model can only learn what the CMMS records.

**Features (42)** — calendar-window features computed from data known at the **end** of `obs_date`; windows are calendar days (missing days stay NaN, OFF days carry no sensor value):

| Group | Columns |
|---|---|
| Daily base (14) | `temp_mean temp_max oil_mean oil_min hyd_mean hyd_min vib_mean vib_max fuel_mean load_mean idle_mean n_readings run_share engine_hours` |
| Fault counts (5) | `warn_cnt_1d crit_cnt_1d warn_cnt_7d crit_cnt_7d warn_cnt_14d` (WARN/CRIT fault occurrences, not episodes) |
| Rolling means (12) | `{temp,oil,hyd,vib}_mean_{3d,7d,14d}` (NaN-aware, `min_periods=1`) |
| Trends (4) | `{temp,oil,hyd,vib}_trend` = 3-day mean − 14-day mean |
| Rolling max (2) | `temp_max_7d vib_max_7d` |
| Maintenance (3) | `days_since_last_pm days_since_last_cm cm_count_90d` (from resolved, non-duplicate work orders) |
| Static (2) | `equipment_class_code asset_age_years` |

**Purged time-based splits** (column `split`; **use it, do not re-split**): a 7-day gap removes label overlap between sets.

| `split` | Dates | Rows | Positives |
|---|---|---|---|
| `warmup` | 04-01 … 04-14 | 3,976 | 196 (not used for training: rolling windows still filling) |
| `train` | 04-15 … 07-24 | 28,520 | 1,639 |
| `gap` | 07-25 … 07-31 and 08-25 … 08-31 | 3,830 | 219 (purged) |
| `valid` | 08-01 … 08-24 | 6,591 | 353 |
| `test` | 09-01 … 09-23 | 6,111 | 274 |
| `unlabeled` | 09-24 … 09-29 | 1,584 | – (label window crosses the cutoff) |
| `score` | 09-30 | 264 | – (the assets scored for the demo) |

**Models and expected metrics** (HistGradientBoosting `max_iter=300, learning_rate=0.06, max_leaf_nodes=24, l2_regularization=1.0, early_stopping=False, random_state=0`;
logistic regression = median imputer + standard scaler + `C=0.5`):

| Model | valid PR-AUC | test PR-AUC | test ROC-AUC |
|---|---|---|---|
| Prevalence (dummy) | 0.054 | 0.045 | 0.50 |
| Rule baseline (`crit_cnt_7d > 0` or `warn_cnt_7d ≥ 2`) | 0.064 | 0.068 | 0.58 |
| Logistic regression | 0.292 | 0.292 | 0.74 |
| **HistGradientBoosting** | 0.336 | **0.385** | 0.75 |
| HGB without fault-code features (ablation) | 0.323 | 0.284 | 0.72 |

Metrics are **approximate across library versions**: logistic regression and the baselines are identical on scikit-learn 1.6 and 1.9, gradient boosting moves by up to
≈ ±0.02 PR-AUC. Quote ranges, not decimals.
Lift at top 5 % of asset-days ≈ 8x the 4.5 % prevalence. This is a realistic, modest signal: the point of the workshop is the platform and the process,
not a miracle model.

**Teaching points built into the data**: (a) ~6-8x lift only — a model can be useful at 0.38 PR-AUC; (b) label noise caps the ceiling;
(c) time-based splits with a purge gap versus random splits (a random split inflates PR-AUC); (d) CRIT codes arrive with or after the failure,
so the "obvious" rule baseline is weak; (e) the ablation shows how much the fault-code features carry.

**Frozen scores rule.** `reference_out/ml_failure_risk_score.csv` (scores on 2026-09-30, final model refit on all labelled days, 264 assets:
High 9, Medium 7, Low 248) is **frozen**. Risk bands depend on library versions (the pandas 2.2 / scikit-learn 1.6 run gives different bands).
For Part 4, **load the frozen CSV into `ml.failure_risk_score`** instead of re-scoring, so the agent answers match `agent_eval.jsonl` (questions Q21-Q25).
Parts 1-3 train and score live; their numbers are expected to be close, not identical.

**Reason codes** (`top_drivers`, up to 3, `;`-joined, rule based — **not** model attributions, say so out loud):
`CRIT_FAULT_7D` (`crit_cnt_7d ≥ 1`), `REPEATED_WARNINGS` (`warn_cnt_7d ≥ 3`), `ENGINE_TEMP_RISING` (`temp_trend ≥ 3`),
`OIL_PRESSURE_FALLING` (`oil_trend ≤ −10`), `HYDRAULIC_PRESSURE_FALLING` (`hyd_trend ≤ −8`), `VIBRATION_RISING` (`vib_trend ≥ 0.3`),
`PM_OVERDUE` (`days_since_last_pm ≥ 90`), otherwise `NO_STRONG_SIGNAL`.

Top 5 frozen scores on 2026-09-30: EQ-02893 (0.95, Excavator, ES-MAD-01), EQ-07040 (0.88, Generator, NL-RTM-01), EQ-01714 (0.88, FR-PAR-01),
EQ-01503 (0.87, FR-PAR-01), EQ-02054 (0.85, WheelLoader, FR-PAR-01).

---

## 9. Drift scenario (monitoring demo)

* Reference window: September 2026 RUN readings. New batch: `telematics_drift/` (2026-10-01 … 2026-10-14, 15,367 events), pushed through the same silver logic.
* Statistic: **PSI** (population stability index) on 10 reference deciles, per equipment class x sensor (47 combinations, RUN readings).
  `< 0.10` stable, `0.10 - 0.25` moderate, `> 0.25` major.
* Injected shift (a firmware/calibration change): **Excavator and WheelLoader**, `vibration_mm_s` × 1.35 and `engine_temp_c` +4 °C.

| Class | Sensor | PSI | Status |
|---|---|---|---|
| Excavator | `engine_temp_c` | 0.88 | major |
| Excavator | `vibration_mm_s` | 3.71 | major |
| WheelLoader | `engine_temp_c` | 0.96 | major |
| WheelLoader | `vibration_mm_s` | 2.78 | major |
| Paver / Compactor / MobileCrane | `engine_temp_c` | 0.19 / 0.11 / 0.10 | moderate — **seasonal ambient cooling, expected** (good discussion point: not every alert is a defect) |

40 of 47 combinations are stable. Labels for October do not exist yet (the 7-day look-ahead and the work-order delay), so monitoring must rely on
**input drift and prediction drift**, not on accuracy. Expected action: alert → investigate → retrain/recalibrate → champion/challenger gate.

---

## 10. Ground truth and acceptance checks

`reference_out/ground_truth.json` is machine readable. A demo is correct when it reproduces these numbers **exactly** (all counts are
deterministic and identical on pandas 2.2 and 3.0; only ML numbers are approximate):

| Check | Expected |
|---|---|
| Bronze rows: telematics / CMMS / ERP | 208,900 / 2,359 / 316 |
| Silver telemetry rows (after 1,209 duplicates removed; 217 spikes nulled) | 207,691 |
| Resolution (telematics events): EXACT_NORM / SERIAL / CROSSWALK / UNRESOLVED | 196,810 / 4,350 / 2,180 / 4,351 |
| `gold.fact_telemetry_daily` / `fact_fault_episode` / `fact_work_order` | 51,353 / 3,459 / 2,345 |
| Fault episodes by severity: CRIT / WARN / INFO | 399 / 1,406 / 1,654 |
| Significant episodes: MATCHED / UNMATCHED / PENDING | 455 / 91 / 11 (total 557) |
| CRIT episodes: MATCHED / UNMATCHED / PENDING | 367 / 30 / 2 |
| CRIT match rate (matched / (matched + unmatched)) | 92.44 % |
| Median CRIT fault → work order delay | 5.58 h |
| `fact_recon_match` rows / `fact_recon_exception` rows | 468 / 211 |
| Exceptions by type | ACTIVE_ASSET_SILENT 12, DUPLICATE_WO 6, FAULT_WITHOUT_WO 91, RETIRED_ASSET_REPORTING 6, UNRESOLVED_ASSET_CMMS 3, UNRESOLVED_ASSET_TELEMATICS 6, WO_TIME_ANOMALY 8, WO_WITHOUT_FAULT 79 |
| Corrective work orders / matched to an episode | 445 / 366 |
| Assets with telemetry / Active with telemetry | 284 / 274 |
| `ml.asset_day_features` rows; labelled; positive rate | 50,876; 49,028; 5.47 % |
| HGB test PR-AUC / ROC-AUC | ≈ 0.385 / ≈ 0.75 (± 0.02) |
| Frozen risk bands High / Medium / Low | 9 / 7 / 248 |
| Drift: major combinations | 4 (Excavator and WheelLoader x temp and vibration) |

The pipeline's own self-check compares its results with the hidden truth: telematics and CMMS identity resolution 100 % correct, CMMS local-to-UTC
conversion correct, duplicates and time anomalies found exactly. Only one number is informational: of 36 real, truly unreported failures with a CRIT code,
the reconciliation surfaces 28 (recall 0.78) and 28 of the 30 unmatched CRIT episodes are explained by a real unreported failure (precision 0.93).
This is the honest answer to "does the reconciliation find real problems?".

---

## 11. Agent evaluation set (`reference_out/agent_eval.jsonl`, 30 questions)

One JSON object per line: `id`, `type` (`count`, `list`, `agg`, `lookup`, `detail`, `multi-hop`, `unanswerable`, `out_of_scope`, `guardrail`),
`difficulty` (`easy`/`medium`/`hard`), `question`, `expected_answer` (natural language), `expected_values` (machine checkable; `tolerance_*` keys give
the accepted rounding), `tables` (the gold tables needed), `depends_on_frozen_scores` (true for Q21-Q25).

* Q01-Q20: reconciliation questions answered from gold tables (counts per exception type, duplicates, retired-but-reporting assets, unresolved devices and tags,
  match rate by month/site, delay, parts cost, repair hours, one "why is this asset flagged" drill-down).
* Q21-Q25: risk questions — **require the frozen `ml.failure_risk_score`** (bands, High-risk list, share by class, multi-hop with work orders and exceptions).
* Q26-Q30: **traps** the agent must not answer: fuel cost, operator, safety incidents (data does not exist → say so), a forecast for a future date (out of scope),
  and a request to delete data (the agent is read-only → refuse).
  For these, `expected_values = {"answerable": false}`; the correct behaviour is a clear refusal with an explanation, not a guess.

Every expected answer is computed from the gold tables by code, never typed by hand.

---

## 12. Platform assumptions shared by the demos

* Everything is built on **synthetic data you can regenerate in 40 seconds**. Nothing in this repository needs customer data.
* Region for demos: **West Europe**, **France Central** or **Sweden Central** (EU data residency; Foundry/data-agent availability to be re-checked by the presenter).
* Fabric: a **paid F-SKU (F2 or higher)** is required for the data agent (the Trial capacity has no data agent); F64 is comfortable for the whole day.
* Azure ML: compute is CPU only (`Standard_DS3_v2` class). Estimated demo-day cost is a few USD to ~10 USD (unverified; check the pricing page).
* Python in the demos must run on **Fabric Runtime 2.0 (Python 3.13, scikit-learn 1.6, mlflow-skinny 2.22)** and **Fabric Runtime 1.3 (Spark 3.5)** where Spark is used;
  Azure ML environments pin **MLflow ≤ 2.16.2** with `azureml-mlflow`.

## 13. Honest limitations (say them before the audience does)

* The data is synthetic: patterns are plausible, not real. Four readings per day instead of a continuous stream.
* The signal is modest by design (PR-AUC ≈ 0.3-0.4) and the labels are noisy.
* Reason codes are rules, not SHAP values.
* The reconciliation uses rules and a deterministic match window — it is not probabilistic entity resolution.
* Nothing here was executed in a live Fabric / Azure ML / Foundry tenant by the author; the pandas reference pipeline is the only executed code.
  **Rehearse every demo in your own tenant before the workshop.**
