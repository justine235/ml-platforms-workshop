"""Part 1: Fabric vs Azure ML with MLflow concepts (P1.0-P1.19)."""
from __future__ import annotations

from deck_core import HEAD, MONO, box, text
from deck_lib import Deck
from facts import F, n, pct, d3


FABRIC_MLFLOW_SRC = "Microsoft Learn: Fabric MLflow/runtime, verified 2026-10-18"
AML_MLFLOW_SRC = "Microsoft Learn: Azure ML MLflow docs, verified 2026-10-18"
HYBRID_SRC = "Microsoft Learn: OneLake with Azure ML, verified 2026-10-18"

FABRIC_MLFLOW_URLS = [
    "https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-experiment",
    "https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-model",
    "https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging",
    "https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging",
    "https://learn.microsoft.com/en-us/fabric/data-science/model-scoring-predict",
    "https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints",
    "https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview",
]

AML_MLFLOW_URLS = [
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-mlflow-models-online-endpoints?view=azureml-api-2",
]

ONELAKE_URLS = [
    "https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-machine-learning",
    "https://learn.microsoft.com/en-us/python/api/azure-ai-ml/azure.ai.ml.entities.onelakedatastore?view=azure-python",
    "https://learn.microsoft.com/en-us/fabric/data-factory/azure-machine-learning-activity",
]


def _part_divider(d: Deck, sid: str, number: int | str, title: str, subtitle: str, goals: list[str], when: tuple[str, str],
                  *, minutes: float, notes: str, chapter: bool = False) -> None:
    def draw(f):
        s = f.s
        box(s, 0.0, 0.0, 4.5, 7.5, tone="solid", radius=0.01, name="bleed panel")
        text(s, 0.55, 1.45, 3.5, 0.3, ["CHAPTER" if chapter else "PART"], size=16, color="azure_line",
             font=MONO, bold=True, track=3, wrap=False, lint=False, name="label")
        text(s, 0.5, 1.8, 3.7, 2.45, [str(number)], size=148, color="white", font=HEAD, bold=True,
             wrap=False, lint=False, name="number")
        text(s, 0.6, 6.0, 3.4, 0.28, [when[0]], size=15, color="white", font=MONO, bold=True, wrap=False,
             lint=False, name="time")
        text(s, 0.6, 6.32, 3.4, 0.26, [when[1]], size=13.5, color="azure_line", wrap=False, lint=False, name="length")
        text(s, 5.2, 2.9, 7.2, 0.78, [subtitle], size=19, color="muted", name="subtitle")
        text(s, 5.2, 4.05, 7.0, 0.25, ["WHAT YOU WILL LEAVE WITH"], size=11, color="azure", font=MONO,
             bold=True, track=1.2, wrap=False, lint=False, name="goals heading")
        y = 4.4
        for goal in goals:
            text(s, 5.2, y, 7.0, 0.34, [f"• {goal}"], size=17, anchor="m", name=f"goal {goal[:20]}")
            y += 0.48

    d.custom(sid, title, draw, kind="section", notes=notes, minutes=minutes, footer="num",
             title_box=(5.2, 1.5, 7.4, 1.15), title_size=31)


def build(d: Deck) -> None:
    _part_divider(
        d,
        "P1.0",
        1,
        "Understanding the ML platforms at Microsoft",
        "Two ML platforms share MLflow, but they start from different operating models.",
        ["See where Fabric starts", "See where Azure ML starts", "Reuse one MLflow mental model in both"],
        ("09:20 – 10:50", "90 minutes"),
        minutes=1,
        notes="""This part gives the audience a map before we touch MLOps.

I want to make one point early: this is not an old-versus-new story. Fabric and Azure Machine Learning exist because teams start from different centers of gravity. Some teams begin with the lake, notebooks, and shared analytics. Others begin with dedicated ML environments, managed endpoints, and release controls.

Today I use the same scenario and the same MLflow vocabulary in both, so the comparison stays concrete. The question is not "which brand wins." The question is "which operating model fits this team, this data, and this release path."

TRANSITION: Let us start with the shortest honest map of the platform landscape.""",
    )

    d.arch(
        "P1.1",
        "Three platforms exist because they start from different work",
        [
            dict(id="fabric", label="Microsoft Fabric", sub="Data first: OneLake, lakehouse, notebooks, BI", col=0, row=0, tone="azure"),
            dict(id="aml", label="Azure Machine Learning", sub="ML lifecycle first: compute, jobs, registries, endpoints", col=1, row=0, tone="node"),
            dict(id="foundry", label="Microsoft Foundry", sub="Models and agents first: tools, responses, orchestration", col=2, row=0, tone="success"),
            dict(id="shared", label="Shared Azure base", sub="Entra ID, storage, networking, governance, monitoring", col=0, row=1, cspan=3, tone="paper"),
        ],
        edges=[
            ("shared", "fabric"),
            ("shared", "aml"),
            ("shared", "foundry"),
        ],
        groups=[dict(label="Different center of gravity, shared identity and governance", c0=0, r0=0, c1=2, r1=1, tone="azure")],
        takeaway="Think in centers of gravity: data platform, ML platform, or agent platform.",
        minutes=5,
        notes="""If someone asks me for the one-slide answer, this is it.

Fabric starts from shared data work. The natural first questions are about lakehouse storage, Spark notebooks, pipelines, SQL, and BI. Azure Machine Learning starts from the model lifecycle. The natural first questions are about training compute, environments, jobs, registries, deployment, and monitoring. Microsoft Foundry starts from models, tools, and agents. The natural first question there is how an application reasons and acts across enterprise systems.

Underneath, they are not three disconnected worlds. Identity is still Microsoft Entra ID. Storage, networking, and monitoring still live in Azure. That is why hybrid patterns are practical instead of painful.

For this workshop, the structured data and model path live mostly in Fabric and Azure ML. Foundry appears later as the agent layer on top of reconciled data.

SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:2] + AML_MLFLOW_URLS[:1]) + """
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry
TRANSITION: First, let me show the Fabric side in its own terms.""",
    )

    d.cards(
        "P1.2",
        "Fabric is a data platform that also does machine learning",
        [
            dict(title="OneLake", body="One storage plane for files, tables, shortcuts, and analytics items.", tone="azure"),
            dict(title="Lakehouse + Spark", body="The lakehouse notebook is the normal place to clean, join, and feature-engineer data.", tone="azure"),
            dict(title="Experiments + models", body="MLflow tracking is built in through Experiment and ML model items.", tone="azure"),
            dict(title="SQL + BI scoring", body="Registered models can score with `PREDICT` when the signature is valid.", tone="node"),
            dict(title="RTI + reports", body="Real-Time Intelligence and Power BI stay close to the same shared data copy.", tone="node"),
        ],
        cols=3,
        core=False,
        minutes=3,
        notes="""When I say Fabric is data-first, I mean the storage and analytics plane comes before the model-management plane.

The strength is proximity. The same workspace can hold the lakehouse, the notebook, the SQL endpoint, the semantic model, and the MLflow-tracked experiment. That keeps the path from raw data to scored table short and visible to the same team.

It also changes the mental model of ML. In Fabric, machine learning is another workload beside data engineering, SQL, and BI. That is efficient when one team owns the whole path from source to report.

The trade-off is that some production ML controls are lighter or newer than in a dedicated ML platform. We will be precise about those differences instead of hiding them.

IF SHORT ON TIME: Skip this slide and keep the simpler platform comparison on P1.4 and P1.7.
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:5]) + """ """,
    )

    d.cards(
        "P1.3",
        "Azure Machine Learning is an ML platform that connects to your data",
        [
            dict(title="Workspace", body="One control plane for runs, jobs, models, endpoints, and monitoring.", tone="azure"),
            dict(title="Compute + jobs", body="You choose clusters, environments, schedules, and command or pipeline jobs.", tone="azure"),
            dict(title="Registry + endpoints", body="Models, environments, and components promote through explicit ML assets.", tone="azure"),
            dict(title="Data assets", body="Data usually stays in ADLS, Blob, or OneLake `/Files`, then AML reads it.", tone="node"),
            dict(title="Operations", body="RBAC, rollout controls, monitoring, and endpoint auth are first-class concerns.", tone="node"),
        ],
        cols=3,
        core=False,
        minutes=3,
        notes="""Azure Machine Learning starts from a different question: how do I run and operate models with explicit control?

The workspace is an ML control plane. Compute, jobs, environments, model registration, endpoints, schedules, and monitoring are front and center. That suits teams who separate data engineering from ML engineering, or who need stronger operational boundaries around training and serving.

The data usually lives elsewhere. AML connects to it through datastores, data assets, direct paths, or shared storage patterns. That is why the data story can feel more decoupled than Fabric, but the ML operations story can feel more complete.

The important practical point for today is that AML still speaks MLflow. The same training and model-logging concepts remain recognizable even when the surrounding platform is different.

IF SHORT ON TIME: Skip this slide and use P1.4 plus the MLflow chapter as the main comparison.
SOURCE: """ + " ; ".join(AML_MLFLOW_URLS) + """ """,
    )

    d.table_slide(
        "P1.4",
        "Follow one model through its life: each platform is strong in a different place",
        ["Lifecycle step", "Fabric", "Azure ML"],
        [
            ["Prepare", "Lakehouse tables, notebooks, and pipelines stay together.", "Read data assets or storage paths; prep can stay outside AML."],
            ["Explore", "Notebook next to the lake and BI context.", "Notebook or compute instance with explicit env choice."],
            ["Train", "Notebook or Spark job; MLflow is preconfigured.", "Command job, pipeline job, or notebook with AML tracking."],
            ["Track", "Experiment item with built-in run comparison.", "Workspace tracking server with job lineage."],
            ["Register", "ML model item, version-first.", "Workspace registry, version-first with AML asset controls."],
            ["Deploy", "Batch scoring is mature; endpoints are preview.", "Managed online and batch endpoints are the production path."],
            ["Monitor", "Build it from jobs, metrics, reports, alerts.", "Managed endpoint logs and model monitoring are current."],
            ["Retrain", "Often notebook or pipeline driven inside Fabric.", "Often schedule, event, or pipeline driven inside AML."],
        ],
        col_w=[1.45, 2.5, 2.5],
        size=12.5,
        takeaway="Fabric keeps more of the lifecycle inside the data workspace; Azure ML externalizes the ML control plane.",
        minutes=6,
        notes="""This is the slide I use when the room wants the fast operational answer.

Walk down the lifecycle once. Preparation and exploration are naturally strong in Fabric because the lakehouse, notebooks, and analytics surfaces are already together. Training and tracking work in both. Registration also works in both, but the registry semantics are not identical, which matters later. Deployment and monitoring are where Azure ML is more mature as a dedicated ML platform.

So the decision is not about whether one of them can technically train a model. Both can. The decision is about where the team wants the center of operational gravity to be.

ASK: In your current estate, which row causes the most friction today: data prep, deployment, or monitoring?
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:6] + AML_MLFLOW_URLS[:4]) + """
TRANSITION: The next difference is not features. It is how compute and cost behave.""",
    )
    d.compare(
        "P1.5",
        "Compute and cost behave differently because the bill is attached to different things",
        dict(
            title="Microsoft Fabric",
            sub="Shared capacity",
            tone="azure",
            items=[
                "One capacity pays for notebooks, SQL, pipelines, BI, and ML together.",
                "Usage is measured in capacity units and smoothed over short windows.",
                "Great when one platform team shares the same lake-centric estate.",
                "Preview serving features still sit inside that same platform bill.",
            ],
        ),
        dict(
            title="Azure Machine Learning",
            sub="Per-compute / endpoint resources",
            tone="node",
            items=[
                "Training clusters, jobs, and endpoints consume their own ML resources.",
                "Clusters can scale to zero; endpoints remain an explicit serving surface.",
                "Great when ML engineering wants isolated compute and release controls.",
                "Quota, warm-up, and endpoint reservation details matter earlier.",
            ],
        ),
        core=False,
        takeaway="Ask first: are you buying a shared analytics platform, or a dedicated ML control plane?",
        minutes=4,
        notes="""This is where many platform debates finally become concrete.

Fabric puts many workloads on one shared capacity. That is elegant when the same organization owns notebooks, pipelines, SQL, BI, and machine learning in one place. The cost question becomes: how much shared platform do we want to reserve, and when do we pause or scale it?

Azure Machine Learning is different. Training compute, endpoints, and related resources are more explicit. That gives ML engineers more control over isolation, rollout, and operations, but it also means cluster warm-up, endpoint capacity, and quota planning show up sooner in the design.

So I do not present this as cheaper versus more expensive. I present it as a different answer to "which bill is this work attached to?"

WATCH OUT: Do not quote list prices on stage. The workshop only needs the operating-model difference, not exact euros.
SOURCE: https://learn.microsoft.com/en-us/fabric/enterprise/plan-capacity
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online?view=azureml-api-2
TRANSITION: The next choice is where the data physically sits and how the ML platform reaches it.""",
    )

    d.arch(
        "P1.6",
        "Data access is the practical bridge: OneLake on one side, datastores on the other",
        [
            dict(id="fabric", label="Fabric workspace", sub="Lakehouse, SQL, notebooks", col=0, row=0, tone="azure"),
            dict(id="onelake", label="OneLake `/Files`", sub="The documented easy path for AML access", col=1, row=0, tone="azure"),
            dict(id="shortcuts", label="Shortcuts / ABFSS", sub="Reuse shared storage paths without duplicate copies", col=0, row=1, tone="paper"),
            dict(id="aml", label="AML datastores + data assets", sub="Read ADLS, Blob, or OneLake files", col=2, row=0, tone="node"),
            dict(id="tables", label="Lakehouse `/Tables`", sub="Often copy or code path, not the simple UI story", col=1, row=1, tone="amber"),
        ],
        edges=[
            ("fabric", "onelake"),
            ("shortcuts", "onelake", "shared path"),
            ("onelake", "aml", "ABFSS"),
            ("tables", "aml", "careful"),
        ],
        groups=[dict(label="Best-documented hybrid path today", c0=0, r0=0, c1=2, r1=1, tone="azure")],
        core=False,
        source=HYBRID_SRC,
        minutes=3,
        notes="""This slide matters because hybrid architecture succeeds or fails on boring path details.

The best-documented easy story today is OneLake files, especially through ABFSS or a datastore-style reference. Azure ML can read OneLake `/Files`, and that is enough for the workshop path where Fabric engineers create features and AML trains or serves the model.

The awkward bit is lakehouse `/Tables`. Code-based reads may work, but the simple no-copy UI story is not the documented easy route. When people say "OneLake and AML integrate," I immediately ask whether they mean files or tables.

The safer teaching line is this: Fabric is very comfortable producing the feature export, and AML is very comfortable consuming that export, especially through files and shared storage.

SOURCE: """ + " ; ".join(ONELAKE_URLS) + """
TRANSITION: With that bridge in mind, here is the most honest side-by-side summary.""",
    )

    d.table_slide(
        "P1.7",
        "Fabric and Azure ML side by side",
        ["Dimension", "Fabric", "Azure ML"],
        [
            ["Main user", "Data team in one workspace", "ML engineer / platform team"],
            ["Compute", "Shared capacity", "Clusters, jobs, endpoints"],
            ["Tracking", "Experiment item, preconfigured", "Workspace MLflow tracking server"],
            ["Registry", "ML model item, versions first", "Workspace registry, versions first"],
            ["Deployment", "Batch strong; endpoints preview", "Managed online and batch endpoints"],
            ["CI/CD", "Git + deployment metadata", "Assets, jobs, registries, OIDC pipelines"],
            ["Networking + governance", "Workspace-centric", "Explicit ML resource controls"],
            ["Maturity", "Integrated analytics + ML", "Dedicated production ML platform"],
        ],
        col_w=[1.55, 2.35, 2.45],
        size=12.5,
        side=[
            dict(title="Caution", body="Fabric ML model endpoints are still preview, so call that out in the room.", tone="amber"),
            dict(title="Why both exist", body="Fabric optimizes for shared data work. Azure ML optimizes for explicit ML operations.", tone="azure"),
        ],
        core=False,
        source="Microsoft Learn: Fabric and AML docs, verified 2026-10-18",
        minutes=4,
        notes="""This is the compressed comparison I would leave up during questions.

Notice how often the difference is not capability but emphasis. Both platforms can track runs and register models. Both can train. Both can participate in MLOps. The distinction is where each platform makes the experience native and where it expects you to bring more explicit engineering choices.

I changed the planned compare layout to a native table because eight rows read more honestly as a table than as crowded side bullets.

WATCH OUT: Say clearly that Fabric model endpoints are preview. That single sentence prevents a lot of over-interpretation.
IF SHORT ON TIME: Skip this slide if P1.4 already landed well.
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:6] + AML_MLFLOW_URLS[:4]) + """
TRANSITION: Up to now we have compared platforms. Next I switch to the shared language underneath them.""",
    )

    _part_divider(
        d,
        "P1.8",
        "ML",
        "MLflow is the common language of both platforms",
        "If you know experiments, runs, model packages, and registry versions, you already know most of the story.",
        ["Map the same objects in both platforms", "See where registry semantics diverge", "Use one portable training script"],
        ("MLflow chapter", "Core concept block"),
        minutes=1,
        chapter=True,
        notes="""Now I switch from products to vocabulary.

This is the most important teaching move in Part 1. Many people in the room already know open-source MLflow or a Databricks-flavored MLflow workflow. If I anchor the rest of the comparison on experiment, run, model package, signature, and registry version, the platform differences become much easier to understand.

So for the next slides, do not think Fabric first or Azure ML first. Think MLflow first.

TRANSITION: Here is the whole object model in one picture.""",
    )

    d.arch(
        "P1.9",
        "MLflow keeps the same object model even when the platform wrapper changes",
        [
            dict(id="exp", label="Experiment", sub="Groups all attempts on one problem", col=0, row=0, tone="azure"),
            dict(id="run", label="Run", sub="One execution with params, metrics, tags, artifacts", col=1, row=0, tone="azure"),
            dict(id="model", label="Model folder", sub="Flavors, signature, input example, requirements", col=2, row=0, tone="azure"),
            dict(id="reg", label="Registry", sub="Named model plus immutable versions", col=3, row=0, tone="node"),
            dict(id="serve", label="Serving / scoring", sub="Batch or online paths load the same model contract", col=4, row=0, tone="success"),
            dict(id="portable", label="Portable unit", sub="Move the MLflow model folder, not the UI state", col=1, row=1, cspan=3, tone="amber"),
        ],
        edges=[
            ("exp", "run"),
            ("run", "model"),
            ("model", "reg"),
            ("reg", "serve"),
            ("model", "portable"),
        ],
        groups=[dict(label="Same MLflow nouns in local, Fabric, and Azure ML", c0=0, r0=0, c1=4, r1=0, tone="azure")],
        takeaway="The portable thing is the model package; the platform wrapper around it is not fully portable.",
        minutes=5,
        notes="""This is the mental model I want people to keep for the rest of the day.

An experiment groups attempts. A run records one attempt. Inside that run, MLflow stores parameters, metrics, tags, artifacts, and possibly a logged model. That logged model is a folder with an `MLmodel` contract, flavor metadata, requirements, and, when we do it properly, a signature and input example. The registry gives that model a stable name and immutable versions.

Everything after that is where the wrapper matters. Fabric wraps the model in ML model items and Fabric scoring paths. Azure ML wraps it in its workspace registry and managed deployment surfaces. But the core MLflow nouns are still there.

ASK: Which of these nouns already exists in your current toolchain today?
SOURCE: https://mlflow.org/docs/latest/ml/tracking/
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:2] + AML_MLFLOW_URLS[:3]) + """
TRANSITION: First, let us look at tracking, because that is where the two notebooks feel most similar.""",
    )

    d.compare(
        "P1.10",
        "Tracking looks the same in both platforms, but the tracking URI lives in a different place",
        dict(
            title="Fabric",
            sub="Preconfigured in the notebook",
            tone="azure",
            items=[
                "Import `mlflow` and tracking is already wired for the current workspace.",
                "Experiment items show params, metrics, artifacts, and run comparison.",
                "Autologging is on by default in data-science notebooks.",
                "Cross-workspace logging uses an `sds://.../mlflow` URI when you set it explicitly.",
            ],
        ),
        dict(
            title="Azure ML",
            sub="Workspace tracking server",
            tone="node",
            items=[
                "AML jobs and AML compute wire tracking automatically inside the workspace.",
                "External clients fetch `mlflow_tracking_uri` and set it explicitly.",
                "Runs, params, metrics, and artifacts are still normal MLflow objects.",
                "Autologging is available, but you call it intentionally.",
            ],
        ),
        source=FABRIC_MLFLOW_SRC,
        minutes=4,
        notes="""This is the first place where the audience should feel continuity instead of product shock.

The run object is the same. Parameters, metrics, tags, artifacts, and experiments still behave like MLflow. The difference is how the platform helps you connect to the tracking backend.

In Fabric, the notebook experience is very opinionated. Tracking and authentication are preconfigured for the current workspace, and autologging is on by default in Data Science notebooks. In Azure ML, jobs and AML-hosted notebooks also wire tracking automatically, but the external-client story is more explicit: fetch the workspace tracking URI and point MLflow at it.

That is why I say the platforms speak real MLflow. The client API remains familiar. The first wrapper difference is simply where the URI comes from and what the notebook preconfigures for you.

SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:4] + AML_MLFLOW_URLS[:2]) + """
TRANSITION: Next, let us look at the one model detail that makes later scoring paths much easier.""",
    )

    d.code_slide(
        "P1.11",
        "Models: the signature is what makes scoring easy",
        """signature = infer_signature(
    valid[core.FEATURES].head(20),
    model.predict(valid[core.FEATURES].head(20)),
)
info = compat.log_sklearn_model(
    model=model,
    model_name="model",
    signature=signature,
    input_example=valid[core.FEATURES].head(5),
)""",
        file="03-demo-mlflow-tour\\code\\mlflow_tour_local.py",
        hl=[1, 7, 8],
        side=[
            dict(title="Fabric impact", body="`PREDICT` and Fabric model endpoints need a usable signature.", tone="azure"),
            dict(title="AML impact", body="No-code deployment works best when the MLflow model carries signature and input example.", tone="node"),
        ],
        takeaway="Always log signature and input example. They turn a model artifact into a safer contract.",
        minutes=4,
        notes="""This code is short, but it prevents a lot of pain later.

The signature tells the scoring surface what columns and shapes the model expects. The input example gives a concrete sample payload. In the live tour I use this to provoke a schema error on purpose, because that makes the value obvious: the model refuses silent misuse instead of accepting the wrong shape and returning nonsense.

In Fabric, that signature is effectively required for the comfortable scoring paths, especially `PREDICT` and model-endpoint scenarios. In Azure ML, it is not just documentation. It improves the deployment contract and keeps the MLflow model useful for no-code deployment paths.

WATCH OUT: Say clearly that the reason-code strings in later demos are not model attributions. The signature is the input-output contract, not an explanation method.
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[4:6] + AML_MLFLOW_URLS[1:2]) + """
TRANSITION: Once the model package exists, the biggest platform differences start in the registry.""",
    )

    d.compare(
        "P1.12",
        "The registry is where the two platforms differ most",
        dict(
            title="Fabric",
            sub="ML model item, version-first",
            tone="azure",
            items=[
                "The safe teaching pattern is a named model plus immutable versions.",
                "Loading by `models:/name/1` is documented and stable.",
                "Docs emphasize default version and endpoint activation, not stage promotion.",
                "Stages and aliases are not a documented Fabric-first pattern.",
            ],
        ),
        dict(
            title="Azure ML",
            sub="MLflow registry inside the workspace",
            tone="node",
            items=[
                "Registry operations are workspace-local in the MLflow integration.",
                "Load by version or `latest`; those are clearly documented.",
                "Stages exist only through the MLflow SDK, not as a Studio or SDK-v2 primitive.",
                "Deployment from a model stage is not supported.",
                "Aliases are VERIFY, so the safest workshop pattern is versions plus tags.",
            ],
        ),
        takeaway="Teach version numbers as the shared truth; treat stages and aliases as platform-specific and uneven.",
        source=AML_MLFLOW_SRC,
        minutes=5,
        notes="""This is the practical MLOps difference that surprises people most.

Fabric's documented model story is version-first. Azure ML also has versions at the center, but it keeps more of the old MLflow stage semantics alive through the MLflow SDK. Even there, stage-based deployment is not supported, and the modern AML Studio and SDK-v2 story does not revolve around stages.

So my safe line for a mixed audience is simple: use immutable model versions as the truth, add tags for context, and do not build the workshop story around aliases or stage promotion.

VERIFY: Current AML docs do not give me a workshop-safe alias story, so I do not depend on aliases live.
VERIFY: Current Fabric docs do not document a Fabric-native stage or alias workflow as the main pattern.
SOURCE: """ + " ; ".join(FABRIC_MLFLOW_URLS[:2] + AML_MLFLOW_URLS[2:3]) + """
TRANSITION: The registry differences are important, but the quieter trap is version compatibility in the runtimes themselves.""",
    )

    d.table_slide(
        "P1.13",
        "Versions are the quiet trap",
        ["Surface", "Verified version state", "Safe workshop rule"],
        [
            ["Fabric Runtime 1.3", "Bundled `mlflow-skinny 2.12.2`", "Classic MLflow 2.x patterns only."],
            ["Fabric Runtime 2.0", "Bundled `mlflow-skinny 2.22.0`", "Current GA runtime, still MLflow 2.x by default."],
            ["Fabric MLflow 3", "Supported up to 3.1 with explicit install", "Treat as Fabric-only extension, not shared baseline."],
            ["Azure ML", "`mlflow<=2.16.2` with `azureml-mlflow`", "Pin the environment and stay on classic model logging."],
        ],
        col_w=[1.5, 2.4, 2.4],
        size=12.5,
        side=[
            dict(title="Lowest common contract", body="Shared demo code stays on classic MLflow 2.x semantics and a portable model folder.", tone="azure"),
            dict(title="Amber warning", body="Do not let notebook-scoped `%pip` upgrades drift across platforms before Friday.", tone="amber"),
        ],
        source="Microsoft Learn: Fabric runtime and AML MLflow pin, verified 2026-10-18",
        minutes=4,
        notes="""This is the slide that saves the presenter from avoidable surprises.

Fabric Runtime 1.3 and Runtime 2.0 ship different bundled MLflow versions. Fabric can also do MLflow 3, but only after an explicit install. Azure ML is stricter: its MLflow integration is pinned to 2.16.2 or earlier through `azureml-mlflow`.

So the safe workshop pattern is not to chase the newest MLflow feature everywhere. The safe pattern is to keep the shared script on the lowest common operational contract and treat MLflow 3 features as a Fabric-only extension when needed.

WATCH OUT: Say this twice, because people will otherwise assume that "MLflow-compatible" means "latest MLflow everywhere."
SOURCE: https://github.com/microsoft/synapse-spark-runtime
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview
SOURCE: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
TRANSITION: The good news is that the training script itself can stay almost unchanged.""",
    )

    d.code_slide(
        "P1.14",
        "The same training script runs on a laptop, in Fabric, and in an Azure ML job",
        """compat.configure_tracking(args.tracking_uri)
compat.set_experiment(args.experiment)
df = core.load_features(features_path)
model, metrics = core.train_and_evaluate(
    df, kind=args.model_kind
)
with mlflow.start_run(run_name=args.run_name):
    flat = core.mlflow_metrics(metrics)
    mlflow.log_metrics(flat)""",
        file="03-demo-mlflow-tour\\code\\train_fleet_model.py",
        hl=[1, 2, 7, 8],
        side=[
            dict(
                title="Only line that moves",
                body=[
                    dict(text='Local: `sqlite:///mlflow.db`', bullet=True),
                    dict(text="Fabric: no URI in the notebook", bullet=True),
                    dict(text="AML: use `workspace.mlflow_tracking_uri` or let the job inject it", bullet=True),
                ],
                tone="azure",
            ),
            dict(title="What stays the same", body="Features, train/evaluate logic, metrics, and model packaging do not change.", tone="success"),
        ],
        minutes=3,
        notes="""This is the portability point I want them to remember.

The model code and the data contract stay the same. The platform-specific lines sit around the edge: where files live, how the tracking URI is set, and how a registry or job wrapper is invoked. That is a much healthier form of portability than rewriting the training logic for each platform.

In practice, the same shared script runs on a laptop, in Fabric, and in an AML job. The wrapper changes. The training logic, metrics, and model package do not.

SOURCE: See `03-demo-mlflow-tour\\code\\train_fleet_model.py`, `fabric\\nb_mlflow_tour_fabric.py`, and `azureml\\aml_mlflow_tour.py`.
TRANSITION: Now that the audience has the vocabulary, I can walk the live demo with one script and three backends.""",
    )

    d.demo(
        "P1.15",
        "Demo 1: the MLflow tour, one script and three platforms",
        [
            ("Local: show the tracking URI, experiment, and one finished leaderboard", "5 min"),
            ("Fabric: open the Experiment item and compare the same run shape", "5 min"),
            ("Fabric: call out runtime pin and version-first model registration", "5 min"),
            ("Azure ML: show the tracking URI and the `mlflow<=2.16.2` pin", "5 min"),
            ("Azure ML: show registration / no-code deploy path and close on portability", "5 min"),
        ],
        [
            "Use the saved `summary.json` and local notebook outputs if training is slow.",
            "If Fabric is unavailable, switch to a prebuilt Experiment item or screenshot.",
            "If AML compute is cold, use the AML notebook cells and `job-train-fleet.yml`.",
        ],
        [
            f"HGB test PR-AUC is about {d3(F.pr_auc_test['hgb'])}; ROC-AUC is about {d3(F.roc_auc_test['hgb'])}.",
            "The signature check should fail when `temp_mean` is missing.",
            "Keep repeating the honest line: portable model folder yes, portable run history no.",
        ],
        "25 min",
        where="Laptop  →  Fabric workspace  →  Azure ML workspace",
        core=False,
        minutes=25,
        notes="""This demo is comparison, not showmanship. I want the room to see the same MLflow ideas three times with as little drama as possible.

Start local, because it is the cleanest baseline. Show the tracking URI, the experiment, and the run leaderboard. Keep it short. The local segment only exists so the rest of the comparison feels familiar.

Then spend the next ten minutes in Fabric. Show the Experiment item and one run. Say clearly that the run semantics are the same MLflow run semantics, but the notebook and workspace preconfigure more for you. Also say clearly that Runtime 2.0 ships MLflow 2.22.0, while MLflow 3 is an explicit upgrade, not a default.

Finish with ten minutes on Azure ML. Show the tracking URI pattern, the pin to MLflow 2.16.2 or earlier, and the registry plus deployment story. End on the honest portability line.

DEMO: Follow `03-demo-mlflow-tour\\run-of-show.md`.
WATCH OUT: Do not improvise on aliases or stage-based deployment.
IF SHORT ON TIME: Use the 10-minute version from `run-of-show.md`.
SOURCE: `03-demo-mlflow-tour\\run-of-show.md`
SOURCE: `03-demo-mlflow-tour\\README.md`
SOURCE: `03-demo-mlflow-tour\\troubleshooting.md`
TRANSITION: After the demo, I land the limits in one explicit portability slide.""",
    )

    d.cards(
        "P1.16",
        "What travels between platforms and what does not",
        [
            dict(title="Portable", body="The MLflow model folder: `MLmodel`, flavors, weights, signature, input example, requirements. Tested from older to newer MLflow only.", tone="azure"),
            dict(title="Portable", body="The shared data contract and the training logic in `fleet_ml_core.py` and `train_fleet_model.py`.", tone="azure"),
            dict(title="Not portable", body="Run history, lineage graphs, comparison UI, and platform-native registry metadata.", tone="amber"),
            dict(title="Not portable", body="Endpoint objects, workspace RBAC, and stage or alias semantics.", tone="amber"),
        ],
        cols=2,
        takeaway="Move the model artifact deliberately; rebuild the operational wrapper in the target platform.",
        minutes=3,
        notes="""This is the most honest slide after the demo.

I want the audience to leave with a precise portability claim, not a vague one. The portable thing is the MLflow model folder and the code that produced it. That folder carries the `MLmodel` contract, the flavors, the requirements, the signature, and the inference behavior.

What does not move cleanly is the wrapper around it: run history, lineage views, endpoint objects, platform RBAC, and registry semantics. Those must be rebuilt or re-registered in the target platform.

That is not a weakness. It is normal. A model artifact is portable. An operating model is not automatically portable.

WATCH OUT: The tested direction is forward only. A model exported under MLflow 2.12.2 loaded under 3.17.0 with identical predictions. The reverse, a model saved by MLflow 3.x and loaded on a 2.x runtime such as Fabric Runtime 1.3 or Azure ML, was not tested and I would expect it to fail (3.x saves scikit-learn models in the skops format by default). Train on the oldest runtime you plan to target.

SOURCE: `03-demo-mlflow-tour\\portability\\portability.md`
TRANSITION: Once the audience accepts that limit, choosing a platform becomes much easier.""",
    )

    d.flow(
        "P1.17",
        "How to choose: five questions usually point to Fabric, Azure ML, or both",
        [
            dict(title="Where is the data?", body="Lakehouse first often leans Fabric.", tone="azure"),
            dict(title="Who builds?", body="Unified data team or dedicated ML team?", tone="node"),
            dict(title="How is it served?", body="Batch, BI, online API, or all three?", tone="node"),
            dict(title="What governance?", body="Workspace-centric or explicit ML controls?", tone="node"),
            dict(title="What skills exist?", body="Spark + SQL, MLOps, or both?", tone="success"),
        ],
        back=dict(label="MANY TEAMS END UP USING BOTH"),
        core=False,
        minutes=3,
        notes="""I use these five questions more than feature checklists.

If the data gravity is in the lakehouse and the same team owns preparation, analysis, and reporting, Fabric often feels natural. If serving, rollout, monitoring, and explicit ML platform ownership dominate the discussion, Azure ML usually starts to win. And when the answer is different for different rows in the lifecycle, the honest answer is both.

This is why I do not push a dogmatic recommendation. The better question is where each concern belongs.

ASK: Which of these five questions would decide the answer fastest in your organization?
TRANSITION: The rest of the workshop uses the hybrid answer, because that is where many real teams land.""",
    )

    d.arch(
        "P1.18",
        "The hybrid pattern we will build today keeps Fabric close to data and AML close to serving",
        [
            dict(id="src", label="Raw sources", sub="Telematics, CMMS, ERP", col=0, row=0, tone="amber"),
            dict(id="fabric", label="Fabric ETL + features", sub="Reconcile and publish features", col=1, row=0, tone="azure"),
            dict(id="files", label="OneLake `/Files`", sub="Documented bridge for AML input", col=2, row=0, tone="azure"),
            dict(id="aml", label="Azure ML train + serve", sub="Job, registry, online or batch endpoint", col=3, row=0, tone="node"),
            dict(id="consumers", label="Scores to BI + agent", sub="Write back for reporting and questions", col=4, row=0, tone="success"),
        ],
        edges=[
            ("src", "fabric"),
            ("fabric", "files"),
            ("files", "aml"),
            ("aml", "consumers"),
        ],
        groups=[
            dict(label="Fabric data plane", c0=0, r0=0, c1=2, r1=0, tone="azure"),
            dict(label="Azure ML control plane", c0=3, r0=0, c1=3, r1=0, tone="node"),
        ],
        core=False,
        source=HYBRID_SRC,
        minutes=3,
        notes="""This is the architecture we build in the rest of the day.

Fabric does what it is naturally good at: ingest, reconcile, shape, and publish the feature-ready data. Azure ML does what it is naturally good at: controlled training, registration, and managed serving. Then the scores come back to shared data so reports and agents can consume them.

This is also why I keep saying `/Files` out loud. The bridge is simplest when the exported features are files with a clean path, not an assumption that every table surface is equally easy to consume everywhere.

SOURCE: """ + " ; ".join(ONELAKE_URLS) + """
TRANSITION: Let me close Part 1 in three sentences before we move to MLOps ideas.""",
    )

    d.recap(
        "P1.19",
        "Part 1 in three sentences",
        [
            dict(title="One vocabulary", body="Fabric and Azure ML both speak MLflow: experiments, runs, model packages, and versions."),
            dict(title="Two wrappers", body="The operational wrapper differs most in data gravity, registry semantics, and serving maturity."),
            dict(title="One honest hybrid", body="For this workshop, Fabric owns the data path and Azure ML owns the serving path."),
        ],
        question="Which of those three sentences is closest to the architecture you have today?",
        minutes=1,
        notes="""Let me land Part 1 clearly.

First, both platforms speak real MLflow, so the core concepts travel well. Second, the wrapper around those concepts is not identical, and the registry plus serving story is where the practical differences matter most. Third, the workshop uses a hybrid path because that is often the most realistic design in large organizations.

ASK: Which sentence matches your architecture today, and which one do you want to move toward?
TRANSITION: Part 2 is about MLOps concepts that sit above both platforms.""",
    )
