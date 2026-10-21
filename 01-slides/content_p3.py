"""Part 3 (Fabric half): P3.0-P3.14 -- intro plus ETL, ML and MLOps on Microsoft Fabric."""
from __future__ import annotations

from deck_lib import Deck
from facts import F, d2, d3, n, pct

FABRIC_SRC = "Microsoft Learn: Fabric data science docs, verified 2026-10-18"
FABRIC_URLS = [
    "https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging",
    "https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model",
    "https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict",
    "https://learn.microsoft.com/en-us/fabric/cicd/manage-deployment",
    "https://learn.microsoft.com/en-us/fabric/cicd/variable-library/overview-variable-library",
]


def build(d: Deck) -> None:
    d.section(
        "P3.0", 3, "Part 3: One use case, end to end, twice",
        "Fabric first, then Azure Machine Learning: same data, same rules, two operating models.",
        ["Walk raw files to a scored, monitored model", "See where Fabric and Azure ML each do the work",
         "Keep every number traceable to the contract"],
        ("13:20 \u2013 15:15", "115 min: Fabric 55, AML 45, bridge 15"),
        minutes=1,
        notes="""Part 3 is a guided rebuild, not a slide deck about architecture.

We take the Contoso Fleet scenario from raw files to a scored and monitored model, twice: once on Microsoft Fabric, once on Azure Machine Learning. This first half is Fabric only, about 55 minutes including the live demo.

The goal is not to declare a winner. It is to show the same business logic running on two different operating models, so you can judge which one fits your team.

TRANSITION: Let me show the whole path on one picture before we touch any tool.""")

    d.arch(
        "P3.1", "What we will build: files to a scored, monitored model",
        [dict(id="src", label="Raw files", sub="3 sources", icon="database", col=0, row=1, tone="amber"),
         dict(id="bronze", label="Bronze", sub="Land as-is", icon="lakehouse", col=1, row=1, tone="node"),
         dict(id="silver", label="Silver", sub="Resolve identity", icon="workflow", col=2, row=1, tone="node"),
         dict(id="gold", label="Gold", sub="Match faults, WOs", icon="table", col=3, row=1, tone="node"),
         dict(id="feat", label="ML features", sub="42 cols, purged", icon="flask-conical", col=4, row=0, tone="azure"),
         dict(id="model", label="Model", sub="Train, gate, register", icon="experiment", col=5, row=0, tone="azure"),
         dict(id="score", label="Scores", sub="Risk band per asset", icon="ml-model", col=6, row=0, tone="azure"),
         dict(id="ops", label="Pipeline", sub="Schedule, drift, CI/CD", icon="repeat", col=5, row=2, tone="success", h=1.5)],
        edges=[("src", "bronze"), ("bronze", "silver"), ("silver", "gold"), ("gold", "feat"), ("feat", "model"),
               ("model", "score"), ("score", "ops", "monitor"), ("ops", "model", "retrain")],
        groups=[dict(label="ETL (medallion)", c0=1, r0=1, c1=3, r1=1, tone="node"),
                dict(label="ML and MLOps", c0=4, r0=0, c1=6, r1=2, tone="azure")],
        minutes=3,
        gap=(0.3, 0.4), node_title=12.5, node_sub=11,
        notes="""This is the canvas for the next 55 minutes. Every slide that follows is one box or one arrow on this picture.

The left half is the medallion: bronze lands the raw files untouched, silver cleans and resolves identity, gold reconciles faults against work orders. That is classic Fabric lakehouse engineering, and it is also the foundation Azure Machine Learning will reuse this afternoon.

The right half is the ML loop: build features, train and track candidates, gate a challenger against the champion, register and score, then monitor drift and retrain. The loop closes through the pipeline and the drift alert, which can trigger the next training run.

I will follow this picture left to right, live, in Fabric notebooks. Keep this slide in mind: when I show a table or a number, I will say which box we are in.

TRANSITION: Before any code, let's look at why this data needs cleaning at all.""")

    d.table_slide(
        "P3.2", "The same machine, three spellings",
        ["System", "Field", "Example for one machine", "Format"],
        [["ERP (golden key)", "`erp_asset_id`", "`EQ-00143`", "CSV, clean key"],
         ["Telematics", "`asset_ref`", "`eq00143`, `EQ_00143`, `EQ-143`", "JSON lines, installer-typed"],
         ["CMMS", "`asset_tag`", "`E00143`, `EQ 00143`, legacy `LEG-4172`", "CSV, legacy tags and typos"]],
        col_w=[0.26, 0.16, 0.34, 0.24],
        tbl=dict(bold_first=True, mono_cols=[1]),
        source="Scenario contract section 3",
        minutes=2,
        notes="""Before we clean anything, look at the problem we are cleaning.

The ERP asset register holds the golden key: `EQ-00143`, always five digits, always the same format. But the telematics installer typed the same machine as `eq00143`, `EQ_00143`, or `EQ-143` depending on the device batch. The CMMS technician typed it by hand on a work order: `E00143`, `EQ 00143`, or sometimes a legacy tag like `LEG-4172` that predates the ERP system entirely.

This is not a contrived example. Every fleet or asset-heavy organization I have worked with has some version of this: one golden system, and several operational systems that spell the same identity differently because humans and different device firmwares wrote it down.

WATCH OUT: do not let the audience think this is solved by a simple uppercase or trim. The four-tier resolution later in this section exists because trim and uppercase alone leave thousands of rows unresolved.

TRANSITION: Spelling is only one of the problems hiding in this data.""")

    d.table_slide(
        "P3.3", "What is wrong with the data, on purpose",
        ["Problem", "Where", "Count", "Why it is there"],
        [["Duplicate telematics events", "Bronze telematics", n(F.duplicates), "Retried uploads from the device"],
         ["Out-of-range sensor spikes", "Bronze telematics", n(F.out_of_range), "Nulled, never silently kept"],
         ["Late-arriving events", "Silver telemetry", n(F.late_rows), "Flagged `is_late`, not dropped"],
         ["Unresolved asset identity", "Silver telemetry", n(F.unresolved), "No spelling tier matched an ERP id"],
         ["Mixed time zones and clocks", "Telematics and CMMS", "3 formats", "ISO with `Z`/offset, epoch ms, site-local wall clock"]],
        col_w=[0.3, 0.2, 0.14, 0.36],
        tbl=dict(bold_first=True, align=["l", "l", "r", "l"]),
        source="Ground truth: silver layer, scenario contract section 4",
        minutes=2,
        notes="""These are not edge cases I found by accident. The data generator injects every one of these problems on purpose, with a known answer key, so the pipeline can be graded.

{dup} duplicate telematics events come from retried uploads: the same device sends the same reading twice after a network retry. {oor} sensor readings are physically impossible spikes, and we null them rather than silently averaging them away. {late} events arrive after their own ingest window and get flagged `is_late` instead of being dropped, because a late reading is still a real reading. {unresolved} events never resolve to an ERP id through any of the four tiers, and that is an exception we surface, not hide.

On top of that, three different time representations meet in this pipeline: ISO timestamps with `Z` or an offset, raw epoch milliseconds, and site-local wall-clock time with no zone attached at all.

WATCH OUT: resist the urge to say "in a real project this would not happen". It happens constantly; this is why the demo exists.
TRANSITION: Now let's actually build the pipeline that handles all of this, live.""".format(
            dup=n(F.duplicates), oor=n(F.out_of_range), late=n(F.late_rows), unresolved=n(F.unresolved)))

    d.demo(
        "P3.4", "Demo 2a: Fabric end to end, about 33 live minutes",
        [
            ("Setup and bronze: land raw files", "5 min"),
            ("Silver: dedupe and resolve identity", "4 min"),
            ("Gold: reconcile and close the ETL", "6 min"),
            ("Features, train and compare: five models", "7 min"),
            ("Register, score, and check drift", "6 min"),
            ("Promotion gate, pipeline and CI/CD", "5 min"),
        ],
        [
            "`lh_fleet` lakehouse already has `Files/raw` populated",
            "One completed training run with a run-comparison artifact",
            "`ml.failure_risk_score` and `ml.drift_report` already written once",
        ],
        [
            "If a notebook run queues or stalls, open the matching pre-run output in the same notebook",
            "If a table preview looks empty, the Spark write likely finished before the SQL endpoint caught up: wait or reopen",
        ],
        "~33 min",
        where="Microsoft Fabric  \u00b7  workspace ws-fleet-dev  \u00b7  lakehouse lh_fleet",
        minutes=3,
        notes="""This cue slide sets expectations before I touch Fabric. The live plan is the SHORT paths from both run-of-show files: ETL about 15 minutes plus ML/MLOps about 18 minutes, roughly 33 live minutes, inside this 55-minute Fabric block (the rest of the block is the intro slides you just saw plus buffer). The full 25-minute ETL and 30-minute ML/MLOps walkthroughs stay in the kit for a longer rebuild session; I am not running them today.

DEMO: open `lh_fleet`, show `Files/raw`, then move through `nb_00_setup` to `nb_08_promotion_gate` in order, using the pre-run output and table previews named in the two short-path tables rather than rerunning every notebook live. The slide titles from here on match the notebooks one for one.

WATCH OUT: the two live risks are notebook queueing and SQL-endpoint preview lag, not the Python logic. Say so if it happens; do not apologize for Fabric being Fabric.

IF SHORT ON TIME: drop steps in this order first: the Spark `MLFlowTransformer` rerun on P3.11 (show the code, do not execute), the live drift notebook rerun on P3.13 (show the pre-run `ml.drift_report` table instead), then the pipeline canvas walk-through on P3.12 (describe the chain from this slide's notes instead of opening the canvas). Keep the gold reconciliation numbers and the leaderboard live if at all possible; those are the two slides the room remembers.

SOURCE: repo files `04-demo-fabric-e2e\\etl\\run-of-show.md` (15-minute short path) and `04-demo-fabric-e2e\\ml-mlops\\run-of-show.md` (18-minute short path)
TRANSITION: Let's start where every medallion starts: landing the raw files.""")

    d.cards(
        "P3.5", "Bronze: land the raw files and keep them as they came",
        [dict(icon="activity", title="Telematics", body=f"{n(F.bronze_rows)} JSON-line events; `ts` stays a mixed-format string.", tone="amber"),
         dict(icon="wrench", title="CMMS", body=f"{n(F.cmms_rows)} work orders; site-local timestamps untouched.", tone="amber"),
         dict(icon="database", title="ERP, sites, catalog", body="Asset register, site master, fault codes and the legacy crosswalk.", tone="node"),
         dict(icon="shield-check", title="Ingest metadata", body="`_source_file`, `_ingest_ts`, `_batch_id` on every bronze row.", tone="azure")],
        cols=4, icon_pos="top", source=FABRIC_SRC,
        takeaway="Bronze never fixes data; it proves what arrived and when.",
        minutes=5,
        notes="""Bronze has one job: prove what arrived, without opinions about quality.

DEMO: open `nb_01_bronze_ingest`, show the explicit schemas for telematics and CMMS, then run it. Point at `write_table`, which always writes Delta with explicit schemas. Open `bronze.telematics_events` and show the `ts` column: it is still a string, because the source genuinely mixes ISO timestamps, offsets and epoch milliseconds, and bronze must not quietly normalize that away.

The six bronze tables land at fixed counts: {bronze} telematics events, {cmms} CMMS work orders, and the four small reference tables (assets, sites, fault codes, crosswalk). Those counts are the acceptance test: if they do not match, something upstream changed.

WATCH OUT: if the live run is slow, open the pre-run `bronze.telematics_events` preview and the saved notebook output instead; the counts are identical either way.
IF SHORT ON TIME: skip the live run and only show the table preview plus the mixed-`ts` column.
TRANSITION: Bronze is boring on purpose. Silver is where the real engineering starts.""".format(
            bronze=n(F.bronze_rows), cmms=n(F.cmms_rows)))

    d.flow(
        "P3.6", "Silver: resolve identity in four tiers, first hit wins",
        [dict(icon="key-round", title="EXACT_NORM", body=f"{n(F.tiers['EXACT_NORM'])} events. Normalize the reference, accept only if the id exists in ERP.", tone="azure"),
         dict(icon="tag", title="SERIAL", body=f"{n(F.tiers['SERIAL'])} events. Normalize the serial number, look it up in ERP.", tone="node"),
         dict(icon="git-merge", title="CROSSWALK", body=f"{n(F.tiers['CROSSWALK'])} events. Look up the legacy reference in `asset_crosswalk`.", tone="amber"),
         dict(icon="alert-triangle", title="UNRESOLVED", body=f"{n(F.tiers['UNRESOLVED'])} events. Keep the row, null the asset id, raise an exception.", tone="amber")],
        numbered=True,
        takeaway="Three normalization tiers resolve 203,340 events; the fourth tier is an honest exception, not a failure.",
        minutes=6,
        notes="""This cascade is deterministic and it runs in that exact order: the first tier that matches wins, and later tiers never re-check an already-resolved row.

DEMO: open `nb_02_silver_clean_resolve`, show `apply_resolution`, and run it. Then open the notebook output and read the four counts out loud: they are the acceptance test for this step. {exact} events normalize straight to an ERP id. {serial} more resolve through the serial number on the device. {crosswalk} resolve through the legacy crosswalk table, for tags that predate the ERP system. {unresolved} events resolve to none of the three, so we null the asset id and raise an exception rather than guessing.

The same cascade runs on CMMS work orders with far smaller numbers, because CMMS technicians type fewer distinct spellings than telematics device firmwares do.

WATCH OUT: do not let `UNRESOLVED` sound like a bug. It is a designed outcome: 4,351 events is the honest cost of real-world identity drift, and gold keeps them visible as exceptions instead of dropping them.
IF SHORT ON TIME: skip the rerun, open the saved notebook output, and read the four counts from there.
TRANSITION: Once every event has an asset, gold can start asking business questions: which faults got fixed?""".format(
            exact=n(F.tiers["EXACT_NORM"]), serial=n(F.tiers["SERIAL"]), crosswalk=n(F.tiers["CROSSWALK"]),
            unresolved=n(F.tiers["UNRESOLVED"])))

    d.arch(
        "P3.7", "Gold: match fault episodes to corrective work orders",
        [dict(id="fault", label="Fault episode", sub="Starts, then clears", icon="alert-triangle", col=0, row=0, tone="amber"),
         dict(id="window", label="Match window", sub="24 h before start to 7 days after", icon="clock", col=1, row=0, tone="node"),
         dict(id="wo", label="Corrective work order", sub="Opened inside the window", icon="wrench", col=2, row=0, tone="node"),
         dict(id="status", label="Status", sub="MATCHED / UNMATCHED / PENDING", icon="shield-check", col=3, row=0, tone="azure"),
         dict(id="exc", label="Exceptions", sub="Fault with no WO, WO with no fault", icon="file-text", col=3, row=2, tone="amber", h=1.2)],
        edges=[("fault", "window"), ("window", "wo"), ("wo", "status"), ("status", "exc", "if unresolved")],
        minutes=3,
        notes="""Gold answers one business question: did a fault get fixed, and on time?

DEMO: open `nb_03_gold_reconcile`, show the window constants (`DAY = 86400`, match window `[start - 24h, end + 7d]`), and run it. The logic is a single join plus a window function: for every significant fault episode, find corrective work orders opened inside that window, keep the closest one by time, and record the delay in hours.

Three outcomes come out of that join: `MATCHED`, when a corrective work order falls inside the window; `UNMATCHED`, when the window has closed with nothing found; `PENDING`, when the window has not closed yet. Anything that does not resolve cleanly becomes a row in `gold.fact_recon_exception`, in one of two directions: a fault with no work order, or a work order with no fault behind it.

WATCH OUT: the window is asymmetric on purpose. 24 hours before the fault catches work orders opened just ahead of a known issue; 7 days after allows for normal maintenance lead time.
TRANSITION: Let's look at what this reconciliation actually found.""")

    d.chart_slide(
        "P3.8", "What the reconciliation found",
        ["Matched", "Unmatched", "Pending"],
        {"Significant episodes": [F.recon["MATCHED"], F.recon["UNMATCHED"], F.recon["PENDING"]]},
        fmt="0",
        chart=dict(highlight=1),
        side=[dict(title="The business finding", body=f"{n(F.recon['UNMATCHED'])} significant episodes, including 30 CRIT faults, have no corrective work order at all.", icon="alert-triangle", tone="amber"),
              dict(title="Exceptions table", body=f"{n(F.exceptions)} rows total: faults without a work order and work orders without a fault.", icon="file-text", tone="node")],
        takeaway="Reconciliation turns millions of readings into one list a maintenance planner can act on.",
        minutes=3,
        notes="""This is the payoff of the medallion: one short list a planner can actually use.

DEMO: open `gold.fact_recon_exception` and filter to `severity = CRIT`. Read the headline: {unmatched} significant fault episodes never produced a corrective work order, and 30 of those were CRIT severity, the most urgent class. Then open `gold.fact_recon_match` and show the `delta_hours` column for a matched example, so the room sees the window logic working, not just the exception.

The `{exceptions}`-row exception table splits two ways: faults without a work order (`FAULT_WITHOUT_WO`), which is the safety-relevant direction, and work orders without a fault behind them (`WO_WITHOUT_FAULT`), which often means preventive or inspection work, not a missed signal.

ASK: if you ran this reconciliation on your own fleet tomorrow, which exception type would your maintenance team want first?
IF SHORT ON TIME: show only the chart and the one exception-table preview; skip the matched-example drill-down.
TRANSITION: Gold's daily telemetry and work orders now feed the ML half of this build: features.""".format(
            unmatched=n(F.recon["UNMATCHED"]), exceptions=n(F.exceptions)))

    d.table_slide(
        "P3.9", "Features: 42 columns known at the end of each day",
        ["Group", "Columns", "Count"],
        [["Daily base", "`temp_mean`, `oil_mean`, `vib_mean`, `run_share`, `engine_hours`, ...", "14"],
         ["Fault counts", "`warn_cnt_1d`, `crit_cnt_1d`, `warn_cnt_7d`, `crit_cnt_7d`, `warn_cnt_14d`", "5"],
         ["Rolling means", "`{temp,oil,hyd,vib}_mean_{3d,7d,14d}`", "12"],
         ["Trends", "`{temp,oil,hyd,vib}_trend` = 3-day mean minus 14-day mean", "4"],
         ["Rolling max", "`temp_max_7d`, `vib_max_7d`", "2"],
         ["Maintenance", "`days_since_last_pm`, `days_since_last_cm`, `cm_count_90d`", "3"],
         ["Static", "`equipment_class_code`, `asset_age_years`", "2"]],
        col_w=[0.22, 0.58, 0.1],
        tbl=dict(bold_first=True, align=["l", "l", "r"]),
        source="Scenario contract section 8",
        takeaway=f"Label `fail_next_7d`: {n(F.labelled_rows)} labelled rows, about {pct(F.positive_rate)} positive.",
        minutes=4,
        notes="""Every one of these 42 columns is computed from data known at the end of the observation day; nothing here peeks into the future.

DEMO: open `nb_04_features`, show `build_features`, and run it. Point at the split column it writes: `warmup`, `train`, `gap`, `valid`, `test`, `unlabeled`, `score`. This is exactly the purged time-split pattern from Part 2 slide P2.9, with the same 7-day gap removing label overlap between train and valid, and between valid and test.

The label is `fail_next_7d`: did a non-duplicate, resolved corrective work order open in the next 7 calendar days? {rows} rows get a feature vector; {labelled} of them have a usable label, at about {rate} positive. The remaining rows near the cutoff stay unlabeled on purpose, because their 7-day look-ahead window has not closed yet.

WATCH OUT: the split column is part of the feature contract. Never re-split this table randomly in a notebook; that is exactly the leakage Part 2 warned about.
TRANSITION: With features in place, we can finally train something.""".format(
            rows=n(F.ml_rows), labelled=n(F.labelled_rows), rate=pct(F.positive_rate)))

    d.chart_slide(
        "P3.10", "Train and track: five models, one leaderboard",
        ["Prevalence", "Rule baseline", "Logistic regression", "HGB, no fault codes", "HGB"],
        {"Test PR-AUC": [F.pr_auc_test["prevalence"], F.pr_auc_test["rule"], F.pr_auc_test["logistic"],
                         F.pr_auc_test["hgb_no_fault_codes"], F.pr_auc_test["hgb"]]},
        fmt="0.00",
        chart=dict(highlight=4),
        side=[dict(title="Same split, same metric", body="All five runs score the same frozen test split with the same PR-AUC function.", icon="shield-check", tone="azure"),
              dict(title="Why no fault codes matters", body="The no-fault-codes variant checks the model is not just re-reading the fault log.", icon="flask-conical", tone="node")],
        takeaway="HGB wins on PR-AUC, and it still wins without fault-code features, which is the honest test.",
        minutes=6,
        notes="""Five child runs land in one MLflow experiment; the leaderboard is the whole point of tracking.

DEMO: open `nb_05_train_mlflow`, show the five `mlflow.start_run()` blocks (prevalence, rule baseline, logistic regression, HGB, HGB without fault codes), and run it live if time allows, or open the pre-run experiment view in the Fabric Experiments item. Sort the runs table by test PR-AUC and read it top to bottom.

Two baselines keep the leaderboard honest. Prevalence (about {prevalence}) is what a model gets for always predicting the positive rate; rule baseline (about {rule}) is what a handwritten rule on fault counts gets. Logistic regression (about {logistic}) is a reasonable linear model. HGB (about {hgb}) wins outright, and the no-fault-codes variant (about {hgb_nfc}) still beats every baseline, which tells us the gain is not just the model re-reading the fault log back to us. These are approximate test PR-AUC values: a live retrain can shift the third decimal with library versions, so speak in "about" terms, not exact figures.

WATCH OUT: PR-AUC, not accuracy, is the headline metric here, because positives are rare: about {rate} of labelled rows. Accuracy would reward predicting "no failure" on everything.
IF SHORT ON TIME: skip the live rerun; open the pre-run experiment view and read the sorted table directly.
TRANSITION: The leaderboard names a winner. Registering and scoring it is next.""".format(
            prevalence=d2(F.pr_auc_test["prevalence"]), rule=d2(F.pr_auc_test["rule"]), logistic=d2(F.pr_auc_test["logistic"]),
            hgb=d2(F.pr_auc_test["hgb"]), hgb_nfc=d2(F.pr_auc_test["hgb_no_fault_codes"]), rate=pct(F.positive_rate)))

    d.code_slide(
        "P3.11", "Register and score: PREDICT in a notebook",
        """from synapse.ml.predict import MLFlowTransformer

model = MLFlowTransformer(
    inputCols=feature_cols,
    outputCol="risk_score",
    modelName="fleet_failure_model",
    modelVersion=champion_version,
)

scored_df = model.transform(features_df)
""",
        lang="python",
        file="nb_06_register_score.py",
        side=[
            dict(title="Needs a signature", body="PREDICT/MLFlowTransformer requires an MLflow-format model with a logged signature, which `nb_05` already provides.", icon="shield-check", tone="azure"),
            dict(title="The champion pointer", body="Fabric ML model items have versions, not stages or aliases: `nb_08_promotion_gate` decides the champion and writes it to `ml.model_pointer`.", icon="key-round", tone="node"),
        ],
        source="nb_06_register_score.py, lines 48-59",
        takeaway=f"{n(F.assets_scored)} assets scored for {F.score_date}: roughly 8-10 High and 7-13 Medium; the frozen reference file has {n(F.bands['High'])} and {n(F.bands['Medium'])}.",
        minutes=4,
        notes="""This is the one slide where the code on screen is exactly the code in the repo.

DEMO: open `nb_06_register_score`, scroll to `score_with_mlflow_transformer`, and run it. `champion_version` comes from reading `ml.model_pointer`, the small table that `nb_08_promotion_gate` updates whenever a challenger wins. PREDICT reads that version's MLflow model straight from the Fabric ML model item and scores the features table in one call.

WATCH OUT: Fabric ML model items version models, they do not carry stages or aliases the way some other registries do. That is exactly why the workshop keeps its own `ml.model_pointer` table: it is the explicit, auditable "who is champion right now" record that Fabric does not give you out of the box.

Scoring lands {assets} assets into risk bands for {date}. Expect roughly 8 to 10 High and 7 to 13 Medium out of this live run: the frozen reference file has {high} and {medium}, and another live run gave 8 High and 13 Medium -- the split moves a little with library versions (scenario contract, feature parity notes). That table is what Power BI and the Part 4 data agent both read from.

WATCH OUT: do not present a single fixed split as what today's live notebook will print. The frozen reference file `reference_out\\ml_failure_risk_score.csv` that Part 4 loads has {high} High / {medium} Medium / {low} Low; another live run gave 8 High / 13 Medium. If today's run lands somewhere in that range, that is expected, not a bug.
IF SHORT ON TIME: skip the live run; open the pre-run `ml.failure_risk_score` table and read the band counts from there.
TRANSITION: One notebook run is a demo. A daily, monitored pipeline is production.""".format(
            assets=n(F.assets_scored), date=F.score_date, high=n(F.bands["High"]), medium=n(F.bands["Medium"]), low=n(F.bands["Low"])))

    d.flow(
        "P3.12", "Orchestrate: one pipeline, one schedule, one alert",
        [dict(icon="workflow", title="ETL notebooks", body="`nb_01` to `nb_03`: bronze, silver, gold, each a `TridentNotebook` activity.", tone="node"),
         dict(icon="flask-conical", title="Features and train", body="`nb_04` features, `nb_05` train, each with its own failure-notify email.", tone="node"),
         dict(icon="gauge", title="Score and drift", body="`nb_06` scores the fleet with the champion, then `nb_07` writes the drift report.", tone="azure"),
         dict(icon="activity", title="Gate and alert", body="`nb_08` promotion gate, then `IfDriftAlert` sends `SendDriftAlertEmail` only when drift status is alert.", tone="azure")],
        numbered=True,
        takeaway="`pl_fleet_daily` runs 14 activities on one schedule; `pl_fleet_etl` is the ETL-only subset for reruns.",
        minutes=4,
        notes="""One pipeline runs the whole chain every day, end to end, unattended: 14 activities in `pl_fleet_daily`.

DEMO: open `pl_fleet_daily` in the Fabric pipeline canvas and walk the activities left to right: RunBronzeIngest, RunSilverCleanResolve, RunGoldReconcile, RunFeatures, RunTrainMlflow, RunRegisterScore, RunDriftMonitor, RunPromotionGate, then an `IfDriftAlert` condition whose true branch calls `SendDriftAlertEmail`. Every notebook activity is the same activity type, `TridentNotebook`, so the canvas reads as one consistent pattern, not eight different mechanisms. Each of the five risk-bearing notebook steps (features, train, score, drift, gate) has its own failure-notify email: NotifyFeaturesFailure, NotifyTrainFailure, NotifyScoreFailure, NotifyDriftNotebookFailure, NotifyGateFailure. Every notebook step retries once after 60 seconds, which catches transient capacity or lock contention, not logic bugs.

WATCH OUT: `IfDriftAlert` only fires `SendDriftAlertEmail` when `nb_07_drift_monitor`'s exit value has `"status": "alert"` in it; a moderate-only or stable run sends nothing, by design. Also, `nb_08_promotion_gate` is report-only inside this pipeline: it writes a decision JSON (challenger wins or not) but does not itself flip the champion. Applying a promotion means rerunning `nb_08_promotion_gate` with `apply_pointer_update=True`, by hand or from a separate trigger -- this is the usual champion/challenger order: score, then check drift, then decide, never promote blind. The October scoring batch itself is prepared earlier, in the silver step (`nb_02_silver_clean_resolve`), not in the pipeline's later notebooks.

`pl_fleet_etl` is the smaller sibling: bronze, silver, gold only, for when you need to rerun ingestion without retraining anything.
TRANSITION: What actually triggers that alert is worth a closer look.""")

    d.chart_slide(
        "P3.13", "Monitor: drift report and what triggers the alert",
        [f"{row['equipment_class']} {row['sensor']}" for row in F.drift_major] + [f"{row['equipment_class']} {row['sensor']}" for row in F.drift_moderate],
        {"PSI": [row["psi"] for row in F.drift_major] + [row["psi"] for row in F.drift_moderate]},
        fmt="0.00",
        chart=dict(highlight=0),
        side=[dict(title="No first-party drift monitor", body="Fabric does not ship model-drift monitoring out of the box: `nb_07_drift_monitor` and the alert are custom-built for this workshop.", icon="alert-triangle", tone="amber"),
              dict(title="Thresholds", body="Stable below 0.10, moderate 0.10 to 0.25, major above 0.25, checked across 47 asset-class and sensor combinations.", icon="bar-chart-3", tone="node")],
        takeaway=f"{len(F.drift_major)} major, {len(F.drift_moderate)} moderate, {F.drift_stable} stable: separate expected season from a real signal shift.",
        minutes=4,
        notes="""This is the same PSI table Part 2 showed, now computed by our own Fabric notebook instead of a managed service.

DEMO: open `nb_07_drift_monitor`, show the PSI function and the two thresholds, and run it against the reference (September) and new (first half of October) windows. Read the headline: {major} combinations are major shift, all four are the firmware change we injected on Excavator and WheelLoader engine temperature and vibration. {moderate} are moderate: engine-temperature drift on Compactor, MobileCrane, and Paver, which is expected October cooling, not a fault.

WATCH OUT: say plainly that Fabric has no first-party model-drift monitoring at the time of this workshop. `nb_07_drift_monitor` and the alert email are something we built, not a managed Fabric feature. That is an honest limitation, not a criticism.
IF SHORT ON TIME: show only the chart and the two side notes; skip the live notebook rerun.
TRANSITION: Before this goes anywhere near production, it needs a real deployment story across environments.""".format(
            major=len(F.drift_major), moderate=len(F.drift_moderate)))

    d.arch(
        "P3.14", "Ship it: Git, variables and deployment per environment",
        [dict(id="dev", label="ws-fleet-dev", sub="Git-connected, daily work", icon="database", col=0, row=0, tone="node"),
         dict(id="deploy", label="fabric-cicd", sub="GitHub Actions: deploy.py + config.yml", icon="workflow", col=1, row=0, tone="azure"),
         dict(id="test", label="ws-fleet-test", sub="Deployment pipeline stage", icon="shield-check", col=2, row=0, tone="node"),
         dict(id="prod", label="ws-fleet-prod", sub="Deployment pipeline stage", icon="rocket", col=3, row=0, tone="node"),
         dict(id="varlib", label="Variable Library", sub="`fleet_mlops`: one item, dev/test/prod value sets", icon="settings", col=1, row=2, tone="amber", h=1.3),
         dict(id="gitshape", label="What Git stores", sub="notebook source + `.platform` logicalId; pipeline points by id", icon="git-branch", col=3, row=2, tone="node", h=1.3)],
        edges=[("dev", "deploy"), ("deploy", "test"), ("test", "prod"), ("varlib", "deploy", "per-stage values")],
        minutes=5,
        notes="""Shipping across environments is the part teams underestimate: it is not just "copy the workspace."

DEMO: open the `fabric-mlops-deploy.yml` GitHub Actions workflow, show the `AzureCliCredential()` step after `azure/login@v2`, and then `cicd/deploy.py` calling `deploy_with_config(...)` against `cicd/config.yml`, which scopes Notebook, DataPipeline, and VariableLibrary items.

WATCH OUT: be precise about what the Variable Library actually does. `fleet_mlops` is one Variable Library item holding dev/test/prod value sets, and notebooks can read it at runtime with `notebookutils.variableLibrary`. But in this kit the wiring is simpler than that: the per-environment connection id and alert recipient are injected at deploy time, by `cicd/parameter.yml` replacing placeholder GUIDs before `deploy_with_config` runs, not by every notebook calling the variable-library API live. Say both are real Fabric mechanisms; say which one this kit actually uses.

What Git really stores for each item: a `notebook-content.py` source file plus a `.platform` file carrying a `logicalId` GUID. `pl_fleet_daily` references its notebooks by that logicalId, not by workspace-specific item id, so the same `fabric-git` folder syncs into `ws-fleet-dev` and deploys into test and prod through `fabric-cicd` without the pipeline JSON changing.

Git integration and deployment pipelines move notebooks, data pipelines, and variable sets cleanly, but for ML experiment and model items that integration is metadata-only today. The model binary itself does not travel with the deployment: each environment re-trains or re-logs its own model, and `nb_08_promotion_gate` decides the champion per workspace by writing to that workspace's own `ml.model_pointer` table.

NOTES ONLY: the three shared Python files used across notebooks (feature logic, scoring helpers, drift math) live in a code folder under the lakehouse `Files` area in this kit, imported with a path append rather than packaged; the production alternative is a Fabric Environment item with a custom wheel, so the dependency is versioned and attached once instead of copy-pasted per notebook.

ASK: how would your platform team govern a champion decision that is re-made independently in three workspaces?
TRANSITION: That is the whole Fabric path. Azure Machine Learning builds the identical pipeline on a different operating model next.""")
