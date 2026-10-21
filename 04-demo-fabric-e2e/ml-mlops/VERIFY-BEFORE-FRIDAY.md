# Verify before Friday

## D-5 to D-0 checklist

| Day | Check |
|---|---|
| D-5 | Confirm the workspace is pinned to Fabric Runtime 1.3 (see "Runtime pin" below), then import the five notebooks, variable library, and `pl_fleet_daily` into it. |
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

## Runtime pin

Pin the workspace to Fabric Runtime 1.3 (Spark 3.5, Python 3.11). This kit was rehearsed on that package set [the ML notebooks ran end to end on the Runtime 1.3 Python libraries (pandas 2.1.4, numpy 1.26.4, scikit-learn 1.2.2, pyarrow 14.0.2, mlflow-skinny 2.12.2) and reproduced the contract: counts exact, metrics within the +/-0.03 tolerance; this was a local Python plus simulated-Fabric run, not a Fabric tenant]. Runtime 2.0 (Spark 4.1, Python 3.13) is the newer runtime; the Python/ML code was also run on a Runtime-2.0-like package set, but the ETL notebooks were not rehearsed on Spark 4.1, so pin 1.3 for the whole demo workspace. Set it in the workspace Spark settings (see the ETL guide, `..\etl\rebuild-guide.md` section 3).

- Lifecycle (Microsoft Learn, lifecycle page, read 2026-10-21): Runtime 1.3 is in the end-of-support-announced (EOSA) stage. Its support ended on 2026-09-30; Long Term Support (LTS) runs from 2026-10-01 for six months (through March 2027). Runtime 2.0 (Spark 4.1) is generally available, and a new workspace may default to it, so pin 1.3 explicitly before importing anything. Do not present Runtime 1.3 as the newest runtime on a slide.
- ⚠ UNVERIFIED: that Runtime 1.3 can still be selected in the target tenant on the day. Check it on Thursday (see `..\etl\VERIFY-BEFORE-FRIDAY.md`). If it cannot be selected, use Runtime 2.0 for the whole workspace and rehearse the full chain once: the ML code ran on a Runtime-2.0-like package set (scikit-learn 1.6.1, MLflow 2.22.0), the ETL notebooks never ran on Spark 4.1.
- ⚠ UNVERIFIED: the optional Spark scoring path in `nb_06` (`synapse.ml.predict` / `MLFlowTransformer`) on the chosen runtime. The live notebook path is pandas; nothing local exercised the Spark path.
- Capacity: a Trial capacity runs the notebooks and pipelines; only the Part 4 data agent (and Copilot / AI functions) needs a paid F2+ capacity (same wording as `..\etl\rebuild-guide.md` section 2).

## Settings to confirm

- Workspace role = Contributor or above for the presenter
- Workspace pinned to Fabric Runtime 1.3 (see "Runtime pin" below); `print(spark.version)` in a notebook shows `3.5.x`
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
