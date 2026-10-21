# Verify before Friday

## D-5 to D-0 checklist

| Day | Check |
|---|---|
| D-5 | Confirm the workspace runs the default Fabric Runtime 2.0 (`print(spark.version)` shows `4.1.x`; Runtime 1.3 is the fallback, see "Runtime" below), then import the five notebooks, variable library, and `pl_fleet_daily` into it. |
| D-4 | Attach `lh_fleet` to every notebook and run the full chain once. |
| D-3 | Replace all placeholder IDs in the pipeline and CI/CD parameter file with real dev/test/prod values. |
| D-2 | Rehearse the 30-minute live path and the 18-minute short path. |
| D-1 | Warm the Experiment item, ML model item, and table previews. Verify the alert channel. |
| D-0 | Keep the fallback tables and gate notebook open before the audience arrives. |

## Preview items

- `Machine learning experiments` in Git integration and deployment pipelines — ⚠ PREVIEW
  - Page: `https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-artifacts-git-deployment-pipelines`
- `Machine learning models` in Git integration and deployment pipelines — ⚠ PREVIEW
  - Same page as above
- Fabric deployment pipeline new UI — ⚠ PREVIEW
  - Page: `https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines`
- Activator parameter passing to Fabric items — ⚠ PREVIEW
  - Page: `https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-trigger-fabric-items#pass-parameter-values-to-fabric-items-preview`

## Unverified items

- ⚠ UNVERIFIED: exact import label in the Fabric portal for these item folders in the target tenant
  - Check in workspace UI during rehearsal
- ⚠ UNVERIFIED: `IfDriftAlert` expression `@equals(json(activity('RunDriftMonitor').output.result.exitValue).status, 'alert')` uses `output.result.exitValue`, a community-documented path not on the Fabric Learn Notebook-activity page as of this writing
  - Check: on the first live run, open the `RunDriftMonitor` activity's Output JSON in the Monitor hub, confirm `result.exitValue` exists, and confirm its parsed `status` reads `alert` when drift is major
- ⚠ UNVERIFIED: `nb_07` should print `thresholds source: variable library` when the `fleet_mlops` Variable Library is correctly deployed and attached; it currently prints `thresholds source: default` in local validation (no library available outside Fabric), which is expected locally but must flip to `variable library` in the live workspace
  - Check: if it still prints `default` live, check the library name (`fleet_mlops`) and variable names (`driftModerateThreshold`/`driftMajorThreshold`, case-sensitive) and the active DEV/TEST/PROD value set
- ⚠ UNVERIFIED: simplest Friday-ready binding path from `ml.drift_report` into Activator without an extra report or eventstream
  - Check Activator rule authoring in the target tenant
- ⚠ UNVERIFIED: whether the presenter wants Office 365 email only, Teams only, or both for the drift alert
  - Check available shared connections and audience preference
- ⚠ UNVERIFIED: the separate break-glass notebook path and ownership in the final workshop repo layout
  - Check `06-demo-foundry-data-agent\fabric-setup\nb_10_load_gold_break_glass.py`
- ⚠ UNVERIFIED: the exact ML model item UI labels for version comparison in the target tenant skin
  - Check during rehearsal in the ML model item
- ⚠ UNVERIFIED: Spark 4 behaviour of the Spark calls the ML notebooks make (`spark.read.table`, `toPandas`, `createDataFrame`, `saveAsTable`), including whether Fabric Runtime 2.0 keeps Spark 4's ANSI mode on by default
  - Check: see "Spark calls to watch in the first Fabric run" below; in a notebook print `spark.version` and `spark.conf.get("spark.sql.ansi.enabled")`, run the chain once, then compare the table row counts with "Numbers to sanity-check live".
- ⚠ UNVERIFIED: the exception that real Fabric raises when `ml.model_pointer` does not exist yet (first run on a fresh workspace). `read_model_pointer` now treats a missing table as "no pointer yet" (fixed in code, 2026-10-21) and was tested only against a fake exception, so the real exception class and message are not confirmed
  - Check: `nb_05_train_mlflow` on the fresh workspace is expected to end by writing one row to `ml.model_pointer`; if it stops with a "table or view not found" error instead, see the `read_model_pointer` row under "Spark calls to watch in the first Fabric run".

## Runtime

Keep the workspace default (Runtime 2.0: Spark 4.1, Python 3.13). Runtime 1.3 (Spark 3.5, Python 3.11; long-term support until March 2027) is the fallback. Nothing was run in Fabric itself. The ML notebooks ran end to end on the Python libraries of both runtimes [a Runtime-2.0-like set (pandas 2.2.3, numpy 2.5.4, scikit-learn 1.6.1, pyarrow 19.0.1, mlflow 2.22.0) and the Runtime 1.3 set (pandas 2.1.4, numpy 1.26.4, scikit-learn 1.2.2, pyarrow 14.0.2, mlflow-skinny 2.12.2)] and reproduced the contract on both: counts exact, metrics within the +/-0.03 tolerance. Those were local Python runs with a simulated Fabric and the ETL tables read through pyarrow, so the Spark calls of the ML notebooks (and Spark 4's ANSI default) were not exercised; they are listed in `VERIFY-BEFORE-FRIDAY.md`, "Spark calls to watch in the first Fabric run". The ETL kit passes 39 of 39 checks on local Spark 4.1.1 + Delta 4.2.0 and on Spark 3.5.6 + Delta 3.2.1 (Python 3.13.15, Java 17), also not in Fabric. Check the runtime with `print(spark.version)` (4.1.x on Runtime 2.0, 3.5.x on Runtime 1.3; see the ETL guide, `..\etl\rebuild-guide.md` section 3).

- Lifecycle (Microsoft Learn, lifecycle page, read 2026-10-21): Runtime 1.3 is in the end-of-support-announced (EOSA) stage. Its support ended on 2026-09-30; Long Term Support (LTS) runs from 2026-10-01 for six months (through March 2027). Runtime 2.0 (Spark 4.1) is generally available and, per the ETL guide, the default for new workspaces (`..\etl\rebuild-guide.md` section 3, step 2), so leave a new workspace as it is and confirm it with `print(spark.version)`. On a slide say "default Runtime 2.0; Runtime 1.3 is the long-term-support fallback", and do not call either runtime "the newest".
- ⚠ UNVERIFIED: that Runtime 1.3 can still be selected in the target tenant on the day; this only matters for the fallback. Check it on Thursday (see `..\etl\VERIFY-BEFORE-FRIDAY.md`; the switch path is in `..\etl\rebuild-guide.md` section 3, step 2). Switch to 1.3 only if the chain fails on Runtime 2.0: restart the session and rehearse the full chain once. Nothing has run on Fabric Runtime 2.0 or 1.3 themselves: the ML code ran on the Python libraries of both (scikit-learn 1.6.1 / MLflow 2.22.0 and scikit-learn 1.2.2 / MLflow-skinny 2.12.2), and the ETL kit reports its notebooks passing locally on Spark 4.1.1 + Delta 4.2.0 and on Spark 3.5.6 + Delta 3.2.1 (its `RESULTS.md`, "Round 5, follow-up T5").
- ⚠ UNVERIFIED: the optional Spark scoring path in `nb_06` (`synapse.ml.predict` / `MLFlowTransformer`) on the runtime you present on. The live notebook path is pandas; nothing local exercised the Spark path.
- Capacity: a Trial capacity runs the notebooks and pipelines; only the Part 4 data agent (and Copilot / AI functions) needs a paid F2+ capacity (same wording as `..\etl\rebuild-guide.md` section 2).

## Spark calls to watch in the first Fabric run

⚠ UNVERIFIED limit: the ML notebooks were exercised with the pandas / fake-Spark simulation (`local-validation\fabric_sim.py`), and the ETL tables were read through pyarrow (`local-validation\integration_etl_to_ml.py`). Spark 4 behaviour of the Spark calls below was therefore NOT exercised, on any Spark. Spark 4 turns ANSI mode on by default (`spark.sql.ansi.enabled`); whether Fabric Runtime 2.0 keeps it is UNVERIFIED. File:line refer to the sources in `notebooks\`; the notebooks under `fabric-git\` are generated from them and number their lines differently.

| File:line | Spark call | What to watch |
|---|---|---|
| `notebook_common.py:179` | `self.spark.read.table(table_name).toPandas()` in `NotebookContext.read_table` (Fabric mode) | Every table read goes through it: `nb_04_features.py:72-76`, `nb_05_train_mlflow.py:129`, `nb_06_register_score.py:77-78`, `nb_07_drift_monitor.py:63-65`, and the pointer table via `read_model_pointer` (`notebook_common.py:452`; called at `nb_05_train_mlflow.py:183`, `nb_06_register_score.py:79`, `nb_08_promotion_gate.py:64`). Check the pandas dtypes it returns (first bullet below). |
| `notebook_common.py:187` | `self.spark.createDataFrame(frame).write.format("delta").mode("overwrite").saveAsTable(table_name)` in `NotebookContext.write_table` (Fabric mode) | Every table write goes through it: `nb_04_features.py:83` (`ml.asset_day_features`), `nb_06_register_score.py:103` (`ml.failure_risk_score`), `nb_07_drift_monitor.py:76` (`ml.drift_report`), and the pointer table via `upsert_model_pointer` (`notebook_common.py:490`; called at `nb_05_train_mlflow.py:185`, and at `nb_08_promotion_gate.py:85` and `:114` only when `apply_pointer_update` is True). Check the schema Spark infers (second bullet below). |
| `nb_06_register_score.py:57-67` | optional `MLFlowTransformer(...)`, `context.spark.createDataFrame(...)`, `transformer.transform(spark_input).toPandas()` | Off by default (`run_spark_transformer` is `False` at line 20 and is read at line 111). It never ran anywhere; leave it off unless you rehearse it. |
| `notebook_common.py:450-458` | `read_model_pointer`: reads `ml.model_pointer` (`:452`); a missing table now means "no pointer yet" (`_is_missing_table_error`, `:445-447`) | Fixed in code (2026-10-21), tested only against a fake exception. On a fresh workspace nothing has written `ml.model_pointer` yet, and real Spark is expected to raise `AnalysisException` ("table or view not found"). `read_model_pointer` now returns an empty pointer when the exception class is named `AnalysisException` or its message contains `TABLE_OR_VIEW_NOT_FOUND`, `cannot be found` or `does not exist`, and re-raises every other exception. The tests are `local-validation\tests\test_read_model_pointer.py` (a fake `read.table` that raises such an exception) and the fake spark of `fabric_sim.py`, which now raises the same kind of error; before the fix it raised `KeyError`, which hid the problem. **⚠ UNVERIFIED: the real Fabric exception class and message.** The match is deliberately broad: any `AnalysisException` from this read counts as "no pointer yet". What to watch: the first `nb_05_train_mlflow` run is expected to end by writing one row to `ml.model_pointer` (`nb_05_train_mlflow.py:183-185`); if it stops there with "table or view not found", the real exception does not match the rule: create the empty table once, re-run `nb_05`, and note the exact class and message so `_is_missing_table_error` can be adjusted. Optional belt-and-braces, not needed if the fix works (it can also be run once before the first run): `spark.sql("CREATE TABLE IF NOT EXISTS ml.model_pointer (model_name STRING, champion_version STRING, updated_at_utc STRING, updated_by STRING, note STRING) USING DELTA")` (⚠ UNVERIFIED in Fabric). |

- dtypes after `toPandas()` (the integration check emulated them with pyarrow, not with Spark): `date` columns arrive as Python `date` objects, an integer column that holds NULL arrives as float64, decimals as `Decimal`, timestamps as `datetime64`. `nb_04_features.py:48` and `:64` compute day numbers with `.dt.days` (independent of the datetime unit); `:57` turns `opened_utc` into epoch seconds with `.astype("int64") // 1_000_000_000`, which assumes nanosecond timestamps, so another datetime unit would shift that feature by a constant factor without raising an error. If the `nb_04` summary or the features differ from the contract (50,876 rows, 49,028 labelled), start there.
- Schema inference in `createDataFrame(frame)`: a column that is entirely None / NaN has no inferable type, and `mode("overwrite")` onto an existing table whose column types changed needs the `overwriteSchema` option (not used). Check the table schemas in the lakehouse explorer after the first run.
- ANSI mode: none of these calls runs a Spark SQL cast, a division or any other arithmetic (no `spark.sql`, `.cast(`, `selectExpr`, `withColumn` or `pyspark.sql.functions` in `nb_04`..`nb_08`, `notebook_common.py` or `notebooks\shared\`; grep on 2026-10-21). All string-to-number conversion, division, log and rate arithmetic of the ML code runs in pandas / numpy / scikit-learn after `toPandas()`, where ANSI mode does not apply. So no ANSI string-to-number cast, divide-by-zero or overflow failure is expected from the ML notebooks' own Spark calls; that is a reading of the source, not a run. If an ANSI error does appear on a read or write, the ETL guide names the switch back: `spark.conf.set("spark.sql.ansi.enabled", "false")` in the first cell (Apache's documented setting, ⚠ UNVERIFIED in Fabric; `..\etl\rebuild-guide.md` section 3, step 2).

## Settings to confirm

- Workspace role = Contributor or above for the presenter
- Workspace on the default Fabric Runtime 2.0 (see "Runtime" above); `print(spark.version)` in a notebook shows `4.1.x` (`3.5.x` means the Runtime 1.3 fallback is active)
- Default lakehouse = `lh_fleet`
- Office 365 or Teams connection shared to the workspace
- Pipeline trigger disabled until the rehearsal passes
- `RunPromotionGate` is report-only by default (no `typeProperties.parameters`, so `nb_08` runs with `apply_pointer_update = False`) -- confirm this is still the desired demo behavior before Friday; applying a promotion is a deliberate re-run with `apply_pointer_update = True`, not something the daily pipeline does automatically

## Numbers to sanity-check live

- `ml.asset_day_features` rows = 50,876
- `ml.failure_risk_score` rows = 264
- risk bands = about 9 High / 7 Medium (exact Medium/Low split depends on library versions; the frozen file used for Part 4 has 9 / 7 / 248 exactly)
- `ml.drift_report` combinations = 47
- drift summary = 4 major / 3 moderate / 40 stable
