"""Opening: O1-O5 (20 minutes). Also the style reference for the other content modules."""
from __future__ import annotations

from deck_lib import Deck
from facts import F, n


def build(d: Deck) -> None:
    d.title_slide(
        "O1", "From notebook to production: ML platforms on Microsoft",
        "Fabric, Azure Machine Learning and Foundry: a workshop for data scientists and data engineers",
        "23 OCTOBER 2026  \u00b7  FULL-DAY WORKSHOP",
        [("microsoft-fabric", "Microsoft Fabric", "Data and machine learning on one platform"),
         ("azure-machine-learning", "Azure Machine Learning", "The ML lifecycle, with full control"),
         ("microsoft-foundry", "Microsoft Foundry", "Models and agents on your data")],
        minutes=2,
        notes="""Welcome, everyone, and thank you for giving this day to the workshop.

Today is practical. We start with a map of the machine learning platforms at Microsoft, so you know what each one is for. Then we add the MLOps concepts that apply to all of them. After lunch we build one complete system, twice: once on Fabric and once on Azure Machine Learning. We finish with an agent that answers questions on top of the reconciled data.

Three promises for the day. First, everything you see is rebuildable: the data, the code and the guides are in the repository, with the numbers you should expect. Second, all data is synthetic, so there is nothing confidential on screen. Third, I will tell you what is generally available and what is still in preview, because that changes how you plan.

Please interrupt me at any time. You work with data and models every day, and your questions are more useful than my slides.""")

    d.agenda(
        "O2", "Today in four parts, with three demos you can rebuild",
        [("09:00 \u2013 09:20", "Opening", "The story we follow all day, and what you will take away", "20 MIN", "talk"),
         ("09:20 \u2013 10:50", "Part 1  \u00b7  Fabric vs Azure ML", "The two ML platforms and the MLflow concepts behind both. Demo 1: MLflow tour", "90 MIN", "part"),
         ("10:50 \u2013 11:05", "Break", "", "", "break"),
         ("11:05 \u2013 12:20", "Part 2  \u00b7  MLOps concepts", "From a notebook to a system you can trust", "75 MIN", "part"),
         ("12:20 \u2013 13:20", "Lunch", "", "", "break"),
         ("13:20 \u2013 15:15", "Part 3  \u00b7  End-to-end demo", "ETL, ML and MLOps on Fabric, then on Azure ML. Demo 2", "115 MIN", "part"),
         ("15:15 \u2013 15:30", "Break", "", "", "break"),
         ("15:30 \u2013 16:45", "Part 4  \u00b7  Foundry and the data agent", "Reconcile logs from several sources, then ask questions. Demo 3", "75 MIN", "part"),
         ("16:45 \u2013 17:00", "Wrap-up", "Takeaways, resources and next steps", "15 MIN", "talk")],
        minutes=3, takeaway="Parts 1 and 2 give you the vocabulary. Parts 3 and 4 put it to work.",
        notes="""Here is the rhythm of the day. We alternate between short concept blocks and live demos, with two breaks and a one-hour lunch.

Part 1 is about the platforms: what Fabric is, what Azure Machine Learning is, and why MLflow is the common language between them. You will see the first demo there, a short MLflow tour with one script running in three places.

Part 2 is about MLOps as a set of ideas, independent of any product: versioning, testing, release gates, monitoring and who owns what.

Part 3 is the longest block. We take one use case from raw logs to a scored, monitored model, first on Fabric and then on Azure ML.

Part 4 puts an agent on the reconciled data, so people can ask questions in plain language.

If we run late, I will cut optional slides, never the demos. And if you only have time for half of the day, the speaker notes say which parts are core.

TRANSITION: Before the content, let me ask what you expect to leave with.""")

    d.cards(
        "O3", "By the end of the day you can do five things",
        [dict(icon="scale", title="Choose a platform", body="Pick Fabric, Azure ML or both for a given team and workload."),
         dict(icon="git-branch", title="Explain MLflow in both", body="Experiments, runs, models and the registry, and where the two differ."),
         dict(icon="workflow", title="Draw an MLOps flow", body="From versioned data to a gated release and a drift alert."),
         dict(icon="repeat", title="Rebuild the demos", body="Run each demo from the repository and check your numbers."),
         dict(icon="bot", title="Put an agent on your data", body="Ask in plain language, and know when the agent should refuse.")],
        cols=5, icon_pos="top", minutes=5,
        notes="""These are outcomes, not features. If you can do these five things on Monday morning, the day was worth it.

One: choose a platform. Not by fashion, but by looking at where your data lives, who builds the models and how they are served.

Two: explain MLflow in both platforms. MLflow is the thread that ties the day together. Experiments, runs, models and the registry exist in Fabric and in Azure ML, with small but important differences.

Three: draw an MLOps flow on a whiteboard. From versioned data to a release gate to a drift alert.

Four: rebuild the demos. Each demo folder has a rebuild guide with the expected numbers.

Five: put an agent on top of your data in a safe way, including the questions it should refuse to answer.

ASK: A quick poll, hands up. Who uses Databricks today? Azure Machine Learning? Fabric? Nothing yet, just notebooks? Note the answers: I will come back to them in Parts 1 and 3 so the comparisons match your starting point.""")

    d.arch(
        "O4", "Three systems disagree about the same machines",
        [dict(id="tel", label="Telematics", sub=f"{n(F.bronze_rows)} raw readings, JSON", icon="activity", col=0, row=0, tone="amber"),
         dict(id="cmms", label="CMMS", sub=f"{n(F.cmms_rows)} work orders, CSV", icon="wrench", col=0, row=1, tone="amber"),
         dict(id="erp", label="ERP", sub=f"{n(F.erp_assets)} registered assets, CSV", icon="database", col=0, row=2, tone="amber"),
         dict(id="rec", label="Reconcile", sub="Match ids, time zones and faults", icon="git-merge", col=1, row=1, tone="azure"),
         dict(id="gold", label="Reconciled tables", sub="One version of the truth", icon="table", col=2, row=1, tone="azure"),
         dict(id="risk", label="Failure-risk model", sub="Work order needed in 7 days?", icon="flask-conical", col=3, row=0, tone="azure"),
         dict(id="agent", label="Data agent", sub="Questions in plain language", icon="bot", col=3, row=2, tone="success")],
        edges=[("tel", "rec"), ("cmms", "rec"), ("erp", "rec"), ("rec", "gold"), ("gold", "risk", "features"),
               ("gold", "agent", "tables"), ("risk", "agent", "scores")],
        groups=[dict(label="Same machines, three spellings", c0=0, r0=0, c1=0, r1=2, tone="amber")],
        minutes=6, source="All data is synthetic. Contoso Fleet is a fictional company.",
        notes="""Here is the story we follow all day. Contoso Fleet is a fictional construction company with about 300 heavy machines on 12 sites in 8 European countries.

Three systems describe those machines, and none of them agrees with the others. The telematics platform sends a reading every six hours: temperatures, pressures, vibration, fuel and fault codes, as JSON lines. The maintenance system, the CMMS, holds the work orders, in CSV, in local time with no time zone. The ERP holds the asset register: the golden list of machines, with a clean key.

The trouble is that each system spells the machine's identity differently, uses a different clock and has its own mistakes. The same excavator can appear under five different spellings.

From this one dataset come three problems, and they are the three threads of the day. First, reconcile the sources: which critical faults never led to a work order, and which work orders have no fault behind them? Second, predict which machine needs a corrective work order in the next seven days. Third, let people ask questions on top of the reconciled data.

Everything is synthetic and generated by a script, so there is no customer data. The same data and the same expected numbers appear in every demo: if your screen shows a different count, it is a bug, not a surprise.

TRANSITION: Let me show you where everything lives, because you will rebuild it.""")

    d.cards(
        "O5", "Everything you see today is rebuildable",
        [dict(icon="database", title="Demo data",
              body=[dict(text="`02-demo-data`", size=13, color="muted"),
                    "A generator and a reference pipeline. Regenerate the data in about 40 seconds."]),
         dict(icon="git-branch", title="Demo 1: MLflow tour",
              body=[dict(text="`03-demo-mlflow-tour`", size=13, color="muted"),
                    "One training script on a laptop, in Fabric and in Azure ML."]),
         dict(icon="microsoft-fabric", title="Demo 2a: Fabric",
              body=[dict(text="`04-demo-fabric-e2e`", size=13, color="muted"),
                    "Notebooks, pipelines and CI/CD, with a rebuild guide."]),
         dict(icon="azure-machine-learning", title="Demo 2b: Azure ML",
              body=[dict(text="`05-demo-azureml-e2e`", size=13, color="muted"),
                    "Jobs, endpoints and GitHub Actions, with a rebuild guide."]),
         dict(icon="bot", title="Demo 3: data agent",
              body=[dict(text="`06-demo-foundry-data-agent`", size=13, color="muted"),
                    "The data agent, a Foundry agent and 30 test questions."]),
         dict(icon="file-text", title="Slides and guide",
              body=[dict(text="`01-slides`  `00-presenter-guide`", size=13, color="muted"),
                    "These slides with speaker notes, and the presenter guide."])],
        cols=3, minutes=4, core=False,
        notes="""This is the map of the repository. One folder per demo, and each folder has the same set of files: a README, a rebuild guide with the expected numbers, a run of show, a troubleshooting page and the code.

The demo data folder is the foundation. A generator creates the three raw sources and a reference pipeline computes every expected number in about forty seconds on a laptop. When we say that a count should be 207,691 silver rows, that is the number the reference pipeline produced.

The demos then reuse that data. Demo 1 is the MLflow tour. Demo 2 is the end-to-end build, in two halves: Fabric and Azure ML. Demo 3 is the agent.

You do not need to take notes on this: the slides and the speaker notes are in the same repository, along with a presenter guide that explains how each demo is run.

If something in the live demo breaks, and sometimes it will, there is a pre-baked fallback for every step. I will show you how to use it. That is also useful for you when you rebuild at your own pace.

TRANSITION: Enough preparation. Let us start with the platforms.""")
