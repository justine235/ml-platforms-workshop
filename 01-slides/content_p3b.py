"""Part 3b: Azure ML half plus bridge and wrap-up (P3.15-P3.25)."""
from __future__ import annotations

from deck_lib import Deck
from facts import F, d3, n, pct


AML_SRC = "Microsoft Learn: Azure ML docs, verified 2026-10-18"
BRIDGE_SRC = "Microsoft Learn: OneLake and AML bridge, verified 2026-10-18"
HYBRID_SRC = "Microsoft Learn: Fabric and AML docs, verified 2026-10-18"

AML_URLS = [
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-mlflow-configure-tracking?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-log-mlflow-models?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints-online?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-safely-rollout-online-endpoints?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-model-deployments?view=azureml-api-2",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-github-actions-machine-learning?view=azureml-api-2",
]

BRIDGE_URLS = [
    "https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-machine-learning",
    "https://learn.microsoft.com/en-us/fabric/data-factory/azure-machine-learning-activity",
    "https://learn.microsoft.com/en-us/azure/machine-learning/how-to-use-batch-fabric?view=azureml-api-2",
]


def build(d: Deck) -> None:
    d.demo(
        "P3.15", "Demo 2b: Azure ML end to end in 45 minutes",
        [
            ("Tour the workspace, cluster, environment, and ACR", "5 min"),
            ("Submit the training pipeline and open the job graph", "8 min"),
            ("Read metrics, registry tags, and the promotion gate", "8 min"),
            ("Invoke blue, mirror to green, then shift traffic", "11 min"),
            ("Trigger the nightly batch path and return scores", "7 min"),
            ("Close with GitHub Actions, OIDC, and the bridge", "6 min"),
        ],
        [
            "Environment image already built once",
            "Online endpoint shell plus blue and green already provisioned",
            "Compute cluster warmed and one successful run already finished",
        ],
        [
            "If the job queues, open the last successful run and keep the story moving",
            "If cloud quota blocks the live step, switch to the prepared local validation fallback",
        ],
        "45 min",
        where="Azure ML Studio  ·  mlw-fleet-dev  ·  cpu-cluster",
        minutes=4,
        core=False,
        notes="""I open this half by resetting the room. The business problem did not change. Only the operating model changed.

The message is that Fabric already handled the heavy lakehouse work. Azure Machine Learning now owns the production-style ML workflow: explicit compute, explicit environments, explicit rollout, and explicit promotion. That is why I start with the workspace tour before I run anything.

DEMO: Show the workspace, the `cpu-cluster`, the prebuilt `env-fleet-sklearn` environment, and the dedicated ACR. Then submit `jobs\\pipeline-train.yml`, open the graph, and keep the audience oriented around the five stages: prep, train, evaluate, gate, register. After the run starts, jump to the managed online endpoint, invoke blue and green, mirror 10% to green, then give green a small live share, then trigger one batch run. Close in GitHub Actions and `bridge-fabric-aml.md`.

WATCH OUT: if the cluster is cold, say so out loud. The live risk is startup time, not code complexity. If the run stalls, open a previous successful run, the registered model, and the endpoint state. The fallback order in `run-of-show.md` is deliberate.

IF SHORT ON TIME: skip the live batch completion and only show the submitted batch job plus the target output location in OneLake.

SOURCE: repo file `05-demo-azureml-e2e\\run-of-show.md`
TRANSITION: The fastest way to show the logic is the YAML pipeline itself.""",
    )

    d.code_slide(
        "P3.16", "Azure ML: a pipeline in YAML, from data asset to registered model",
        """settings:
  default_compute: azureml:cpu-cluster
inputs:
  raw_features:
    path: azureml:fleet-asset-day-features-reference:1
jobs:
  prep:     component: ./components/prep.yml
  train:    component: ./components/train.yml
  evaluate: component: ./components/evaluate.yml
  gate:     component: ./components/gate.yml
  register: component: ./components/register.yml
""",
        lang="yaml",
        file="jobs\\pipeline-train.yml",
        side=[
            dict(title="Same contract", body=f"The input is still `{n(F.ml_rows)}` feature rows with the shared split column.", icon="table", tone="azure"),
            dict(title="Same model name", body="The experiment and registered model stay `fleet-failure-7d` across both platforms.", icon="ml-model", tone="node"),
            dict(title="Why AML", body="The pipeline is a first-class asset instead of notebook sequencing by convention.", icon="azure-machine-learning", tone="success"),
        ],
        takeaway="The logic is unchanged from Fabric: prep, train, evaluate, gate, register.",
        minutes=8,
        core=False,
        notes="""Here I want the audience to notice what did not change first.

The input contract is the same `ml.asset_day_features` export. The model name is the same. The five steps are the same. The honest comparison is not "Fabric does one thing and AML does another." It is that AML turns the same training path into an explicit pipeline asset with typed inputs and typed outputs.

The useful difference for a data engineer is visibility. Each stage has a component boundary. The useful difference for a data scientist is that the training script still reuses the same shared ML core, so the notebook logic did not have to be rewritten around a new platform vocabulary.

DEMO: point at `raw_features`, then trace the job graph in Studio from prep to register. Call out that `champion_metrics` comes in as an input too, because promotion is part of the pipeline, not an afterthought.

WATCH OUT: keep the excerpt short. The audience does not need every property. They need to see that YAML is describing the same process they just saw in notebooks.

SOURCE: """ + AML_URLS[0] + """
SOURCE: repo file `05-demo-azureml-e2e\\jobs\\pipeline-train.yml`
TRANSITION: Once the pipeline exists, AML can search the same model family more systematically.""",
    )

    d.flow(
        "P3.17", "Sweep, then gate: promote only a better model",
        [
            dict(icon="repeat", title="Sweep", body="Random search over 3 HGB knobs.\n9 trials, 2 concurrent."),
            dict(icon="bar-chart-3", title="Best trial", body=f"Primary metric is `valid_pr_auc`.\nThe baseline sits around {d3(F.pr_auc_valid['hgb'])}."),
            dict(icon="scale", title="Exact gate", body="Test PR-AUC up by 0.01 or more. Precision at the top 5% down by 0.02 at most."),
            dict(icon="file-text", title="Decision JSON", body='Rehearsal run (local):\n`approved: true`\nPR-AUC about +0.10\nPrecision about +0.07'),
            dict(icon="package", title="Register", body="Only a passing challenger becomes a new model version."),
        ],
        takeaway="Both metrics improved, so the 0.02 precision tolerance was never needed.",
        minutes=7,
        core=False,
        notes="""This is the slide where I slow down and get precise.

The sweep job is deliberately small: three approved hyper-parameters, nine total trials, two concurrent. The point is not brute-force tuning. The point is to show that AML can search, compare, and then apply the same release rule every time.

The gate text on the slide paraphrases `src\\gate.py`. I read it exactly once: the challenger must improve `test_pr_auc` by at least 0.01, and `precision@top5%` must not get worse by more than 0.02. That guardrail is intentionally simple enough for a live workshop and still honest enough to reject weak wins.

DEMO: after the sweep, open the best run, then show the gate report JSON. The numbers on the slide come from a local rehearsal run, not a guaranteed live number: the champion there is a plain logistic regression (test_pr_auc about 0.29) and the challenger is the gradient-boosting model (about 0.385), so expect different second decimals live.

WATCH OUT: do not let the room confuse validation ranking with production promotion. The sweep picks on validation. The gate approves on the frozen test metrics and a precision guardrail.

SOURCE: repo files `05-demo-azureml-e2e\\jobs\\sweep-job.yml`, `src\\gate.py`, `tests\\test_gate.py`
TRANSITION: After the model is registered, AML's most visible differentiator is deployment control.""",
    )

    d.arch(
        "P3.18", "Deploy: a managed online endpoint with blue and green",
        [
            dict(id="caller", label="Caller", sub="Portal, app, or smoke test", icon="users", col=0, row=1, tone="node"),
            dict(id="endpoint", label="fleet-risk-online", sub="Managed online endpoint", icon="azure-machine-learning", col=1, row=1, tone="azure"),
            dict(id="blue", label="Blue", sub="Live: answers every call\nno-code MLflow deploy", icon="ml-model", col=2, row=0, tone="success", h=1.02),
            dict(id="green", label="Green", sub="Shadow: gets a 10% copy\nreplies are not returned", icon="ml-model", col=2, row=2, tone="amber", h=1.02),
            dict(id="logs", label="Logs and metrics", sub="App Insights + Log Analytics", icon="application-insights", col=3, row=1, tone="paper"),
        ],
        edges=[
            dict(a="endpoint", b="green", dash=True, color="amber"),
            ("caller", "endpoint"),
            ("endpoint", "blue"),
            ("blue", "logs"),
            ("green", "logs"),
        ],
        groups=[dict(label="Managed online endpoint", c0=1, r0=0, c1=3, r1=2, tone="azure")],
        source=AML_SRC,
        takeaway="Roll out in order: dark, shadow, small live share. A deployment is live or mirrored, never both.",
        minutes=9,
        core=False,
        notes="""This is the clearest operational reason Azure ML is in the workshop.

Fabric can score models, but AML gives me a first-class managed online endpoint with rollout mechanics that are easy to explain to operations teams. I can keep blue live, bring up green beside it with zero traffic, test it directly, mirror a copy of live requests to it without changing user-visible responses, then move a small live share, and roll back in one command.

One rule to say out loud, because it is in the Learn article and people ask: a deployment is either live or mirrored, never both. So the order is dark, then shadow, then a small live share. Mirroring is capped at 50% of traffic and works for one deployment at a time.

The other important phrase here is "no-code MLflow deployment." Because the model was logged with a signature and an input example, AML can stand up the serving stack without a custom scoring script. That reduces code surface, but it also makes the input contract strict.

DEMO: show the endpoint page with blue live and green provisioned. Invoke blue and green with `sample-request.json`. Run the mirror command (mirror-traffic green=10), invoke the endpoint about 20 times WITHOUT naming a deployment (a call that names a deployment is not mirrored), and show green's logs. Clear the mirror (green=0), and only then run the live split (traffic blue=90 green=10). Say clearly that green is only safe because the model signature is already known.

WATCH OUT: the first deployment is slow if the image was not prebuilt. Also mention the quota wrinkle: some SKUs reserve extra capacity during upgrades.

SOURCE: """ + AML_URLS[1] + """
SOURCE: """ + AML_URLS[2] + """
SOURCE: """ + AML_URLS[3] + """
TRANSITION: Our use case is still daily batch scoring, so online is not the only endpoint story.""",
    )
    d.flow(
        "P3.19", "Batch scoring: the nightly job",
        [
            dict(icon="one-lake", title="Input", body="The feature export lands in OneLake `/Files` or a mapped data asset."),
            dict(icon="workflow", title="Invoke", body="The batch endpoint starts an asynchronous scoring run."),
            dict(icon="ml-model", title="Score", body="The batch deployment loads the latest MLflow model on a CPU cluster."),
            dict(icon="table", title="Output", body=f"A CSV file holds {n(F.assets_scored)} scored assets."),
            dict(icon="layers", title="Consume", body="Fabric reloads the scores as a table for BI and the later agent."),
        ],
        takeaway="Daily scoring cares more about a reliable file contract than about low latency.",
        minutes=7,
        core=False,
        notes="""I make this distinction explicitly: the online endpoint proves serving control, but the business requirement here is a daily batch.

Every night, AML reads the prepared feature export, loads the latest registered MLflow model, writes `predictions.csv`, and hands the scored table back to the lake side. That is the right fit when planners want a morning risk list, not millisecond inference.

DEMO: show `batch-endpoint.yml` (endpoint `fleet-risk-batch`, compute `cpu-cluster`), the invoke command, and the target output pattern for `predictions.csv`. Then connect it back to the shared workshop artifact `ml.failure_risk_score`: one scored table reused by reporting and, later, the agent.

What matters operationally is the contract. The input must match the model signature, which means only the 42 feature columns. The output is asynchronous, so I can keep the scoring compute small and cheap, then let Fabric reload the landed files as a standard data product.

WATCH OUT: do not oversell the Fabric-to-AML batch integration path. The preview coupling is on the Fabric side. The AML batch endpoint itself is current. For the workshop, the safest mental model is AML scores, then Fabric reads the resulting files.

SOURCE: """ + AML_URLS[4] + """
SOURCE: repo files `05-demo-azureml-e2e\\endpoints\\batch-endpoint.yml`, `batch-deployment.yml`, `src\\score.py`
TRANSITION: The last Azure ML piece is how we automate all this without stored secrets.""",
    )

    d.arch(
        "P3.20", "CI/CD with OIDC: no secrets in the repository",
        [
            dict(id="ci", label="CI workflow", sub="compile, Ruff, pytest,\nlocal validation", icon="git-pull-request", col=0, row=0, tone="paper", h=1.02),
            dict(id="infra", label="Infra workflow", sub="Bicep what-if\nand deploy", icon="server", col=1, row=0, tone="paper", h=1.02),
            dict(id="train", label="Train workflow", sub="weekday schedule or\nmanual dispatch", icon="repeat", col=2, row=0, tone="paper", h=1.02),
            dict(id="promote", label="Promote workflow", sub="manual prod promotion\nwith staged traffic shift", icon="rocket", col=3, row=0, tone="success", h=1.02),
            dict(id="oidc", label="Federated credential", sub="`azure/login@v2` exchanges a GitHub OIDC token for an Azure token, with no stored secret", icon="shield-check", col=0, row=1, cspan=4, tone="azure", h=0.8),
            dict(id="aml", label="Azure ML + Azure", sub="workspace, registry, resource group", icon="azure-machine-learning", col=1, row=2, cspan=2, tone="azure", h=0.8),
        ],
        edges=[
            ("ci", "oidc"),
            ("infra", "oidc"),
            ("train", "oidc"),
            ("promote", "oidc"),
            ("oidc", "aml"),
        ],
        groups=[dict(label="GitHub repository: four workflows", c0=0, r0=0, c1=3, r1=0, tone="azure")],
        gap=(0.55, 0.42),
        source=AML_SRC,
        takeaway="OIDC removes long-lived cloud secrets from the repository, but keeps full automation.",
        minutes=10,
        core=False,
        notes="""I want the room to see that the automation story is boring in the best possible way.

There are four workflows in the repo. CI proves the Python and contract logic. Infra deploys the Bicep. Train submits the AML pipeline on a weekday schedule or a manual dispatch. Promote is a human-triggered workflow that shares the model, creates the green deployment, smoke-tests it, and then shifts traffic.

The security point is the shared credential bar under the four workflows. GitHub does not store an Azure client secret here. `azure/login@v2` exchanges a GitHub OIDC token for a federated credential in Azure. That keeps the repo cleaner and rotation simpler, while still letting the workflows touch AML.

DEMO: open each workflow YAML quickly and show the repeated `azure/login@v2` step. Then say out loud that production promotion is approval-gated on the GitHub environment, not hidden in a notebook cell.

WATCH OUT: if someone asks for Azure DevOps, say the pattern is conceptually similar, but this workshop repo is GitHub-first.

SOURCE: """ + AML_URLS[5] + """
SOURCE: repo files `05-demo-azureml-e2e\\mlops\\github-workflows\\ci.yml`, `infra.yml`, `train-pipeline.yml`, `promote-model.yml`
TRANSITION: With the AML path clear, we can finally join it back to the Fabric path honestly.""",
    )

    d.arch(
        "P3.21", "The bridge: Fabric ETL feeds Azure ML, scores come back",
        [
            dict(id="fabric", label="Fabric lakehouse", sub="`bronze` → `silver` → `gold`\n`ml.asset_day_features`", icon="lakehouse", col=0, row=0, tone="success"),
            dict(id="files", label="OneLake `/Files`", sub="ABFSS path or shared folder\nGA today", icon="one-lake", col=1, row=0, tone="success"),
            dict(id="asset", label="AML data asset", sub="current AML input pattern", icon="table", col=2, row=0, tone="azure"),
            dict(id="trainaml", label="AML train + deploy", sub="pipeline, registry,\nonline and batch endpoints", icon="azure-machine-learning", col=3, row=0, tone="azure", h=1.28),
            dict(id="scores", label="Scored files back", sub="`predictions.csv` then `ml.failure_risk_score`", icon="table", col=3, row=1, tone="success"),
            dict(id="consumers", label="Fabric consumers", sub="Power BI, notebooks,\nPart 4 agent", icon="layers", col=0, row=1, tone="success"),
            dict(id="preview1", label="Preview / care", sub="Fabric AML batch activity\nnot for a workshop promise", icon="alert-triangle", col=0, row=2, tone="amber"),
            dict(id="preview2", label="Preview / care", sub="OneLakeDatastore is experimental;\n`/Tables` still often copy first", icon="alert-triangle", col=2, row=2, tone="amber", h=1.22),
        ],
        edges=[
            ("fabric", "files"),
            ("files", "asset"),
            ("asset", "trainaml"),
            ("trainaml", "scores"),
            ("scores", "consumers", "reload into the lakehouse"),
        ],
        groups=[
            dict(label="GA path for the workshop", c0=0, r0=0, c1=3, r1=1, tone="success"),
            dict(label="Preview or extra-care items", c0=0, r0=2, c1=2, r1=2, tone="amber"),
        ],
        source=BRIDGE_SRC,
        minutes=4,
        core=False,
        notes="""This is the honest hybrid slide.

The strong path for Friday is the green zone: the top lane goes out to Azure ML and the second lane brings the scores back. Fabric owns ingestion, cleaning, reconciliation, and feature creation. The feature export lands in OneLake `/Files`, because that is the documented easy bridge. AML then reads that export through ABFSS or a data asset, trains and serves the model, and writes scores back as files that Fabric reloads.

The amber zone at the bottom is there on purpose. There are integration options that exist, but are not the same thing as a workshop-safe promise. Fabric calling AML batch endpoints is still preview. The `OneLakeDatastore` Python entity in AML is experimental. And the easy `/Tables` story is still weaker than the `/Files` story, so I do not promise zero-copy table magic on stage.

DEMO: close the section in `bridge-fabric-aml.md` and point at the exact ABFSS path pattern. That is usually enough for the audience to map the idea to their own lake.

SOURCE: """ + BRIDGE_URLS[0] + """
SOURCE: """ + BRIDGE_URLS[1] + """
SOURCE: """ + BRIDGE_URLS[2] + """
TRANSITION: Once both paths are on the table, the useful question is what actually felt different.""",
    )

    d.compare(
        "P3.22", "The same job done two ways: what felt different",
        dict(
            title="Microsoft Fabric",
            sub="Lake-centric, integrated path",
            icon="lakehouse",
            tone="success",
            items=[
                "Effort: fastest first success because the lake, notebooks, SQL, and MLflow start together.",
                "Control: lighter promotion story; Git and deploy stay metadata-first for ML items.",
                "Time and cost: strongest when one team already owns the lakehouse capacity.",
                "Best fit: data teams who want ML close to OneLake and Power BI.",
            ],
        ),
        dict(
            title="Azure Machine Learning",
            sub="Dedicated ML control plane",
            icon="azure-machine-learning",
            tone="azure",
            items=[
                "Effort: more setup because compute, environment, RBAC, ACR, and endpoints are explicit.",
                "Control: blue/green, mirror, batch endpoints, registries, and approvals are first-class.",
                "Time and cost: slower first setup; you pay for the compute and live deployments you keep.",
                "Best fit: teams that separate data engineering from production ML operations.",
            ],
        ),
        takeaway="Both platforms can train the model; the real choice is where you want the operational control plane.",
        minutes=4,
        core=False,
        notes="""I keep this slide deliberately balanced, because the room usually contains both personas.

Fabric felt faster because the data was already there. The same people who cleaned the logs could build the features, track runs, register the model, and hand a scored table to reporting without leaving the workspace. That is a very strong story when the center of gravity is the lake.

Azure ML felt heavier at first because it asks for explicit setup. But the payoff is operational control. Compute, environments, batch endpoints, online endpoints, rollout, registry sharing, and approvals are all first-class. If the team cares more about controlled production ML operations than about staying in one analytics workspace, that extra structure is useful, not bureaucracy.

The cost line also matters. I do not quote exact prices on stage. I explain the method. Fabric is mostly capacity-shaped. AML is mostly pay for the resources you start, with online endpoints billing while they exist.

TRANSITION: The final lesson slide is where I admit the real friction points, not just the architecture wins.""",
    )
    d.cards(
        "P3.23", "What was easy, what was painful",
        [
            dict(icon="clock", title="Metadata sync lag", body="Moving from Spark writes to SQL or semantic consumers is never instant. Rehearse the refresh hand-off.", tone="amber"),
            dict(icon="package", title="Version pins", body="Fabric can move toward MLflow 3. AML must stay at or below MLflow 2.16.2 today.", tone="amber"),
            dict(icon="server", title="Quota and warm-up", body="Cold clusters, image builds, and DS3_v2 quota are the live-demo killers, not the Python.", tone="amber"),
            dict(icon="alert-triangle", title="Preview boundaries", body="Fabric endpoints and Fabric-to-AML batch hooks are useful to mention, but risky to promise live.", tone="amber"),
        ],
        cols=2,
        source=HYBRID_SRC,
        minutes=3,
        core=True,
        notes="""This is the most honest slide in the part, and I do not rush it.

Lesson one: metadata sync lag is real. In Fabric, a Spark write finishing does not automatically mean every downstream SQL or semantic consumer is instantly ready. That is a demo lesson, but also a production lesson about hand-offs.

Lesson two: version pins matter. Fabric can discuss MLflow 3 ideas. Azure ML cannot yet be treated as an MLflow 3 target. The portable unit is still the MLflow model folder, not the full platform surface.

Lesson three: quota and warm-up beat code as the main operational risk. A cold cluster or an unbuilt image can waste more time than a model bug.

Lesson four: preview boundaries should stay visible. Mention them, use them carefully in rehearsal, but do not build your whole promise on them.

ASK: Which of these four feels most familiar in your current platform?
TRANSITION: If you want to replay the workshop after Friday, start with one bounded lab, not the whole estate.""",
    )

    d.discuss(
        "P3.24", "Lab: rebuild one piece in your own tenant",
        [
            dict(title="Bronze + silver in Fabric · 30 min", body="Need a Fabric workspace, `lh_fleet`, raw files under `Files/raw`, and notebook access for `nb_01` plus `nb_02`."),
            dict(title="Train + track in Azure ML · 20 min", body="Need the prepared features export, `cpu-cluster`, `env-fleet-sklearn`, and the AML-safe `mlflow<=2.16.2` pin."),
            dict(title="Deploy one endpoint · 30 min", body="Need a registered MLflow model with a signature, DS3_v2 quota, ACR access, and one smoke-test request."),
        ],
        when="2 min",
        minutes=2,
        core=False,
        notes="""If the audience wants homework, I keep the advice bounded.

Do not tell people to rebuild everything at once. Give them one success path. For data engineers, that is usually the Fabric bronze and silver path. For data scientists, it may be the AML train-and-track path. For platform engineers, it is often one endpoint deployment with a real smoke test.

The durations on the slide assume the prerequisites are already in place. That matters. The workshop repo is designed so each option has a narrow contract and a visible expected result.

IF SHORT ON TIME: turn this into a quick show-of-hands question: which lab would you try first?
TRANSITION: Let me close Part 3 in three sentences before we add an agent in Part 4.""",
    )

    d.recap(
        "P3.25", "Part 3 in three sentences",
        [
            dict(title="One scenario, two control planes", body="Fabric kept ETL and features close to OneLake. Azure ML externalized the ML release path.", tone="success"),
            dict(title="One portable unit", body="The MLflow model with its signature moves cleanly. Run history, UI, and registry semantics do not.", tone="azure"),
            dict(title="One shared destination", body="Scores come back to the lake so reporting and the next-step agent read the same reconciled truth.", tone="node"),
        ],
        question="If Part 3 ends with scored tables, what does Part 4 add? An agent that can ask and answer on top of them.",
        minutes=2,
        core=True,
        notes="""I close Part 3 with three short sentences.

First, we used one scenario and two control planes. Fabric was strongest where the data engineering work lived. Azure Machine Learning was strongest where explicit ML operations and serving control mattered.

Second, the portable unit was the MLflow model plus its signature, not the whole platform wrapper around it. That is why the cross-platform story stayed honest.

Third, the scoring output came back to the shared data layer. That matters because Part 4 is not a new data story. It is a new interaction layer on top of the same reconciled tables and the same failure-risk scores.

TRANSITION: Now that the lake has clean data and the model has produced risk scores, we can put an agent on top of that truth and see what questions it should answer.""",
    )
