# Slide index, W1 edition

| # | id | min | core | headline |
|---|---|---|---|---|
| 1 | O1 | 2 | core | From notebook to production: ML platforms on Microsoft |
| 2 | O2 | 3 | core | Today in four parts, with three demos you can rebuild |
| 3 | O2b | 2 | core | What we heard from you |
| 4 | P1.0 | 1 | core | Part 1: Understanding the ML platforms at Microsoft |
| 5 | P1.1 | 5 | core | Three platforms exist because they start from different work |
| 6 | P1.2 | 3 | optional | Fabric is a data platform that also does machine learning |
| 7 | P1.3 | 3 | optional | Azure Machine Learning is an ML platform that connects to your data |
| 8 | P1.4 | 6 | core | Each platform is strong in a different place |
| 9 | P1.5 | 4 | optional | Compute and cost behave differently because the bill is attached to different things |
| 10 | P1.7 | 4 | optional | Fabric and Azure ML side by side |
| 11 | P1.18 | 3 | optional | The hybrid pattern we will build today keeps Fabric close to data and AML close to serving |
| 12 | P1.17 | 3 | optional | How to choose: four questions usually point to Fabric, Azure ML, or both |
| 13 | P1.8 | 1 | core | MLflow is the common language of both platforms |
| 14 | P1.9 | 5 | core | MLflow keeps the same object model even when the platform wrapper changes  (hidden) |
| 15 | P1.10 | 4 | core | Tracking looks the same in both platforms, but the tracking URI lives in a different place |
| 16 | P1.14 | 3 | core | The same training script runs on a laptop, in Fabric, and in an Azure ML job |
| 17 | P1.15 | 25 | optional | Demo 1: one script and two platforms |
| 18 | P1.19 | 5 | core | Part 1: open talk |
| 19 | P2.0 | 1 | core | Part 2: MLOps from notebook to reliable product |
| 20 | P2.21 | 2.5 | core | Most ML projects stall before they reach production |
| 21 | P2.22 | 4 | core | The ML lifecycle is a loop, and retraining is where manual work piles up |
| 22 | P2.23 | 3 | core | Four continuous practices lead to six capabilities |
| 23 | P2.24 | 3 | core | Version everything that changes: code, data, models and experiments |
| 24 | P2.25 | 3 | optional | Reproducible means the same inputs give the same model and outputs |
| 25 | P2.17 | 3 | optional | When to retrain: schedule, trigger or both |
| 26 | P2.31 | 4 | optional | Data drift: the inputs change before the model notices |
| 27 | P2.32 | 3 | optional | Model drift is what the business feels: performance decays |
| 28 | P2.33 | 4 | optional | Monitoring has three layers: does it run, is the data normal, is the model right |
| 29 | P2.10 | 4 | core | A model is only good compared to a baseline |
| 30 | P2.26 | 4 | core | Evaluate every candidate, then promote automatically |
| 31 | P2.34 | 3 | optional | Validate the data first, then decide whether the pipeline continues |
| 32 | P2.35 | 3 | optional | Responsible AI needs MLOps: every model decision must be explainable and traceable |
| 33 | P2.36 | 4 | optional | One flow: CI builds, CT trains, CD ships and watches |
| 34 | P2.4 | 4 | core | MLOps maturity: five levels from manual to automated |
| 35 | P2.19 | 5 | core | Part 2: open talk |
| 36 | P3.0 | 1 | core | Part 3: MLOps in Fabric and AML |
| 37 | P3.31 | 4 | optional | Architecture A: Fabric for data, Azure ML for the models |
| 38 | P3.32 | 4 | optional | Architecture B: everything in Fabric, with known gaps |
| 39 | P3.33 | 4 | optional | Pillars 1 of 2: build and release |
| 40 | P3.34 | 4 | optional | Pillars 2 of 2: run and improve |
| 41 | P3.41 | 3 | optional | Continuous training: the same loop, two ways to run it |
| 42 | P3.42 | 3 | optional | Model drift: you need labels, so plan the join |
| 43 | P3.43 | 3 | optional | Data drift: compare today's inputs with the training baseline |
| 44 | P3.44 | 3 | optional | A/B testing: Azure ML splits traffic, in Fabric you design the comparison |
| 45 | P3.45 | 4 | optional | Dev, test, prod: you either promote the code or promote the model |
| 46 | P3.46 | 3 | optional | Code-centric view: one workspace or two? |
| 47 | P3.47 | 3 | optional | Model-centric view: train once, then promote the model, never retrain in prod |
| 48 | P3.4 | 3 | core | Demo 2a: Fabric end to end |
| 49 | P3.1 | 3 | core | What we will build: files to a scored, monitored model |
| 50 | P3.15 | 4 | optional | Demo 2b: Azure ML end to end in 45 minutes |
| 51 | P3.18 | 9 | optional | Deploy: a managed online endpoint with blue and green |
| 52 | P3.21 | 4 | optional | The bridge: Fabric ETL feeds Azure ML, scores come back |
| 53 | P3.19 | 5 | core | Part 3: open talk |
| 54 | P3.48 | 5 | optional | Lab: rebuild one piece of the pipeline on your own use case |
| 55 | P4.0 | 1 | core | Part 4: Ask the data, in plain language |
| 56 | P4.7 | 15 | core | Demo 3a: the reconciliation story makes the later agent answers credible |
| 57 | P4.8 | 20 | core | Demo 3b: build the Fabric data agent live, but keep a published safety copy |
| 58 | P4.9 | 2 | optional | Foundry should call the published data agent through Fabric IQ or MCP, not the aging legacy path |
| 59 | P4.10 | 15 | core | Demo 3c: run a question ladder from warm-up counts to trap refusals |
| 60 | P4.11 | 1.5 | optional | A safe analytical agent refuses missing facts, future forecasts, and write actions |
| 61 | P4.12 | 2 | optional | The 30-question evaluation checks both analytical accuracy and refusal behavior |
| 62 | P4.13 | 2 | optional | Guardrails work best in layers: prompt rules, tool limits, SQL checks, and red-team prompts |
| 63 | P4.14 | 2 | optional | Security stays with the user identity and the source permissions, not with the chat window |
| 64 | P4.15 | 2 | optional | Tracing and cost matter because preview stacks fail in boring ways, not dramatic ones |
| 65 | P4.16 | 1.5 | optional | Three dates matter if you plan new work around this demo path |
| 66 | P4.17 | 0.5 | optional | Part 4 in three sentences |
| 67 | C1 | 3 | core | Five things to remember |
| 68 | C2 | 3 | core | Your next 30 days can stay small and concrete |

## Minutes per part

Talk minutes come from the speaker notes. The windows are those of the day plan: what is left in a window is for the demos, the labs and the questions.

| part | window | talk min | left in the window |
|---|---|---:|---:|
| Opening | 09:00 to 09:20 | 7 | 13 |
| Part 1: Fabric vs Azure ML, MLflow in both | 09:20 to 10:50 | 75 | 15 |
| Part 2: MLOps concepts | 11:05 to 12:20 | 57.5 | 17.5 |
| Part 3: End to end on Fabric, then on Azure ML | 13:20 to 15:15 | 72 | 43 |
| Part 4: Foundry and the data agent | 15:30 to 16:45 | 64.5 | 10.5 |
| Wrap-up | 16:45 to 17:00 | 6 | 9 |
