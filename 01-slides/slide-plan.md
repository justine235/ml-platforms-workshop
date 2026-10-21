# Slide plan — ML platforms on Microsoft (full-day workshop)

Audience: data scientists and data engineers. Language: English, simple natural sentences (no slogans). Style: neutral white / blue / amber, Lucide-style outline icons,
official Microsoft product icons, native editable shapes, speaker notes on every slide. One focal visual and one takeaway per slide; detail goes to notes or the appendix.
Evidence column: `FS-*` = fact sheet in `00-presenter-guide/fact-sheets`, `GT` = `02-demo-data/reference_out/ground_truth.json`, `C§n` = scenario contract section, `B*` = builder folder.

Day plan (09:00-17:00): Opening 20 min | Part 1 90 min | break | Part 2 75 min | lunch | Part 3 115 min | break | Part 4 75 min | Wrap 15 min.
Half-day cut: Part 1 45 + Part 2 30 + Part 3 Fabric only 60 + Part 4 45 (slides marked `core` stay; others are skippable).

Layouts: `title` `section` `agenda` `bullets` `cards` `compare` `flow` `arch` `loop` `stat` `code` `chart` `table` `callout` `demo` `ladder` `timeline` `recap` `discuss`.

## Opening (5 slides, 20 min)

| id | Headline (takeaway) | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| O1 | From notebook to production: ML platforms on Microsoft | title | Title, subtitle "Fabric, Azure Machine Learning and Foundry — a workshop for data scientists and data engineers", date 23 Oct 2026 | - | Welcome; set the tone: practical, rebuildable, honest about previews. |
| O2 | Today in four parts, with three demos you can rebuild | agenda | Timeline bar 09:00-17:00 with 4 parts, 2 breaks, lunch; demo markers | day plan | Explain rhythm: 60 percent hands-on views, questions any time, repo has everything. |
| O3 | By the end of the day you can do five things | cards | 5 outcome cards (choose platform, explain MLflow in both, draw an MLOps flow, rebuild the demos, put an agent on reconciled data) | - | Outcomes, not features. Ask the room what they use today (poll: Databricks, AML, Fabric, nothing). |
| O4 | One story all day: three systems that disagree about the same machines | arch | Telematics logs + CMMS work orders + ERP asset register -> reconciled view -> failure risk -> agent | C§1, GT | Introduce Contoso Fleet, synthetic data (not customer data), same data in every demo. |
| O5 | Everything you see today is rebuildable | cards | Repo map: data generator, 4 demo folders, slides, presenter guide; "40 seconds to regenerate the data" | README | Show the folder tree; promise: rebuild guides with expected numbers. |

## Part 1 — Fabric vs Azure ML, with MLflow at the center (20 slides, 90 min incl. 25 min demo)

| id | Headline | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| P1.0 | Part 1: Understanding the ML platforms at Microsoft | section | Part number, title, 90 min, what we will cover | - | One sentence on why two platforms exist. |
| P1.1 | Three platforms, three centers of gravity | arch | Fabric = data first; Azure ML = ML lifecycle first; Foundry = models and agents; shared base (Entra ID, Azure, storage) | FS-fabric-ml, FS-aml, FS-foundry | Not old vs new: different starting points. |
| P1.2 | Fabric is a data platform that also does machine learning | cards | OneLake, Lakehouse + Spark, notebooks, experiments, ML models, PREDICT, Power BI, Real-Time Intelligence | FS-fabric-ml | Everything shares one copy of data and one capacity. |
| P1.3 | Azure Machine Learning is an ML platform that connects to your data | cards | Workspace, compute clusters, jobs and pipelines, environments, registries, endpoints, monitoring | FS-aml | Everything about the model lifecycle; data stays where it is. |
| P1.4 | Follow one model through its life: where does each step run? | table | Rows: prep, explore, train, track, register, deploy, monitor, retrain; columns Fabric / Azure ML | FS-fabric-ml, FS-aml | Walk the lifecycle once; highlight overlaps. |
| P1.5 | Compute and cost work differently | compare | Fabric: shared capacity (F-SKU, CU, smoothing). Azure ML: per-VM-hour clusters that scale to zero. Consequences for notebooks, jobs, endpoints | FS-fabric-ml, FS-aml | "Which bill is it" matters more than features. No exact prices (check pricing page). |
| P1.6 | Data access: one lake or many stores | arch | OneLake (shortcuts, ABFSS) vs datastores and data assets; the bridge between them | FS-aml, FS-fabric-de-rti | Hybrid pattern: Fabric ETL -> OneLake -> Azure ML. |
| P1.7 | Fabric and Azure ML side by side | compare | 8 rows: main user, compute, tracking, registry, deployment, CI/CD, networking and governance, maturity (GA/preview) | FS-* (B3 bridge doc) | Table is honest: Fabric ML endpoints are preview. |
| P1.8 | MLflow is the common language of both platforms | section | Part 1 chapter divider: MLflow | - | If you know MLflow you already know 80 percent. |
| P1.9 | MLflow in one picture: tracking, models, registry | arch | Concept map: experiment -> run -> params/metrics/artifacts -> model (flavor, signature) -> registry -> serving | B1 concept-map | Same objects in both platforms. |
| P1.10 | Tracking: experiments and runs look the same, live in different places | compare | Fabric experiment item vs Azure ML jobs and experiments; tracking URI; what is logged automatically | B1 concept-map, FS | Autolog is on by default in Fabric notebooks. |
| P1.11 | Models: the signature is what makes scoring easy | code | MLmodel file excerpt; why PREDICT and no-code deployment need a signature | B1, FS | Log signature + input example every time. |
| P1.12 | The registry is where the two platforms differ most | compare | Fabric ML model: versions only. Azure ML: registry, stages through SDK, aliases?; patterns for champion/challenger | B1 concept-map | Biggest practical difference for MLOps. |
| P1.13 | Versions are the quiet trap | table | Fabric Runtime 1.3 / 2.0 MLflow versions; Azure ML pinned to MLflow 2.16.2 or lower; MLflow 3 notes | FS-fabric-ml, FS-aml | Pin everything; show the pip line. |
| P1.14 | The same training script runs on a laptop, in Fabric and in an Azure ML job | code | Short code: load features, train, log; where the three platforms differ (one line each) | B1 | Foreshadows the demo. |
| P1.15 | Demo 1: the MLflow tour, one script and three platforms | demo | 25 min timeline: local (5), Fabric (10), Azure ML (10); what to watch for; expected numbers (test PR-AUC about 0.38) | B1 run-of-show | Keep it concrete; compare runs side by side. |
| P1.16 | What travels between platforms and what does not | cards | Portable: model folder, code, params. Not portable: run history, lineage, registry pointers | B1 portability | Honest limits. |
| P1.17 | How to choose: five questions | flow | Where is the data? Who builds? How is it served? What governance? What skills? -> Fabric / Azure ML / both | FS, B3 bridge | Decision guide, no dogma. |
| P1.18 | The hybrid pattern we will build today | arch | Fabric ETL -> OneLake features -> Azure ML train/deploy -> scores back to OneLake -> Power BI and agent | B3 bridge | Most real teams end up here. |
| P1.19 | Part 1 in three sentences | recap | 3 takeaways + one question for the room | - | Check understanding; take questions. |

## Part 2 — MLOps concepts (21 slides, 75 min incl. 10 min exercise)

| id | Headline | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| P2.0 | Part 2: MLOps, from notebooks to a reliable product | section | Part number, 75 min | - | Define the problem before the tools. |
| P2.1 | MLOps is DevOps plus two things that keep changing: data and models | cards | Code / data / model: three things to version, test and release | MLOps docs | The model is a build artifact of code + data + environment. |
| P2.2 | Why models fail after launch | cards | Data drift, silent upstream changes, label delay, ownership gaps | C§4, C§9 | Real examples from our data: firmware change, seasonal shift, late work orders. |
| P2.3 | The ML lifecycle is a loop, not a line | loop | Frame, data, features, train, evaluate, register, deploy, monitor, retrain | MLOps docs | Where each team member sits on the loop. |
| P2.4 | MLOps maturity: five levels from manual to automated | ladder | Level 0 no MLOps ... level 4 full automation; where most teams are | FS-aml (maturity model) | Be honest: level 2 is a great target. |
| P2.5 | What to version: code, data, features, models, environments | table | Artifact / how to version / Fabric / Azure ML | FS | One row per artifact. |
| P2.6 | Reproducible environments start with pins | code | pip pins (MLflow, scikit-learn, pandas); Fabric Environment, Azure ML environment | FS, B2b, B3 | The MLflow 2.16.2 pin story. |
| P2.7 | Experiment tracking is your lab notebook | cards | What to log: params, metrics, data version, git sha, artifacts, tags | B1 | Naming conventions and tags. |
| P2.8 | Data contracts: check the data before you train on it | table | Schema, volume, range, freshness, identity resolution rate; our contract numbers | C§10, GT | Fail fast, with clear messages. |
| P2.9 | Avoid leakage: split by time and leave a gap | chart | Timeline of train / gap / valid / test / score with the 7-day purge gap | C§8 | Why random splits lie for time series. |
| P2.10 | A model is only good compared to a baseline | chart | Native bar chart: prevalence 0.045, rule 0.068, logistic 0.29, HGB 0.38 (test PR-AUC) | GT | Real numbers from our data; "modest signal is fine if it is useful". |
| P2.11 | Promotion needs a gate, not a feeling | flow | Champion vs challenger rule: +0.01 PR-AUC and no precision regression; human approval for prod | B2b, B3 | Gate logic is code. |
| P2.12 | Deployment patterns: batch, online, shadow, canary | compare | When each fits; ours is daily batch plus an optional online endpoint | FS-aml | Choose by latency and cost. |
| P2.13 | Three pipelines: code, training, release | flow | CI (tests), CT (train and evaluate), CD (deploy with approvals) | B2b, B3 | Different triggers, different owners. |
| P2.14 | Dev, test, prod: what you promote | compare | Promote code and retrain vs promote the model artifact; Fabric Git + deployment tooling, Azure ML registries | FS | Tradeoffs: reproducibility vs control. |
| P2.15 | Monitoring: input drift first, accuracy later | cards | Data quality, input drift (PSI), prediction drift, performance with delayed labels, operations | FS, C§9 | Labels arrive weeks later: drift is your early warning. |
| P2.16 | Drift in our data: real shift versus expected season | chart | Native bar chart of PSI by class and sensor (major 0.88-3.71; moderate 0.10-0.19 seasonal) | GT drift | Not every alert is a defect. |
| P2.17 | When to retrain: schedule, trigger or both | flow | Time trigger, drift trigger, performance trigger, manual; retrain is not redeploy | MLOps docs | Cost and risk of each. |
| P2.18 | Governance: know what is deployed, who changed it and why | cards | Lineage, access, approvals, model card, audit trail | FS | Where Fabric and Azure ML give you each piece. |
| P2.19 | Who owns what: roles and hand-offs | table | Data engineer, data scientist, ML engineer, platform, business owner | - | RACI-style, adapt locally. |
| P2.20 | Exercise: where is your team on the ladder? | discuss | 10-minute self-assessment, 5 questions; share one gap | - | Run as pairs; collect on a flipchart. |

## Part 3 — End-to-end demo: ETL + ML + MLOps on Fabric and Azure ML (26 slides, 115 min)

| id | Headline | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| P3.0 | Part 3: One use case, built end to end on two platforms | section | Part number, 115 min: Fabric 55, Azure ML 45, bridge 15 | - | Set expectations: this is a guided rebuild. |
| P3.1 | What we will build | arch | Sources -> bronze -> silver -> gold -> features -> model -> scores -> alerts | C§5 | The medallion and the ML flow on one canvas. |
| P3.2 | The data: three systems that spell the same machine differently | table | Same machine, three spellings: telematics `eq00143` / `EQ_00143` / `EQ-143`; CMMS `E00143` / `EQ 00143` / `LEG-nnnn`; ERP `EQ-00143` | C§3 | Real spellings from the generator. |
| P3.3 | What is wrong with the data, on purpose | table | 1,209 duplicate events, 217 out-of-range sensor values, 2,066 late events, 4,351 events with an unresolvable asset id, mixed time zones | GT silver, C§4 | The problems you will meet in any real log. |
| P3.4 | Demo 2a: Fabric end to end in 55 minutes | demo | Steps with timings: setup, bronze, silver, gold, features, train, register and score, pipeline, drift, CI/CD | B2a, B2b run-of-show | Show the pre-run results first. |
| P3.5 | Bronze: land the raw files and keep them as they came | cards | Telematics JSONL, CMMS CSV, ERP CSV -> Delta; ingest metadata; explicit schemas | B2a | Never fix data in bronze. |
| P3.6 | Silver: clean the data and resolve identities in four tiers | flow | EXACT_NORM 196,810 -> SERIAL 4,350 -> CROSSWALK 2,180 -> UNRESOLVED 4,351 (events) | GT | Resolution tiers with counts. |
| P3.7 | Gold: match faults to work orders | arch | Episodes (24 h before, 7 d after) -> match -> status; exceptions | C§6, GT | The business rule in one picture. |
| P3.8 | What the reconciliation found | chart | Native chart: significant episodes 455 matched / 91 unmatched / 11 pending; exceptions by type (211) | GT | 30 CRIT episodes without any work order. |
| P3.9 | Features: 42 columns known at the end of each day | table | Feature groups, label definition, purged splits | C§8 | Leakage-safe by construction. |
| P3.10 | Train and track: five models, one leaderboard | chart | MLflow experiment leaderboard (valid and test PR-AUC) | B2b, GT | Autolog vs explicit logging. |
| P3.11 | Register and score: PREDICT in a notebook | code | MLFlowTransformer / PREDICT snippet; risk bands 9 / 7 / 248 | B2b, GT | Scores land in a table for Power BI and the agent. |
| P3.12 | Orchestrate: one pipeline, one schedule, one alert | flow | pl_fleet_daily: ETL notebooks -> features -> train -> score -> drift -> alert | B2b | Failure paths and retries. |
| P3.13 | Monitor: drift report and what triggers the alert | chart | PSI table; thresholds 0.10 / 0.25 | GT drift | Expected vs unexpected drift. |
| P3.14 | Ship it: Git, variables and deployment per environment | arch | Dev -> test -> prod; Git, Variable Library, fabric-cicd, GitHub Actions | B2b cicd | Models are re-trained or re-logged per workspace. |
| P3.15 | Demo 2b: Azure ML end to end in 45 minutes | demo | Steps with timings and what is pre-built | B3 run-of-show | Environment build and endpoints are pre-baked. |
| P3.16 | Azure ML: a pipeline in YAML, from data asset to registered model | code | pipeline-train.yml excerpt: prep, train, evaluate, register | B3 | Same logic as the Fabric notebooks. |
| P3.17 | Sweep and gate: find a better model, promote it only if it is better | flow | Sweep job -> best trial -> gate (+0.01 PR-AUC) -> register | B3 | Show the gate decision JSON. |
| P3.18 | Deploy: a managed online endpoint with blue and green | arch | Traffic 90/10, mirror, rollback; no-code MLflow deployment | B3 | Needs a signature. |
| P3.19 | Batch scoring: the nightly job | flow | Batch endpoint -> risk table -> OneLake | B3 | Our use case is daily batch. |
| P3.20 | CI/CD with GitHub Actions and OIDC: no secrets in the repository | arch | CI, infra, train, promote workflows; federated credential | B3 mlops | OIDC in one picture. |
| P3.21 | The bridge: Fabric ETL feeds Azure ML, scores come back | arch | OneLake ABFSS, data asset, endpoint, scores to OneLake | B3 bridge | Preview vs GA items called out. |
| P3.22 | The same job done two ways: what felt different | compare | Step-by-step comparison: effort, control, time, cost | B2b, B3 | Be honest about trade-offs. |
| P3.23 | What was easy, what was painful | cards | 4 lessons from the build (sync lag, pins, quotas, previews) | builders' troubleshooting | Real failure modes. |
| P3.24 | Lab: rebuild one piece in your own tenant | discuss | Options with durations: bronze+silver (30 min), train+track (20 min), deploy endpoint (30 min) | B2a, B2b, B3 | Prerequisites listed on the slide. |
| P3.25 | Part 3 in three sentences | recap | 3 takeaways | - | Bridge to Part 4: now put an agent on top. |

## Part 4 — Foundry and the data agent on reconciled logs (18 slides, 75 min)

| id | Headline | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| P4.0 | Part 4: Ask the data, in plain language | section | Part number, 75 min | - | We now have clean gold tables and risk scores. |
| P4.1 | From dashboards to conversations | callout | Before: query, export, pivot. After: ask, see the SQL, check the answer | - | Keep it grounded: it is a query assistant, not an oracle. |
| P4.2 | Three ways to put an agent on your data | compare | Fabric data agent / Foundry agent with tools / Copilot on a semantic model: when to use which | FS-foundry | Decision table. |
| P4.3 | Microsoft Foundry in one picture | arch | Project, models, agents, tools, evaluations, tracing, safety | FS-foundry | Product name and moving parts, verified. |
| P4.4 | The Fabric data agent: what it can and cannot do | cards | Up to 5 sources, read-only, generates T-SQL/DAX/KQL, identity passthrough | FS-foundry, B4 notes | Preview status stated. |
| P4.5 | An agent is only as good as the data below it | arch | Three sources -> reconciled gold tables -> data agent | C§5 | Why Part 3 had to come first. |
| P4.6 | Four levers make a data agent reliable | cards | Agent instructions, data-source instructions, example queries, schema descriptions | B4 | Show real text from the repo. |
| P4.7 | Demo 3a: What did the reconciliation find? | demo | Walk-through notebook; 25 min; the CRIT story (326 of 367 within 24 h) | B4 run-of-show, GT | Narrative before the agent. |
| P4.8 | Demo 3b: Build the data agent live | demo | Steps: create, add sources, select tables, instructions, examples, test, publish; 20 min | B4 rebuild guide | Pre-build a copy as a safety net. |
| P4.9 | Connect it to a Foundry agent | arch | Foundry agent -> Fabric IQ/MCP tool -> data agent -> lakehouse; legacy tool deprecation callout | FS-foundry, B4 | The legacy Fabric tool deprecates 6 Nov 2026. |
| P4.10 | Demo 3c: Questions, from easy to tricky | demo | Warm-up, reconciliation, drill-down, risk, multi-hop, traps | B4 qa-script | 20 min; read the SQL aloud. |
| P4.11 | Three traps the agent must refuse | cards | Fuel cost (no data), operator (no data), forecast (out of scope), delete request (read-only) | agent_eval | Refusal is the right answer. |
| P4.12 | Evaluate an agent like software: 30 questions with known answers | chart | Native chart: question types and difficulty; pass-rate method | agent_eval, B4 | Tolerances, set equality, refusal checks. |
| P4.13 | Guardrails: read-only, grounded, honest | cards | SQL guard, allow-list, row limit, refusal rules, red-team prompts | B4 guardrails | Defense in layers. |
| P4.14 | Security and governance: the agent sees what you see | cards | Identity passthrough, row-level security, labels, audit | FS-foundry | No service principals for the legacy tool; verify current. |
| P4.15 | Tracing and cost: know what the agent did and what it cost | cards | Traces, token use, capacity consumption; what to monitor | FS-foundry, B4 | Flag what is unverified. |
| P4.16 | What is preview, what is changing | timeline | 6 Nov 2026 legacy Fabric tool deprecation; 1 Dec 2026 visual workflow builder retirement; 20 Apr 2027 prompt flow retirement | FS-foundry | Plan for change. |
| P4.17 | Part 4 in three sentences | recap | 3 takeaways | - | Close the loop with the opening story. |

## Closing and appendix (15 slides)

| id | Headline | Layout | Visual / content | Evidence | Speaker note (gist) |
|---|---|---|---|---|---|
| C1 | Five things to remember | recap | The five takeaways | - | Tie back to the outcomes. |
| C2 | Your next 30 days | flow | Week 1 rehearse, week 2 pilot, week 3 pipeline, week 4 review | - | Concrete, small steps. |
| C3 | Resources: documentation and the repository | table | Real links: Learn pages, repo folders | FS | Links verified. |
| C4 | Questions | title | Thank you and Q&A | - | Collect feedback. |
| A0 | Appendix | section | - | - | - |
| A1 | MLflow concept map: open source, Fabric, Azure ML | table | Full table | B1 | Reference. |
| A2 | Fabric runtimes and library versions | table | Runtime 1.3 / 2.0: Spark, Python, MLflow, scikit-learn | FS-fabric-ml | Reference. |
| A3 | Azure ML versions and pins | table | CLI/SDK versions, MLflow pin, retirements | FS-aml | Reference. |
| A4 | How to estimate cost | table | Fabric capacity vs Azure ML compute; what drives the bill; no prices | FS | Method only. |
| A5 | Security and networking options | table | Private link, managed VNet, trusted workspace access, OBO | FS | Reference. |
| A6 | If you know Databricks: a concept mapping | table | Concepts only, not a feature comparison | FS | Handle with care. |
| A7 | Data dictionary: gold and ml tables | table | Tables, grain, key columns | C§7 | Reference. |
| A8 | Reconciliation rules in one page | table | Identity, time, episodes, match window, exceptions | C§6 | Reference. |
| A9 | Troubleshooting: the ten most likely problems | table | Compiled from the builders | B* | Reference. |
| A10 | Glossary | table | 20 terms | - | Reference. |
