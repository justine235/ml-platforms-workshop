# Schema descriptions

These table and column notes are the source text for the Fabric data-agent schema descriptions.

## gold.dim_asset

Master asset dimension after ERP, telemetry, and site enrichment.

| Column | Type | Business meaning |
| --- | --- | --- |
| `erp_asset_id` | `STRING` | Golden asset identifier EQ-NNNNN. |
| `asset_name` | `STRING` | Human-readable asset name from ERP. |
| `equipment_class` | `STRING` | Equipment family such as Excavator or Generator. |
| `equipment_class_code` | `INT` | Stable numeric class code used by ML features. |
| `manufacturer` | `STRING` | Synthetic manufacturer name. |
| `model` | `STRING` | Synthetic model name. |
| `serial_number` | `STRING` | ERP serial number. |
| `acquisition_date` | `DATE` | ERP acquisition date. |
| `acquisition_cost_eur` | `DOUBLE` | Acquisition cost in EUR. |
| `site_code` | `STRING` | ERP site code. |
| `cost_center` | `STRING` | ERP cost center. |
| `status` | `STRING` | Asset lifecycle status Active, Retired, or Disposed. |
| `retirement_date` | `DATE` | Retirement date when present. |
| `telematics_device_installed` | `STRING` | Y or N flag from ERP. |
| `device_id` | `STRING` | Resolved telematics device id when present. |
| `has_telemetry` | `BOOLEAN` | Whether any telemetry resolved to the asset. |
| `telemetry_rows` | `INT` | Count of telemetry rows tied to the asset. |
| `first_telemetry_utc` | `TIMESTAMP` | First resolved telemetry timestamp in UTC. |
| `last_telemetry_utc` | `TIMESTAMP` | Last resolved telemetry timestamp in UTC. |
| `last_engine_hours` | `DOUBLE` | Latest reported engine-hour value. |
| `asset_age_years` | `DOUBLE` | Age of the asset at the cutoff date. |

## gold.dim_site

Site reference dimension for timezone-aware operations and geography.

| Column | Type | Business meaning |
| --- | --- | --- |
| `site_code` | `STRING` | Stable site identifier. |
| `site_name` | `STRING` | Friendly site name. |
| `country` | `STRING` | Country name. |
| `timezone` | `STRING` | IANA timezone identifier. |
| `latitude` | `DOUBLE` | Site latitude. |
| `longitude` | `DOUBLE` | Site longitude. |
| `project_type` | `STRING` | Synthetic construction project type. |

## gold.fact_telemetry_daily

Daily telemetry aggregates per asset and UTC observation day.

| Column | Type | Business meaning |
| --- | --- | --- |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `site_code` | `STRING` | ERP site for the asset. |
| `obs_date` | `DATE` | UTC observation date. |
| `n_readings` | `INT` | Number of resolved telemetry readings that day. |
| `n_run` | `INT` | Number of RUN-state readings. |
| `engine_hours` | `DOUBLE` | Maximum engine hours seen that day. |
| `temp_mean` | `DOUBLE` | Average engine temperature over RUN readings. |
| `temp_max` | `DOUBLE` | Maximum engine temperature over RUN readings. |
| `oil_mean` | `DOUBLE` | Average oil pressure over RUN readings. |
| `oil_min` | `DOUBLE` | Minimum oil pressure over RUN readings. |
| `hyd_mean` | `DOUBLE` | Average hydraulic pressure over RUN readings. |
| `hyd_min` | `DOUBLE` | Minimum hydraulic pressure over RUN readings. |
| `vib_mean` | `DOUBLE` | Average vibration over RUN readings. |
| `vib_max` | `DOUBLE` | Maximum vibration over RUN readings. |
| `fuel_mean` | `DOUBLE` | Average fuel rate over RUN readings. |
| `load_mean` | `DOUBLE` | Average load percentage over RUN readings. |
| `idle_mean` | `DOUBLE` | Average idle percentage over RUN readings. |
| `run_share` | `DOUBLE` | Share of RUN readings within the day. |
| `is_after_retirement` | `BOOLEAN` | Whether the date is on or after the ERP retirement date. |

## gold.fact_fault_episode

Resolved fault episodes grouped from telemetry fault-code bursts.

| Column | Type | Business meaning |
| --- | --- | --- |
| `episode_id` | `STRING` | Stable episode id within this dataset. |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `site_code` | `STRING` | ERP site for the asset. |
| `fault_code` | `STRING` | Fault code from the catalog. |
| `system` | `STRING` | Subsystem such as ENG or HYD. |
| `severity` | `STRING` | INFO, WARN, or CRIT. |
| `start_utc` | `TIMESTAMP` | First telemetry timestamp in the episode. |
| `end_utc` | `TIMESTAMP` | Last telemetry timestamp in the episode. |
| `n_records` | `INT` | Number of telemetry records in the episode. |
| `is_significant` | `BOOLEAN` | True for CRIT and WARN episodes with at least three records. |
| `recon_status` | `STRING` | NOT_APPLICABLE, MATCHED, UNMATCHED, or PENDING. |
| `matched_wo_number` | `STRING` | Best matched corrective work-order number when present. |
| `month` | `STRING` | Start month in YYYY-MM form. |

## gold.fact_work_order

Resolved, non-duplicate work orders at the business-grain used by reconciliation and ML.

| Column | Type | Business meaning |
| --- | --- | --- |
| `wo_number` | `STRING` | Work-order identifier. |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `site_code` | `STRING` | ERP site for the asset. |
| `wo_type` | `STRING` | PM, CM, or INSP. |
| `priority` | `STRING` | CMMS priority P1 to P4. |
| `status` | `STRING` | Open or Closed status. |
| `failure_code` | `STRING` | CM failure code for corrective work. |
| `failure_system` | `STRING` | Subsystem for the corrective work. |
| `description` | `STRING` | Free-text work-order description. |
| `opened_utc` | `TIMESTAMP` | Opened timestamp normalized to UTC. |
| `closed_utc` | `TIMESTAMP` | Closed timestamp normalized to UTC. |
| `duration_hours` | `DOUBLE` | Elapsed hours between opened and closed. |
| `labor_hours` | `DOUBLE` | Labor hours recorded on the work order. |
| `parts_cost_eur` | `DOUBLE` | Parts cost in EUR. |
| `technician_id` | `STRING` | Synthetic technician identifier. |
| `reported_by` | `STRING` | Synthetic reporter when present. |
| `id_resolution` | `STRING` | Identity-resolution tier used for the asset. |
| `times_corrected` | `BOOLEAN` | True when swapped timestamps were corrected. |

## gold.fact_recon_match

Episode-to-work-order candidate matches inside the reconciliation window.

| Column | Type | Business meaning |
| --- | --- | --- |
| `episode_id` | `STRING` | Fault episode identifier. |
| `wo_number` | `STRING` | Corrective work-order identifier. |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `delta_hours` | `DOUBLE` | Work-order open time minus episode start, in hours. |
| `same_system` | `BOOLEAN` | Whether the fault and work order point to the same subsystem. |
| `is_best_for_episode` | `BOOLEAN` | Whether this row is the best match for the episode. |

## gold.fact_recon_exception

Explicit reconciliation findings and operational exceptions.

| Column | Type | Business meaning |
| --- | --- | --- |
| `exception_id` | `STRING` | Stable exception identifier within this dataset. |
| `exception_type` | `STRING` | Primary exception category. |
| `subtype` | `STRING` | Subtype for categories that have one. |
| `severity` | `STRING` | LOW, MEDIUM, or HIGH. |
| `erp_asset_id` | `STRING` | Resolved asset when applicable. |
| `site_code` | `STRING` | Site when applicable. |
| `reference_id` | `STRING` | Business key such as device id, episode id, or WO number. |
| `event_utc` | `TIMESTAMP` | Anchor timestamp when applicable. |
| `n_records` | `INT` | Number of implicated records. |
| `detail` | `STRING` | Human-readable explanation. |

## gold.agg_recon_monthly

Monthly site-level reconciliation KPI rollup used for trends and match-rate questions.

| Column | Type | Business meaning |
| --- | --- | --- |
| `month` | `STRING` | Month in YYYY-MM form. |
| `site_code` | `STRING` | Site identifier. |
| `crit_episodes` | `INT` | CRIT episodes opened in the month. |
| `crit_matched` | `INT` | CRIT episodes matched to a corrective work order. |
| `crit_unmatched` | `INT` | CRIT episodes with no work order after the window closed. |
| `crit_pending` | `INT` | CRIT episodes still within the open match window. |
| `crit_match_rate` | `DOUBLE` | Matched divided by matched plus unmatched, pending excluded. |
| `warn_episodes_3plus` | `INT` | Significant WARN episodes with at least three records. |
| `warn_matched` | `INT` | WARN episodes matched to a corrective work order. |
| `warn_unmatched` | `INT` | WARN episodes without a work order after the window closed. |
| `cm_work_orders` | `INT` | Corrective work orders opened in the month. |
| `cm_wo_with_fault_signal` | `INT` | Corrective work orders with at least one matched episode. |
| `cm_wo_without_fault_signal` | `INT` | Corrective work orders with no matching episode. |
| `avg_crit_fault_to_wo_hours` | `DOUBLE` | Average hours from CRIT episode start to corrective work order. |
| `cm_repair_hours` | `DOUBLE` | Total corrective repair duration in hours. |

## ml.asset_day_features

ML-ready daily feature table with labels, splits, and frozen score-day rows.

| Column | Type | Business meaning |
| --- | --- | --- |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `obs_date` | `DATE` | Feature observation date. |
| `temp_mean` | `DOUBLE` | Daily mean engine temperature. |
| `temp_max` | `DOUBLE` | Daily maximum engine temperature. |
| `oil_mean` | `DOUBLE` | Daily mean oil pressure. |
| `oil_min` | `DOUBLE` | Daily minimum oil pressure. |
| `hyd_mean` | `DOUBLE` | Daily mean hydraulic pressure. |
| `hyd_min` | `DOUBLE` | Daily minimum hydraulic pressure. |
| `vib_mean` | `DOUBLE` | Daily mean vibration. |
| `vib_max` | `DOUBLE` | Daily maximum vibration. |
| `fuel_mean` | `DOUBLE` | Daily mean fuel rate. |
| `load_mean` | `DOUBLE` | Daily mean load percentage. |
| `idle_mean` | `DOUBLE` | Daily mean idle percentage. |
| `n_readings` | `INT` | Daily reading count. |
| `run_share` | `DOUBLE` | Daily RUN reading share. |
| `engine_hours` | `DOUBLE` | Daily max engine hours. |
| `warn_cnt_1d` | `INT` | WARN fault-count feature over one day. |
| `crit_cnt_1d` | `INT` | CRIT fault-count feature over one day. |
| `warn_cnt_7d` | `DOUBLE` | WARN fault-count feature over seven days. |
| `crit_cnt_7d` | `DOUBLE` | CRIT fault-count feature over seven days. |
| `warn_cnt_14d` | `DOUBLE` | WARN fault-count feature over fourteen days. |
| `temp_mean_3d` | `DOUBLE` | Rolling 3-day temperature mean. |
| `temp_mean_7d` | `DOUBLE` | Rolling 7-day temperature mean. |
| `temp_mean_14d` | `DOUBLE` | Rolling 14-day temperature mean. |
| `oil_mean_3d` | `DOUBLE` | Rolling 3-day oil-pressure mean. |
| `oil_mean_7d` | `DOUBLE` | Rolling 7-day oil-pressure mean. |
| `oil_mean_14d` | `DOUBLE` | Rolling 14-day oil-pressure mean. |
| `hyd_mean_3d` | `DOUBLE` | Rolling 3-day hydraulic-pressure mean. |
| `hyd_mean_7d` | `DOUBLE` | Rolling 7-day hydraulic-pressure mean. |
| `hyd_mean_14d` | `DOUBLE` | Rolling 14-day hydraulic-pressure mean. |
| `vib_mean_3d` | `DOUBLE` | Rolling 3-day vibration mean. |
| `vib_mean_7d` | `DOUBLE` | Rolling 7-day vibration mean. |
| `vib_mean_14d` | `DOUBLE` | Rolling 14-day vibration mean. |
| `temp_trend` | `DOUBLE` | 3-day minus 14-day engine-temperature mean. |
| `oil_trend` | `DOUBLE` | 3-day minus 14-day oil-pressure mean. |
| `hyd_trend` | `DOUBLE` | 3-day minus 14-day hydraulic-pressure mean. |
| `vib_trend` | `DOUBLE` | 3-day minus 14-day vibration mean. |
| `temp_max_7d` | `DOUBLE` | Rolling 7-day max engine temperature. |
| `vib_max_7d` | `DOUBLE` | Rolling 7-day max vibration. |
| `days_since_last_pm` | `DOUBLE` | Days since the last preventive work order. |
| `days_since_last_cm` | `DOUBLE` | Days since the last corrective work order. |
| `cm_count_90d` | `DOUBLE` | Corrective work-order count over the trailing 90 days. |
| `equipment_class_code` | `INT` | Static class code. |
| `asset_age_years` | `DOUBLE` | Static asset age feature. |
| `fail_next_7d` | `DOUBLE` | Binary label for a corrective work order in the next 7 UTC days. |
| `split` | `STRING` | Purged split assignment. |

## ml.failure_risk_score

Frozen failure-risk scores loaded for Part 4 so agent answers stay stable.

| Column | Type | Business meaning |
| --- | --- | --- |
| `score_date` | `DATE` | Scoring date. |
| `erp_asset_id` | `STRING` | Resolved asset identifier. |
| `site_code` | `STRING` | ERP site for the asset. |
| `equipment_class` | `STRING` | Equipment family. |
| `risk_score` | `DOUBLE` | Frozen probability-like risk score. |
| `risk_band` | `STRING` | Low, Medium, or High using frozen thresholds. |
| `risk_rank` | `INT` | Descending rank on the score date. |
| `top_drivers` | `STRING` | Semicolon-joined heuristic driver codes. |
| `model_version` | `STRING` | Frozen model version label. |

## ml.drift_report

Feature-drift PSI summary used in the monitoring discussion.

| Column | Type | Business meaning |
| --- | --- | --- |
| `equipment_class` | `STRING` | Equipment family. |
| `sensor` | `STRING` | Sensor name. |
| `psi` | `DOUBLE` | Population stability index. |
| `ref_mean` | `DOUBLE` | Reference mean. |
| `new_mean` | `DOUBLE` | New-batch mean. |
| `ref_rows` | `INT` | Reference RUN-reading count. |
| `new_rows` | `INT` | New-batch RUN-reading count. |
| `status` | `STRING` | stable, moderate, or major. |
