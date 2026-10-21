"""One sample slide per layout: used to tune the design system and as a living reference for the content modules."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from deck_core import LINT  # noqa: E402
from deck_lib import Deck  # noqa: E402

d = Deck()
d.title_slide("O1", "Machine learning on Microsoft: Fabric, Azure ML and Foundry",
              "One scenario, three platforms. Build, ship and operate machine learning and agents, end to end.",
              "23 OCTOBER 2026  \u00b7  FULL-DAY WORKSHOP",
              [("layers", "Microsoft Fabric", "Data and ML in one SaaS platform"),
               ("flask-conical", "Azure Machine Learning", "The enterprise ML platform"),
               ("bot", "Microsoft Foundry", "Agents and AI applications")],
              notes="Welcome.")
d.section("P1.0", 1, "Fabric vs Azure ML", "Two ML platforms, one MLflow vocabulary: what each is for and when to pick which.",
          ["The mental model of both platforms", "Where MLflow fits in each one", "A decision rule you can reuse"],
          ("09:20 \u2013 10:50", "90 minutes"), notes="Part 1.")
d.agenda("O3", "Today in five blocks, with room for questions", [
    ("09:00 \u2013 09:20", "Opening", "Scenario, goals and ground rules", "20 MIN", "talk"),
    ("09:20 \u2013 10:50", "Part 1  \u00b7  Fabric vs Azure ML", "Two ML platforms and the MLflow concepts behind both", "90 MIN", "part"),
    ("10:50 \u2013 11:05", "Break", "", "", "break"),
    ("11:05 \u2013 12:20", "Part 2  \u00b7  MLOps concepts", "From notebook to a system you can trust", "75 MIN", "part"),
    ("12:20 \u2013 13:20", "Lunch", "", "", "break"),
    ("13:20 \u2013 15:15", "Part 3  \u00b7  End-to-end demo", "ETL, ML and MLOps on Fabric and on Azure ML", "115 MIN", "part"),
    ("15:15 \u2013 15:30", "Break", "", "", "break"),
    ("15:30 \u2013 16:45", "Part 4  \u00b7  Foundry and the data agent", "Reconcile logs from several sources, then ask questions", "75 MIN", "part"),
    ("16:45 \u2013 17:00", "Wrap-up", "Takeaways and next steps", "15 MIN", "talk"),
], notes="Agenda.", takeaway="Parts 1 and 2 give the vocabulary; Parts 3 and 4 put it to work.")
d.bullets("P1.2", "Fabric brings data and ML together; Azure ML goes deeper on the ML lifecycle", [
    ("Fabric is a SaaS analytics platform", "Lakehouse, pipelines, notebooks and ML live in one workspace, on OneLake.", "layers"),
    ("Azure ML is a PaaS for the full ML lifecycle", "Compute, environments, pipelines, endpoints and governance you control.", "server"),
    ("MLflow is the common language", "Experiments, runs, models and a registry exist in both, with small differences.", "git-branch"),
], notes="Say it simply.", takeaway="Same MLflow vocabulary, different operating model.")
d.cards("P1.3", "Four building blocks show up on every ML platform", [
    dict(icon="flask-conical", title="Experiment", body="A named place that groups every attempt at one problem.", tone="azure"),
    dict(icon="repeat", title="Run", body="One execution: parameters in, metrics and artifacts out.", tone="azure"),
    dict(icon="package", title="Model", body="A packaged artifact with a signature, ready to load anywhere.", tone="azure"),
    dict(icon="git-merge", title="Registry", body="Versioned models with lineage and a promotion path.", tone="azure"),
], notes="Concepts.", takeaway="Learn these four words once; they apply to both platforms.")
d.compare("P1.8", "Two platforms, two operating models", dict(title="Microsoft Fabric", sub="SaaS \u00b7 data first", icon="layers", items=[
    "Notebooks, pipelines and models in one workspace", "OneLake is the shared storage layer",
    "MLflow is built in; no tracking server to run", "Capacity (F SKU) is the unit you pay for"]),
    dict(title="Azure Machine Learning", sub="PaaS \u00b7 ML lifecycle first", icon="flask-conical", items=[
        "Workspace with compute, environments and endpoints", "You choose the compute, network and identity",
        "MLflow tracking and registry in the workspace", "Pay for the compute you start"]),
    notes="Compare.", takeaway="Choose by the team you have and the control you need.")
d.stats("P3.20", "The fleet scenario in four numbers", [
    dict(value="208,900", label="Bronze telematics rows", sub="Before cleaning and de-duplication"),
    dict(value="4,351", label="Unresolved readings", sub="Asset id could not be matched", tone="amber"),
    dict(value="92.4 %", label="Critical faults with a work order", sub="After reconciliation", tone="success"),
    dict(value="0.385", label="PR-AUC of the model", sub="Against a prevalence of 0.045"),
], notes="Numbers.")
d.callout("P2.1", "The model is the small part of the system", "In production, the code that trains a model is a small box in a much larger system.",
          support=[dict(icon="database", title="Data", body="Pipelines, quality, lineage."),
                   dict(icon="workflow", title="Process", body="Training, validation, release."),
                   dict(icon="activity", title="Operations", body="Monitoring, drift, rollback.")], notes="Callout.")
d.table_slide("P1.12", "MLflow in Fabric and in Azure ML: same concepts, different details",
              ["Concept", "Microsoft Fabric", "Azure Machine Learning"], [
                  ["Tracking", "Built in; no URI to set in a notebook", "Workspace tracking URI from the SDK"],
                  ["Registry", "Model items with versions only", "Registered models with versions and tags"],
                  ["Stages and aliases", "Not available; promote by workspace", "Aliases and tags to mark champions"],
                  ["Serving", "Preview endpoints and batch scoring", "Managed online and batch endpoints"],
              ], col_w=[1.2, 2.2, 2.2], tbl=dict(bold_first=True), notes="Table.",
              takeaway="Code that logs and loads models moves between both with minimal change.")
d.chart_slide("P3.14", "The model beats the baselines, but the signal is modest", ["HistGradientBoosting", "Logistic regression", "Rule baseline", "Prevalence"],
              {"PR-AUC": [0.385, 0.292, 0.068, 0.045]}, fmt="0.000", chart=dict(highlight=0),
              side=[dict(title="Read it honestly", body="PR-AUC is judged against prevalence, not against zero.", tone="azure"),
                    dict(title="Why it matters", body="A model worth shipping must beat a simple rule.", tone="amber")], notes="Chart.")
d.code_slide("P3.9", "Log a run the same way on both platforms", '''import mlflow
from sklearn.ensemble import HistGradientBoostingClassifier

mlflow.set_experiment("fleet-failure-7d")
with mlflow.start_run(run_name="hgb-baseline"):
    model = HistGradientBoostingClassifier(max_depth=6)
    model.fit(X_train, y_train)
    mlflow.log_params({"max_depth": 6})
    mlflow.log_metric("pr_auc", pr_auc)
    mlflow.sklearn.log_model(model, "model")''', file="nb_05_train.py", hl=[4, 5],
             side=[dict(title="Same code", body="Only the tracking URI differs between Fabric and Azure ML.", tone="azure"),
                   dict(title="What to notice", body="The run appears in the experiment as soon as the cell ends.", tone="success")], notes="Code.")
d.demo("P3.8", "Demo: from raw logs to a clean silver table", [
    ("Open nb_01 and read the bronze telematics table", "2 min"), ("Run the cleaning cells and watch the row counts", "3 min"),
    ("Show the rejected rows and the reason codes", "2 min"), ("Open the Gold table in the SQL endpoint", "2 min")],
     ["Screenshots of each step in the demo folder", "A finished lakehouse in ws-fleet-prod"],
     ["208,900 rows become 207,691", "1,209 duplicates are removed on purpose"], "9 min", where="Fabric  \u00b7  ws-fleet-dev  \u00b7  lh_fleet", notes="Demo.")
d.flow("P2.4", "A model moves through the same five steps on every platform", [
    dict(icon="database", title="Prepare", body="Clean data and build features."), dict(icon="flask-conical", title="Train", body="Track every run."),
    dict(icon="scale", title="Evaluate", body="Compare with baselines."), dict(icon="rocket", title="Deploy", body="Batch or online."),
    dict(icon="activity", title="Monitor", body="Watch data and quality.")], back=dict(label="DRIFT TRIGGERS RETRAINING"), notes="Flow.")
d.arch("P3.2", "The Fabric architecture in one picture", [
    dict(id="src", label="Sources", sub="Telematics, CMMS, ERP", icon="truck", col=0, row=1, tone="amber"),
    dict(id="bronze", label="Bronze", sub="Raw, as received", icon="database", col=1, row=1),
    dict(id="silver", label="Silver", sub="Clean and typed", icon="filter", col=2, row=1),
    dict(id="gold", label="Gold", sub="Facts and dimensions", icon="table", col=3, row=1),
    dict(id="ml", label="ML", sub="Train, register, score", icon="flask-conical", col=3, row=0, tone="azure"),
    dict(id="bi", label="Reports", sub="Semantic model", icon="bar-chart-3", col=3, row=2, tone="success"),
], edges=[("src", "bronze"), ("bronze", "silver"), ("silver", "gold"), ("gold", "ml", "features"), ("gold", "bi")],
       groups=[dict(label="Lakehouse lh_fleet", c0=1, r0=1, c1=3, r1=1, tone="azure")], notes="Arch.")
d.stairs("P2.12", "Four levels of MLOps maturity", [
    dict(tag="Level 0", title="Manual", body="Notebooks, copy and paste."), dict(tag="Level 1", title="Automated training", body="Pipelines retrain on a schedule."),
    dict(tag="Level 2", title="Automated release", body="Tests and approvals gate deployment."),
    dict(tag="Level 3", title="Closed loop", body="Monitoring triggers retraining.")], notes="Stairs.")
d.timeline("P4.15", "Dates to know before you build", [
    dict(when="2026-11-06", title="Legacy Fabric tool", body="Foundry deprecates the original data-agent tool.", tone="amber"),
    dict(when="2026-12-01", title="Visual workflow builder", body="Retires in Foundry.", tone="amber"),
    dict(when="2027-04-20", title="Prompt flow", body="Retirement date announced.", tone="amber")], notes="Timeline.")
d.recap("C1", "Three things to take away", [
    dict(title="One vocabulary", body="Experiments, runs, models and a registry exist on both platforms."),
    dict(title="One pipeline", body="Bronze, silver and gold feed features, training and scoring."),
    dict(title="One loop", body="Monitoring closes the loop back to retraining.")], question="Which of these will you try first on your own data?", notes="Recap.")
d.discuss("P2.18", "Where would you stop the line?", ["A drift alert fires at 2 a.m. What happens next?", "Who approves a model for production today?"],
          when="5 min", notes="Discuss.")

out = Path(__file__).parent / "out"
out.mkdir(exist_ok=True)
p = d.save(out / "showcase.pptx")
print("saved", p)
print("\n".join(LINT) or "no lint warnings")
