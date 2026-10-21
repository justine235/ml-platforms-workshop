| Metric | Expected | Got | OK |
|---|---:|---:|:---:|
| bronze.telematics_events rows | 208900 | 208900 | OK |
| bronze.telematics_events duplicates removed | 1209 | 1209 | OK |
| bronze.telematics_events out_of_range_values_nulled | 217 | 217 | OK |
| silver.telemetry rows | 207691 | 207691 | OK |
| silver.telemetry late_rows | 2066 | 2066 | OK |
| silver.telemetry EXACT_NORM | 196810 | 196810 | OK |
| silver.telemetry SERIAL | 4350 | 4350 | OK |
| silver.telemetry CROSSWALK | 2180 | 2180 | OK |
| silver.telemetry UNRESOLVED | 4351 | 4351 | OK |
| silver.work_orders rows | 2359 | 2359 | OK |
| silver.work_orders EXACT_NORM | 2305 | 2305 | OK |
| silver.work_orders SERIAL | 28 | 28 | OK |
| silver.work_orders CROSSWALK | 18 | 18 | OK |
| silver.work_orders UNRESOLVED | 8 | 8 | OK |
| gold.dim_asset rows | 316 | 316 | OK |
| gold.dim_site rows | 12 | 12 | OK |
| gold.fact_telemetry_daily rows | 51353 | 51353 | OK |
| gold.fact_fault_episode rows | 3459 | 3459 | OK |
| gold.fact_work_order rows | 2345 | 2345 | OK |
| gold.fact_recon_match rows | 468 | 468 | OK |
| gold.fact_recon_exception rows | 211 | 211 | OK |
| gold.agg_recon_monthly rows | 72 | 72 | OK |
| gold.fact_recon_exception ACTIVE_ASSET_SILENT | 12 | 12 | OK |
| gold.fact_recon_exception DUPLICATE_WO | 6 | 6 | OK |
| gold.fact_recon_exception FAULT_WITHOUT_WO | 91 | 91 | OK |
| gold.fact_recon_exception RETIRED_ASSET_REPORTING | 6 | 6 | OK |
| gold.fact_recon_exception UNRESOLVED_ASSET_CMMS | 3 | 3 | OK |
| gold.fact_recon_exception UNRESOLVED_ASSET_TELEMATICS | 6 | 6 | OK |
| gold.fact_recon_exception WO_TIME_ANOMALY | 8 | 8 | OK |
| gold.fact_recon_exception WO_WITHOUT_FAULT | 79 | 79 | OK |
| bronze.telematics_events_drift rows | 15367 | 15367 | OK |
| bronze.telematics_events_drift duplicates removed | 79 | 79 | OK |
| bronze.telematics_events_drift out_of_range_values_nulled | 28 | 28 | OK |
| silver.telemetry_drift rows | 15288 | 15288 | OK |
| silver.telemetry_drift late_rows | 0 | 0 | OK |
| silver.telemetry_drift EXACT_NORM | 14457 | 14457 | OK |
| silver.telemetry_drift SERIAL | 333 | 333 | OK |
| silver.telemetry_drift CROSSWALK | 167 | 167 | OK |
| silver.telemetry_drift UNRESOLVED | 331 | 331 | OK |
