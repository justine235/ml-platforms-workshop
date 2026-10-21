# Run of show — Fabric ML + MLOps

## Pre-flight (before the audience arrives, ideally the day before)

1. Runtime: Pin the workspace to Fabric Runtime 1.3 (Spark 3.5, Python 3.11). This kit was rehearsed on that package set [the ML notebooks ran end to end on the Runtime 1.3 Python libraries (pandas 2.1.4, numpy 1.26.4, scikit-learn 1.2.2, pyarrow 14.0.2, mlflow-skinny 2.12.2) and reproduced the contract: counts exact, metrics within the +/-0.03 tolerance; this was a local Python plus simulated-Fabric run, not a Fabric tenant]. Runtime 2.0 (Spark 4.1, Python 3.13) is the newer runtime; the Python/ML code was also run on a Runtime-2.0-like package set, but the ETL notebooks were not rehearsed on Spark 4.1, so pin 1.3 for the whole demo workspace. Set it in the workspace Spark settings (see the ETL guide, `..\etl\rebuild-guide.md` section 3).
2. Default lakehouse: `lh_fleet` is attached as the DEFAULT lakehouse of all five ML notebooks, and each session was restarted after attaching it.
3. Shared code: the `notebooks\` folder (`__init__.py`, `notebook_common.py`, `shared\*.py`) is uploaded to `lh_fleet`'s `Files/code/notebooks/...` (`rebuild-guide.md` section 1, item 4a).
4. Inputs: the ETL tables exist (`silver.telemetry`, `silver.telemetry_drift`, `gold.*`, `bronze.fault_code_catalog`). If they do not, use the break-glass path (`README.md`, Prerequisites).

## 30-minute live path

| Min | Step | On screen | What to click / run | What to say | Checkpoint | Fallback |
|---:|---|---|---|---|---|---|
| 00:00-00:45 | Set context | Lakehouse item + notebook list | Open `lh_fleet`, then `nb_04_features` | “The ETL half already produced reconciled daily tables. This half starts where data engineering hands off to ML.” | CP0 | Open `gold.fact_telemetry_daily` preview if notebook list is slow. |
| 00:45-04:30 | Features | `nb_04_features` | Show parameters, run the notebook, then open `ml.asset_day_features` | “We build one feature row per asset-day. Same logic as the laptop reference pipeline; only the storage engine changes.” “The acceptance numbers are fixed: 50,876 rows, 49,028 labelled, 264 score rows.” | CP1 | Open the already-written `ml.asset_day_features` table and point to `split` counts. |
| 04:30-05:15 | Explain leakage guardrail | Same notebook output / table preview | Point to `split` column values | “These splits are precomputed and purged. We never random-split this dataset because that would leak future maintenance signals.” | CP1 | Open `mlops-facts-for-slides.md` section for splits. |
| 05:15-12:45 | Train and track | `nb_05_train_mlflow`, then Experiment item | Run notebook, then click through to Experiment item and run comparison | “We deliberately keep the model family small and put the time on tracking.” “Five child runs: prevalence, rules, logistic regression, HGB, and HGB without fault-code features.” “The winner is chosen by validation PR-AUC, then registered.” | CP2 | Open existing Experiment item or the run-comparison artifact if notebook execution is slow. |
| 12:45-13:30 | Narrate leaderboard | Experiment comparison UI | Sort by validation PR-AUC / show metrics | “About 0.336 valid PR-AUC and about 0.385 test PR-AUC (+/-0.03) for HGB is the expected shape. This is useful-but-modest signal, not magic.” | CP2 | Open `mlops-facts-for-slides.md` leaderboard table. |
| 13:30-18:15 | Register and score | `nb_06_register_score`, then `ml.failure_risk_score` table | Run notebook; show pointer resolution and model version; preview score table | “Fabric model items are versioned, not staged. We keep the active champion in a small pointer table.” “Scoring writes an operational table for Power BI and downstream consumers.” | CP3 | Open `ml.failure_risk_score` table directly and sort by `risk_rank`. |
| 18:15-19:15 | Show Spark scoring path | Same notebook cell | Highlight `MLFlowTransformer` snippet, do not rerun if time is tight | “The live notebook path is pandas plus the registered model. The Fabric-native Spark path uses MLFlowTransformer, and `PREDICT` needs the model signature.” | CP3 | Open the code cell only; no execution needed. |
| 19:15-23:00 | Drift monitoring | `nb_07_drift_monitor`, then `ml.drift_report` | Run notebook; show JSON exit summary and drift table | “October labels do not exist yet, so we monitor inputs, not accuracy.” “PSI flags four major shifts and three expected moderate temperature shifts.” | CP4 | Open `ml.drift_report` and filter to `status = major`. |
| 23:00-24:00 | Alert meaning | Drift output | Point to major rows and expected moderate rows | “This is the honest part: not every alert is bad. Paver, Compactor, and MobileCrane temperature drift is seasonal cooling, not a broken process.” | CP4 | Open `ground_truth.json` drift section in `mlops-facts-for-slides.md`. |
| 24:00-27:30 | Promotion gate | `nb_08_promotion_gate` | Show gate notebook and rule cell; run if needed with existing versions | “Promotion is small and explicit: PR-AUC must improve by 0.01, and precision at the top 5% must not drop by more than 0.02.” “It always computes the decision, but the pipeline runs it report-only by default -- we apply a promotion with a deliberate re-run (`apply_pointer_update = True`), we do not pretend Fabric gives us model stages here.” | CP5 | Open notebook and read the rule cell without executing. |
| 27:30-29:00 | Pipeline | Pipeline canvas / authored JSON if UI unavailable | Open `pl_fleet_daily` once authored; show notebook chain, gate step, and alert branch | “One scheduled path: ETL, features, train, score, drift, gate, then alert on condition. Notebook exits are machine-readable so the pipeline can branch, and every notebook step has its own failure-notify email.” | CP6 | Open `mlops-facts-for-slides.md` authored pipeline structure. |
| 29:00-30:00 | CI/CD close | `cicd\README.md` or diagram once authored | Point to dev/test/prod story | “Git integration for Fabric ML artifacts is metadata-only in preview, so we promote code and retrain or re-log in each workspace. The gate decides the champion, not Git copy.” | CP7 | Use the one-paragraph CI/CD summary from `mlops-facts-for-slides.md`. |

## 18-minute short path

| Min | Step | On screen | What to click / run | What to say | Checkpoint | Fallback |
|---:|---|---|---|---|---|---|
| 00:00-02:00 | Features | `nb_04_features` + `ml.asset_day_features` | Show notebook result or prebuilt table | “Same feature logic as the reference pipeline. Fixed split contract, 50,876 rows, 264 assets to score.” | CP1 | Open prebuilt table. |
| 02:00-07:00 | Train + compare | `nb_05_train_mlflow` + Experiment item | Open completed run comparison | “Five candidates under one parent run. HGB is best at about 0.336 valid PR-AUC and about 0.385 test PR-AUC (+/-0.03).” | CP2 | Open run-comparison artifact CSV. |
| 07:00-10:00 | Register + score | `nb_06_register_score` + `ml.failure_risk_score` | Show model version and output table | “Model versions only, plus a pointer table for the champion. Scoring writes the operational risk table. Bands are about 9 High and 7 Medium — exact Medium/Low split depends on library versions; the frozen file used for Part 4 has 9/7/248.” | CP3 | Open score table preview. |
| 10:00-13:00 | Drift | `nb_07_drift_monitor` + drift table | Show major shifts only | “No October labels yet, so we watch inputs. Four major PSI shifts: Excavator and WheelLoader, temperature and vibration.” | CP4 | Open drift table filtered to major. |
| 13:00-15:00 | Gate | `nb_08_promotion_gate` | Show rule cell | “Promote only if PR-AUC gains at least 0.01 and top-5% precision does not lose more than 0.02.” | CP5 | Read from notebook cell or facts file. |
| 15:00-18:00 | Pipeline + CI/CD | Pipeline canvas / CI/CD docs | Show structure only | “Daily orchestration is notebooks, the gate, then the alert branch. CI/CD moves code and metadata; models are retrained or re-logged per workspace.” | CP6-CP7 | Use facts file bullet list. |

## Checkpoints to keep pre-opened

| Checkpoint | Keep ready |
|---|---|
| CP0 | `lh_fleet` lakehouse with `gold.*` tables visible |
| CP1 | `ml.asset_day_features` already populated |
| CP2 | Experiment item with one completed training run and comparison artifact |
| CP3 | `ml.failure_risk_score` table preview |
| CP4 | `ml.drift_report` table preview |
| CP5 | `nb_08_promotion_gate` open on the rule cell |
| CP6 | `pl_fleet_daily` pipeline canvas or authored JSON |
| CP7 | CI/CD summary doc and workflow file |
