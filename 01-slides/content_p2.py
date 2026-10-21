"""Part 2: MLOps concepts (P2.0-P2.20)."""
from __future__ import annotations

from datetime import date

from deck_core import BODY, HEAD, MONO, add_icon, arrow, box, label, pill, polyline, text
from deck_lib import Deck
from facts import F, d2, d3, n, pct


def _draw_time_split(f) -> None:
    s = f.s
    start = date.fromisoformat(F.splits["train"]["first"])
    end = date.fromisoformat(F.splits["score"]["last"])
    total_days = (end - start).days + 1

    def x_for(day_text: str) -> float:
        current = date.fromisoformat(day_text)
        offset = (current - start).days
        return f.x + 0.35 + (f.w - 0.7) * offset / total_days

    axis_y = f.y + 2.15
    arrow(s, f.x + 0.35, axis_y, f.r - 0.35, axis_y, color="sand", w=2.0, name="split axis")

    month_marks = [
        ("2026-05-01", "May"),
        ("2026-06-01", "Jun"),
        ("2026-07-01", "Jul"),
        ("2026-08-01", "Aug"),
        ("2026-09-01", "Sep"),
        ("2026-10-01", "Score"),
    ]
    for day_text, name in month_marks:
        x = x_for(day_text)
        arrow(s, x, axis_y - 0.12, x, axis_y + 0.12, color="line", w=1.0, tail=False, name=f"mark {name}")
        text(s, x - 0.35, axis_y + 0.16, 0.7, 0.22, [name], size=10.5, color="muted", font=MONO, align="c",
             wrap=False, lint=False, name=f"month {name}")

    segments = [
        dict(title="Train", tone="azure", start="2026-04-15", end="2026-07-24",
             body=f"{n(F.splits['train']['rows'])} rows\n{n(F.splits['train']['positives'])} positives"),
        dict(title="Gap", tone="amber", start="2026-07-25", end="2026-07-31", body="7d"),
        dict(title="Valid", tone="node", start="2026-08-01", end="2026-08-24",
             body=f"{n(F.splits['valid']['rows'])} rows\n{n(F.splits['valid']['positives'])} positives"),
        dict(title="Gap", tone="amber", start="2026-08-25", end="2026-08-31", body="7d"),
        dict(title="Test", tone="success", start="2026-09-01", end="2026-09-23",
             body=f"{n(F.splits['test']['rows'])} rows\n{n(F.splits['test']['positives'])} positives"),
        dict(title="Score", tone="solid", start="2026-09-30", end="2026-09-30", body=n(F.splits["score"]["rows"])),
    ]

    y_main, h_main = f.y + 0.7, 0.92
    for seg in segments:
        x0 = x_for(seg["start"])
        x1 = x_for(seg["end"]) + (f.w - 0.7) / total_days
        width = max(0.42, x1 - x0)
        if seg["title"] == "Score":
            width = 0.72
            x0 = min(x0, f.r - width)
        h = 0.58 if seg["title"] == "Gap" else h_main
        y = y_main + (h_main - h) / 2
        box(s, x0, y, width, h, tone=seg["tone"], radius=0.08, name=f"segment {seg['title']} {seg['start']}")
        t_color = "white" if seg["tone"] == "solid" else "ink"
        size = 15 if seg["title"] not in ("Gap", "Score") else 12
        text(s, x0 + 0.05, y + 0.04, width - 0.1, h - 0.08,
             [dict(text=seg["title"], size=size, bold=True, font=HEAD, color=t_color, align="c", after=2),
              dict(text=seg["body"], size=11.5, color=t_color if seg["tone"] == "solid" else "muted", align="c")],
             align="c", anchor="m", lint=False, name=f"text {seg['title']} {seg['start']}")

    box(s, f.x + 0.48, f.y + 2.68, 2.0, 0.84, tone="paper", radius=0.08, name="warmup note")
    pill(s, f.x + 0.62, f.y + 2.78, "Warm-up", tone="node", size=10, h=0.24)
    text(s, f.x + 0.62, f.y + 3.02, 1.72, 0.42,
         [f"{n(F.splits['warmup']['rows'])} rows fill the rolling windows"], size=11.5, color="muted",
         align="c", anchor="m", name="warmup body")

    box(s, f.r - 2.65, f.y + 2.68, 2.28, 0.84, tone="paper", radius=0.08, name="label delay note")
    pill(s, f.r - 2.48, f.y + 2.78, "Label delay", tone="amber", size=10, h=0.24)
    text(s, f.r - 2.48, f.y + 3.02, 1.95, 0.42,
         [f"{n(F.splits['unlabeled']['rows'])} rows stay unlabeled before score day"], size=11.5, color="muted",
         align="c", anchor="m", name="label delay body")
    label(s, f.x + 5.98, axis_y - 0.42, 1.58, f"Purged: {n(F.splits['gap']['rows'])}",
          size=10.0, color="amber", bold=True, fill="paper", h=0.28, name="gap summary")

    text(s, f.x + 0.45, f.b - 0.74, 4.2, 0.7,
         [dict(text="Why this matters", size=13.5, bold=True, font=HEAD, color="azure", after=2),
          dict(text="A random split lets fault precursors and delayed work orders leak across train and test.", size=12.5)],
         name="why")
    text(s, f.r - 4.35, f.b - 0.74, 4.0, 0.7,
         [dict(text="Contract check", size=13.5, bold=True, font=HEAD, color="azure", after=2),
          dict(text="The split column is part of the feature contract. Use it as-is, never re-split in a notebook.", size=12.5)],
         name="contract")


def build(d: Deck) -> None:
    d.section(
        "P2.0", 2, "Part 2: MLOps from notebook to reliable product",
        "The concepts stay the same whether you run in Fabric, Azure Machine Learning, or both.",
        ["Version the things that change", "Add a gate before production", "Monitor the data before labels arrive"],
        ("11:05 – 12:20", "75 minutes"),
        minutes=1,
        notes="""Now that Part 1 gave us the platform map, Part 2 gives us the operating vocabulary.

The main point is that MLOps is not a product feature. It is the discipline that keeps a useful notebook from becoming a fragile production dependency. I will stay product-neutral on purpose: every concept we cover here shows up again in Part 3 on Fabric and on Azure Machine Learning.

For this audience, I want every concept to end with a Monday-morning action. If you are a data scientist, what should you log, test, or refuse to do by hand? If you are a data engineer, what should be checked before a pipeline trains or scores anything?

TRANSITION: Let us start with the simplest definition of the problem.""",
    )

    d.cards(
        "P2.1", "MLOps is DevOps plus two things that keep changing: data and models",
        [
            dict(icon="git-branch", title="Code", body="Training logic, feature code, and pipeline definitions still live in Git.", tone="node"),
            dict(icon="database", title="Data", body="Schemas, row counts, late arrivals, and identity resolution can drift every day.", tone="azure"),
            dict(icon="workflow", title="Model", body="The model is a build artifact of code, data, and an environment pin.", tone="success"),
        ],
        takeaway="A model file alone is never the product; the product is the loop around it.",
        minutes=4, core=True,
        notes="""My short definition is this: MLOps is DevOps, plus data drift and model drift.

Software teams already know how to version code, run tests, and promote builds. In machine learning, the code is only one third of the system. The input data keeps moving, and the model you deploy today may be retrained next month with different labels, features, or package versions.

In Contoso Fleet, the HistGradientBoosting model is not something I can explain without its feature table, the split column, and the environment pin. If I retrain with a different split rule or a different MLflow version, I may get a different artifact and a different deployment story.

For a data scientist on Monday morning, that means: log the data version, the Git SHA, the model family, and the output metrics every time. For a data engineer, it means: treat the feature table and the scoring contract as first-class versioned assets, not just intermediate files.

TRANSITION: So what actually breaks after launch?""",
    )

    d.cards(
        "P2.2", "Why models fail after launch",
        [
            dict(icon="refresh-cw", title="Data drift", body="A firmware change raises engine temperature and vibration for two equipment classes.", tone="amber"),
            dict(icon="database", title="Silent changes", body="A new sensor field or a missing join key changes the feature contract without warning.", tone="amber"),
            dict(icon="clock", title="Label delay", body="Corrective work orders arrive days later, so October has no trustworthy accuracy labels yet.", tone="amber"),
            dict(icon="users", title="Ownership gaps", body="Nobody knows who stops the line when identity resolution or drift crosses a threshold.", tone="amber"),
        ],
        takeaway="Most production failures start outside the estimator: upstream data, late labels, or unclear ownership.",
        minutes=4, core=True,
        notes="""Here are the four failure modes I want the room to remember.

First, data drift. In our scenario, a firmware or calibration change pushes Excavator and WheelLoader temperature and vibration upward. The model can still run, but it is now reading a different world.

Second, silent upstream change. The classic example here is `coolant_level_pct`: it appears only after July for newer firmware. Another is an identity-resolution rate that quietly drops because a source system changed how it spells an asset id.

Third, label delay. We predict a corrective work order in the next seven days, but the work order can be opened three to six days late. That means a perfectly healthy October monitoring job still cannot talk about October accuracy yet.

Fourth, ownership gaps. If the data engineer sees a schema drift and the data scientist sees a weaker model, who makes the go/no-go call?

ASK: Which of these four hurts you most today?

TRANSITION: That is why the lifecycle is a loop, not a straight line.""",
    )

    d.flow(
        "P2.3", "The ML lifecycle is a loop, not a line",
        [
            dict(icon="message-square", title="Frame", body="Define the business event, the label, and what success means."),
            dict(icon="database", title="Data", body="Land, clean, resolve identities, and declare the contract."),
            dict(icon="table", title="Features", body="Build only what is known at the end of each day."),
            dict(icon="workflow", title="Train", body="Compare baselines, candidates, and their logged runs."),
            dict(icon="rocket", title="Deploy", body="Score in batch or serve online with an approval gate."),
            dict(icon="activity", title="Monitor", body="Watch quality, drift, delayed labels, and operations."),
        ],
        back=dict(label="MONITORING TRIGGERS A NEW CYCLE"),
        minutes=3, core=True,
        notes="""I want to slow down on the word loop.

Too many teams think of machine learning as a one-way project plan: collect data, train, deploy, done. In reality, deployment is the midpoint. The system only becomes reliable when monitoring sends you back into a new cycle with better evidence.

In our workshop story, the framing question is clear: which asset-day is likely to need a corrective work order within seven days? That framing drives the label, the split, the features, the gate, and the monitoring. If we changed the business question to spare-parts forecasting, almost every downstream artifact would change.

For a data scientist, Monday morning means checking that the label definition, the split, and the baseline still make sense before chasing a better model. For a data engineer, it means keeping the loop operational: data lands, contracts run, scores publish, drift jobs alert, and somebody can reproduce the whole path.

TRANSITION: Teams do not jump from notebooks to full automation in one step.""",
    )

    d.stairs(
        "P2.4", "MLOps maturity: five levels from manual to automated",
        [
            dict(tag="Level 0", title="No MLOps", body="Manual training, manual testing, manual release, little traceability.", tone="node"),
            dict(tag="Level 1", title="DevOps but no MLOps", body="Code CI exists, but training and deployment still depend on heroics.", tone="azure"),
            dict(tag="Level 2", title="Automated training", body="Reusable pipelines, scheduled retraining, and centralized experiment tracking.", tone="azure"),
            dict(tag="Level 3", title="Automated deployment", body="A gate, approvals, and repeatable promotion into serving.", tone="solid"),
            dict(tag="Level 4", title="Automated operations", body="Monitoring, retraining, and promotion become policy-driven loops.", tone="solid"),
        ],
        source="Microsoft Learn: AML MLOps maturity model, verified 2026-10-18",
        takeaway="Level 2 is already a strong and realistic target for many data teams.",
        minutes=4, core=True,
        notes="""This ladder comes from the Microsoft MLOps maturity model, and I like it because it is honest.

Most teams are not choosing between chaos and perfection. They are choosing the next useful step. Level 2 is a very good target: reproducible training, scheduled retraining, and centralized tracking solve many real operational problems before you automate deployment.

Level 3 adds the release discipline: a model gate, human approval, and a controlled promotion path. Level 4 is where monitoring and policy start to drive the loop with much less manual intervention.

For the workshop, we will show pieces of all five levels in one repository. That does not mean every team should implement all five at once. For many groups, the right Monday-morning move is to get from Level 1 to Level 2: stop retraining by hand, pin the environment, and make the feature contract explicit.

SOURCE: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/mlops-maturity-model
TRANSITION: To do that, you need to know what is worth versioning.""",
    )

    d.table_slide(
        "P2.5", "What to version: code, data, features, models, environments",
        ["Artifact", "Version it as", "Fabric", "Azure ML"],
        [
            ["Code", "Git commit + CI result", "Notebook or repo source", "Repo, components, and YAML jobs"],
            ["Data contract", "Manifest + checks", "Lakehouse tables + pipeline checks", "Data asset + prep checks"],
            ["Features", "Named table + split column", "`ml.asset_day_features`", "Registered input asset"],
            ["Model", "Version + metrics + lineage", "ML model version + pointer table", "Registered model + registry"],
            ["Environment", "Pinned packages", "Runtime or Environment item", "`env-fleet-sklearn` and image build"],
        ],
        col_w=[1.1, 1.5, 2.0, 1.7],
        size=14,
        side=[
            dict(title="Data scientist", body="Treat the split, label, and environment as part of the experiment.", icon="user", tone="node"),
            dict(title="Data engineer", body="Fail the pipeline if the contract changed and nobody approved it.", icon="server", tone="azure"),
        ],
        takeaway="If you cannot name and reload an artifact, you have not really versioned it.",
        minutes=2.5, core=False,
        notes="""This table is deliberately practical. If I ask, "Which exact thing do I need to rebuild the prediction table from last month?", I want an answer for each row.

Code is obvious: Git commit, tests, pipeline definition. Data contract means the raw and curated inputs have named checks and expected counts. Features means the table name and the split column are stable and not recreated ad hoc. Model means the version, the metrics, and the lineage back to the run. Environment means the package set that made the run reproducible.

Fabric and Azure ML express these ideas differently, but the concept is the same. Fabric tends to keep more of the story close to the lakehouse and workspace. Azure ML tends to formalize the assets and the serving path.

On Monday morning, I want data scientists to stop thinking of the model file as the only artifact. And I want data engineers to stop treating feature and scoring tables as disposable by-products.

TRANSITION: The environment pin is the easiest place to see why this matters.""",
    )

    d.code_slide(
        "P2.6", "Reproducible environments start with pins",
        """name: env-fleet-sklearn
dependencies:
  - python=3.11
  - pip:
      - mlflow==2.16.2
      - azureml-mlflow
      - scikit-learn==1.6.1
      - pandas==2.2.3
      - sqlalchemy<2.1
""",
        lang="yaml",
        file="environments\\conda-fleet-sklearn.yml",
        side=[
            dict(title="AML constraint", body="The MLflow 2.16.2 pin is a platform compatibility rule, not a workshop preference.", icon="alert-triangle", tone="amber"),
            dict(title="Fabric contrast", body="Fabric Runtime 2.0 is GA, but MLflow 3 still needs an explicit install in notebooks.", icon="layers", tone="node"),
        ],
        source="Microsoft Learn: AML MLflow compatibility, verified 2026-10-18",
        minutes=2.5, core=False,
        notes="""This slide is the most useful small habit in the part: pin first, then optimize.

In Azure Machine Learning, the hard constraint is explicit. The documented safe path is MLflow 2.16.2 with `azureml-mlflow`. If someone upgrades to MLflow 2.17 or MLflow 3 semantics, the workshop can stop being reproducible very quickly. That is why the rebuild guide literally says the pin is not optional.

Fabric tells a slightly different story. Runtime 2.0 is the current GA runtime and its built-in packages are stable, but Fabric's MLflow 3 support still requires an explicit install because notebooks ship MLflow 2.x by default. So the Monday-morning action is the same in both worlds: do not rely on accidental package state.

For data scientists, this means that "it worked in my notebook yesterday" is not enough evidence. For data engineers, it means environment definitions belong in the same review path as code and pipeline changes.

SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview
TRANSITION: Once the environment is stable, the run itself becomes your lab notebook.""",
    )

    d.cards(
        "P2.7", "Experiment tracking is your lab notebook",
        [
            dict(icon="git-branch", title="Parameters", body="Model kind, learning rate, leaf count, and the feature set.", tone="node"),
            dict(icon="bar-chart-3", title="Metrics", body="Log precision@top5% plus valid and test PR-AUC and ROC-AUC.", tone="azure"),
            dict(icon="database", title="Data version", body="Record the exact feature asset or table build you trained on.", tone="azure"),
            dict(icon="file-text", title="Artifacts", body="Keep the PR curve, MLmodel file, signature, and evaluation JSON.", tone="success"),
            dict(icon="git-merge", title="Tags", body="Use tags such as workshop, git SHA, and candidate status for search and promotion.", tone="success"),
        ],
        cols=5,
        takeaway="If a future you cannot explain a run in two minutes, you did not log enough.",
        minutes=3, core=True,
        notes="""Experiment tracking is not bureaucracy. It is memory.

In the MLflow tour, the parent run carries the workshop tag and each child run logs the model family, the flat metrics, and, for the winning model, the signature and input example. In the end-to-end demos, the training and promotion flow add the data version, the Git SHA, and the candidate status tag on the registered version.

That matters because six weeks later nobody remembers which run was the "good one" unless the run is searchable and self-explaining. A PR-AUC without its split, label, and data contract is only a number.

For a data scientist, Monday morning means: every serious run logs parameters, metrics, signature, and enough tags to search it later. For a data engineer, it means: the pipeline should stamp the run with the upstream asset version and the source commit automatically.

WATCH OUT: tags are not a substitute for a clean naming convention. Use both.
TRANSITION: But even a perfectly logged run is unsafe if the data contract is weak.""",
    )

    d.table_slide(
        "P2.8", "Data contracts: check the data before you train on it",
        ["Check", "Why it matters", "Our contract", "Monday morning"],
        [
            ["Schema", "Do not break when a field appears late", "`coolant_level_pct` appears only after 2026-07-01", "Keep bronze ingestion tolerant, document the change"],
            ["Volume", "Catch missing files and late arrivals", f"{n(F.bronze_rows)} raw rows; {n(F.late_rows)} late events", "Alert on missing partitions before training"],
            ["Range/null", "Bad values should become explicit nulls", f"{n(F.out_of_range)} spikes nulled, never imputed silently", "Fail or quarantine when sensors leave their physical range"],
            ["Identity resolution", "Joins are only useful when ids match", f"Telematics resolved {pct(1 - F.unresolved / F.silver_rows)}", "Stop the line if mapping drops below the agreed floor"],
            ["Label window", "Do not train on incomplete futures", f"Labels stop on 2026-09-23; positive rate {pct(F.positive_rate)}", "Keep unlabeled and score rows out of evaluation"],
        ],
        col_w=[1.0, 1.45, 1.55, 1.55],
        tbl=dict(size=13.5),
        takeaway="A data contract turns 'bad data' into a fast, readable failure instead of a hidden model bug.",
        minutes=4, core=True,
        notes="""This is where MLOps becomes very concrete for data engineers.

Every row here comes from our shared contract. We know schema evolution happens. We know some events arrive late. We know 217 spikes are out of physical range and must become null. We know identity resolution is a first-class quality signal, not just a side effect of a join. And we know the label window closes on 2026-09-23, so rows after that date are not eligible for evaluation.

The most important example for this audience is identity resolution. If your telemetry mapping suddenly drops from about 97.9 percent to 94 percent, the model has not failed yet, but your features are already suspect. That is a data-contract failure and should stop training.

For data scientists, Monday morning means checking that the contract explains what the model can trust. For data engineers, it means turning these checks into named assertions with clear messages, not tribal knowledge.

TRANSITION: The split itself is also part of the contract, because leakage can make a weak model look brilliant.""",
    )

    d.custom(
        "P2.9", "Avoid leakage: split by time and leave a gap",
        _draw_time_split,
        takeaway="Time-based splits with a purge gap tell the truth; random splits usually flatter the model.",
        minutes=5, core=True,
        notes="""This is one of the most important pictures in the deck.

Our label asks whether a corrective work order opens in the next seven days. That means rows close together in time can share future information. If I randomly split asset-days, some precursors of the same failure can land in train and test at the same time. The model then looks smarter than it really is.

So we keep the split column from the contract and we purge seven days on both sides of the validation block. The train window runs from 2026-04-15 to 2026-07-24. Validation is 2026-08-01 to 2026-08-24. Test is 2026-09-01 to 2026-09-23. The two purge windows remove overlap in the label horizon. We also leave the late September rows unlabeled and score only the final day.

For a data scientist, Monday morning means: do not re-split in a notebook because it is convenient. For a data engineer, it means the pipeline should publish the split column once and every downstream job should respect it.

IF SHORT ON TIME: keep this slide and skip the optional promotion slides later.
TRANSITION: Once the split is honest, we can compare models honestly too.""",
    )

    d.chart_slide(
        "P2.10", "A model is only good compared to a baseline",
        ["Prevalence", "Rule baseline", "Logistic regression", "Gradient boosting"],
        {"Test PR-AUC": [
            F.pr_auc_test["prevalence"],
            F.pr_auc_test["rule"],
            F.pr_auc_test["logistic"],
            F.pr_auc_test["hgb"],
        ]},
        fmt="0.000",
        chart=dict(highlight=3),
        side=[
            dict(title="Read it honestly", body=f"The positive rate is about {d3(F.pr_auc_test['prevalence'])}, so the baseline is not zero.", icon="line-chart", tone="node"),
            dict(title="Useful signal", body=f"The winning model is about {d3(F.pr_auc_test['hgb'])}; without fault-code features it drops to about {d3(F.pr_auc_test['hgb_no_fault_codes'])}.", icon="activity", tone="success"),
        ],
        takeaway="A modest model can still be valuable when it clearly beats prevalence and a simple rule.",
        minutes=4, core=True,
        notes="""I want to normalize a healthy engineering mindset here.

This is a five-percent-positive problem. So a test PR-AUC near 0.045 is the prevalence baseline, not a failure. Our hand-written rule baseline gets to about 0.068. Logistic regression gets to about 0.29. HistGradientBoosting lands around 0.38, which is better but not magical.

That is exactly the right teaching point. We are not selling a miracle model. We are showing an honest workflow that can take a modest but useful signal into production safely. The model is worth considering because it beats the naive baselines and because planners can act on a ranked list every day.

The ablation is also useful: without the fault-code features, the best model drops to about 0.28 on test. That tells us those features carry real information.

For a data scientist, Monday morning means always plotting a baseline before celebrating a candidate. For a data engineer, it means the pipeline should publish the baseline metrics too, not just the winner.

TRANSITION: And the winner still does not go live by intuition.""",
    )

    d.flow(
        "P2.11", "Promotion needs a gate, not a feeling",
        [
            dict(icon="table", title="Freeze the test split", body="Champion and challenger are both scored on the same held-out test rows."),
            dict(icon="bar-chart-3", title="Compare the JSON", body="Use test PR-AUC and precision@top5% from code, not from memory."),
            dict(icon="shield-check", title="Apply the rule", body="Promote only if PR-AUC improves by at least 0.01 and precision drops by no more than 0.02."),
            dict(icon="users", title="Approve production", body="A person still approves the prod change before traffic or pointers move."),
        ],
        minutes=3.5, core=False,
        notes="""The key sentence here is that the gate is code.

Both demos implement the same logic. The challenger must beat the champion on test PR-AUC by at least 0.01, and precision at the top five percent of asset-days must not get worse by more than 0.02. If that rule fails, the decision is hold or reject, even if the model felt promising during exploration.

Fabric expresses the outcome by updating a small champion pointer table after the gate passes. Azure Machine Learning expresses it through the gate report, model registration, and the later promotion workflow. Different mechanics, same idea: do not let taste replace a repeatable decision.

Just as important, the gate is not the same thing as production approval. The workshop flow keeps a human approval step before the live production move. That is where business risk, outage windows, and downstream consumers still matter.

WATCH OUT: use a frozen test split for the gate. Do not keep reusing validation metrics as if they were independent evidence.
TRANSITION: After the gate, you still need the right deployment pattern.""",
    )

    d.compare(
        "P2.12", "Deployment patterns: batch, online, shadow, canary",
        dict(
            title="Daily batch first",
            sub="Our default path for planners",
            icon="calendar",
            tone="azure",
            items=[
                "Best when users can wait for the nightly score table.",
                "Cheap, replayable, and easy to audit in OneLake or SQL.",
                "Fits our workshop scenario: 264 assets scored on 2026-09-30.",
                "One failed run can be retried without user-visible downtime.",
            ],
        ),
        dict(
            title="Online with rollout",
            sub="Only when latency is a requirement",
            icon="rocket",
            tone="amber",
            items=[
                "Use when a human or system needs a score immediately.",
                "Shadow or mirrored traffic lets a new model observe live inputs safely.",
                "Canary or blue/green rollout makes the new version user-visible gradually.",
                "In this workshop, AML is the mature online path; Fabric model endpoints are still preview.",
            ],
        ),
        source="Microsoft Learn: AML endpoints and Fabric model endpoints, verified 2026-10-18",
        takeaway="Choose the serving pattern from latency and risk, not from what looks more modern.",
        minutes=3.0, core=False,
        notes="""This slide is really a decision slide.

Our business use case is daily maintenance planning, so batch scoring is the right default. It is cheaper, easier to replay, and easier to inspect. A planner wants a trustworthy table in the morning, not millisecond latency.

Online serving is the right answer only when latency is the business requirement. The benefit of Azure Machine Learning here is not only the endpoint itself. It is the rollout discipline: traffic split, blue/green, and mirror or shadow traffic. That lets a new model watch real requests before it takes responsibility for decisions.

I also want to be explicit about preview status. Fabric ML model endpoints exist, but they are still preview, so they are not the operational anchor of this workshop. The safer live-demo and production story for online rollout is Azure Machine Learning.

For Monday morning, data scientists should ask which consumers truly need immediate scoring. Data engineers should ask how they would replay or roll back each serving pattern.

SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online?view=azureml-api-2
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints
TRANSITION: Whatever the serving pattern, three different pipelines usually sit behind it.""",
    )

    d.flow(
        "P2.13", "Three pipelines: code, training, release",
        [
            dict(icon="git-branch", title="CI", body="Lint code, validate assets, and keep environment or YAML definitions healthy.", tone="node"),
            dict(icon="workflow", title="CT", body="Prepare data, train, evaluate, gate, and register the candidate.", tone="azure"),
            dict(icon="rocket", title="CD", body="Promote with approvals, then move traffic or pointers in a controlled way.", tone="success"),
        ],
        back=dict(label="MONITORING CREATES THE NEXT CT RUN"),
        takeaway="CI checks the code, CT checks the candidate model, and CD moves only approved artifacts.",
        minutes=3.5, core=False,
        notes="""One source of confusion in ML projects is that people say pipeline when they mean three different things.

Continuous integration, or CI, is the software path: lint, unit checks, asset validation, maybe infrastructure what-if. Continuous training, or CT, is the machine-learning path: prep the feature data, train a candidate, evaluate it, and produce a gate result. Continuous deployment, or CD, is the release path: move the approved artifact into serving, with approvals and rollback options.

Those triggers are different, so the owners are different too. A pull request can fire CI. A schedule or drift alert can fire CT. A human approval and an environment rule can fire CD.

For data scientists, Monday morning means knowing where their experimental notebook ends and the CT pipeline begins. For data engineers, it means refusing to mix every concern into one giant job just because the scheduler makes that easy.

TRANSITION: Once you separate the pipelines, you can be much clearer about what actually gets promoted.""",
    )

    d.compare(
        "P2.14", "Dev, test, prod: what you promote",
        dict(
            title="Promote code and retrain",
            sub="Common when the workspace owns the data",
            icon="layers",
            tone="azure",
            items=[
                "Move notebooks, pipelines, and environment metadata through dev, test, and prod.",
                "Retrain or re-log the model in each target workspace on local data.",
                "Strong fit for Fabric where Git sync focuses on item metadata, not model run history.",
                "Tradeoff: the prod model is reproducible from code, but not byte-identical to dev by default.",
            ],
        ),
        dict(
            title="Promote the tested artifact",
            sub="Common when serving discipline leads",
            icon="server",
            tone="success",
            items=[
                "Register the candidate once, then share the same model version through an AML registry.",
                "Deploy the tested model and its environment into test and prod workspaces.",
                "Traceability is strong because the serving artifact is the thing you approved.",
                "Tradeoff: registry access, approvals, and rollout controls become part of the platform contract.",
            ],
        ),
        minutes=3.5, core=False,
        notes="""There are two honest promotion stories, and teams often mix them.

The first is code promotion. You move the notebook, pipeline, and environment definitions forward, then the target workspace retrains or re-logs the model there. This is a very natural Fabric story because Git sync focuses on item metadata and does not ship model run history or model versions as the main artifact.

The second is artifact promotion. In Azure Machine Learning, the recommended enterprise pattern is to share the winning model and environment through a registry, then deploy that tested version into test and prod workspaces. That gives tighter reproducibility on the thing users actually consume.

Neither path is universally better. The right choice depends on whether your operational center of gravity is the lakehouse or the serving platform.

For Monday morning, data scientists should ask whether they need the same exact tested artifact in prod. Data engineers should ask which path is easier to audit and recover in their organization.

TRANSITION: After deployment, monitoring becomes the early-warning system.""",
    )

    d.cards(
        "P2.15", "Monitoring: input drift first, accuracy later",
        [
            dict(icon="shield-check", title="Data quality", body="Schema, volume, freshness, and identity checks run before scoring.", tone="node"),
            dict(icon="line-chart", title="Input drift", body="PSI on sensors and classes tells us when the input world changed.", tone="azure"),
            dict(icon="bar-chart-3", title="Prediction drift", body="Watch score distributions while labels are still delayed.", tone="azure"),
            dict(icon="clock", title="Delayed labels", body="Accuracy arrives later because work orders lag the physical event.", tone="amber"),
            dict(icon="bell", title="Operations", body="Alert routing, retries, and run logs decide whether monitoring is useful.", tone="success"),
        ],
        cols=5,
        takeaway="When labels are late, input drift and score drift are the first signals you can trust.",
        minutes=3.5, core=False,
        notes="""Monitoring is not one chart. It is a stack of signals with different latencies.

The first layer is data quality: did the files arrive, did the schema change, did the identity-resolution rate drop? The second is input drift: did the sensor distributions move enough that the feature space now looks different? The third is prediction drift: are we suddenly scoring far more assets as risky, even before labels arrive? Only after that do we get delayed performance evidence from the work orders themselves.

That is why I say input drift first, accuracy later. In our October drift batch, we do not have trustworthy October labels yet, so it would be misleading to pretend otherwise.

For data scientists, Monday morning means deciding which monitoring signal is an early warning and which one is final proof. For data engineers, it means routing alerts to humans who can act, not just writing a CSV nobody reads.

TRANSITION: Here is what that looks like on our own data.""",
    )

    d.chart_slide(
        "P2.16", "Drift in our data: real shift versus expected season",
        [
            "Excavator vibration",
            "WheelLoader vibration",
            "WheelLoader temp",
            "Excavator temp",
            "Paver temp",
            "Compactor temp",
            "MobileCrane temp",
        ],
        {"PSI": [3.7113, 2.7825, 0.9587, 0.8804, 0.1862, 0.1097, 0.1033]},
        fmt="0.00",
        chart=dict(highlight=0),
        side=[
            dict(title="Major shift", body="PSI above 0.25 means investigate now. Our four major pairs come from the injected firmware change.", icon="alert-triangle", tone="amber"),
            dict(title="Moderate does not mean broken", body="Engine-temperature drift around 0.10 to 0.19 is expected seasonal cooling for three classes.", icon="calendar", tone="node"),
        ],
        takeaway="The monitoring job should separate expected seasonality from genuinely suspicious shift.",
        minutes=3.5, core=False,
        notes="""These are real PSI values from the contract, and they tell a good operational story.

The major shifts are the ones we injected on purpose: Excavator and WheelLoader temperature and vibration. Those are the pairs I would want on an alert. They clearly exceed the 0.25 threshold.

But I also want to protect the team from noisy monitoring. Paver, Compactor, and MobileCrane show moderate engine-temperature drift because October is cooler than September. That is an expected seasonal effect, not a broken process. So the job of monitoring is not only to detect movement. It is to classify movement well enough that humans do not lose trust in the alert stream.

For a data scientist, Monday morning means checking whether the shift is plausible before calling for retraining. For a data engineer, it means attaching enough context to the alert that people can tell expected seasonality from a pipeline or device problem.

TRANSITION: Once the alerts exist, you still need a retraining policy.""",
    )

    d.flow(
        "P2.17", "When to retrain: schedule, trigger or both",
        [
            dict(icon="calendar", title="Schedule", body="Retrain weekly or monthly when the process is stable and the cost is predictable.", tone="node"),
            dict(icon="bell", title="Drift trigger", body="Start a candidate run when PSI or score drift crosses an agreed threshold.", tone="azure"),
            dict(icon="bar-chart-3", title="Performance trigger", body="Use delayed labels to confirm whether the live model actually degraded.", tone="azure"),
            dict(icon="users", title="Manual override", body="Let a human force or block a run after incidents, outages, or business changes.", tone="success"),
        ],
        back=dict(label="RETRAIN IS NOT REDEPLOY"),
        minutes=3, core=False,
        notes="""Retraining policy is really risk policy.

Pure schedules are easy to operate, but they can be wasteful. Pure trigger-based retraining sounds elegant, but it can be noisy or fragile if the upstream alert logic is immature. Most teams end up with both: a predictable schedule plus drift or performance signals that can create an extra candidate run.

The important phrase on the slide is retrain is not redeploy. A retrained candidate still goes through evaluation and the same promotion gate. Drift is evidence to investigate, not automatic permission to replace the champion.

For data scientists, Monday morning means agreeing which trigger creates a new candidate and which trigger only pages a human. For data engineers, it means keeping the schedule and trigger wiring separate enough that one failure mode does not disable both.

TRANSITION: Policies matter because someone will later ask who changed the model and why.""",
    )

    d.cards(
        "P2.18", "Governance: know what is deployed, who changed it and why",
        [
            dict(icon="git-merge", title="Lineage", body="A score should point back to a model version, a run, and a feature build.", tone="node"),
            dict(icon="lock", title="Access", body="Separate who can train, approve, deploy, and view production logs.", tone="azure"),
            dict(icon="users", title="Approvals", body="Production moves should leave a visible human decision trail.", tone="azure"),
            dict(icon="file-text", title="Model card", body="Keep the purpose, data assumptions, metrics, and limits close to the artifact.", tone="success"),
            dict(icon="clock", title="Audit trail", body="When something looks wrong, you need the timeline of changes before the blame game starts.", tone="success"),
        ],
        cols=5,
        minutes=3, core=False,
        notes="""Governance can sound abstract, so I reduce it to five questions.

Can I trace a score back to the model, run, and feature build that created it? Can the same person both approve and deploy without oversight? When production changes, can I see who approved it? If a new team member inherits the system, is there a short model card that explains what the artifact is for and what it assumes? And if something fails, can I reconstruct the timeline quickly?

Fabric and Azure Machine Learning give different pieces of this picture. Fabric is strong on workspace context and lakehouse lineage. Azure Machine Learning is strong on explicit serving, rollout, and model registry patterns. In both cases, the Monday-morning action is the same: make the audit path boring and obvious before you need it under pressure.

TRANSITION: Governance is easier when the hand-offs between people are explicit too.""",
    )

    d.table_slide(
        "P2.19", "Who owns what: roles and hand-offs",
        ["Role", "Monday morning", "Owns", "Hands off to"],
        [
            ["Data engineer", "Are the raw feeds, contracts, and feature tables healthy?", "Pipelines, checks, tables", "Data scientist with a clean feature contract"],
            ["Data scientist", "Did the candidate beat the baseline and stay explainable enough?", "Label, features, runs, gate evidence", "ML engineer with a promoted candidate"],
            ["ML engineer", "Can the artifact be served, rolled out, and rolled back safely?", "Endpoints, rollout, gate wiring", "Platform team for runtime and identity changes"],
            ["Platform team", "Is the environment, RBAC, and networking path stable?", "Compute, identities, registries", "All teams through shared standards"],
            ["Business owner", "Will this change improve a real decision and who accepts the risk?", "Approval criteria and action path", "Prod approver and consumers"],
        ],
        col_w=[1.0, 1.65, 1.25, 1.55],
        tbl=dict(size=13.5),
        takeaway="Most MLOps failures are role failures before they are tooling failures.",
        minutes=3.5, core=False,
        notes="""This is the least glamorous slide in the part, and often the most important.

In a real project, the weak point is frequently not the model or the pipeline. It is the hand-off. The data engineer assumes someone else is watching identity resolution. The data scientist assumes the endpoint team will catch a signature mismatch. The business owner is asked to approve a production change without a clear success criterion.

So I like to phrase each role as a Monday-morning question. What is the first thing this person checks when they sit down? If that question is fuzzy, the operating model is fuzzy too.

Please adapt these rows locally. Small teams may combine roles. Large teams may split them further. The point is not the job titles. The point is that each critical decision has an owner and each owner knows what evidence they should see.

TRANSITION: Let us close Part 2 with a quick self-assessment.""",
    )

    d.discuss(
        "P2.20", "Exercise: where is your team on the ladder?",
        [
            dict(title="Q1  Versions", body="Do you version code, data contract, feature table, model, and environment together?"),
            dict(title="Q2  Split", body="Is your train, valid, and test split fixed in code and defended against leakage?"),
            dict(title="Q3  Gate", body="What evidence must a challenger show before someone says yes to production?"),
            dict(title="Q4  Monitor", body="Which signal tells you first that the live world changed: quality, drift, labels, or incidents?"),
            dict(title="Q5  Owner", body="Who stops the line when the contract fails or drift crosses the threshold?"),
        ],
        when="10 min",
        minutes=10, core=False,
        notes="""Here is the exercise script.

Ask people to work in pairs for five minutes. Each pair answers the five questions quickly, without overthinking the perfect future-state design. The goal is not a maturity score. The goal is to surface one gap that would matter on Monday morning.

After five minutes, ask each pair to share only one gap and one next step. Capture those on a flipchart or whiteboard. Good examples are: "we do not version environments", "our split is still random", "we have no clear owner for drift alerts", or "prod approval is informal and not recorded".

If the room is quiet, give them a starter: most teams already know more than they think about Levels 0 and 1, and their first valuable move is often a Level 2 habit.

ASK: Which single improvement would reduce your operational risk the most in the next 30 days?
IF SHORT ON TIME: ask for written answers to Q3 and Q5 only.
TRANSITION: In Part 3 we take these concepts off the slide and into the actual build.""",
    )
