# Demo 2a-ML slide facts — Fabric ML and MLOps

Sources used: `02-demo-data\scenario-contract.md` sections 8-10, `02-demo-data\reference_out\ground_truth.json`, `00-presenter-guide\fact-sheets\fabric-ml.md`, `00-presenter-guide\fact-sheets\fabric-de-rti.md`, notebook sources in `notebooks\`.

## Notebook: `nb_04_features`
- Purpose: build `ml.asset_day_features` from reconciled daily telemetry, work orders, asset metadata, and fault occurrences with the fixed split contract.
- Important code lines (verbatim):
  - `notebooks\nb_04_features.py:41-47` — `def _normalize_daily_frame(daily: pd.DataFrame) -> pd.DataFrame:` / `if "day" not in normalized.columns:` / `normalized["day"] = (pd.to_datetime(normalized["obs_date"]) - EPOCH_DAY_ZERO).dt.days.astype("int64")` / `if "is_after_retirement" not in normalized.columns:` / `normalized["is_after_retirement"] = False`
  - `notebooks\nb_04_features.py:50-54` — `def _normalize_work_orders(work_orders: pd.DataFrame) -> pd.DataFrame:` / `if "opened_fix" not in normalized.columns and "opened_utc" in normalized.columns:` / `normalized["opened_fix"] = pd.to_datetime(normalized["opened_utc"], utc=True).astype("int64") // 1_000_000_000`
  - `notebooks\nb_04_features.py:57-61` — `def _normalize_dim_asset(dim_asset: pd.DataFrame) -> pd.DataFrame:` / `if "acq_day" not in normalized.columns:` / `normalized["acq_day"] = (pd.to_datetime(normalized["acquisition_date"]) - EPOCH_DAY_ZERO).dt.days.astype("int64")`
  - `notebooks\nb_04_features.py:69-76` — `daily = _normalize_daily_frame(context.read_table(params["daily_table"]))` / `work_orders = _normalize_work_orders(context.read_table(params["work_order_table"]))` / `dim_asset = _normalize_dim_asset(context.read_table(params["asset_table"]))` / `cutoff_epoch = next_day_cutoff_epoch(daily["obs_date"])` / `occurrences = fault_occurrences(telemetry, fault_catalog)` / `features = build_features(daily, work_orders, dim_asset, occurrences, cutoff_epoch)`
  - `notebooks\nb_04_features.py:77-84` — `features[FEATURES] = features[FEATURES].round(4)` / `context.write_table(params["output_table"], features)` / `"rows": int(len(features))` / `"labelled_rows": int(features["fail_next_7d"].notna().sum())` / `"positive_rate_labelled": round(float(features.loc[features["fail_next_7d"].notna(), "fail_next_7d"].mean()), 4)` / `"split_counts": compute_split_counts(features)`
  - `notebooks\nb_04_features.py:87-92` — `summary["reference_comparison"] = compare_frames_with_tolerance(` / `key_cols=["erp_asset_id", "obs_date", "split"],` / `numeric_cols=[*FEATURES, "fail_next_7d"],` / `tolerance=1e-6,`
- Output facts:
  - feature count = 42
  - rows = 50,876
  - labelled rows = 49,028
  - split rows = warmup 3,976 / train 28,520 / gap 3,830 / valid 6,591 / test 6,111 / unlabeled 1,584 / score 264
  - positive rate on labelled rows = about 5.47%
- Timing to speak to: 4 minutes live, 2 minutes short path

## Notebook: `nb_05_train_mlflow`
- Purpose: train five candidates, log them to one Fabric Experiment item, register the best validation PR-AUC model, and bootstrap the champion pointer if needed.
- Important code lines (verbatim):
  - `notebooks\notebook_common.py:192-206` — `if context.tracking_uri:` / `mlflow.set_tracking_uri(context.tracking_uri)` / `if context.registry_uri:` / `mlflow.set_registry_uri(context.registry_uri)` / `experiment = client.get_experiment_by_name(experiment_name)` / `if experiment is None:` / `experiment_id = client.create_experiment(experiment_name, artifact_location=artifact_location)` / `mlflow.set_experiment(experiment_name)`
  - `notebooks\nb_05_train_mlflow.py:52-53` — `with mlflow_module.start_run(run_name=run_name, nested=True) as child_run:` / `mlflow_module.set_tags({"candidate_kind": run_name, "feature_count": len(feature_cols), "tracked_metrics": ",".join(fleet_ml_core.METRIC_KEYS)})`
  - `notebooks\nb_05_train_mlflow.py:61-63` — `mlflow_module.log_params({"baseline": "rule", "rule_definition": "crit_cnt_7d > 0 or warn_cnt_7d >= 2"})` / `artifact_path = context.write_json_artifact("rule-baseline-metrics.json", metrics)` / `mlflow_module.log_artifact(str(artifact_path))`
  - `notebooks\nb_05_train_mlflow.py:67-72` — `model, metrics = fleet_ml_core.train_and_evaluate(df, kind=estimator_kind, features=feature_cols)` / `final_estimator = fleet_ml_core.fit_final_model(df, kind=estimator_kind, features=feature_cols)` / `wrapped = ProbabilityScoringClassifier(final_estimator)` / `flat_metrics = flatten_metrics(metrics)` / `mlflow_module.log_params({"estimator_kind": estimator_kind, "feature_subset": run_name, "feature_count": len(feature_cols)})` / `mlflow_module.log_metrics(flat_metrics)`
  - `notebooks\nb_05_train_mlflow.py:75-85` — `pr_curve_path = create_pr_curve_artifact(` / `context.artifact_dir / ("pr-curve-%s.png" % run_name),` / `mlflow_module.log_artifact(str(pr_curve_path), artifact_path="charts")` / `importance = feature_importance_frame(model, valid_frame[feature_cols], valid_frame[fleet_ml_core.LABEL], feature_cols)` / `importance.to_csv(importance_path, index=False, lineterminator="\n")` / `mlflow_module.log_artifact(str(importance_path), artifact_path="importance")`
  - `notebooks\nb_05_train_mlflow.py:87-94` — `signature = infer_signature(train_frame[feature_cols].head(5), wrapped.predict(train_frame[feature_cols].head(5)))` / `mlflow_module.sklearn.log_model(` / `sk_model=wrapped,` / `artifact_path="model",` / `signature=signature,` / `input_example=train_frame[feature_cols].head(5),` / `code_paths=notebook_source_paths(),`
  - `notebooks\nb_05_train_mlflow.py:126-131` — `candidate_specs = [` / `("prevalence", list(fleet_ml_core.FEATURES)),` / `("rule_baseline", list(fleet_ml_core.FEATURES)),` / `("logistic_regression", list(fleet_ml_core.FEATURES)),` / `("hist_gradient_boosting", list(fleet_ml_core.FEATURES)),` / `("hist_gradient_boosting_no_fault_codes", list(fleet_ml_core.NO_FAULT_FEATURES)),`
  - `notebooks\nb_05_train_mlflow.py:152-170` — `best_name = max(comparable, key=lambda name: comparable[name]["metrics"]["valid"]["pr_auc"])` / `registered = mlflow.register_model(model_uri="runs:/%s/model" % best_run_id, name=params["model_name"])` / `client.set_model_version_tag(params["model_name"], registered.version, "candidate_status", "pending_gate")` / `client.set_model_version_tag(params["model_name"], registered.version, "selected_by", "valid_pr_auc")` / `client.set_model_version_tag(params["model_name"], registered.version, "candidate_kind", best_name)` / `client.set_model_version_tag(params["model_name"], registered.version, "source_run_id", best_run_id)` / `comparison.to_csv(comparison_path, index=False, lineterminator="\n")` / `mlflow.log_artifact(str(comparison_path), artifact_path="comparison")`
  - `notebooks\nb_05_train_mlflow.py:174-180` — `if params["bootstrap_pointer_if_missing"] and pointer_before[pointer_before["model_name"] == params["model_name"]].empty:` / `upsert_model_pointer(` / `champion_version=str(registered.version),` / `note="Bootstrapped because no champion pointer existed yet.",` / `updated_by="nb_05_train_mlflow",`
- MLflow facts:
  - Experiment name = `fleet-failure-7d`
  - Parent run name = `nb_05_train_mlflow`
  - Child run names = `prevalence`, `rule_baseline`, `logistic_regression`, `hist_gradient_boosting`, `hist_gradient_boosting_no_fault_codes`
  - Logged params:
    - for rule baseline: `baseline=rule`, `rule_definition=crit_cnt_7d > 0 or warn_cnt_7d >= 2`
    - for trained models: `estimator_kind`, `feature_subset`, `feature_count`
    - parent run: `registered_candidate`, `registered_version`
  - Logged metrics on trained candidates = `valid_pr_auc`, `valid_roc_auc`, `test_pr_auc`, `test_roc_auc`, `test_precision_at_top5pct`, `test_recall_at_top5pct`
  - Logged tags:
    - child run tags: `candidate_kind`, `feature_count`, `tracked_metrics`
    - parent run tags: `demo_notebook=nb_05_train_mlflow`, `registered_model_name`, `registered_model_version`
    - registered model version tags: `candidate_status=pending_gate`, `selected_by=valid_pr_auc`, `candidate_kind`, `source_run_id`
  - Logged artifacts:
    - `rule-baseline-metrics.json`
    - `charts/pr-curve-<candidate>.png`
    - `importance/importance-<candidate>.csv`
    - `comparison/run-comparison.csv`
  - Signature + input example: yes, via `infer_signature(...)` and `input_example=train_frame[feature_cols].head(5)`
  - Registration:
    - model name = `fleet-failure-7d`
    - code path = `mlflow.register_model(model_uri="runs:/%s/model" % best_run_id, name=params["model_name"])`
    - Fabric model item fact: versions only; no stages, no aliases in the workshop pattern
- Leaderboard from `ground_truth.json` (say "about"; tolerance +/-0.03 on test PR-AUC):

| Candidate | valid PR-AUC | test PR-AUC |
|---|---:|---:|
| HistGradientBoosting | about 0.336 | about 0.385 |
| HGB without fault-code features | about 0.323 | about 0.284 |
| Logistic regression | about 0.292 | about 0.292 |
| Rule baseline | about 0.064 | about 0.068 |
| Prevalence | about 0.054 | about 0.045 |

- Timing to speak to: 8 minutes live, 4 minutes short path

## Notebook: `nb_06_register_score`
- Purpose: load the chosen registered model version, score the `score` split, optionally show `MLFlowTransformer`, and write `ml.failure_risk_score`.
- Important code lines (verbatim):
  - `notebooks\nb_06_register_score.py:48-64` — `def score_with_mlflow_transformer(context, score_frame, model_name: str, model_version: str) -> dict:` / `from synapse.ml.predict import MLFlowTransformer` / `transformer = MLFlowTransformer(` / `inputCols=list(fleet_ml_core.FEATURES),` / `outputCol="risk_score",` / `modelName=model_name,` / `modelVersion=int(model_version),` / `transformed = transformer.transform(spark_input).toPandas()`
  - `notebooks\nb_06_register_score.py:73-79` — `features = context.read_table(params["features_table"])` / `dim_asset = context.read_table(params["asset_table"])` / `pointer = read_model_pointer(context, table_name=params["pointer_table"])` / `model_version = resolve_model_version(client, params["model_name"], params["model_version"], pointer)` / `model_uri = "models:/%s/%s" % (params["model_name"], model_version)` / `scoring_model = load_sklearn_model(model_uri)`
  - `notebooks\nb_06_register_score.py:80-85` — `score_frame = fleet_ml_core.get_split(features, "score").copy()` / `pyfunc_scores = load_pyfunc_scores(model_uri, score_frame[fleet_ml_core.FEATURES])` / `sklearn_scores = scoring_model.predict_proba(score_frame[fleet_ml_core.FEATURES])[:, 1]` / `score_frame["risk_score"] = pyfunc_scores.round(4)` / `score_frame["risk_band"] = [fleet_ml_core.risk_band(score) for score in score_frame["risk_score"]]` / `score_frame["top_drivers"] = fleet_ml_core.reason_codes(score_frame)`
  - `notebooks\nb_06_register_score.py:86-99` — `result_table = score_frame.merge(` / `dim_asset[["erp_asset_id", "site_code", "equipment_class"]].drop_duplicates(),` / `result_table = result_table.rename(columns={"obs_date": "score_date"})` / `result_table["model_version"] = str(model_version)` / `result_table = result_table.sort_values(["risk_score", "erp_asset_id"], ascending=[False, True], kind="stable").reset_index(drop=True)` / `result_table["risk_rank"] = np.arange(1, len(result_table) + 1)` / `context.write_table(params["output_table"], result_table)`
  - `notebooks\nb_06_register_score.py:101-118` — `"bands": {str(k): int(v) for k, v in result_table["risk_band"].value_counts().sort_index().items()}` / `"pyfunc_vs_sklearn_max_abs_diff": round(float(np.max(np.abs(pyfunc_scores - sklearn_scores))), 8)` / `reference = context.read_reference(params["reference_scores_name"])` / `reason_code_match = int((merged["top_drivers_actual"] == merged["top_drivers_expected"]).sum())` / `band_match = int((merged["risk_band_actual"] == merged["risk_band_expected"]).sum())`
  - `notebooks\shared\fleet_ml_core.py:111-124` — `def risk_band(score: float) -> str:` / `return "High" if score >= HIGH_RISK else "Medium" if score >= MEDIUM_RISK else "Low"` / `rules = [("CRIT_FAULT_7D", s["crit_cnt_7d"] >= 1), ("REPEATED_WARNINGS", s["warn_cnt_7d"] >= 3), ("ENGINE_TEMP_RISING", s["temp_trend"] >= 3.0),` / `("OIL_PRESSURE_FALLING", s["oil_trend"] <= -10.0), ("HYDRAULIC_PRESSURE_FALLING", s["hyd_trend"] <= -8.0),` / `("VIBRATION_RISING", s["vib_trend"] >= 0.3), ("PM_OVERDUE", s["days_since_last_pm"] >= 90)]`
- Scoring snippet to quote:
  ```python
  transformer = MLFlowTransformer(
      inputCols=list(fleet_ml_core.FEATURES),
      outputCol="risk_score",
      modelName=model_name,
      modelVersion=int(model_version),
  )
  spark_input = context.spark.createDataFrame(score_frame[["erp_asset_id", "obs_date", *fleet_ml_core.FEATURES]])
  transformed = transformer.transform(spark_input).toPandas()
  ```
- Table written:
  - table name = `ml.failure_risk_score`
  - columns = `score_date, erp_asset_id, site_code, equipment_class, risk_score, risk_band, risk_rank, top_drivers, model_version`
  - rows scored = 264
  - risk bands = about 9 High / 7 Medium on a live run; exact Medium/Low split depends on library versions and can shift one asset between bands (local runs on the Runtime 1.3 package set -- scikit-learn 1.2.2, pandas 2.1.4 -- and on a Runtime-2.0-like set -- scikit-learn 1.6.1, pandas 2.2 -- both gave 9 High / 8 Medium / 247 Low) -- the frozen reference file used for Part 4 is High 9 / Medium 7 / Low 248 exactly. Do not assert exact band counts in the live notebook.
- Timing to speak to: 5 minutes live, 3 minutes short path

## Notebook: `nb_07_drift_monitor`
- Purpose: compare September RUN telemetry with the October drift batch using PSI, write `ml.drift_report`, and return machine-readable alert status.
- Important code lines (verbatim):
  - `notebooks\nb_07_drift_monitor.py:44-50` — `reference = telemetry[(telemetry["is_run"]) & (telemetry["erp_asset_id"].notna()) & (telemetry["day"] >= to_day(params["reference_start"]))].copy()` / `current = new_batch[(new_batch["is_run"]) & (new_batch["erp_asset_id"].notna())].copy()` / `reference = reference.merge(dim_asset, on="erp_asset_id", how="left")` / `current = current.merge(dim_asset, on="erp_asset_id", how="left")` / `report = psi_table(reference, current)` / `context.write_table(params["output_table"], report)`
  - `notebooks\nb_07_drift_monitor.py:52-59` — `major, expected_moderate = major_shift_summary(report)` / `"status": "alert" if major else "ok",` / `"major_shift_count": int((report["status"] == "major").sum()),` / `"moderate_shift_count": int((report["status"] == "moderate").sum()),` / `"major_shifts": major,` / `"expected_moderate_shifts": expected_moderate,`
  - `notebooks\nb_07_drift_monitor.py:61-68` — `reference_report = context.read_reference(params["reference_report_name"])` / `summary["reference_comparison"] = compare_frames_with_tolerance(` / `key_cols=["equipment_class", "sensor"],` / `numeric_cols=["psi", "ref_mean", "new_mean", "ref_rows", "new_rows"],` / `tolerance=1e-6,`
  - `notebooks\nb_07_drift_monitor.py:70-71` — `if params["emit_notebook_exit"]:` / `context.notebook_exit(summary)`
  - `notebooks\shared\fleet_ml_core.py:141-152` — `def psi(ref, cur, bins: int = 10) -> float:` / `"""Population Stability Index vs the reference deciles: < 0.10 stable, 0.10-0.25 moderate shift, > 0.25 major shift."""` / `edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))` / `r, c = (np.clip(np.histogram(x, edges)[0] / len(x), 1e-4, None) for x in (ref, cur))` / `return float(np.sum((c - r) * np.log(c / r)))` / `def psi_status(v: float) -> str:` / `return "major" if v > 0.25 else "moderate" if v > 0.10 else "stable"`
- Exact drift thresholds as coded:
  - stable: `< 0.10`
  - moderate: `> 0.10` and `<= 0.25`
  - major: `> 0.25`
- Drift results from `ground_truth.json` / `drift_report.csv`:
  - 47 class x sensor combinations total
  - 4 major = Excavator `engine_temp_c` 0.8804, Excavator `vibration_mm_s` 3.7113, WheelLoader `engine_temp_c` 0.9587, WheelLoader `vibration_mm_s` 2.7825
  - 3 moderate = Compactor `engine_temp_c` 0.1097, MobileCrane `engine_temp_c` 0.1033, Paver `engine_temp_c` 0.1862
  - 40 stable
- Timing to speak to: 4 minutes live, 3 minutes short path

## Notebook: `nb_08_promotion_gate`
- Purpose: compare champion and challenger on their already-logged holdout metrics and decide whether to update the champion pointer. **Fixed during Round 2 (G11): this notebook no longer loads or scores any model** — an earlier version re-loaded the registered (refit-on-everything) model and re-scored it on the "test" split, which was in-sample and produced an inflated PR-AUC of about 0.96. See "What changed" below.
- Important code lines (verbatim, current file):
  - `notebooks\\nb_08_promotion_gate.py:44-46` — `# We only promote when test PR-AUC improves by at least 0.01 and precision in the top 5% does not get worse by more than 0.02.`
  - `notebooks\\notebook_common.py` (`gate_decision`, unchanged by G11) — `def gate_decision(` / `min_pr_auc_gain: float = 0.01,` / `max_precision_drop: float = 0.02,` / `pr_auc_gain = float(challenger["test_pr_auc"] - champion["test_pr_auc"])` / `precision_drop = float(champion["test_precision_at_top5pct"] - challenger["test_precision_at_top5pct"])` / `passed_pr = challenger["test_pr_auc"] >= champion["test_pr_auc"] + min_pr_auc_gain` / `passed_precision = challenger["test_precision_at_top5pct"] >= champion["test_precision_at_top5pct"] - max_precision_drop` / `decision = "promote" if (passed_pr and passed_precision) else "hold"`
  - `notebooks\\notebook_common.py` (`get_holdout_metrics`, new in G11) — `details = client.get_model_version(model_name, version)` / `run_id = details.run_id` / `metrics = client.get_run(run_id).data.metrics` / reads `test_pr_auc` / `test_precision_at_top5pct` (and the other `METRIC_KEYS`) off the SOURCE run already logged by `nb_05_train_mlflow`, **before** the registered artifact is refit on every split. No model is loaded.
  - `notebooks\\nb_08_promotion_gate.py` (`run`) — `champion_metrics = get_holdout_metrics(client, params["model_name"], str(champion_version))` / `challenger_metrics = get_holdout_metrics(client, params["model_name"], str(challenger_version))` / `decision = gate_decision(champion_metrics, challenger_metrics)` / `decision.update({..., "metrics_source": "logged holdout metrics of the source run; model fit on train splits only"})`
  - `notebooks\\nb_08_promotion_gate.py` (`run`, bootstrap/apply-pointer paths unchanged) — `if params["apply_pointer_update"]:` / `upsert_model_pointer(` / `model_name=params["model_name"],` / `champion_version=str(challenger_version),` / `note="Bootstrap champion because none existed yet.",`
  - `notebooks\\notebook_common.py:306-340` — `def model_pointer_schema() -> list[str]:` / `return ["model_name", "champion_version", "updated_at_utc", "updated_by", "note"]` / `def upsert_model_pointer(` / `"model_name": model_name,` / `"champion_version": str(champion_version),` / `"updated_at_utc": utc_now(),` / `"updated_by": updated_by,` / `"note": note,`
- Exact gate rule to quote on slides:
  ```python
  min_pr_auc_gain: float = 0.01,
  max_precision_drop: float = 0.02,
  passed_pr = challenger["test_pr_auc"] >= champion["test_pr_auc"] + min_pr_auc_gain
  passed_precision = challenger["test_precision_at_top5pct"] >= champion["test_precision_at_top5pct"] - max_precision_drop
  decision = "promote" if (passed_pr and passed_precision) else "hold"
  ```
- What changed (G11, real correctness fix): the gate used to re-load the registered (refit-on-everything) model and re-score it on the "test" split — because that artifact was itself fit on the test rows, this was in-sample and produced PR-AUC about **0.96**, not a generalization number. The fix reads the honest `test_pr_auc`/`test_precision_at_top5pct` already logged by `nb_05_train_mlflow` on each model version's SOURCE run (before the final refit). Slide-ready sentence: **"The gate does not re-score any model — it compares the honest holdout metrics each candidate already logged during training, because the shipped model artifact is refit on every labelled split and re-scoring it on 'test' would be in-sample."**
- Timing to speak to: 4 minutes live, 3 minutes short path
## Shared ML-core facts for speaking
- `notebooks\shared\fleet_ml_core.py:18-33`
  - label = `fail_next_7d`
  - model kinds = `("prevalence", "logistic_regression", "hist_gradient_boosting")`
  - HGB params = `max_iter=300, learning_rate=0.06, max_leaf_nodes=24, l2_regularization=1.0, early_stopping=False, random_state=0`
  - logistic regression params = `C=0.5, max_iter=2000`
  - thresholds = `HIGH_RISK, MEDIUM_RISK = 0.30, 0.10`
  - final refit splits = `("train", "gap", "valid", "test")`
- `notebooks\shared\fleet_ml_core.py:79-81`
  - exact rule baseline code = `return ((d["crit_cnt_7d"] > 0) | (d["warn_cnt_7d"] >= 2)).astype(float).to_numpy()`

## Fabric UI places worth showing
- Experiment item run comparison — VERIFIED in Learn/fact sheet
- Experiment run artifacts (`comparison/run-comparison.csv`, PR-curve PNGs, importance CSVs) — VERIFIED
- ML model item version list and version tags — VERIFIED
- Apply this version wizard / generated `PREDICT` code path — VERIFIED
- Lakehouse tables for `ml.asset_day_features`, `ml.failure_risk_score`, `ml.drift_report`, `ml.model_pointer` — VERIFIED
- Pipeline canvas for `pl_fleet_daily` notebook chain — VERIFIED as Fabric pipeline capability; exact final labels depend on authored item
- Monitor hub for experiment visibility — ⚠ PREVIEW / exact hub wording not yet confirmed in this folder

## `pl_fleet_daily` structure
- Location: `fabric-git\pl_fleet_daily.DataPipeline\pipeline-content.json`
- Activity chain:
  1. `RunBronzeIngest` → `nb_01_bronze_ingest` ⚠ owned by ETL finisher
  2. `RunSilverCleanResolve` → `nb_02_silver_clean_resolve` ⚠ owned by ETL finisher
  3. `RunGoldReconcile` → `nb_03_gold_reconcile` ⚠ owned by ETL finisher
  4. `RunFeatures` → `nb_04_features`
  5. `RunTrainMlflow` → `nb_05_train_mlflow`
  6. `RunRegisterScore` → `nb_06_register_score`
  7. `RunDriftMonitor` → `nb_07_drift_monitor`
  8. `RunPromotionGate` → `nb_08_promotion_gate`
  9. `IfDriftAlert` → `SendDriftAlertEmail` on major drift only
- Every `TridentNotebook` activity (steps 1-8) has a dedicated `NotifyXFailure` Office365Email branch on `Failed`: `NotifyFeaturesFailure`, `NotifyTrainFailure`, `NotifyScoreFailure`, `NotifyDriftNotebookFailure`, `NotifyGateFailure` (the three ETL notebooks are owned by the ETL finisher and are not re-documented here).
- Notebook activity type = `TridentNotebook`
- Retry policy on notebook activities = `retry: 1`, `retryIntervalInSeconds: 60`
- Failure-notify activities present = `NotifyFeaturesFailure`, `NotifyTrainFailure`, `NotifyScoreFailure`, `NotifyDriftNotebookFailure`, `NotifyGateFailure`
- `IfDriftAlert` expression: `@equals(json(activity('RunDriftMonitor').output.result.exitValue).status, 'alert')`. ⚠ UNVERIFIED: `output.result.exitValue` is the community-documented path to a notebook activity's exit value; it is NOT on the Fabric Learn Notebook-activity page as of this writing. VERIFY on first live run: open the `RunDriftMonitor` activity's Output JSON in the Monitor hub and confirm `result.exitValue` exists with a parsed `status` field.
- `RunPromotionGate` passes no `typeProperties.parameters`, so the pipeline always runs `nb_08_promotion_gate` with its default `apply_pointer_update = False` — **the pipeline computes a promotion decision every day but never moves `ml.model_pointer` on its own.** One slide-ready sentence: "the pipeline always scores with the current champion, then asks the gate whether today's challenger should become tomorrow's champion — but a human applies that decision by re-running the gate notebook with `apply_pointer_update = True`." `nb_08` now also returns its decision via `context.notebook_exit(decision)`, so the full decision JSON is visible as the `RunPromotionGate` activity's exit value in the Monitor hub, the same pattern `nb_07`'s drift payload already uses.

## Variable Library (`fleet_mlops`) — what is actually consumed
- One Fabric Variable Library item (`fleet_mlops`) is deployed with DEV/TEST/PROD value sets. It is **not** a general settings store that every notebook reads: per-environment IDs that genuinely differ by environment (workspace ID, lakehouse ID, Office 365 connection ID, alert recipients) are handled by `cicd\parameter.yml` find/replace at deploy time, same as the ETL demo. Notebook/pipeline IDs are NOT in `parameter.yml`: every `TridentNotebook` activity already carries the real `notebookId` (the target notebook's own `.platform` `config.logicalId`) with a zero-GUID `workspaceId`, and `fabric-cicd` resolves logicalId -> real item ID natively during Git sync/deploy -- the same pattern the public sample uses.
- The only thing the kit's code actually reads from the Variable Library is `nb_07_drift_monitor`'s two PSI thresholds: `driftModerateThreshold` (default 0.10) and `driftMajorThreshold` (default 0.25), via a new `get_env_setting(name, default, library="fleet_mlops")` helper in `notebook_common.py`. In Fabric it calls `notebookutils.variableLibrary.getLibrary("fleet_mlops")` then reads the named attribute; any failure (wrong name, library not deployed) falls back to the hardcoded default. `nb_07` prints `thresholds source: variable library | default` so a presenter can see live which one was used — this local validation run printed `thresholds source: default` (no library present locally) and reproduced the exact same 47/4/3/40 drift counts, confirming the default path is unchanged.
- Everything else the library stores (`experimentName`, `modelName`, `scoreTable`, `driftTable`, `workspaceId`, `lakehouseFleet`, `office365ConnectionId`, `alertTo`) is **not read by any notebook or pipeline activity today** — it exists for future wiring and/or as a native-feature teaching example. The pipeline's own native alternative for its own parameters is the Library variables tab (`@pipeline().libraryVariables.<ref>`), documented as an optional rebuild-guide exercise, not used by the shipped `pipeline-content.json`.
- VERIFY: check that the live `nb_07` run prints `thresholds source: variable library`; if it prints `default` instead, check the library name (`fleet_mlops`) and variable names (`driftModerateThreshold`/`driftMajorThreshold`, case-sensitive) and the active value set.

## CI/CD assets in one paragraph
- `cicd\deploy.py` uses the current documented `fabric-cicd` `deploy_with_config(...)` pattern with `AzureCliCredential()` after `azure/login@v2`; `cicd\config.yml` scopes deployment to `Notebook`, `DataPipeline`, and `VariableLibrary` items under `fabric-git\`; `cicd\parameter.yml` replaces workspace IDs, lakehouse ID, Office 365 connection ID, and alert recipients for `DEV`, `TEST`, and `PROD` (notebook/pipeline IDs are resolved natively by `fabric-cicd` from each item's own `.platform` logicalId, so they are not in this file); `cicd\github-workflows\fabric-mlops-deploy.yml` runs lint/validation first, then sequential dev/test/prod deployments with GitHub environment approvals; the honest promotion story stays the same: Git/deployment paths move ML experiment/model metadata only, so model versions are retrained or re-logged per workspace and the champion is chosen by `nb_08_promotion_gate`.

## Timing summary
- Full 30-minute path: features 4 / train and track 8 / register and score 5 / pipeline 5 / drift 4 / CI/CD 4
- Short 18-minute path: features 2 / train and track 5 / register and score 3 / pipeline 3 / drift 3 / CI/CD 2
