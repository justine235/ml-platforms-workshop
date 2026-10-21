"""Wrap-up and appendix slides: C1-C4 and A0-A10."""
from __future__ import annotations

from deck_lib import Deck
from facts import F, d3, n, pct
from deck_core import BODY, MONO, PAL, box, text


def build(d: Deck) -> None:
    d.recap(
        "C1", "Five things to remember",
        [dict(title="Choose with purpose",
              body="Fabric keeps data and ML together, Azure ML goes deeper on ML, and Foundry adds agents."),
         dict(title="Keep one language",
              body="Experiments, runs, models, registry: one MLflow vocabulary."),
         dict(title="Draw the loop",
              body="Versioned data, a release gate and monitoring close the path from training back to retraining."),
         dict(title="Trust the numbers",
              body=f"{n(F.bronze_rows)} bronze rows become {n(F.silver_rows)} silver rows, then {n(F.assets_scored)} assets are scored."),
         dict(title="Ground agents in facts",
              body=f"{n(F.exceptions)} exceptions are explicit, and {pct(F.crit_match_rate)} of judged critical episodes match a work order.",
              tone="success")],
        question="Which of these five outcomes will you try first in your own environment?",
        minutes=3,
        takeaway="Pick the platform for the job, then keep the same data, MLflow and MLOps discipline across all of them.",
        notes="""This is the moment to close the loop with the five outcomes from the opening.

First, choose a platform deliberately. Fabric is strongest when the data estate, notebooks, pipelines and BI conversation want one shared workspace. Azure Machine Learning is stronger when the team needs a deeper classical-ML operating model with compute, environments, endpoints and registries under explicit control. Foundry matters when the question becomes agents, model choice and tool orchestration.

Second, keep one vocabulary. The audience only needs to learn experiment, run, model and registry once. After that, the platform differences are details of packaging, promotion and serving.

Third, draw the loop. A real system starts with versioned data, adds validation and release gates, then watches quality and drift in production. That is the MLOps picture I want them to remember.

Fourth, trust the numbers because they are reproducible. The same synthetic scenario starts from `bronze.telematics_events`, lands in deterministic gold tables, and reaches a held-out PR-AUC of about `0.385`.

Fifth, ground agents in facts. The agent is useful because the reconciled tables already encode business rules, exceptions and refusal cases.

ASK: Which of the five outcomes matters most in your team this quarter?
TRANSITION: If you wanted to start next week, here is a small 30-day plan.""")

    d.flow(
        "C2", "Your next 30 days can stay small and concrete",
        [dict(title="Week 1", body="Rehearse one demo end to end in your own tenant, and write down every prerequisite."),
         dict(title="Week 2", body="Pick one use case with one table owner, one success metric, and one business question."),
         dict(title="Week 3", body="Automate one pipeline: data in, features out, model tracked, and one repeatable score."),
         dict(title="Week 4", body="Review what failed, what drifted, and what should become a standard for the next pilot.")],
        back=dict(label="Review the pilot, then choose the next use case"),
        minutes=3,
        takeaway="Do one rebuild, one pilot, one pipeline and one review before you scale the ambition.",
        notes="""I want the next step to feel realistic, not heroic.

Week one is rehearsal. Pick only one demo path, ideally the one that looks most like your own platform choice, and run it in your own tenant. Do not optimize yet. Just discover the missing permissions, quotas, packages and naming rules.

Week two is a pilot selection exercise. Choose one use case, one table owner and one metric that business people already care about. Keep the question narrow enough that one team can actually finish it.

Week three is about turning a notebook into a repeatable system. The minimum bar is simple: one pipeline that lands data, one tracked training run, one registered model or equivalent version, and one repeatable scoring path.

Week four is the review. Look at failures, drift, manual steps and access problems. Decide what becomes a standard and what was only a demo convenience.

WATCH OUT: teams often try to pick three use cases and two platforms at once. That is how a pilot turns into a committee.
IF SHORT ON TIME: read the four week titles only and pause for questions.
TRANSITION: These are the public references and the repository folders I would use first.""")

    d.table_slide(
        "C3", "Resources: documentation and the repository",
        ["Topic", "Page on learn.microsoft.com", "What you will find"],
        [["Fabric data science", "`fabric/data-science`",
          "Notebooks, experiments, models, scoring and runtimes."],
         ["Fabric MLflow", "`fabric/data-science/mlflow-autologging`",
          "How Fabric configures MLflow and autologging."],
         ["Azure ML + MLflow", "`azure/machine-learning/how-to-use-mlflow-configure-tracking`",
          "Tracking URI, auth patterns and workspace behavior."],
         ["Azure ML MLOps", "`azure/machine-learning/how-to-github-actions-machine-learning`",
          "GitHub Actions with OIDC: a safe CI/CD start."],
         ["Foundry agents", "`azure/foundry/agents/quickstarts/prompt-agent`",
          "The agent-service quickstart for new work."],
         ["Fabric data agent", "`fabric/data-science/how-to-create-data-agent`",
          "Create, configure and publish a data agent."]],
        col_w=[1.0, 3.0, 2.2],
        size=12,
        side=[dict(title="Workshop kit (shared after the session)", tone="azure",
                   body=["`02-demo-data`  generator and reference outputs",
                         "`03-demo-mlflow-tour`  one script, three MLflow hosts",
                         "`04-demo-fabric-e2e`  Fabric ETL, ML and CI/CD",
                         "`05-demo-azureml-e2e`  AML pipeline, tracking and endpoints",
                         "`06-demo-foundry-data-agent`  serving, agents and eval"])],
        minutes=2,
        source="Microsoft Learn pages fetched 2026-10-19; repository paths are local.",
        notes="""These are the six public pages I would bookmark first, plus the repository folders that mirror the workshop structure.

The rule is simple. Start from the landing page when you need orientation, then jump to the narrower page when you need one exact behavior. That is why the list mixes broad entries, such as Fabric data science, with narrow entries, such as Fabric MLflow autologging or AML tracking configuration.

The repository is organized the same way as the day. `02-demo-data` is the foundation because it contains the generator and the deterministic reference outputs. `03-demo-mlflow-tour` isolates the common MLflow story. `04-demo-fabric-e2e`, `05-demo-azureml-e2e`, and `06-demo-foundry-data-agent` hold the three practical build paths.

If you rebuild later, start by reading the rebuild guide and troubleshooting page in the relevant folder before you run anything.

WATCH OUT: if you share this kit after the session, share only folders 02 to 06. Never share the presenter guide, and never share the hidden answer-key folder `truth/`.

SOURCE:
- https://learn.microsoft.com/en-us/fabric/data-science/
- https://learn.microsoft.com/en-us/fabric/data-science/mlflow-autologging
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-github-actions-machine-learning?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
TRANSITION: Thank you for spending the day on this. Let us use the remaining time for questions and for your own cases.""")

    def draw_questions(f):
        s = f.s
        text(s, f.x, f.y + 0.2, 9.4, 0.8,
             ["Thank you for the discussion, the challenges and the healthy skepticism."],
             size=23, color="ink", bold=True, name="thanks")
        text(s, f.x, f.y + 1.05, 8.8, 0.45,
             ["Which use case, constraint or pilot would you try first?"], size=17, color="muted", name="prompt")
        cards = [("Your case", "Name one use case, one data source and one operating constraint."),
                 ("One rebuild", "Point to the first demo path you want to rehearse next week."),
                 ("One improvement", "Tell me what would make the workshop more useful for your team.")]
        x = f.x
        y = f.y + 1.6
        w = 2.55
        gap = 0.25
        for title, body in cards:
            box(s, x, y, w, 2.15, tone="paper", name=f"q {title}")
            text(s, x + 0.18, y + 0.18, w - 0.36, 0.6, [title], size=18, bold=True, color="azure", name=f"qtitle {title}")
            text(s, x + 0.18, y + 0.62, w - 0.36, 1.15, [body], size=15, color="ink", name=f"qbody {title}")
            x += w + gap
        box(s, f.x, y + 2.45, 7.95, 0.78, tone="dark", radius=0.22, name="cta")
        text(s, f.x + 0.2, y + 2.55, 7.55, 0.52,
             ["If the room is quiet, restart with one choice: Fabric, Azure ML, or a hybrid path?"], size=16,
             color="white", bold=True, anchor="m", name="cta text")

    d.custom(
        "C4", "Questions", draw_questions,
        minutes=7,
        notes="""This slide is intentionally simple. The formal content is finished, and the remaining time is for the room.

I would open by thanking the audience for staying practical. They work with real pipelines, real failures and real delivery pressure, so their objections improve the workshop.

Then I would guide the Q and A with three prompts. First, their own use case: what business question, what data source and what operating constraint matter most? Second, the easiest rebuild path: which demo should they repeat first in their own environment? Third, feedback: what did they want more or less of today?

If the room is quiet, I would restart the conversation with one concrete question: based on today, would you start with Fabric, Azure ML, or a hybrid path?

IF SHORT ON TIME: keep the thank-you sentence and take only one final question.
TRANSITION: The remaining slides are reference slides for follow-up questions.""")

    def draw_appendix(f):
        s = f.s
        text(s, f.x, f.y + 0.05, 7.2, 0.3, ["WHAT IS INSIDE"], size=12, color="muted", font=MONO, bold=True, name="inside")
        goals = [
            ("MLflow concepts and version pins", "Fabric runtimes, AML pins and the cross-platform concept map."),
            ("Security, cost and troubleshooting", "The reference checklists I would use before a real pilot."),
            ("Scenario tables, rules and glossary", "The data contract, reconciliation logic and shared vocabulary.")
        ]
        y = f.y + 0.45
        for i, (title, body) in enumerate(goals, 1):
            box(s, f.x, y, 8.9, 1.1, tone="paper", name=f"goal {i}")
            text(s, f.x + 0.2, y + 0.24, 0.5, 0.3, [f"{i:02d}"], size=16, color="azure", font=MONO, bold=True, name=f"goal num {i}")
            text(s, f.x + 0.75, y + 0.2, 8.0, 0.34, [title], size=20, bold=True, color="ink", name=f"goal title {i}")
            text(s, f.x + 0.75, y + 0.64, 8.0, 0.36, [body], size=16, color="muted", name=f"goal body {i}")
            y += 1.3
        box(s, 9.85, 0.55, 2.95, 6.2, tone="dark", radius=0.28, name="rail")
        text(s, 10.2, 1.2, 2.3, 0.26, ["REFERENCE ONLY"], size=12, color="white", font=MONO, bold=True,
             name="rail label")
        text(s, 10.2, 1.75, 2.45, 3.2,
             ["Open these slides only when a detail question needs a precise answer."], size=21, color="white",
             bold=True, name="rail body")
        box(s, 10.2, 5.55, 1.6, 0.56, tone="amber_solid", radius=0.22, name="rail pill")
        text(s, 10.2, 5.6, 1.6, 0.46, ["A1-A10"], size=17, color="white", bold=True, align="c", anchor="m",
             name="rail pill text")

    d.custom(
        "A0", "Reference slides for follow-up questions", draw_appendix,
        title_box=(0.533, 0.66, 8.9, 0.6), title_size=30,
        minutes=0.5,
        notes="""This appendix is not part of the spoken story. It is here so we can answer practical follow-up questions without leaving the deck.

The first appendix slides summarize MLflow concepts and the main Fabric and Azure ML version pins. The middle block covers cost, security, Databricks-oriented mapping and the scenario data contract. The last slides cover troubleshooting and a glossary.

If someone asks a detail question, I would jump here instead of opening a browser.

IF SHORT ON TIME: skip the appendix entirely unless a question needs it.""")

    d.table_slide(
        "A1", "MLflow concept map: open source, Fabric, Azure ML",
        ["Concept", "Open-source MLflow", "Fabric", "Azure ML"],
        [["Tracking URI", "You point the client to a backend URI.", "Tracking is preconfigured; cross-workspace uses `sds://.../mlflow`.", "Jobs auto-configure; external clients fetch the workspace URI."],
         ["Experiment and run", "Experiment groups runs; runs log params, metrics and artifacts.", "Experiment item plus the same run semantics, with comparison UI.", "Standard MLflow experiment and run semantics in the AML workspace."],
         ["Autologging", "Opt in with `mlflow.autolog()`.", "On by default in Fabric data science notebooks.", "Supported, but you call it explicitly."],
         ["Signature", "Recommended model contract.", "Needed for the nice scoring paths and endpoints.", "Improves no-code deploy and Swagger."],
         ["Registry", "Standard registered model + versions.", "ML model items are version-first.", "Workspace-local registry with versions and lineage."],
         ["Stages and aliases", "Aliases are current; stages are deprecated since 2.9.", "Not a safe documented Fabric-first pattern.", "Stages are SDK-only; aliases are not a safe workshop dependency."],
         ["Batch scoring", "You build it around the model artifact.", "`PREDICT`, generated notebooks or `MLFlowTransformer`.", "Batch endpoints support MLflow models with a no-code path."],
         ["Real-time serving", "Not a managed service by itself.", "ML model endpoints exist, but are still preview.", "Managed online endpoints are the production-oriented managed path."]],
        col_w=[1.0, 1.45, 1.95, 1.95],
        size=12.0,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Concept map condensed from verified docs, 2026-10-18.",
        notes="""This is the appendix version of the Part 1 comparison. It keeps only the rows I would want during a follow-up question.

The most important simplification is that the same four MLflow nouns still hold: experiment, run, model and registry. The differences show up in how the platform wraps those nouns with UI, deployment and promotion patterns.

The two rows to underline in discussion are stages and aliases, and real-time serving. Fabric is version-first and its model endpoints are preview. Azure ML is the production-oriented managed serving path, but its MLflow integration is pinned to the older MLflow contract.

SOURCE:
- `03-demo-mlflow-tour/concept-map.md`
- `03-demo-mlflow-tour/slide-facts.md`
- https://learn.microsoft.com/en-us/fabric/data-science/machine-learning-cross-workspace-logging
- https://learn.microsoft.com/en-us/fabric/data-science/model-endpoints
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-mlflow-models-online-endpoints?view=azureml-api-2
VERIFY: alias support remains intentionally conservative because current platform docs do not make it a safe workshop dependency.""")

    d.table_slide(
        "A2", "Fabric runtimes and library versions",
        ["Area", "Runtime 2.0", "Runtime 1.3", "Why it matters"],
        [["Status", "Current GA production runtime.", "LTS baseline.", "Choose one runtime on purpose; do not mix silently."],
         ["Core stack", "Spark 4.1, Python 3.13, Delta 4.2.", "Older Spark/Python/Delta stack.", "Notebook behavior and package compatibility change with the runtime."],
         ["MLflow", "`mlflow-skinny 2.22.0`.", "`mlflow-skinny 2.12.2`.", "Cross-platform demos must respect AML's lower MLflow ceiling."],
         ["scikit-learn", "`1.6.1`.", "`1.2.2`.", "Metrics stay close, but packaging and warnings can move."],
         ["Data stack", "`pandas 2.3.3`, `numpy 2.4.1`, `pyarrow 24.0.0`.", "`pandas 2.1.4`, `numpy 1.26.4`, `pyarrow 14.0.2`.", "Pin the environment when a rebuild must stay reproducible."],
         ["SynapseML path", "`synapseml 1.1.3+spark4.1`, `synapseml-mlflow 2.0.4`.", "`synapseml 1.1.3`, `synapseml-mlflow 1.0.31`.", "Cross-workspace logging and scoring helpers follow these pins."],
         ["Extra notes", "MLflow 3 up to 3.1 is supported with explicit install; pure Python notebooks default to Python 3.12.", "Runtime 1.3 remains the safer comparison point for older examples.", "Fabric model endpoints are preview, so do not turn runtime facts into a serving promise."]],
        col_w=[1.15, 1.85, 1.65, 1.85],
        size=12.2,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Microsoft Learn and runtime manifests, verified 2026-10-18.",
        notes="""This slide answers the version-pin question that usually comes up after the workshop.

The message is simple. Fabric Runtime 2.0 is the current GA production runtime, but Runtime 1.3 is still the important LTS baseline because many examples and older notebooks still assume it. The biggest operational difference for this workshop is the MLflow version pin: Fabric can run newer MLflow than Azure ML can.

The other reminder is that pure Python notebooks and Spark notebooks are different experiences. That matters when people want a lighter-weight exploration path inside Fabric.

SOURCE:
- `00-presenter-guide/fact-sheets/fabric-ml.md`
- https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-2-0
- https://learn.microsoft.com/en-us/fabric/data-engineering/lifecycle
- https://github.com/microsoft/synapse-spark-runtime
- https://learn.microsoft.com/en-us/fabric/data-science/mlflow-3-overview
- https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook
VERIFY: Runtime 2.0 is clearly current GA, but the exact word 'default' is still not perfectly synchronized across docs.""")

    d.table_slide(
        "A3", "Azure ML versions and pins",
        ["Area", "Current / pin", "Status or date", "Why it matters"],
        [["AML platform", "AML v2 is the current platform.", "Current production path.", "Use current jobs, pipelines, endpoints and registries."],
         ["CLI v1", "Support ended.", "2025-09-30.", "Old scripts need migration before a new pilot."],
         ["Python SDK v1", "Support ended.", "2026-06-30.", "Examples should stay on `azure-ai-ml` and the v2 stack."],
         ["MLflow", "`mlflow<=2.16.2`.", "Explicit Learn pin.", "This is the hard ceiling for AML-compatible MLflow code."],
         ["Plugin", "`azureml-mlflow 1.62.0.post6` on PyPI.", "Latest seen 2026-09-02.", "Plugin compatibility matters more than the newest MLflow release."],
         ["Endpoints", "Managed online and batch endpoints are current.", "Current.", "They are the serving surfaces to design around."],
         ["Prompt flow", "Still documented, but retires 2027-04-20.", "Retirement announced.", "Do not make it part of a 2026-2027 forward plan."],
         ["Preview caveats", "Feature store and Responsible AI dashboard stay preview in current docs.", "Preview.", "Good to mention, not good to depend on in a live workshop."]],
        col_w=[1.1, 1.85, 1.25, 2.3],
        size=12.4,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Azure ML fact sheet and Learn docs, verified 2026-10-18.",
        notes="""This is the Azure ML appendix slide I would use when someone asks, 'Which pins are real, and which are just sample defaults?'

The answer is that the MLflow pin is the real constraint. AML is still the strong managed platform for classic ML jobs, endpoints and MLOps, but its MLflow integration deliberately stays on the older `<=2.16.2` contract. That is why the workshop uses the portable MLflow model folder as the cross-platform teaching primitive.

The retirement rows matter because they help people avoid dead ends. CLI v1 and SDK v1 are already behind us, and Prompt flow has a published retirement date.

SOURCE:
- `00-presenter-guide/fact-sheets/aml.md`
- `05-demo-azureml-e2e/aml-facts-for-slides.md`
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models-mlflow?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online?view=azureml-api-2
VERIFY: exact PyPI latest versions are informational only; the AML Learn compatibility pin remains the source of truth.""")

    d.table_slide(
        "A4", "How to estimate cost",
        ["Area", "Fabric", "Azure ML", "What to estimate"],
        [["Billing unit", "Capacity in F-SKU and capacity units.", "Compute, endpoints and supporting resources.", "Map the billing unit before you design the demo shape."],
         ["Idle cost", "Capacity exists whether one notebook is busy or not.", "Clusters can scale to zero; online endpoints bill while deployments exist.", "Ask what keeps billing alive when nobody is clicking."],
         ["Training", "Notebook runtime time and concurrency consume capacity.", "Job compute time, environment build time and retries drive cost.", "Separate one-off environment work from actual model runs."],
         ["Serving", "Model endpoints are preview and consume endpoint CU-seconds when active.", "Managed online endpoints bill while the instances exist.", "Serving cost depends more on uptime than on request count for a small workshop."],
         ["Batch path", "Notebook or pipeline runs consume the shared Fabric capacity.", "Batch endpoints mainly bill when the jobs run.", "Batch scoring is easier to bound than a long-lived endpoint."],
         ["Small extras", "Storage, monitoring and admin choices still matter.", "Storage, ACR, Log Analytics and App Insights add small overhead.", "Do not forget the support services around the model."],
         ["Practical method", "Count runtimes, warm-up windows and concurrency.", "Count cluster hours, endpoint hours, build time and cleanup lag.", "Estimate with your own subscription and region, then add a safety margin."]],
        col_w=[1.1, 1.8, 1.9, 1.9],
        size=12.3,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Method only: no prices on this slide.",
        notes="""This slide is intentionally about method, not quote values.

The main teaching point is that Fabric and Azure ML expose different budgeting questions. Fabric starts with shared capacity: how much work runs on the capacity, how concurrent it is, and whether the capacity already exists for broader analytics. Azure ML starts with explicit resources: which compute cluster, which endpoint, which environment build, and how long they stay alive.

For workshops and pilots, the two biggest mistakes are forgetting endpoint uptime in AML and forgetting background capacity pressure in Fabric. The clean way to estimate is to list the exact activities: one rehearsal, one warm-up, one live run, one batch score, one cleanup.

SOURCE:
- `00-presenter-guide/fact-sheets/fabric-ml.md`
- `00-presenter-guide/fact-sheets/aml.md`
- `05-demo-azureml-e2e/cost-and-cleanup.md`
VERIFY: price anchors are omitted here on purpose because they depend on subscription, region and timing.""")

    d.table_slide(
        "A5", "Security and networking options",
        ["Area", "Fabric", "Azure ML / Foundry", "Takeaway"],
        [["Inbound private access", "Private Link gives private inbound access to Fabric.", "AML uses managed network and private endpoint patterns.", "Private ingress and data egress are separate questions."],
         ["Outbound private access", "Managed private endpoints and outbound access protection cover supported destinations.", "Managed VNet patterns isolate AML compute and endpoints.", "Ask how the platform reaches storage, registries and logs."],
         ["Storage firewall access", "Trusted workspace access lets named workspaces reach Azure Storage through firewall rules.", "Use managed identity plus datastore or storage RBAC.", "This is the Fabric-specific answer to a common enterprise ask."],
         ["Identity to data", "Fabric data agents query with the signed-in user's Entra identity.", "AML jobs and endpoints use user, managed identity or service principal flows.", "Say clearly whether access is delegated or app-owned."],
         ["Endpoint auth", "Fabric scoring REST paths support user, service principal or managed identity.", "AML online endpoints support `key`, `aml_token` and Entra token auth.", "Pick the auth mode before you promise self-service access."],
         ["Foundry + Fabric", "The legacy Foundry Fabric tool uses OBO.", "Service principals are not supported on that legacy path; Fabric IQ is preferred.", "OBO is the caveat to say out loud when agents touch governed data."],
         ["Governance and caveats", "Purview, labels, audit logs and CMK cover the Fabric estate; trusted workspace access needs paid F SKU.", "Key Vault, App Insights, Log Analytics, quota and private DNS still matter.", "Enterprise-ready means feature-ready and quota-ready, not only doc-ready."]],
        col_w=[1.15, 1.85, 1.95, 1.65],
        size=12.1,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Fabric and AML security docs, verified 2026-10-18.",
        notes="""This appendix slide is a way to answer the security architecture question without drawing a new diagram live.

The key distinction is between inbound access, outbound access and delegated identity. Fabric's Trusted Workspace Access is the specific answer when Azure Storage firewalls are the blocker. Azure ML's answer is more often managed network plus identity and storage RBAC. Foundry adds the agent-identity conversation on top.

The row I would say slowly is the OBO row. The legacy Foundry Fabric tool runs as the signed-in user, not as a headless service principal, so every user needs the underlying Fabric permissions.

SOURCE:
- `00-presenter-guide/fact-sheets/fabric-de-rti.md`
- `00-presenter-guide/fact-sheets/aml.md`
- `00-presenter-guide/fact-sheets/foundry-dataagent.md`
- https://learn.microsoft.com/en-us/fabric/security/security-private-links-overview
- https://learn.microsoft.com/en-us/fabric/security/security-managed-private-endpoints-overview
- https://learn.microsoft.com/en-us/fabric/security/security-trusted-workspace-access
- https://learn.microsoft.com/en-us/azure/machine-learning/how-to-authenticate-online-endpoint?view=azureml-api-2
- https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
VERIFY: the slide stays at option level; exact AML managed-network combinations still depend on the tenant and selected endpoint pattern.""")

    d.table_slide(
        "A6", "If you know Databricks: a concept mapping",
        ["Databricks-shaped idea", "Fabric term", "Azure ML term", "How to use the mapping"],
        [["Workspace + shared data", "Fabric workspace with OneLake and lakehouse items.", "AML workspace plus linked storage and data assets.", "Think 'analytics home' in Fabric and 'ML control plane' in AML."],
         ["Notebook runtime", "Spark notebook or pure Python notebook.", "Compute instance, job cluster or serverless job runtime.", "Both can run Python, but the operating model is different."],
         ["Experiment tracking", "Experiment item with MLflow tracking built in.", "AML workspace tracking server for MLflow.", "The MLflow nouns still match even when the UI changes."],
         ["Model registry", "ML model item, version-first.", "Workspace registry plus AML registries for promotion.", "Teach versions and lineage, not stage folklore."],
         ["Batch scoring", "`PREDICT`, generated notebooks or pipeline runs.", "Batch endpoints or pipeline jobs.", "Map the concept first: repeatable offline inference."],
         ["Online serving", "Preview model endpoints.", "Managed online endpoints.", "Respect the maturity difference; this is not a parity claim."],
         ["Automation and CI/CD", "Pipelines, schedules, Git integration and `fabric-cicd`.", "Command jobs, pipeline jobs, GitHub Actions and IaC.", "Both belong in software engineering, not only in notebooks."],
         ["Identity and network", "Fabric identity, Private Link, managed private endpoints and trusted workspace access.", "Azure RBAC, managed identity, managed network and private endpoints.", "Keep the conversation respectful: same concerns, different platform boundaries."]],
        col_w=[1.55, 1.7, 1.7, 1.75],
        size=12.1,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Concept mapping only; not a feature-comparison scorecard.",
        notes="""This slide is for the people in the room who already have a Databricks mental model and want a bridge, not a debate.

I would say clearly that this is not a parity chart. It is a concept map. The point is to give them the nearest Microsoft concept so the rest of the workshop makes sense quickly. Some ideas map more naturally to Fabric, some to Azure ML, and some to the hybrid path.

The most important respectful line is that the concerns are the same everywhere: versioned data, tracked runs, promoted models, repeatable jobs, governed identities and secure network paths. The platforms package those concerns differently.

SOURCE:
- `03-demo-mlflow-tour/concept-map.md`
- `00-presenter-guide/fact-sheets/fabric-ml.md`
- `00-presenter-guide/fact-sheets/fabric-de-rti.md`
- `00-presenter-guide/fact-sheets/aml.md`
VERIFY: this is intentionally conceptual and should not be read as a one-to-one feature parity statement.""")

    d.table_slide(
        "A7", "Data dictionary: gold and ml tables",
        ["Table", "Grain", "Key columns", "Why it exists"],
        [["`gold.dim_asset` + `gold.dim_site`", "One row per asset / one row per site.", "`erp_asset_id`; `site_code`.", "Reference joins, site context and asset status."],
         ["`gold.fact_telemetry_daily`", "One row per asset-day.", "`erp_asset_id`, `obs_date`.", "Daily operating signals for BI and feature engineering."],
         ["`gold.fact_fault_episode`", "One row per fault episode.", "`episode_id`, `erp_asset_id`, `fault_code`.", "Business event view of warnings and critical faults."],
         ["`gold.fact_work_order`", "One row per resolved corrective work order kept for gold.", "`wo_number`, `erp_asset_id`.", "Maintenance truth for reconciliation and labels."],
         ["`gold.fact_recon_match` + `gold.fact_recon_exception`", "Match rows and exception rows.", "`episode_id`, `wo_number`; `exception_id`.", "Show what matched and what stayed unresolved."],
         ["`gold.agg_recon_monthly`", "One row per month and site.", "`month`, `site_code`.", "Compact KPI table for a manager or data agent question."],
         ["`ml.asset_day_features`", "One row per asset-day candidate.", "`erp_asset_id`, `obs_date`, `split`.", "42 engineered features plus the `fail_next_7d` label."],
         ["`ml.failure_risk_score`", "One row per scored asset.", "`score_date`, `erp_asset_id`, `risk_rank`.", "Operational scores with risk band and top drivers."],
         ["`ml.drift_report`", "One row per class-sensor pair.", "`equipment_class`, `sensor`.", "PSI summary for monitoring and drift discussion."]],
        col_w=[1.55, 1.45, 1.45, 2.15],
        size=12.0,
        tbl=dict(bold_first=True, zebra=True, mono_cols=[0]),
        minutes=0.5,
        core=False,
        source="Scenario contract sections 5 and 7; counts from facts.F.",
        notes="""This is the one-page data dictionary for the synthetic scenario.

The slide is deliberately about table purpose and grain, not about every column. If someone asks for a specific field, the contract in the repo is the deeper reference. The point here is to remind the audience that the business questions, the ML task and the agent all sit on top of the same gold and ml contract.

SOURCE:
- `02-demo-data/scenario-contract.md` sections 5 and 7
- `01-slides/facts.py`
TRANSITION: The next slide compresses the reconciliation rules that make these tables trustworthy.""")

    d.table_slide(
        "A8", "Reconciliation rules in one page",
        ["Area", "Rule", "Key numbers", "Why it matters"],
        [["Identity resolution", "First hit wins: EXACT_NORM, then SERIAL, then CROSSWALK, else UNRESOLVED.", f"T {n(F.tiers['EXACT_NORM'])} / {n(F.tiers['SERIAL'])} / {n(F.tiers['CROSSWALK'])} / {n(F.unresolved)}; W {n(F.cmms_tiers['EXACT_NORM'])} / {n(F.cmms_tiers['SERIAL'])} / {n(F.cmms_tiers['CROSSWALK'])} / {n(F.cmms_unresolved)}.", "Every later join depends on this order."],
         ["Time", "Telemetry becomes UTC; CMMS local time uses the site timezone; swapped close/open stamps are fixed.", f"Cutoff `2026-10-01`; {n(F.cmms_time_anomalies)} time anomalies.", "Without a common clock, matching and labels drift."],
         ["Silver cleanup", "Drop duplicate telematics events, null bad sensor values, and flag duplicate corrective work orders for gold exclusion.", f"{n(F.duplicates)} telematics duplicates; {n(F.out_of_range)} values nulled; {n(F.cmms_duplicates)} WO duplicates.", "Traceability stays intact without double counting noise or labels."],
         ["Fault episodes", "Group same-asset, same-code signals until the gap exceeds 24 hours.", f"{n(F.episodes)} episodes; CRIT or WARN with `n_records >= 3` are significant.", "Episode logic turns noisy events into business incidents."],
         ["Matching and status", "Corrective work orders match the same asset in `[start-24h, end+7d]`; status becomes `NOT_APPLICABLE`, `MATCHED`, `UNMATCHED` or `PENDING`.", f"{n(F.gold['fact_recon_match'])} match rows; critical match rate {pct(F.crit_match_rate)} of judged critical episodes ({n(F.crit_recon['MATCHED'])} of {n(F.crit_total - F.crit_recon['PENDING'])} judged; {n(F.crit_recon['PENDING'])} still pending).", "These are the business answers the room usually wants first."],
         ["Exceptions", "Unresolved assets, silent assets, unmatched faults, unmatched work orders and time anomalies become explicit rows.", f"{n(F.exceptions)} exception rows.", "The exception table lets the agent answer honestly instead of guessing."]],
        col_w=[1.0, 1.9, 1.95, 1.9],
        size=12.0,
        tbl=dict(bold_first=True, zebra=True),
        minutes=0.5,
        core=False,
        source="Scenario contract section 6; counts from facts.F.",
        notes="""This is the reconciliation contract on one slide.

If the audience challenges the logic, this is where I would slow down. The two things to emphasize are first-hit identity resolution, and the explicit time window between a fault episode and a corrective work order. Those two rules explain most of the later counts.

The other important point is that exceptions are first-class data, not hidden leftovers. That design choice is what makes the Foundry and data-agent part credible.

SOURCE:
- `02-demo-data/scenario-contract.md` section 6
- `01-slides/facts.py`
TRANSITION: The next appendix slide compiles the troubleshooting patterns that are most likely to save time before Friday.""")

    d.table_slide(
        "A9", "Troubleshooting: the ten most likely problems",
        ["Problem", "Likely cause", "First fix", "Demo area"],
        [["Metrics or counts do not match the reference", "Wrong inputs, wrong split, or accidental reshuffle.", "Go back to `02-demo-data/reference_out` and the fixed split contract before changing code.", "Local / Fabric / AML"],
         ["MLflow registration or scoring rejects the model", "Registry backend or signature contract is wrong.", "Use a database-backed local store, and re-log with `infer_signature(...)` plus `input_example=`.", "Local / Fabric / AML"],
         ["Fabric notebook cannot see code, files or packages", "Wrong lakehouse, wrong `Files/` path, or `%pip` restart not finished.", "Reattach `lh_fleet`, check `CODE_DIR`, restart after `%pip`, and rerun from the top.", "Fabric"],
         ["AML training or deployment stalls", "Cold cluster, bad MLflow pin, low quota, or missing ACR permission.", "Warm `cpu-cluster`, keep `mlflow==2.16.2`, verify DS3_v2 quota, and recheck ACR roles.", "AML"],
         ["AML invoke or batch score fails on payload", "Request shape or input columns do not match the model signature.", "Use the prepared request sample and score the feature contract, not a raw export.", "AML"],
         ["Gate or drift alerts look wrong", "Reference and current windows are wrong, or raw telemetry slipped in.", "Recheck September reference, October drift batch, and the frozen gate metrics before promoting.", "Fabric / AML MLOps"],
         ["The data agent answers badly or should have refused", "Wrong table, stale example queries, or loose instructions.", "Re-ask with the scripted wording, tighten instructions, and verify the selected tables.", "Fabric data agent"],
         ["Foundry/Fabric integration breaks", "Published agent, connection ids, region guidance or OBO permissions are wrong.", "Confirm the published agent, refresh ids, and verify the signed-in user has Fabric access.", "Foundry + Fabric"]],
        col_w=[1.75, 1.7, 1.95, 1.0],
        size=12.0,
        tbl=dict(bold_first=True, zebra=True, pad_y=0.055),
        minutes=0.5,
        core=False,
        source="VERIFY: compiled from troubleshooting notes, not a live tenant run.",
        notes="""This is the practical triage page I would keep hidden until something goes wrong.

The point is not to predict every failure. It is to shorten the first five minutes of diagnosis. Most workshop failures fall into one of these buckets: wrong input contract, missing signature, wrong path, cold or under-permissioned cloud resource, or an agent pointed at the wrong semantic surface.

I would also say clearly that this slide is intentionally marked VERIFY. The local guides and fact sheets are solid, but this exact sequence was not re-run end to end in one live tenant by this module author.

SOURCE:
- `03-demo-mlflow-tour/troubleshooting.md`
- `04-demo-fabric-e2e/etl/etl-facts-for-slides.md`
- `04-demo-fabric-e2e/ml-mlops/mlops-facts-for-slides.md`
- `05-demo-azureml-e2e/troubleshooting.md`
- `06-demo-foundry-data-agent/troubleshooting.md`
VERIFY: whole slide. Compiled from local docs and fact sheets; the exact live-tenant symptom wording still needs a final rehearsal.""")

    d.table_slide(
        "A10", "Glossary",
        ["Term", "Meaning", "Term", "Meaning"],
        [["MLflow\nExperiment", "MLflow is the tracking contract used across the workshop.\nAn experiment is the named container that groups related runs.", "Run\nSignature", "A run records one execution with params, metrics and artifacts.\nA signature defines the inputs and outputs expected at scoring time."],
         ["Registry\nMedallion", "A registry stores versioned models and their lineage.\nMedallion means moving data from raw bronze to cleaner silver to business-ready gold.", "OneLake\nDelta", "OneLake is Fabric's shared storage layer.\nDelta is the table format with ACID transactions and schema evolution."],
         ["F-SKU and capacity unit\nEndpoint", "An F-SKU is a Fabric capacity tier measured in capacity units.\nAn endpoint is the managed interface that serves a model online or in batch.", "PSI\nPR-AUC", "PSI measures distribution shift versus a reference window.\nPR-AUC is the precision-recall area used for rare positive classes."],
         ["Leakage\nChampion/challenger", "Leakage means the model learned from information unavailable at prediction time.\nChampion/challenger compares the current production model with a candidate.", "OIDC\nData contract", "OIDC lets a client get cloud access without a long-lived secret.\nA data contract is the agreed shape and rules of a shared dataset."],
         ["Identity resolution\nData agent", "Identity resolution matches different source identifiers to one business entity.\nA data agent answers natural-language questions over governed structured data.", "MCP\nFoundry", "MCP is the protocol that lets a client discover and call tools.\nFoundry is Microsoft's platform for models, agents and tool-based GenAI workflows."]],
        col_w=[1.2, 2.3, 1.2, 2.3],
        size=12.0,
        tbl=dict(zebra=True),
        minutes=0.5,
        core=False,
        source="Workshop glossary for follow-up questions.",
        notes="""This glossary is intentionally plain and short. It is here so the room can align on words quickly after the session.

The terms are the ones that tend to trigger follow-up questions: MLflow basics, storage and data concepts, serving terms, quality metrics, security and identity, and the specific agent vocabulary used in Part 4.

If someone wants a deeper definition, the better move is to jump from here to the relevant appendix slide or repository folder rather than reading the glossary cell by cell.

SOURCE:
- `03-demo-mlflow-tour/concept-map.md`
- `02-demo-data/scenario-contract.md`
- `00-presenter-guide/fact-sheets/fabric-ml.md`
- `00-presenter-guide/fact-sheets/aml.md`
- `00-presenter-guide/fact-sheets/foundry-dataagent.md`""")

# @@NEXT@@
