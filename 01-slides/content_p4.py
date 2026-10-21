"""Part 4: Microsoft Foundry and the Fabric data agent on reconciled logs (P4.0-P4.17)."""
from __future__ import annotations

import json
from pathlib import Path

from deck_core import MONO
from deck_lib import Deck
from facts import F, d2, d3, n, pct


ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "06-demo-foundry-data-agent"
FACT_SHEET = ROOT / "00-presenter-guide" / "fact-sheets" / "foundry-dataagent.md"
REPORT_DIR = DEMO_DIR / "foundry-agent" / "reports"

_EXAMPLES = json.loads((DEMO_DIR / "data-agent" / "example-queries.json").read_text(encoding="utf-8"))
_ORACLE = json.loads((REPORT_DIR / "oracle-eval.json").read_text(encoding="utf-8"))
_NAIVE = json.loads((REPORT_DIR / "naive-eval.json").read_text(encoding="utf-8"))
_GT = json.loads((ROOT / "02-demo-data" / "reference_out" / "ground_truth.json").read_text(encoding="utf-8"))

P4_SOURCE = "Microsoft Learn: Foundry + Fabric data agent, verified 2026-10-18"
FABRIC_AGENT_SOURCE = "Microsoft Learn: Fabric data agent docs, verified 2026-10-18"
PREVIEW_SOURCE = "Microsoft Learn: preview timelines, verified 2026-10-18"

AGENT_SCOPE_EXCERPT = "Answer only from the published `lh_fleet` gold and ml tables in this demo."
DATA_SOURCE_EXCERPT = "Prefer `gold.*` for reconciliation and maintenance questions."
EXAMPLE_QUERY_EXCERPT = next(item["question"] for item in _EXAMPLES if item["id"] == "Q03")
SCHEMA_EXCERPT = "`delta_hours`: work-order open time minus episode start, in hours."

ORACLE_PASS = _ORACLE["summary"]["pass_rate"]
NAIVE_PASS = _NAIVE["summary"]["pass_rate"]
TYPE_COUNTS = _ORACLE["summary"]["by_type"]
DIFF_COUNTS = _ORACLE["summary"]["by_difficulty"]
UNANSWERABLE_COUNT = TYPE_COUNTS["unanswerable"]["total"] + TYPE_COUNTS["guardrail"]["total"] + TYPE_COUNTS["out_of_scope"]["total"]


def build(d: Deck) -> None:
    d.section(
        "P4.0", 4, "Part 4: Ask the data, in plain language",
        "We now have reconciled gold tables and frozen risk scores, so we can put a query assistant on top.",
        ["See the Fabric data-agent building blocks", "Connect it to Foundry with guardrails", "Evaluate answers and refusals before a live demo"],
        ("15:30 – 16:45", "75 minutes"),
        minutes=1,
        notes="""We finish the day where many business users want to start: asking questions in plain language.

The important setup is already done. Part 3 gave us reconciled gold tables, explicit exception facts, and one frozen risk-score table for a single scoring date. That means the agent does not need to invent business logic on the fly. It can stay close to curated tables with clear definitions.

I will keep this grounded. This is a query assistant, not an oracle. It is useful when the data model is strong, the scope is narrow, and the refusal rules are clear. It is dangerous when we pretend it knows things that are not in the data.

In this part I first show the operating model, then the live build in Fabric, then the Foundry wrapper, then the evaluation and guardrails.

TRANSITION: Let me start with the behavior change we actually want for users.""",
    )

    d.callout(
        "P4.1", "A good data agent gets users from question to checked SQL faster",
        "The value is not chat for its own sake. The value is faster, grounded access to reconciled tables, with the query visible and the limits explicit.",
        support=[
            dict(icon="database", title="Before", body="Open SQL, export rows, pivot manually, then explain the answer.", tone="node"),
            dict(icon="bot", title="After", body="Ask in English, inspect the SQL, then decide whether the answer is trustworthy.", tone="azure"),
            dict(icon="shield-check", title="Boundary", body="If the data is absent or the action is unsafe, refusal is the correct result.", tone="amber"),
        ],
        takeaway="The agent helps people reach curated data faster, but the data model still does the real work.",
        minutes=1.5, core=False,
        notes="""This is the mindset I want the room to keep for the whole part.

I am not selling conversation as a replacement for modeling. The useful pattern is much narrower. We already did the hard work: reconcile ids, normalize timestamps, define exceptions, freeze one scoring table. Now we let someone ask for the answer in English and we keep the generated SQL visible enough to inspect.

That is why I call it a query assistant. It accelerates access to trusted tables. It does not replace data engineering, and it does not replace judgement about whether the answer is complete.

If the room remembers one sentence, it is this: a helpful agent is transparent about both the SQL it used and the limits of the data it did not find.

ASK: How many of you would trust an answer more if the underlying SQL stayed visible?
TRANSITION: There are three practical ways to offer that experience today.""",
    )

    d.table_slide(
        "P4.2", "Three ways to put an agent on curated data fit different jobs",
        ["Path", "Best for", "Strength", "Watch out"],
        [
            ["Fabric data agent", "Fast Q&A over curated Fabric tables", "Native Fabric experience and easy analyst handoff", "Preview-heavy and limited to five sources"],
            ["Foundry agent + tools", "Guardrailed multi-tool orchestration", "Adds tracing, evaluation, refusal logic, and fallback tools", "More setup and more moving preview parts"],
            ["Copilot on a semantic model", "BI-style exploration for common analytics", "Lowest friction for business exploration", "Less explicit control over tool routing and guard logic"],
        ],
        col_w=[1.45, 1.75, 1.95, 1.95], size=15, core=False, minutes=2,
        source=P4_SOURCE,
        notes="""The three options overlap, but they are not the same product story.

The Fabric data agent is the shortest path when your data already lives in Fabric and the main need is read-only analytics over a curated source. That is why we build it first.

Foundry becomes useful when you want a wider control plane around that capability. In our demo it adds an explicit prompt-agent definition, tool routing, a fallback SQL function, tracing, and an offline evaluation harness.

Copilot over a semantic model is the lightest experience for business consumers who already live in BI-style exploration. I mention it because not every analytics question needs a custom agent stack.

So the decision is not “which one is best?” The decision is which control plane you need around the same underlying curated data.

SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
TRANSITION: To understand the Foundry layer, we need one picture of its moving parts.""",
    )

    d.arch(
        "P4.3", "Foundry wraps the data tool with models, tracing, and evaluation",
        [
            dict(id="user", label="User question", sub="Natural language prompt", icon="bot", col=0, row=1, tone="paper"),
            dict(id="project", label="Foundry project", sub="Identity, connections, telemetry", icon="microsoft-foundry", col=1, row=0, cspan=3, tone="node", h=0.9),
            dict(id="agent", label="Prompt agent", sub="Instructions, tool choice, refusal policy", icon="workflow", col=1, row=1, tone="azure", h=1.05),
            dict(id="model", label="Chat model", sub="Grounded generation, not business logic", icon="azure-openai-foundry-models", col=2, row=1, tone="success", h=1.05),
            dict(id="tools", label="Tools", sub="Fabric IQ, MCP, or a fallback SQL function", icon="data-agent", col=3, row=1, tone="azure", h=1.05),
            dict(id="eval", label="Evaluation set", sub="30 fixed questions with known answers", icon="scale", col=1, row=2, tone="paper", h=1.05),
            dict(id="trace", label="Tracing", sub="Project telemetry and Application Insights path", icon="application-insights", col=2, row=2, tone="paper", h=1.05),
            dict(id="safety", label="Safety controls", sub="Read-only guardrails, row caps, red-team prompts", icon="shield-check", col=3, row=2, tone="amber", h=1.05),
        ],
        edges=[
            ("user", "agent"),
            ("agent", "model"),
            ("model", "tools"),
            ("eval", "agent", "tests"),
            ("trace", "model", "records"),
            ("safety", "tools", "limits"),
        ],
        groups=[dict(label="Build once, then inspect every answer path", c0=1, r0=0, c1=3, r1=2, tone="azure")],
        takeaway="Foundry is the control plane around the tool call, not the place where reconciliation truth is created.",
        minutes=2, core=False, source=P4_SOURCE,
        notes="""This is the picture I use to explain why Foundry shows up only at the end of the day.

The reconciled truth still lives in Fabric tables. The Foundry layer adds the application scaffolding around that truth: project identity, model deployment, tool connections, tracing, and evaluation.

Notice what is not in the picture. The model is not where we define the CRIT match rate or decide how to count a reconciliation exception. Those definitions are already in the gold tables and the prompt instructions. Foundry helps route questions to the right tool and makes the behavior easier to observe and test.

That distinction matters in workshops because agent demos often look more magical than they are. Here I want the audience to see a normal software control plane around a very ordinary analytics problem.

SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
TRANSITION: Before we add Foundry, let us be honest about the Fabric data agent itself.""",
    )

    d.cards(
        "P4.4", "The Fabric data agent is useful because it is narrow, read-only, and source-aware",
        [
            dict(title="Five sources max", body="A data agent can use up to five sources, so the schema must stay curated.", icon="database", tone="azure"),
            dict(title="Source-native queries", body="It generates T-SQL, KQL, or DAX for the selected source.", icon="sql", tone="node"),
            dict(title="Your identity", body="Access runs under the signed-in Microsoft Entra ID user and source permissions.", icon="microsoft-entra-id", tone="node"),
            dict(title="Paid capacity", body="It needs paid Fabric capacity such as F2 or higher. Trial capacity has no data agent.", icon="microsoft-fabric", tone="amber"),
            dict(title="Still moving", body="Fabric IQ is preview, and the old Foundry Fabric tool is near deprecation.", icon="shield-alert", tone="amber"),
        ],
        cols=5, icon_pos="top", core=False, minutes=1.5, source=FABRIC_AGENT_SOURCE,
        notes="""These constraints are not a weakness of the slide. They are the reason the demo is believable.

The Fabric data agent works best when you give it a small number of well-described sources and keep the task analytical. It is not meant to front every operational system in the company.

The access model is equally important. Queries run with the signed-in user identity and whatever that user can read in the source. Sharing the agent does not magically grant table access underneath it.

I also want to say the commercial and lifecycle caveats out loud. The agent needs paid Fabric capacity, not Trial. And several related pieces are still preview-heavy, especially when we bridge out to Foundry.

SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
VERIFY: Re-check the exact tenant setting labels and any UI field limits in the live Fabric tenant before Friday.
TRANSITION: The biggest quality lever is not the prompt. It is the curated data model underneath.""",
    )

    d.arch(
        "P4.5", "Part 3 already turned three logs into one business grain",
        [
            dict(id="tel", label="Telematics", sub=f"{n(F.gold['fact_telemetry_daily'])} daily rows and {n(F.severity['CRIT'])} CRIT episodes", icon="database", col=0, row=0, tone="paper"),
            dict(id="cmms", label="CMMS", sub=f"{n(F.gold['fact_work_order'])} resolved work orders", icon="workflow", col=0, row=1, tone="paper"),
            dict(id="erp", label="ERP", sub=f"{n(F.gold['dim_asset'])} assets on one canonical id", icon="microsoft-fabric", col=0, row=2, tone="paper"),
            dict(id="gold", label="Gold facts", sub=f"{n(F.gold['fact_recon_exception'])} exceptions and {n(F.gold['agg_recon_monthly'])} monthly KPI rows", icon="data-warehouse", col=1, row=1, tone="azure"),
            dict(id="risk", label="Frozen score table", sub=f"{n(F.assets_scored)} assets scored on 2026-09-30", icon="line-chart", col=2, row=0, tone="success"),
            dict(id="agent", label="Data agent", sub="Answers are only as good as the curated tables and definitions", icon="data-agent", col=2, row=2, tone="azure", h=1.05),
        ],
        edges=[("tel", "gold"), ("cmms", "gold"), ("erp", "gold"), ("gold", "risk"), ("gold", "agent"), ("risk", "agent")],
        groups=[dict(label="Curated, reconciled, and frozen where stability matters", c0=1, r0=0, c1=2, r1=2, tone="azure")],
        takeaway="A weak schema gives a weak agent. A strong gold layer lets the agent stay boring and reliable.",
        minutes=1.5, core=False,
        notes="""I want to connect Part 4 back to Part 3 very explicitly.

The agent is not clever enough to rescue a messy model. It works because we already collapsed three disagreeing systems into one business grain. We have one canonical asset id, one exception fact table, one monthly reconciliation rollup, and one frozen risk-score table for demo stability.

That means the agent can answer from curated outputs instead of re-deriving business logic from raw logs. When someone asks about CRIT match rate, the best path is the monthly aggregate. When someone asks about a specific asset, the best path is the exception table plus the asset dimension.

This is the main engineering lesson of the part. If you want a trustworthy analytical agent, improve the model first and the prompting second.

TRANSITION: Once the tables are strong, four configuration levers matter far more than model temperature.""",
    )

    d.cards(
        "P4.6", "Four levers make the agent more reliable before any LLM tuning starts",
        [
            dict(title="Agent instructions", body=[dict(text=AGENT_SCOPE_EXCERPT, font=MONO, size=12.5)], icon="bot", tone="azure"),
            dict(title="Source instructions", body=[dict(text=DATA_SOURCE_EXCERPT, font=MONO, size=12.5)], icon="database", tone="node"),
            dict(title="Example query", body=[dict(text=EXAMPLE_QUERY_EXCERPT, font=MONO, size=11.5)], icon="sql", tone="success"),
            dict(title="Schema note", body=[dict(text=SCHEMA_EXCERPT, font=MONO, size=12.0)], icon="file-text", tone="paper"),
        ],
        cols=2, core=False, minutes=2,
        takeaway="Prompting helps, but examples and schema notes teach the join path and the business grain.",
        notes="""These four boxes are short because they are copied from real repo files, not invented for the slide.

The first lever is the agent instruction file. It narrows the role, the allowed tables, the frozen score date, and the refusal cases. The second lever is the data-source instruction file. That is where we teach table preference and business definitions such as when to use the monthly rollup instead of a detailed fact scan.

The third lever is example queries. They are the fastest way to teach join paths, groupings, and exact phrasings that must stay stable in the workshop. The fourth lever is schema description. If a column like `delta_hours` is ambiguous, the agent will write unstable SQL.

This is also why I do not start with model fine-tuning. For a query assistant, better metadata often beats a smarter model.

SOURCE: ..\\06-demo-foundry-data-agent\\data-agent\\agent-instructions.md
SOURCE: ..\\06-demo-foundry-data-agent\\data-agent\\data-source-instructions.md
SOURCE: ..\\06-demo-foundry-data-agent\\data-agent\\example-queries.json
SOURCE: ..\\06-demo-foundry-data-agent\\fabric-setup\\schema-descriptions.md
TRANSITION: Now let us use the walkthrough notebook to anchor the business story before the live build.""",
    )

    d.demo(
        "P4.7", "Demo 3a: the reconciliation story makes the later agent answers credible",
        [
            ("Open `nb_11_recon_walkthrough` and show the exception counts table", "3 min"),
            ("Tell the CRIT status split: 367 matched, 30 unmatched, 2 pending out of 399 total", "4 min"),
            ("Show response speed: 326/367 within 24h; 17 over 3 days", "3 min"),
            ("Use the monthly trend and site outlier: July at 83.3%; FR-PAR-01 leads with 6 misses", "3 min"),
            ("Drill into EQ-00619 and remind the room that the notebook also runs offline", "2 min"),
        ],
        ["`nb_11_recon_walkthrough` already works locally against `reference_out`", "Gold and ml tables can be loaded from `nb_10_load_gold_break_glass` if the workspace is empty"],
        ["The CRIT match rate excludes pending episodes from the denominator", "If Fabric is slow, show the notebook output or the frozen `ground_truth.json` checks instead of improvising"],
        "15 min", where="Fabric notebook  ·  `fabric-setup\\nb_11_recon_walkthrough`",
        minutes=15, core=True,
        notes="""I use this cue slide to do the business story before anyone sees an agent answer.

DEMO: Open `fabric-setup\\nb_11_recon_walkthrough`. First show the exception counts, so the audience sees the gold layer is explicit about what went wrong. Then move to the CRIT story. Be precise: there are **399** CRIT episodes in total, split into **367 matched**, **30 unmatched**, and **2 pending**. The match-rate denominator is the judged set, so the rate is **367 / 397 = 92.4 %**. After that, show response speed: **326** of the matched CRIT episodes got a corrective work order within 24 hours, and **17** took more than 3 days.

Next, use the monthly trend to show the weakest month, **2026-07 at 83.3 %**, then the site outlier, **FR-PAR-01 with 6** unmatched CRIT episodes. Finish with the EQ-00619 drill-down to prove the walkthrough can go from KPI to asset-level evidence.

WATCH OUT: Say “judged CRIT episodes” when you quote the rate. The full total is 399, but pending episodes are not judged yet.
IF SHORT ON TIME: Skip the truth-check precision/recall cell at the end. The extended version adds that quality discussion.
SOURCE: ..\\06-demo-foundry-data-agent\\fabric-setup\\nb_11_recon_walkthrough.py
TRANSITION: Once the room trusts the curated tables, I can build the Fabric data agent in front of them.""",
    )

    d.demo(
        "P4.8", "Demo 3b: build the Fabric data agent live, but keep a published safety copy",
        [
            ("Create **New item -> Fabric data agent** and name it `da_fleet_recon`", "3 min"),
            ("Add the SQL endpoint and select only the curated gold and ml tables", "4 min"),
            ("Paste the source description, source instructions, agent instructions, and schema notes", "4 min"),
            ("Import `example-queries.json` and test Q11, Q20, Q21, and Q30", "5 min"),
            ("Publish the agent and keep the pre-built copy visible as fallback", "4 min"),
        ],
        ["A drafted or already published `da_fleet_recon` copy is the safety net", "The exact files to paste are all under `06-demo-foundry-data-agent\\data-agent`"],
        ["Select only the curated tables listed in `rebuild-guide.md`", "If a trap answers instead of refusing, tighten instructions first and re-import the examples"],
        "20 min", where="Fabric workspace  ·  data-agent configuration UI",
        minutes=20, core=True,
        notes="""This live build is only convincing if it stays disciplined and a little boring.

DEMO: Create the Fabric data agent in the workspace and name it `da_fleet_recon`. Add the lakehouse SQL analytics endpoint, then select only the curated tables from the rebuild guide. Do not browse or add raw tables on stage. After that, paste the data-source description, data-source instructions, agent instructions, and schema descriptions. Import `example-queries.json`, then immediately test one monthly KPI question, one asset drill-down, one risk-band question, and one refusal.

The point of the live build is not to show every button. The point is to show that reliability comes from curation: narrow tables, explicit instructions, real examples, and published configuration files.

WATCH OUT: Keep the published safety copy ready. If the live draft UI is slow or the import path changes, switch to the safety copy and keep the teaching point.
IF SHORT ON TIME: In the extended version I show more schema-description detail. In the 20-minute version, stay with the four tests from the rebuild guide.
VERIFY: Re-check the live UI field limits, import-size behavior, and exact tenant settings before Friday.
SOURCE: ..\\06-demo-foundry-data-agent\\rebuild-guide.md
SOURCE: ..\\06-demo-foundry-data-agent\\troubleshooting.md
TRANSITION: Publishing the Fabric agent is useful on its own, but Foundry adds the control plane around it.""",
    )

    d.arch(
        "P4.9", "Foundry should call the published data agent through Fabric IQ or MCP, not the aging legacy path",
        [
            dict(id="user", label="User prompt", sub="Question arrives in the Foundry app or portal", icon="bot", col=0, row=1, tone="paper"),
            dict(id="foundry", label="Foundry agent", sub="`agents.create_version`", icon="microsoft-foundry", col=1, row=1, tone="azure", h=1.3),
            dict(id="iq", label="Fabric IQ / MCP", sub="Preferred preview successor for new work", icon="data-agent", col=2, row=0, tone="success"),
            dict(id="mcp", label="Published data agent", sub="One MCP tool over the curated Fabric source", icon="microsoft-fabric", col=3, row=0, tone="node", h=1.3),
            dict(id="sql", label="Fallback SQL tool", sub="Read-only allow-list and 200-row cap", icon="sql", col=2, row=1, tone="paper"),
            dict(id="tables", label="Lakehouse tables", sub="Gold and ml schemas behind both paths", icon="lakehouse", col=3, row=1, tone="paper"),
            dict(id="legacy", label="Legacy Fabric tool", sub="Preview, deprecated on 2026-11-06", icon="shield-alert", col=2, row=2, tone="amber"),
        ],
        edges=[
            dict(a="foundry", b="legacy", dash=True, color="amber"),
            ("user", "foundry"),
            ("foundry", "iq"),
            ("iq", "mcp"),
            ("foundry", "sql"),
            ("sql", "tables"),
            ("mcp", "tables"),
        ],
        groups=[dict(label="Use the published agent as a tool, not as hidden magic", c0=1, r0=0, c1=3, r1=2, tone="azure")],
        core=False, minutes=2, source=P4_SOURCE,
        notes="""This slide is where I say the roadmap point plainly.

For new work, the direction is Fabric IQ and MCP around the published data agent. That is the bridge the docs point to now. In our demo repo, the Foundry prompt agent also carries a fallback read-only SQL function, because preview paths can wobble and I want the guardrails explicit.

The old Microsoft Fabric data-agent tool still exists in Foundry, but it is preview and scheduled for deprecation on **2026-11-06**. That is why it is amber on the slide. I would not anchor a new design on it this close to the date.

In the same family of roadmap changes, the Foundry visual workflow builder is retiring on **2026-12-01**, and prompt flow is retiring on **2027-04-20**. I repeat those dates on the timeline later because people do plan against them.

VERIFY: Re-check the exact portal banners, the Fabric IQ connection flow, and the MCP tool name in the live tenant on Friday morning.
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
TRANSITION: With the path clear, we can run a question ladder from easy counts to trap refusals.""",
    )

    d.demo(
        "P4.10", "Demo 3c: run a question ladder from warm-up counts to trap refusals",
        [
            ("Warm-up: 316 assets, split 300 Active / 10 Retired / 6 Disposed", "2 min"),
            ("Reconciliation: 211 exceptions and 30 CRIT episodes without a work order", "3 min"),
            ("Drill-down: EQ-00619 is `ACTIVE_ASSET_SILENT`, last telemetry 2026-08-18T18:00:00Z", "3 min"),
            ("Risk: High 9, Medium 7, Low 248; FR-PAR-01 has the most High-risk assets", "3 min"),
            ("Multi-hop and traps: ask for top-5 risk context, then force a refusal on fuel cost or delete", "4 min"),
        ],
        ["Keep `qa-script.md` open beside the chat window", "The published safety copy and offline oracle report are valid fallbacks if the live stack hesitates"],
        ["Ask for SQL on at least one answer", "If a number drifts, repeat the exact wording from the script before you debug anything else"],
        "15 min", where="Fabric data agent or Foundry chat  ·  `qa-script.md` open",
        minutes=15, core=True,
        notes="""This is the live Q&A segment, and the trick is to make it feel systematic rather than magical.

DEMO: Start with the warm-up count question so the audience sees the business grain immediately. Then move to the exception total and the unreported-CRIT count. After that, use the EQ-00619 drill-down because it proves the agent can name both the exception type and the last telemetry timestamp. For the risk section, ask the frozen 2026-09-30 band question and the site with the most High-risk assets. Finish with one multi-hop question and one refusal. I like Q26 on fuel cost or Q30 on delete because the refusal is obviously correct.

Read the SQL aloud for at least one answer. That keeps the audience focused on grounding instead of style.

WATCH OUT: If an answer is wrong, do not improvise a new phrasing. Repeat the exact script wording first, because the evaluation set was tuned to those questions.
IF SHORT ON TIME: The extended version adds more site and month variations. In the 15-minute version, keep the ladder to one example per category.
SOURCE: ..\\06-demo-foundry-data-agent\\qa-script.md
TRANSITION: The most important thing after the demo is knowing what the agent should refuse.""",
    )

    d.cards(
        "P4.11", "A safe analytical agent refuses missing facts, future forecasts, and write actions",
        [
            dict(title="Fuel cost", body="Refuse. The dataset has fuel-rate style telemetry, not any price or cost table.", icon="shield-alert", tone="amber"),
            dict(title="Operator identity", body="Refuse. No driver or operator identity exists in the demo sources.", icon="shield-alert", tone="amber"),
            dict(title="Future forecast", body="Refuse. The frozen score table covers one scoring date only.", icon="shield-alert", tone="amber"),
            dict(title="Delete request", body="Refuse. The agent is read-only and must not close or change work orders.", icon="shield-alert", tone="amber"),
        ],
        cols=2, core=False, minutes=1.5,
        takeaway="A refusal is not a failure when the question asks for data or actions outside the contract.",
        notes="""I like this slide because it normalizes a behavior many users initially dislike.

These refusals are not edge cases. They are part of the product quality. The Fabric tables do not contain fuel prices, operator identity, or future forecasts past the frozen score date. And the whole assistant is defined as read-only. So a confident answer would be worse than no answer.

This is why the evaluation set includes refusal cases on purpose. We are not only scoring analytical correctness. We are also checking whether the agent knows when to stop.

If someone in the room asks whether we could add fuel cost later, the answer is yes, but only by loading a real cost source and updating the contract. We do not solve a missing dataset with a better prompt.

TRANSITION: Once refusals are part of the contract, we can evaluate the agent like any other software component.""",
    )

    d.chart_slide(
        "P4.12", "The 30-question evaluation checks both analytical accuracy and refusal behavior",
        ["agg", "count", "list", "multi-hop", "refusal", "easy", "medium", "hard"],
        {"Questions": [
            TYPE_COUNTS["agg"]["total"],
            TYPE_COUNTS["count"]["total"],
            TYPE_COUNTS["list"]["total"],
            TYPE_COUNTS["multi-hop"]["total"],
            UNANSWERABLE_COUNT,
            DIFF_COUNTS["easy"]["total"],
            DIFF_COUNTS["medium"]["total"],
            DIFF_COUNTS["hard"]["total"],
        ]},
        fmt="0",
        side=[
            dict(title="Pass rule", body="Exact counts where they are exact; tolerance checks for rates and scores; set equality for lists; refusal checks for traps.", tone="azure"),
            dict(title="Difficulty mix", body=f"Easy {DIFF_COUNTS['easy']['total']}, medium {DIFF_COUNTS['medium']['total']}, hard {DIFF_COUNTS['hard']['total']} questions.", tone="node"),
            dict(title="Reference scores", body=f"Stand-in oracle {ORACLE_PASS * 100:.0f}%; naive baseline {NAIVE_PASS * 100:.0f}%. These are offline harness results, not live LLM measurements.", tone="amber"),
        ],
        core=False, minutes=2,
        takeaway="The dataset and the scoring logic are fixed, so we can test the agent before the live workshop.",
        notes="""I want this slide to feel closer to software testing than to benchmark theatre.

The evaluation set has 30 fixed questions with known answers. It covers aggregates, counts, lists, multi-hop questions, and refusal cases. The scoring code then checks structured outputs, not just prose. Counts must match exactly. Lists can pass if the same set appears in a different order. Rates, durations, costs, and risk scores use explicit numeric tolerances. Trap questions pass only if the result is a refusal or clearly unanswerable.

That is why I describe the scores carefully. The **oracle** here is a stand-in that answers from the validated example SQL, so it gets **100 %**. The **naive** baseline intentionally does not follow the contract and scores **0 %**. These are harness endpoints, not live model benchmarks.

SOURCE: ..\\06-demo-foundry-data-agent\\b4_fleet_demo\\scoring.py
SOURCE: ..\\06-demo-foundry-data-agent\\foundry-agent\\reports\\oracle-eval.md
SOURCE: ..\\06-demo-foundry-data-agent\\foundry-agent\\reports\\naive-eval.md
TRANSITION: The next question is how we stop a real agent from drifting outside that contract.""",
    )

    d.cards(
        "P4.13", "Guardrails work best in layers: prompt rules, tool limits, SQL checks, and red-team prompts",
        [
            dict(title="Read-only contract", body="Instructions say no writes, no hidden prompts, no future forecasts, and no made-up entities.", icon="shield-check", tone="azure"),
            dict(title="Allow-list", body="The fallback SQL tool only permits approved gold and ml tables.", icon="database", tone="node"),
            dict(title="200-row cap", body="Generated SQL is sanitized to SELECT only and forced under the configured row limit.", icon="line-chart", tone="node"),
            dict(title="Red-team set", body="Prompt injections, data exfiltration asks, and unsafe actions are tested before the workshop.", icon="shield-alert", tone="amber"),
        ],
        cols=2, core=False, minutes=2,
        takeaway="One good prompt is not a guardrail strategy. The tool path needs its own controls.",
        notes="""If I had to summarize the guardrail philosophy in one line, it would be “assume one layer can fail.”

The prompt instructions already say read-only, but that is not enough. The fallback SQL path has its own allow-list of approved tables. It rejects comments, non-SELECT statements, and oversize result sets. The configured cap is 200 rows, which is enough for workshop evidence but small enough to stop casual over-export. On top of that, the repo includes red-team prompts that try to provoke policy overrides, hidden-schema requests, and operational write actions.

This is also why the Foundry wrapper is useful. It gives us a place to add explicit tool controls even if the Fabric data agent itself is the main business-facing surface.

SOURCE: ..\\06-demo-foundry-data-agent\\foundry-agent\\guardrails.py
SOURCE: ..\\06-demo-foundry-data-agent\\foundry-agent\\red-team-prompts.md
TRANSITION: Security and governance follow the same principle: the agent inherits permissions, it does not bypass them.""",
    )

    d.compare(
        "P4.14", "Security stays with the user identity and the source permissions, not with the chat window",
        dict(
            title="What follows the user",
            sub="Verified from current docs",
            icon="microsoft-entra-id",
            tone="azure",
            items=[
                "Queries run under the signed-in Microsoft Entra ID identity and source permissions.",
                "Row-level and column-level security continue to apply where configured.",
                "Sharing the data agent does not grant underlying source access by itself.",
                "For semantic-model querying, Read is enough; Build is not required.",
            ],
        ),
        dict(
            title="What admins still own",
            sub="Least privilege and tenant checks",
            icon="shield-check",
            tone="node",
            items=[
                "Assign Foundry User for build/test and Project Manager only for connection setup.",
                "Legacy Foundry Fabric-tool integration uses delegated user access, not service principals.",
                "Keep Fabric and Foundry in the same tenant and follow region guidance.",
                "Re-check the exact tenant setting labels before the live rehearsal.",
            ],
        ),
        core=False, minutes=2, source=P4_SOURCE,
        notes="""People often assume a chat layer changes the security model. In this case it does not.

The important verified point is that access still follows the signed-in Microsoft Entra ID user and the permissions on the source. If row-level or column-level security is configured, it continues to apply. Sharing the agent does not grant table access underneath it. That is the healthy default story.

The admin side still matters, though. Foundry User is enough for building and testing an agent. Project Manager is only for creating project-level connections. And the legacy Foundry Fabric-tool integration is still delegated-user oriented, which is one reason it is a weak fit for unattended daemon patterns.

VERIFY: Confirm the exact tenant setting labels and connection path in the live environment. I am avoiding any claim about portal wording because that changes quickly.
SOURCE: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
TRANSITION: After permission flow, the next operational question is what we can actually observe and cost.""",
    )

    d.cards(
        "P4.15", "Tracing and cost matter because preview stacks fail in boring ways, not dramatic ones",
        [
            dict(title="Project traces", body="Responses on the Foundry project endpoint flow into the project telemetry path.", icon="application-insights", tone="azure"),
            dict(title="Code hook", body="The repo instruments tracing through `AIProjectInstrumentor().instrument(...)`.", icon="workflow", tone="node"),
            dict(title="Cost split", body="Fabric capacity pays for the data agent path; Foundry adds model and tool usage.", icon="microsoft-foundry", tone="amber"),
            dict(title="Day-of check", body="Exact portal trace views, latency, and tenant billing labels remain VERIFY items.", icon="shield-alert", tone="amber"),
        ],
        cols=2, core=False, minutes=2, source=P4_SOURCE,
        notes="""There are two practical reasons to show tracing and cost, even briefly.

First, preview-heavy stacks usually fail in small operational ways: the wrong connection, the wrong model deployment name, a tool not surfacing traces where you expected. The repo already includes a tracing helper that instruments the Foundry project path and can pull an Application Insights connection string when available. That is enough to explain the observability pattern without pretending we verified a full tenant wiring.

Second, cost has two layers. The Fabric data-agent path depends on Fabric capacity. The Foundry wrapper adds model and tool usage on top. I do not quote exact prices because the tenant deployment type and billing configuration can change them.

VERIFY: Re-check the exact trace surfacing path and billing labels in the chosen project before Friday. Those are operational facts, not stable teaching facts.
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
SOURCE: ..\\06-demo-foundry-data-agent\\foundry-agent\\tracing.py
TRANSITION: Finally, let me put the moving roadmap dates on one slide so nobody leaves with an outdated anchor.""",
    )

    d.timeline(
        "P4.16", "Three dates matter if you plan new work around this demo path",
        [
            dict(when="2026-11-06", title="Legacy Fabric tool", body="Preview Foundry Fabric data-agent tool is scheduled for deprecation.", tone="amber"),
            dict(when="2026-12-01", title="Visual workflow builder", body="Foundry visual workflows retire; new work should anchor on Agent Framework patterns.", tone="amber"),
            dict(when="2027-04-20", title="Prompt flow", body="Prompt flow retirement stays on the roadmap, so do not build new dependencies on it.", tone="amber"),
        ],
        core=False, minutes=1.5, source=PREVIEW_SOURCE,
        notes="""I keep this slide short, but I do not skip it.

These dates matter because the architecture choice is different when a path is healthy for net-new work versus when it is only still available. The clearest immediate date is **2026-11-06** for the legacy Foundry Fabric data-agent tool. That is close enough that I would treat it as a migration path, not a foundation. The next date is **2026-12-01** for the Foundry visual workflow builder. Then **2027-04-20** for prompt flow.

The practical message is simple: use the data agent itself where it helps, but anchor orchestration and guardrails on the current Foundry agent patterns, not on retiring surfaces.

VERIFY: Re-check these portal banners and dates in the live tenant on the day of the workshop.
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow
SOURCE: https://learn.microsoft.com/en-us/azure/foundry/concepts/prompt-flow
TRANSITION: Let me close Part 4 by tying this back to the workshop story from the morning.""",
    )

    d.recap(
        "P4.17", "Part 4 in three sentences",
        [
            dict(title="Curated data first", body="The agent works because the gold tables and the frozen score table already carry the business truth.", tone="azure"),
            dict(title="Agent quality is testable", body="We can score fixed questions, expected refusals, and tool behavior before any live session.", tone="node"),
            dict(title="Roadmaps matter", body="Use the current Fabric IQ and Foundry patterns, and keep preview and retirement dates visible.", tone="amber"),
        ],
        question="Which of your own questions would you only trust after seeing the SQL, the contract, and a refusal test?",
        core=False, minutes=0.5,
        notes="""I close this part with the same discipline I wanted throughout the demo.

First, the agent only looks smart because the data model is strong. Second, the behavior is testable. We do not have to trust a vibe; we can check counts, lists, tolerances, and refusals before we ever show the workflow to users. Third, the roadmap matters. This is an area where product names and preferred paths are still moving, so we design with those dates in mind.

If the audience leaves with one practical next step, I want it to be this: pick one narrow analytical use case, curate the tables, define the refusal cases, and evaluate the agent like software.

TRANSITION: That closes the workshop story from raw logs to a guarded question-answering layer.""",
    )
