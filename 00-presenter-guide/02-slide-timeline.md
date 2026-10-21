# Slide-by-slide clock

Generated from `01-slides/slide-index.md` by `01-slides/make_timeline.py`. Do not edit by hand: rebuild the deck, then run the script again.

How to read it
- **Start** is the clock time if every slide takes its planned minutes. Parts have fixed start times, so a slide that overruns eats the next one, not the break.
- **Core** slides are the half-day path. **Optional** slides are the first to cut (`01-day-plan.md`, section 4).
- **Demo** slides are bold. Their minutes are the budget in the full-day plan; the short paths are in `01-day-plan.md`, section 3.

## Opening

Starts 09:00, ends 09:20 (budget 20 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 09:00 | O1 | 2 | core | From notebook to production: ML platforms on Microsoft |
| 09:02 | O2 | 3 | core | Today in four parts, with three demos you can rebuild |
| 09:05 | O3 | 5 | core | By the end of the day you can do five things |
| 09:10 | O4 | 6 | core | Three systems disagree about the same machines |
| 09:16 | O5 | 4 | optional | Everything you see today is rebuildable |

5 slides, 20 min in total, 16 min core, 4 min optional.

## Part 1: Fabric vs Azure ML, MLflow in both

Starts 09:20, ends 10:50 (budget 90 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 09:20 | P1.0 | 1 | core | Understanding the ML platforms at Microsoft |
| 09:21 | P1.1 | 5 | core | Three platforms exist because they start from different work |
| 09:26 | P1.2 | 3 | optional | Fabric is a data platform that also does machine learning |
| 09:29 | P1.3 | 3 | optional | Azure Machine Learning is an ML platform that connects to your data |
| 09:32 | P1.4 | 6 | core | Follow one model through its life: each platform is strong in a different place |
| 09:38 | P1.5 | 4 | optional | Compute and cost behave differently because the bill is attached to different things |
| 09:42 | P1.6 | 3 | optional | Data access is the practical bridge: OneLake on one side, datastores on the other |
| 09:45 | P1.7 | 4 | optional | Fabric and Azure ML side by side |
| 09:49 | P1.8 | 1 | core | MLflow is the common language of both platforms |
| 09:50 | P1.9 | 5 | core | MLflow keeps the same object model even when the platform wrapper changes |
| 09:55 | P1.10 | 4 | core | Tracking looks the same in both platforms, but the tracking URI lives in a different place |
| 09:59 | P1.11 | 4 | core | Models: the signature is what makes scoring easy |
| 10:03 | P1.12 | 5 | core | The registry is where the two platforms differ most |
| 10:08 | P1.13 | 4 | core | Versions are the quiet trap |
| 10:12 | P1.14 | 3 | core | The same training script runs on a laptop, in Fabric, and in an Azure ML job |
| 10:15 | **P1.15** | 25 | optional | Demo 1: the MLflow tour, one script and three platforms |
| 10:40 | P1.16 | 3 | core | What travels between platforms and what does not |
| 10:43 | P1.17 | 3 | optional | How to choose: five questions usually point to Fabric, Azure ML, or both |
| 10:46 | P1.18 | 3 | optional | The hybrid pattern we will build today keeps Fabric close to data and AML close to serving |
| 10:49 | P1.19 | 1 | core | Part 1 in three sentences |

20 slides, 90 min in total, 42 min core, 48 min optional.

**10:50: Break (15 min).**

## Part 2: MLOps concepts

Starts 11:05, ends 12:20 (budget 75 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 11:05 | P2.0 | 1 | core | Part 2: MLOps from notebook to reliable product |
| 11:06 | P2.1 | 4 | core | MLOps is DevOps plus two things that keep changing: data and models |
| 11:10 | P2.2 | 4 | core | Why models fail after launch |
| 11:14 | P2.3 | 3 | core | The ML lifecycle is a loop, not a line |
| 11:17 | P2.4 | 4 | core | MLOps maturity: five levels from manual to automated |
| 11:21 | P2.5 | 2.5 | optional | What to version: code, data, features, models, environments |
| 11:24 | P2.6 | 2.5 | optional | Reproducible environments start with pins |
| 11:26 | P2.7 | 3 | core | Experiment tracking is your lab notebook |
| 11:29 | P2.8 | 4 | core | Data contracts: check the data before you train on it |
| 11:33 | P2.9 | 5 | core | Avoid leakage: split by time and leave a gap |
| 11:38 | P2.10 | 4 | core | A model is only good compared to a baseline |
| 11:42 | P2.11 | 3.5 | optional | Promotion needs a gate, not a feeling |
| 11:46 | P2.12 | 3 | optional | Deployment patterns: batch, online, shadow, canary |
| 11:48 | P2.13 | 3.5 | optional | Three pipelines: code, training, release |
| 11:52 | P2.14 | 3.5 | optional | Dev, test, prod: what you promote |
| 11:56 | P2.15 | 3.5 | optional | Monitoring: input drift first, accuracy later |
| 11:59 | P2.16 | 3.5 | optional | Drift in our data: real shift versus expected season |
| 12:02 | P2.17 | 3 | optional | When to retrain: schedule, trigger or both |
| 12:06 | P2.18 | 3 | optional | Governance: know what is deployed, who changed it and why |
| 12:08 | P2.19 | 3.5 | optional | Who owns what: roles and hand-offs |
| 12:12 | P2.20 | 10 | optional | Exercise: where is your team on the ladder? |

21 slides, 77 min in total, 32 min core, 45 min optional.  Over the budget by 2 min: skip or shorten an optional slide to end on time.

**12:20: Lunch (60 min).**

## Part 3: End to end on Fabric, then on Azure ML

Starts 13:20, ends 15:15 (budget 115 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 13:20 | P3.0 | 1 | core | Part 3: One use case, end to end, twice |
| 13:21 | P3.1 | 3 | core | What we will build: files to a scored, monitored model |
| 13:24 | P3.2 | 2 | core | The same machine, three spellings |
| 13:26 | P3.3 | 2 | core | What is wrong with the data, on purpose |
| 13:28 | **P3.4** | 3 | core | Demo 2a: Fabric end to end, about 33 live minutes |
| 13:31 | P3.5 | 5 | core | Bronze: land the raw files and keep them as they came |
| 13:36 | P3.6 | 6 | core | Silver: resolve identity in four tiers, first hit wins |
| 13:42 | P3.7 | 3 | core | Gold: match fault episodes to corrective work orders |
| 13:45 | P3.8 | 3 | core | What the reconciliation found |
| 13:48 | P3.9 | 4 | core | Features: 42 columns known at the end of each day |
| 13:52 | P3.10 | 6 | core | Train and track: five models, one leaderboard |
| 13:58 | P3.11 | 4 | core | Register and score: PREDICT in a notebook |
| 14:02 | P3.12 | 4 | core | Orchestrate: one pipeline, one schedule, one alert |
| 14:06 | P3.13 | 4 | core | Monitor: drift report and what triggers the alert |
| 14:10 | P3.14 | 5 | core | Ship it: Git, variables and deployment per environment |
| | | | | *Azure ML and bridge block starts. Target clock: 14:15* |
| 14:15 | **P3.15** | 4 | optional | Demo 2b: Azure ML end to end in 45 minutes |
| 14:19 | P3.16 | 8 | optional | Azure ML: a pipeline in YAML, from data asset to registered model |
| 14:27 | P3.17 | 7 | optional | Sweep, then gate: promote only a better model |
| 14:34 | P3.18 | 9 | optional | Deploy: a managed online endpoint with blue and green |
| 14:43 | P3.19 | 7 | optional | Batch scoring: the nightly job |
| 14:50 | P3.20 | 10 | optional | CI/CD with OIDC: no secrets in the repository |
| 15:00 | P3.21 | 4 | optional | The bridge: Fabric ETL feeds Azure ML, scores come back |
| 15:04 | P3.22 | 4 | optional | The same job done two ways: what felt different |
| 15:08 | P3.23 | 3 | core | What was easy, what was painful |
| 15:11 | P3.24 | 2 | optional | Lab: rebuild one piece in your own tenant |
| 15:13 | P3.25 | 2 | core | Part 3 in three sentences |

26 slides, 115 min in total, 60 min core, 55 min optional.

**15:15: Break (15 min).**

## Part 4: Foundry and the data agent

Starts 15:30, ends 16:45 (budget 75 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 15:30 | P4.0 | 1 | core | Part 4: Ask the data, in plain language |
| 15:31 | P4.1 | 1.5 | optional | A good data agent gets users from question to checked SQL faster |
| 15:32 | P4.2 | 2 | optional | Three ways to put an agent on curated data fit different jobs |
| 15:34 | P4.3 | 2 | optional | Foundry wraps the data tool with models, tracing, and evaluation |
| 15:36 | P4.4 | 1.5 | optional | The Fabric data agent is useful because it is narrow, read-only, and source-aware |
| 15:38 | P4.5 | 1.5 | optional | Part 3 already turned three logs into one business grain |
| 15:40 | P4.6 | 2 | optional | Four levers make the agent more reliable before any LLM tuning starts |
| 15:42 | **P4.7** | 15 | core | Demo 3a: the reconciliation story makes the later agent answers credible |
| 15:56 | **P4.8** | 20 | core | Demo 3b: build the Fabric data agent live, but keep a published safety copy |
| 16:16 | P4.9 | 2 | optional | Foundry should call the published data agent through Fabric IQ or MCP, not the aging legacy path |
| 16:18 | **P4.10** | 15 | core | Demo 3c: run a question ladder from warm-up counts to trap refusals |
| 16:34 | P4.11 | 1.5 | optional | A safe analytical agent refuses missing facts, future forecasts, and write actions |
| 16:35 | P4.12 | 2 | optional | The 30-question evaluation checks both analytical accuracy and refusal behavior |
| 16:37 | P4.13 | 2 | optional | Guardrails work best in layers: prompt rules, tool limits, SQL checks, and red-team prompts |
| 16:39 | P4.14 | 2 | optional | Security stays with the user identity and the source permissions, not with the chat window |
| 16:41 | P4.15 | 2 | optional | Tracing and cost matter because preview stacks fail in boring ways, not dramatic ones |
| 16:43 | P4.16 | 1.5 | optional | Three dates matter if you plan new work around this demo path |
| 16:44 | P4.17 | 0.5 | optional | Part 4 in three sentences |

18 slides, 75 min in total, 51 min core, 24 min optional.

## Wrap-up

Starts 16:45, ends 17:00 (budget 15 min).

| Start | Slide | Min | Core | What it says |
|---|---|---:|---|---|
| 16:45 | C1 | 3 | core | Five things to remember |
| 16:48 | C2 | 3 | core | Your next 30 days can stay small and concrete |
| 16:51 | C3 | 2 | core | Resources: documentation and the repository |
| 16:53 | C4 | 7 | core | Questions |

4 slides, 15 min in total, 15 min core, 0 min optional.

## Half-day path (core slides only)

| Block | Core slides | Core min |
|---|---:|---:|
| Opening | 4 | 16 |
| Part 1: Fabric vs Azure ML, MLflow in both | 12 | 42 |
| Part 2: MLOps concepts | 9 | 32 |
| Part 3: End to end on Fabric, then on Azure ML | 17 | 60 |
| Part 4: Foundry and the data agent | 4 | 51 |
| Wrap-up | 4 | 15 |
| **Total** | | **216** |

Add one break of about 15 minutes. Use `ml-platforms-workshop-halfday.pptx`.

## Appendix (not on the clock)

Open these only to answer a question.

| Slide | What it says |
|---|---|
| A0 | Reference slides for follow-up questions |
| A1 | MLflow concept map: open source, Fabric, Azure ML |
| A2 | Fabric runtimes and library versions |
| A3 | Azure ML versions and pins |
| A4 | How to estimate cost |
| A5 | Security and networking options |
| A6 | If you know Databricks: a concept mapping |
| A7 | Data dictionary: gold and ml tables |
| A8 | Reconciliation rules in one page |
| A9 | Troubleshooting: the ten most likely problems |
| A10 | Glossary |
