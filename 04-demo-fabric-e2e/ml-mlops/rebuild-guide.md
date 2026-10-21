# Rebuild guide — Fabric ML and MLOps demo

## 1. Prerequisites

1. Capacity: a Trial capacity runs the notebooks and pipelines in this kit; only the Part 4 data agent (and Copilot / AI functions) needs a paid F2+ capacity (same wording as `..\etl\rebuild-guide.md` section 2).
2. Create or open a workspace in West Europe, France Central, or Sweden Central.
2a. Keep the workspace default (Runtime 2.0: Spark 4.1, Python 3.13). Runtime 1.3 (Spark 3.5, Python 3.11; long-term support until March 2027) is the fallback. Nothing was run in Fabric itself. The ML notebooks ran end to end on the Python libraries of both runtimes [a Runtime-2.0-like set (pandas 2.2.3, numpy 2.5.4, scikit-learn 1.6.1, pyarrow 19.0.1, mlflow 2.22.0) and the Runtime 1.3 set (pandas 2.1.4, numpy 1.26.4, scikit-learn 1.2.2, pyarrow 14.0.2, mlflow-skinny 2.12.2)] and reproduced the contract on both: counts exact, metrics within the +/-0.03 tolerance. Those were local Python runs with a simulated Fabric and the ETL tables read through pyarrow, so the Spark calls of the ML notebooks (and Spark 4's ANSI default) were not exercised; they are listed in `VERIFY-BEFORE-FRIDAY.md`, "Spark calls to watch in the first Fabric run". The ETL kit passes 39 of 39 checks on local Spark 4.1.1 + Delta 4.2.0 and on Spark 3.5.6 + Delta 3.2.1 (Python 3.13.15, Java 17), also not in Fabric. Check the runtime with `print(spark.version)` (4.1.x on Runtime 2.0, 3.5.x on Runtime 1.3; see the ETL guide, `..\etl\rebuild-guide.md` section 3).
3. Create a schema-enabled lakehouse named `lh_fleet`.
4. Make `lh_fleet` the default lakehouse for all five ML notebooks before you run them.
4a. Upload the `notebooks\` folder (`__init__.py`, `notebook_common.py`, `shared\*.py`)
    to `lh_fleet`'s `Files/code/notebooks/...` (portal "Upload folder" is fine). Every
    ML notebook does `from notebooks.notebook_common import ...`; the generated
    notebook-content.py's first cell adds `/lakehouse/default/Files/code` to
    `sys.path` only when `notebookutils` is present, so this upload step is required
    before any ML notebook will import successfully in a fresh workspace. See
    README.md "Sharing code across notebooks" for alternatives (not used here).
5. Make sure the ETL half already produced these tables:
   - `silver.telemetry`
   - `gold.dim_asset`
   - `gold.fact_telemetry_daily`
   - `gold.fact_work_order`
   - `silver.telemetry_drift`
   - `bronze.fault_code_catalog`
6. Break-glass option if ETL tables are missing: run `06-demo-foundry-data-agent\fabric-setup\nb_10_load_gold_break_glass.py` (outside this folder) to load `gold.*` and `ml.*` reference outputs -- it already loads `ml.asset_day_features` and `ml.drift_report`, so once it has run, **skip `nb_04_features` and `nb_07_drift_monitor`** and run only `nb_05_train_mlflow` -> `nb_06_register_score` -> `nb_08_promotion_gate`. `pl_fleet_daily` cannot run end to end this way (its first three activities need the real ETL tables); this is a manual notebook-by-notebook fallback, not a pipeline run. This dependency lives outside this folder; verify it before Friday.

## 2. Import the notebook artifacts

1. In Fabric, open the target workspace.
2. Import the notebook Git folders from `fabric-git\`:
   - `nb_04_features.Notebook`
   - `nb_05_train_mlflow.Notebook`
   - `nb_06_register_score.Notebook`
   - `nb_07_drift_monitor.Notebook`
   - `nb_08_promotion_gate.Notebook`
3. Import the pipeline folder `fabric-git\pl_fleet_daily.DataPipeline`.
4. Import the variable library folder `fabric-git\fleet_mlops.VariableLibrary`.
5. ⚠ UNVERIFIED: the exact portal label may be **Import**, **Upload**, or **Update definition** depending on whether the workspace is Git-connected or using the item-definition APIs.

## 3. Attach the lakehouse

1. Open each notebook.
2. Attach `lh_fleet` as the default lakehouse.
3. Save the notebook after the attachment if Fabric prompts for it.
4. Why this matters: relative `Tables/` and `Files/` paths only work on the default lakehouse; the notebooks assume that attachment.

## 4. Run `nb_04_features`

1. Open `nb_04_features`.
2. Confirm parameters:
   - `telemetry_table = silver.telemetry`
   - `daily_table = gold.fact_telemetry_daily`
   - `work_order_table = gold.fact_work_order`
   - `asset_table = gold.dim_asset`
   - `fault_catalog_table = bronze.fault_code_catalog`
   - `output_table = ml.asset_day_features`
3. Run all cells.
4. Expected result:
   - writes `ml.asset_day_features`
   - 50,876 rows
   - 49,028 labelled rows
   - 5.47% positive rate on labelled rows
   - split rows: warmup 3,976 / train 28,520 / gap 3,830 / valid 6,591 / test 6,111 / unlabeled 1,584 / score 264
5. What to look at:
   - the summary JSON
   - the `split` column in the table preview
6. If it fails:
   - missing `day`, `opened_fix`, or `acq_day` columns are normalized inside the notebook now
   - if a source table is absent, stop and fix ETL first

## 5. Run `nb_05_train_mlflow`

1. Open `nb_05_train_mlflow`.
2. Confirm parameters:
   - `experiment_name = fleet-failure-7d`
   - `model_name = fleet-failure-7d`
   - `features_table = ml.asset_day_features`
3. Run all cells.
4. Expected result:
   - one parent run named `nb_05_train_mlflow`
   - five child runs: prevalence, rule baseline, logistic regression, HGB, HGB without fault-code features
   - best candidate registered as model `fleet-failure-7d`
   - one row in `ml.model_pointer` if no champion existed before
5. Expected metrics to narrate:
   - HGB valid PR-AUC about 0.336
   - HGB test PR-AUC about 0.385 (+/-0.03)
   - logistic regression valid/test PR-AUC about 0.292
6. In the Experiment item, show:
   - run comparison
   - params and metrics
   - artifacts: comparison CSV, PR curves, importance CSVs
7. In the ML model item, show:
   - versions only
   - version tags (`candidate_status`, `selected_by`, `candidate_kind`, `source_run_id`)

## 6. Run `nb_06_register_score`

1. Open `nb_06_register_score`.
2. Confirm parameters:
   - `model_name = fleet-failure-7d`
   - `pointer_table = ml.model_pointer`
   - `output_table = ml.failure_risk_score`
3. Run all cells.
4. Expected result:
   - 264 scored assets
   - output columns: `score_date, erp_asset_id, site_code, equipment_class, risk_score, risk_band, risk_rank, top_drivers, model_version`
   - bands are about 9 High / 7 Medium; exact Medium/Low split depends on library versions (do not assert exact band counts on a live run) -- the frozen reference used for Part 4 is High 9 / Medium 7 / Low 248 exactly
5. Demo points:
   - the active version comes from `ml.model_pointer` unless you override it
   - `MLFlowTransformer` is the Spark-native scoring path
   - `PREDICT` needs an MLflow model with a signature

## 7. Run `nb_07_drift_monitor`

1. Open `nb_07_drift_monitor`.
2. Confirm parameters:
   - `telemetry_table = silver.telemetry`
   - `new_telemetry_table = silver.telemetry_drift`
   - `output_table = ml.drift_report`
   - `reference_start = 2026-09-01`
3. Run all cells.
4. Expected result:
   - writes `ml.drift_report`
   - notebook exit JSON reports `status = alert`
   - 47 combinations total
   - 4 major / 3 moderate / 40 stable
5. Show the drift table and filter to `status = major`.

## 8. Run `nb_08_promotion_gate`

1. Open `nb_08_promotion_gate`.
2. Default is **report-only**: `apply_pointer_update = False`. This is the demo default and what the daily pipeline actually runs (`RunPromotionGate` passes no parameters). The notebook computes the decision, but nothing in the pipeline moves `ml.model_pointer` -- a human decides.
   - Why: scoring (`nb_06`) always serves the **current champion** from the pointer table; the gate then decides whether **today's challenger** becomes **tomorrow's champion**. That is the standard champion/challenger ordering (score with what is trusted today, evaluate the candidate for tomorrow), and keeping the pointer update manual means nothing in production changes without a human looking at the decision first.
3. To apply a promotion as a one-off demo checkpoint, re-run the notebook with:
   - `champion_version` set to the current champion
   - `challenger_version` set to the new model version
   - `apply_pointer_update = True`
4. For an **auto-promote** pipeline (not the default — document as an optional exercise only), the `RunPromotionGate` activity could pass `apply_pointer_update: true` as a `typeProperties.parameters` value:
   ```json
   "typeProperties": {
     "parameters": {
       "apply_pointer_update": { "value": "@pipeline().parameters.autoPromote", "type": "Expression" }
     }
   }
   ```
   This is documentation only — the shipped `pipeline-content.json` does not set this, so the pipeline stays report-only by default.
5. Run all cells.
6. Expected rule:
   - challenger test PR-AUC must improve by at least 0.01
   - challenger top-5% precision must not drop by more than 0.02
7. The notebook returns its decision as the **notebook exit value** (`context.notebook_exit(decision)`), so the full decision JSON — `decision`, `passed`, `champion_version`, `challenger_version`, metrics — is visible as the `RunPromotionGate` activity's `output.result.exitValue` in the Monitor hub, not just in notebook cell output.
8. Show `ml.model_pointer` after the run only if you set `apply_pointer_update = True`; otherwise it is unchanged by design.

## 9. Build the daily pipeline

1. Import or create `pl_fleet_daily` from `fabric-git\pl_fleet_daily.DataPipeline`.
2. Replace placeholders from `cicd\parameter.yml`:
   - workspace ID
   - notebook IDs
   - Office 365 connection ID
   - alert recipient list
3. Check the pipeline chain:
   - ETL notebooks (`RunBronzeIngest` -> `RunSilverCleanResolve` -> `RunGoldReconcile`)
   - `RunFeatures` (`nb_04_features`)
   - `RunTrainMlflow` (`nb_05_train_mlflow`)
   - `RunRegisterScore` (`nb_06_register_score`)
   - `RunDriftMonitor` (`nb_07_drift_monitor`)
   - `RunPromotionGate` (`nb_08_promotion_gate`)
   - `IfDriftAlert` -> `SendDriftAlertEmail` on major drift
   - every notebook activity also has a `NotifyXFailure` Office365Email branch on `Failed`
4. Check retry policy:
   - every notebook activity has `retry = 1`
   - `retryIntervalInSeconds = 60`
5. Check `IfDriftAlert`'s expression: `@equals(json(activity('RunDriftMonitor').output.result.exitValue).status, 'alert')`. This reads the notebook's **exit value**, not a string search over the raw activity output (an earlier draft used `@contains(string(...), '"status": "alert"')`, which can never match because `string(...)` re-escapes the inner quotes). ⚠ UNVERIFIED: `output.result.exitValue` is the community-documented path, not on the Fabric Learn Notebook-activity page as of this writing — on the first live run, open the `RunDriftMonitor` activity's Output JSON in the Monitor hub and confirm `result.exitValue` exists with a parsed `status` field.
6. The pipeline's `RunPromotionGate` step is **report-only** by default (no `typeProperties.parameters` set, so `nb_08` runs with `apply_pointer_update = False`) — see section 8 above for the rationale and the optional auto-promote parameter shape.

## 10. Schedule the pipeline

1. Open the pipeline.
2. Add a schedule trigger for once per day after the ETL arrival window.
3. Suggested demo-day schedule: 06:30 local time for ETL + ML refresh before the session.
4. Keep the trigger disabled until the notebooks are fully wired and tested.

## 11. Configure alerts

1. Pipeline-native alert path:
   - use the `Office365Email` activities already present in the pipeline definition
   - replace the Office 365 connection ID and the recipient list
2. Activator path:
   - use `ml.drift_report` or a derived event source to trigger Teams/email/pipeline/notebook actions
   - see `drift-alert-recipe.md`

## 12. Pre-flight before the live session

1. Run the five notebooks once in the target workspace.
2. Open the Experiment item and ML model item once so the UI is warm.
3. Keep prebuilt fallbacks open:
   - `ml.asset_day_features`
   - Experiment run comparison
   - `ml.failure_risk_score`
   - `ml.drift_report`
   - `nb_08_promotion_gate`
4. Verify every ⚠ UNVERIFIED item listed in `VERIFY-BEFORE-FRIDAY.md`.
