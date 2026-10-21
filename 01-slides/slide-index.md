# Slide index

| # | id | layout | min | core | headline |
|---|---|---|---|---|---|
| 1 | O1 | title | 2 | yes | From notebook to production: ML platforms on Microsoft |
| 2 | O2 | agenda | 3 | yes | Today in four parts, with three demos you can rebuild |
| 3 | O3 | cards | 5 | yes | By the end of the day you can do five things |
| 4 | O4 | arch | 6 | yes | Three systems disagree about the same machines |
| 5 | O5 | cards | 4 | optional | Everything you see today is rebuildable |
| 6 | P1.0 | section | 1 | yes | Understanding the ML platforms at Microsoft |
| 7 | P1.1 | arch | 5 | yes | Three platforms exist because they start from different work |
| 8 | P1.2 | cards | 3 | optional | Fabric is a data platform that also does machine learning |
| 9 | P1.3 | cards | 3 | optional | Azure Machine Learning is an ML platform that connects to your data |
| 10 | P1.4 | table | 6 | yes | Follow one model through its life: each platform is strong in a different place |
| 11 | P1.5 | compare | 4 | optional | Compute and cost behave differently because the bill is attached to different things |
| 12 | P1.6 | arch | 3 | optional | Data access is the practical bridge: OneLake on one side, datastores on the other |
| 13 | P1.7 | table | 4 | optional | Fabric and Azure ML side by side |
| 14 | P1.8 | section | 1 | yes | MLflow is the common language of both platforms |
| 15 | P1.9 | arch | 5 | yes | MLflow keeps the same object model even when the platform wrapper changes |
| 16 | P1.10 | compare | 4 | yes | Tracking looks the same in both platforms, but the tracking URI lives in a different place |
| 17 | P1.11 | code | 4 | yes | Models: the signature is what makes scoring easy |
| 18 | P1.12 | compare | 5 | yes | The registry is where the two platforms differ most |
| 19 | P1.13 | table | 4 | yes | Versions are the quiet trap |
| 20 | P1.14 | code | 3 | yes | The same training script runs on a laptop, in Fabric, and in an Azure ML job |
| 21 | P1.15 | demo | 25 | optional | Demo 1: the MLflow tour, one script and three platforms |
| 22 | P1.16 | cards | 3 | yes | What travels between platforms and what does not |
| 23 | P1.17 | flow | 3 | optional | How to choose: five questions usually point to Fabric, Azure ML, or both |
| 24 | P1.18 | arch | 3 | optional | The hybrid pattern we will build today keeps Fabric close to data and AML close to serving |
| 25 | P1.19 | recap | 1 | yes | Part 1 in three sentences |
| 26 | P2.0 | section | 1 | yes | Part 2: MLOps from notebook to reliable product |
| 27 | P2.1 | cards | 4 | yes | MLOps is DevOps plus two things that keep changing: data and models |
| 28 | P2.2 | cards | 4 | yes | Why models fail after launch |
| 29 | P2.3 | flow | 3 | yes | The ML lifecycle is a loop, not a line |
| 30 | P2.4 | ladder | 4 | yes | MLOps maturity: five levels from manual to automated |
| 31 | P2.5 | table | 2.5 | optional | What to version: code, data, features, models, environments |
| 32 | P2.6 | code | 2.5 | optional | Reproducible environments start with pins |
| 33 | P2.7 | cards | 3 | yes | Experiment tracking is your lab notebook |
| 34 | P2.8 | table | 4 | yes | Data contracts: check the data before you train on it |
| 35 | P2.9 | custom | 5 | yes | Avoid leakage: split by time and leave a gap |
| 36 | P2.10 | chart | 4 | yes | A model is only good compared to a baseline |
| 37 | P2.11 | flow | 3.5 | optional | Promotion needs a gate, not a feeling |
| 38 | P2.12 | compare | 3 | optional | Deployment patterns: batch, online, shadow, canary |
| 39 | P2.13 | flow | 3.5 | optional | Three pipelines: code, training, release |
| 40 | P2.14 | compare | 3.5 | optional | Dev, test, prod: what you promote |
| 41 | P2.15 | cards | 3.5 | optional | Monitoring: input drift first, accuracy later |
| 42 | P2.16 | chart | 3.5 | optional | Drift in our data: real shift versus expected season |
| 43 | P2.17 | flow | 3 | optional | When to retrain: schedule, trigger or both |
| 44 | P2.18 | cards | 3 | optional | Governance: know what is deployed, who changed it and why |
| 45 | P2.19 | table | 3.5 | optional | Who owns what: roles and hand-offs |
| 46 | P2.20 | cards | 10 | optional | Exercise: where is your team on the ladder? |
| 47 | P3.0 | section | 1 | yes | Part 3: One use case, end to end, twice |
| 48 | P3.1 | arch | 3 | yes | What we will build: files to a scored, monitored model |
| 49 | P3.2 | table | 2 | yes | The same machine, three spellings |
| 50 | P3.3 | table | 2 | yes | What is wrong with the data, on purpose |
| 51 | P3.4 | demo | 3 | yes | Demo 2a: Fabric end to end, about 33 live minutes |
| 52 | P3.5 | cards | 5 | yes | Bronze: land the raw files and keep them as they came |
| 53 | P3.6 | flow | 6 | yes | Silver: resolve identity in four tiers, first hit wins |
| 54 | P3.7 | arch | 3 | yes | Gold: match fault episodes to corrective work orders |
| 55 | P3.8 | chart | 3 | yes | What the reconciliation found |
| 56 | P3.9 | table | 4 | yes | Features: 42 columns known at the end of each day |
| 57 | P3.10 | chart | 6 | yes | Train and track: five models, one leaderboard |
| 58 | P3.11 | code | 4 | yes | Register and score: PREDICT in a notebook |
| 59 | P3.12 | flow | 4 | yes | Orchestrate: one pipeline, one schedule, one alert |
| 60 | P3.13 | chart | 4 | yes | Monitor: drift report and what triggers the alert |
| 61 | P3.14 | arch | 5 | yes | Ship it: Git, variables and deployment per environment |
| 62 | P3.15 | demo | 4 | optional | Demo 2b: Azure ML end to end in 45 minutes |
| 63 | P3.16 | code | 8 | optional | Azure ML: a pipeline in YAML, from data asset to registered model |
| 64 | P3.17 | flow | 7 | optional | Sweep, then gate: promote only a better model |
| 65 | P3.18 | arch | 9 | optional | Deploy: a managed online endpoint with blue and green |
| 66 | P3.19 | flow | 7 | optional | Batch scoring: the nightly job |
| 67 | P3.20 | arch | 10 | optional | CI/CD with OIDC: no secrets in the repository |
| 68 | P3.21 | arch | 4 | optional | The bridge: Fabric ETL feeds Azure ML, scores come back |
| 69 | P3.22 | compare | 4 | optional | The same job done two ways: what felt different |
| 70 | P3.23 | cards | 3 | yes | What was easy, what was painful |
| 71 | P3.24 | cards | 2 | optional | Lab: rebuild one piece in your own tenant |
| 72 | P3.25 | recap | 2 | yes | Part 3 in three sentences |
| 73 | P4.0 | section | 1 | yes | Part 4: Ask the data, in plain language |
| 74 | P4.1 | callout | 1.5 | optional | A good data agent gets users from question to checked SQL faster |
| 75 | P4.2 | table | 2 | optional | Three ways to put an agent on curated data fit different jobs |
| 76 | P4.3 | arch | 2 | optional | Foundry wraps the data tool with models, tracing, and evaluation |
| 77 | P4.4 | cards | 1.5 | optional | The Fabric data agent is useful because it is narrow, read-only, and source-aware |
| 78 | P4.5 | arch | 1.5 | optional | Part 3 already turned three logs into one business grain |
| 79 | P4.6 | cards | 2 | optional | Four levers make the agent more reliable before any LLM tuning starts |
| 80 | P4.7 | demo | 15 | yes | Demo 3a: the reconciliation story makes the later agent answers credible |
| 81 | P4.8 | demo | 20 | yes | Demo 3b: build the Fabric data agent live, but keep a published safety copy |
| 82 | P4.9 | arch | 2 | optional | Foundry should call the published data agent through Fabric IQ or MCP, not the aging legacy path |
| 83 | P4.10 | demo | 15 | yes | Demo 3c: run a question ladder from warm-up counts to trap refusals |
| 84 | P4.11 | cards | 1.5 | optional | A safe analytical agent refuses missing facts, future forecasts, and write actions |
| 85 | P4.12 | chart | 2 | optional | The 30-question evaluation checks both analytical accuracy and refusal behavior |
| 86 | P4.13 | cards | 2 | optional | Guardrails work best in layers: prompt rules, tool limits, SQL checks, and red-team prompts |
| 87 | P4.14 | compare | 2 | optional | Security stays with the user identity and the source permissions, not with the chat window |
| 88 | P4.15 | cards | 2 | optional | Tracing and cost matter because preview stacks fail in boring ways, not dramatic ones |
| 89 | P4.16 | timeline | 1.5 | optional | Three dates matter if you plan new work around this demo path |
| 90 | P4.17 | recap | 0.5 | optional | Part 4 in three sentences |
| 91 | C1 | recap | 3 | yes | Five things to remember |
| 92 | C2 | flow | 3 | yes | Your next 30 days can stay small and concrete |
| 93 | C3 | table | 2 | yes | Resources: documentation and the repository |
| 94 | C4 | custom | 7 | yes | Questions |
| 95 | A0 | custom | 0.5 | yes | Reference slides for follow-up questions |
| 96 | A1 | table | 0.5 | optional | MLflow concept map: open source, Fabric, Azure ML |
| 97 | A2 | table | 0.5 | optional | Fabric runtimes and library versions |
| 98 | A3 | table | 0.5 | optional | Azure ML versions and pins |
| 99 | A4 | table | 0.5 | optional | How to estimate cost |
| 100 | A5 | table | 0.5 | optional | Security and networking options |
| 101 | A6 | table | 0.5 | optional | If you know Databricks: a concept mapping |
| 102 | A7 | table | 0.5 | optional | Data dictionary: gold and ml tables |
| 103 | A8 | table | 0.5 | optional | Reconciliation rules in one page |
| 104 | A9 | table | 0.5 | optional | Troubleshooting: the ten most likely problems |
| 105 | A10 | table | 0.5 | optional | Glossary |

## Minutes per part (core / optional vs agenda)

| part | slides | core min | optional min | agenda |
|---|---|---|---|---|
| O | 5 | 16 | 4 | 20 |
| P1 | 20 | 42 | 48 | 90 |
| P2 | 21 | 32 | 45 | 75 |
| P3 | 26 | 60 | 55 | 115 |
| P4 | 18 | 51 | 24 | 75 |
| C | 4 | 15 | 0 | 15 |
| A | 11 | 0.5 | 5 | - |
