# Day plan: Friday 2026-10-23, 09:00 to 17:00

Audience: data scientists and data engineers. One synthetic scenario runs all day ("Contoso Fleet": telematics logs, work orders and an asset register that disagree about the same machines). Everything on screen is in English.

How to use this folder
- **This file** is the clock (section 1), the storyline (2), the demos and their fallbacks (3), what to cut when you are late (4), the half-day version (5) and the rules for a failing demo (6).
- `02-slide-timeline.md` is the slide-by-slide clock.
- `03-qa-cheatsheet.md` answers the questions you will be asked.
- `04-prep-plan.md` is what to prepare between now and Friday.
- `05-glossary.md` explains the vocabulary in plain English.

## Assumptions to confirm

| Assumption | Why it matters |
|---|---|
| Full day, 09:00 to 17:00, with 90 minutes of breaks | The deck has 390 minutes of content. |
| You present alone and drive every demo | The run-of-shows are written for one driver. |
| A **paid** Fabric capacity (F2 or higher) is available | The 60-day trial runs notebooks and pipelines but not the Fabric data agent, so Part 4 needs a paid capacity. |
| An Azure subscription with Azure Machine Learning quota, and a Foundry project | Part 3B and the Foundry layer of Part 4. |
| Participants watch the demos; the lab slides are optional homework | Nobody needs a tenant on the day. |
| All data is synthetic | Nothing from any real company appears anywhere. |

## 1. The day at a glance

| Time | Min | Block | Slides | What the audience takes away |
|---|---:|---|---|---|
| 09:00 to 09:20 | 20 | Opening | O1 to O5 | One scenario, three disagreeing systems, everything rebuildable |
| 09:20 to 10:50 | 90 | **Part 1**: Fabric vs Azure ML, MLflow in both | P1.0 to P1.19, Demo 1 | Different starting points, same MLflow language, the registry is where they differ |
| 10:50 to 11:05 | 15 | Break | | |
| 11:05 to 12:20 | 75 | **Part 2**: MLOps concepts | P2.0 to P2.20 | Leakage, baselines, gates, drift, who owns what |
| 12:20 to 13:20 | 60 | Lunch | | |
| 13:20 to 14:15 | 55 | **Part 3A**: end to end on Fabric (Demo 2a) | P3.0 to P3.14 | ETL, ML and MLOps in one workspace |
| 14:15 to 15:15 | 60 | **Part 3B**: end to end on Azure ML (Demo 2b) and the bridge | P3.15 to P3.25 | Pipelines, gate, endpoints, CI/CD; how the two fit together |
| 15:15 to 15:30 | 15 | Break | | |
| 15:30 to 16:45 | 75 | **Part 4**: Foundry and the data agent (Demo 3) | P4.0 to P4.17 | Ask the reconciled data in plain language, safely |
| 16:45 to 17:00 | 15 | Wrap-up and questions | C1 to C4 | Five things to remember, the next 30 days |

Minute check: 20 + 90 + 15 + 75 + 60 + 115 + 15 + 75 + 15 = 480.

## 2. The storyline in one page

Say the bridge sentence at the end of each block. It keeps the day one story instead of four lectures.

| Block | Key message | Bridge to the next block |
|---|---|---|
| Opening | Three systems describe the same machines in three spellings. By tonight you can rebuild every demo. | "Before we build anything, which platform do we even build it on?" |
| Part 1 | Fabric starts from the data, Azure ML starts from the model. MLflow is the common language, but the registry and the wrapper around it differ. The model file travels; run history and lineage do not. | "We know the tools. Now what makes a model survive after launch?" |
| Part 2 | MLOps is DevOps plus two things that keep changing: data and models. Split by time, beat a baseline, promote through a gate, watch the inputs. | "Let us build all of that once, for real, on two platforms." |
| Part 3A | On Fabric the lakehouse is the center: bronze, silver, gold, features, model, scores, drift, all next to the data. | "Same use case again, now where production ML operations is the center." |
| Part 3B | On Azure ML the center is the model lifecycle: jobs, registry, gate, blue/green endpoints, GitHub Actions with OIDC. | "Clean, reconciled data is also the best food for an agent." |
| Part 4 | A data agent is useful because it is narrow, read-only and source-aware. Foundry adds the model, tracing and evaluation. Refusing is part of the answer. | "Five things to take home." |
| Wrap-up | Five things to remember; keep the next 30 days small and concrete. | Questions. |

## 3. The demos

Every demo has a **short path** and a **pre-baked fallback**. Use the short path on the day: the full paths are for rehearsal and for people who rebuild.

| Demo | Where | Slides | Live length (full / short) | Folder | Pre-bake before the day | If it fails |
|---|---|---|---|---|---|---|
| **1. MLflow tour** (laptop, Fabric, Azure ML) | Part 1, after P1.14 | P1.15 | 25 / 10 min | `03-demo-mlflow-tour` | Local run done once and its `summary.json` kept; one Fabric experiment run; one Azure ML job run | Show the saved `summary.json`; open the experiment item; read the AML YAML |
| **2a. Fabric ETL** (bronze, silver, gold) | Part 3A, from P3.4 | P3.5 to P3.8 | 25 / 15 min | `04-demo-fabric-e2e\etl` | All four ETL notebooks run once, `Files/raw` landed, `lh_fleet` filled | Open the pre-run notebook outputs and table previews in the same workspace |
| **2a. Fabric ML + MLOps** (features, train, score, drift, gate) | Part 3A, after the ETL part | P3.9 to P3.14 | 30 / 18 min | `04-demo-fabric-e2e\ml-mlops` | Features table, one experiment with all runs, score table, drift table, gate notebook open | Open the tables and the run comparison; read the gate rule without running it |
| **2b. Azure ML end to end** | Part 3B | P3.15 to P3.20 | 45 min (slides and demo together) | `05-demo-azureml-e2e` | Environment image built (10 to 20 min, planning estimate), endpoint with the blue deployment created (10 to 15 min), cluster warmed (3 to 5 min), one training run, one invoke and one batch run done | Open the last successful pipeline run, the registered model version and the endpoint state; or run `local-validation\run_local.py` |
| **3. Data agent + Foundry** | Part 4 | P4.7 (3a, 15 min), P4.8 (3b, 20 min), P4.10 (3c, 15 min) | 50 min in total | `06-demo-foundry-data-agent` | Gold and ml tables loaded; a saved copy of `da_fleet_recon`; Foundry project and chat model ready; offline evaluation reports | Use the saved agent copy; ask the questions from `qa-script.md`; load tables with `nb_10_load_gold_break_glass` |

**Part 3A is tighter than the two run-of-shows.** The Fabric block is 55 minutes: about 8 minutes of intro slides plus the demos. The full live paths add up to 55 minutes of clicking on their own (25 + 30), so use the short paths (15 + 18 = 33 minutes) and let pre-run output carry the rest. Each Part 3A slide has an `IF SHORT ON TIME:` line in its notes that says what to cut.

## 4. If you are late: the cut order

Each slide's notes start with `[ID · ~N min · CORE or OPTIONAL]`. Cut from the top of this list. The savings are minutes of the **full-day** plan.

| Cut | What | Saves | What to say |
|---:|---|---:|---|
| 1 | Exercise P2.20 ("where is your team on the ladder?") | 10 | "Take this slide back to your team; we will not do it live." |
| 2 | Demo 1 from 25 to 10 minutes (use the short version) | 15 | "I will show the differences; the full tour is in the repository." |
| 3 | P1.5, P1.6, P1.7 (cost, data access, side by side) | 11 | "Reference slides: they stay in the deck you receive." |
| 4 | P1.17 (how to choose) | 3 | Fold it into the Part 1 recap. |
| 5 | P2.18, P2.19 (governance, roles) | 6.5 | One sentence: know what is deployed, who changed it and why. |
| 6 | P2.5, P2.6 (what to version, pins) | 5 | One sentence each. |
| 7 | P3.19 (batch scoring) and P3.24 (lab) | 9 | Show the pre-run batch result only. |
| 8 | P4.12 to P4.15 (evaluation, guardrails, security, tracing) | 8 | Keep the one-sentence version of each. |

Never cut: P1.12 (registry), P2.9 (leakage gap), P2.10 (baseline), P3.23 (what was easy and what was painful), P4.11 (refusals), P4.16 (the three dates) and every recap slide. Keep the 15:15 break: Part 4 needs people awake.

Clock checkpoints (if you are behind here, start cutting): about 10:15 you start Demo 1 (P1.15); 12:20 end of Part 2; 14:15 end of Part 3A; 15:15 end of Part 3B. The exact slide for each minute is in `02-slide-timeline.md`.

## 5. The half-day version (core slides only)

Open `ml-platforms-workshop-halfday.pptx`: it keeps only the core slides of each part.

| Block | Min |
|---|---:|
| Opening | 16 |
| Part 1 (core) | 42 |
| Part 2 (core) | 32 |
| Part 3 (Fabric only, plus the two Part 3B wrap slides) | 60 |
| Part 4 (core: the three demos) | 51 |
| Wrap-up | 15 |
| **Total** | **216** |

That is 3 hours 36 minutes plus one break of about 15 minutes. Azure ML is covered by the comparison slides of Parts 1 and 3B only; say so at the start.

## 6. When a demo fails

1. Say it once, calmly: "This is exactly why we pre-ran it."
2. Switch to the pre-run output **in the same tool** (the saved notebook output, the existing table, the last successful run). It is more convincing than a screenshot.
3. Never debug live for more than a minute. Park it for the break and point at the troubleshooting file of that demo.
4. Keep the clock: the minutes on the demo slide are the budget, failure or not.
5. Say "preview" out loud every time you show a preview feature, and mention the dates on P4.16 (2026-11-06, 2026-12-01, 2027-04-20).
6. Part 4 has a second safety net: a saved copy of the data agent, and a direct call to the data agent if the Foundry tool path misbehaves.
