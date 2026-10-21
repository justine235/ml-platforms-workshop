# Prep plan: now to Friday 2026-10-23

Revised on Wednesday 2026-10-21, in the afternoon. Building the kit took longer than planned, so the original Tuesday build day is gone. You now have this afternoon, tonight and Thursday. Anything that depends on another person (tenant admin, capacity, quota, a model deployment) is the critical path: ask for it **before** you start building.

**Three rules**
1. **Start the long waits first.** The Azure ML infrastructure, the environment image build and the first endpoint deployment each take 10 minutes or more and run in the background. Start them, then work on Fabric while they build.
2. **Thursday 18:00 is a freeze.** After that you change nothing: no package updates, no portal experiments, no "one last improvement".
3. **Cut early, not late.** The cut list in section 3 says what to drop first if you run out of time.

Nothing in this kit was run in a real Fabric, Azure ML or Foundry tenant. The code was checked locally and statically. Treat every first tenant run as a test, and expect to fix small things (labels, names, IDs).

## 1. Decisions to take first

| # | Decision | Assumed by the kit | Needed by |
|---|---|---|---|
| 1 | Date and length | Fri 2026-10-23, full day 09:00 to 17:00. A half-day deck (about 3.5 hours) also exists | Now |
| 2 | Fabric capacity | A **paid** F SKU. F2 is the smallest; start the ETL on F4 or F8 (a starting point, not a verified sizing: time it in your rehearsal). The 60-day trial runs notebooks and pipelines but **not** Copilot, the data agent or AI functions, so Part 4 needs a paid capacity | Now |
| 3 | Azure subscription for Azure ML | You can create resources (Contributor or Owner) and have quota for `Standard_DS3_v2` in the chosen region | Now |
| 4 | Foundry project and chat model | One project and one chat model deployment. Pick a **Data Zone EU** deployment type if data residency matters; the "Global" types do not guarantee it | Now |
| 5 | GitHub repository for CI/CD | A private repository you control, for Fabric Git sync and for the GitHub Actions + OIDC step on Azure ML | Now |
| 6 | Hands-on or watch-only | **Watch-only.** The rebuild guides are the take-home. Hands-on would need a workspace and a capacity per person | Now |
| 7 | Alert channel for the drift alert | Email. Teams also works if a shared connection exists | Thu morning |
| 8 | Region | Fabric capacity, Azure ML workspace and Foundry project in the same geography (the first three are West Europe, France Central or Sweden Central) | Now |

Names to fill in: tenant admin ______ ; Azure subscription owner ______ ; GitHub org owner ______ ; venue AV contact ______ .

## 2. Start now: things with a lead time

| Item | Why it takes time | Details |
|---|---|---|
| **Fabric tenant settings** (asked of the tenant admin) | One email to an admin can take days | Table below |
| **Paid Fabric capacity**, assigned to your workspace | Needs a subscription and an admin | Decision 2 |
| **Azure ML quota** for `Standard_DS3_v2` (4 vCPUs each) | Quota requests are not instant. Ask for at least 24 vCPUs in the DSv2 family: a cluster of 2 nodes, a blue and a green endpoint instance, and the extra reservation that online endpoints can take (about 20 %). ⚠ planning estimate | `05-demo-azureml-e2e\VERIFY-BEFORE-FRIDAY.md` |
| **Foundry project and model deployment** | Check tokens-per-minute quota in the region, not just the model name | `06-demo-foundry-data-agent\VERIFY-BEFORE-FRIDAY.md` |
| **Access for the presenter** | Contributor or above on the Fabric workspace; contributor on the Azure resource group; write on the GitHub repository | |
| **Entra app or managed identity with a federated credential** for GitHub Actions | Needs someone who can create app registrations | `05-demo-azureml-e2e\rebuild-guide.md` |

Fabric tenant settings to ask for (Admin portal, Tenant settings; in the current portal this is also reachable from OneLake catalog, Govern, Configurations; labels can differ slightly):

| Setting | Needed for |
|---|---|
| Users can create Fabric items | Everything in Fabric |
| Users can synchronize workspace items with their Git repositories (and the GitHub variant) | Fabric Git integration, Part 3A CI/CD |
| ML model endpoints (⚠ PREVIEW) | Only if you show a Fabric model endpoint |
| Users can use Copilot and other features powered by Azure OpenAI | The Fabric data agent (Part 4) |
| Capacities can be designated as Fabric Copilot capacities | The Fabric data agent (Part 4) |
| The two cross-geography AI processing and storage settings | Only if the capacity is outside the EU data boundary and the US |
| The service principal setting for Fabric APIs | Only if CI/CD runs as a service principal |

## 3. Schedule

Effort numbers are planning estimates, not measurements. The blocks add up to about 8 hours tonight and about 9 hours on Thursday when the waiting time overlaps with other work.

### Priorities and the cut list

| Priority | Block | Hands-on time | If you run out of time |
|---|---|---|---|
| 1 | Fabric ETL, ML and MLOps (Part 3A, 55 minutes in the deck) | 5 h | Do not cut it. If the ETL fails, the break-glass notebook restores the tables |
| 2 | Data agent and Foundry agent (Part 4, 51 core minutes) | 3 h | Needs a paid capacity. Without one, show the saved agent copy and screenshots, and say so |
| 3 | Azure ML (Part 3B) | 3 to 4 h, mostly waiting | Show pre-built objects only. Drop the GitHub Actions run first, then the drift schedule, then the green deployment |
| 4 | Local MLflow tour (Demo 1) | 1 h | Laptop only: do it while something else is building |
| 5 | Timed dry run of the short paths | 2 h 20 min | Run the Fabric short paths at least once |
| 6 | Fallback pack: PDF, screenshots, saved outputs | 1 h | Never cut it. It is your insurance |

A demo shown from a pre-run result, with a screenshot behind it, is better than a live demo that fails in front of the room.

### Wed 21, first 30 minutes (before anything else)
- [ ] Take the eight decisions above; send the admin, capacity and quota requests today. If an admin cannot act before Thursday morning, use a tenant where you are the admin.
- [ ] Create the GitHub repository (private) and copy this kit's folders into it, **without** the `truth/` folder (the hidden answer key stays on your laptop). The repository root is the workshop folder, the one that contains `02-demo-data` to `06-demo-foundry-data-agent`: the Azure ML data assets, the Fabric deploy script and the GitHub workflows all assume it.

### Wed 21 evening: build the environments and the Fabric half (about 8 hours of work, the waiting overlaps)
Order matters: start the Azure ML infrastructure and the environment image first, because they build while you work on Fabric.

Azure ML: start this first, it builds in the background (about 1.5 hours hands-on, 3 hours elapsed)
- [ ] Deploy the infrastructure from `05-demo-azureml-e2e\infra` (run `what-if` first; 8 to 12 minutes). It creates the workspace `mlw-fleet-dev`, the cluster `cpu-cluster` (`Standard_DS3_v2`, min nodes 0, max 2), storage, Key Vault, Log Analytics, Application Insights and the container registry. If the region has no quota, switch to France Central or Sweden Central.
- [ ] Register the environment `env-fleet-sklearn` and the three data assets (the reference features, `dim_asset` and the champion metrics) first: `rebuild-guide.md`, step 2. Every job, component, endpoint and schedule fails with "asset not found" until all four exist. The first image build takes 10 to 20 minutes (⚠ planning estimate); keep the `mlflow==2.16.2` pin.
- [ ] Run the local fallback once: `05-demo-azureml-e2e\local-validation\run_local.py`.

Fabric ETL (about 2 hours)
- [ ] Create workspace `ws-fleet-dev`, assign the paid capacity, create the schema-enabled lakehouse `lh_fleet` (`04-demo-fabric-e2e\etl\rebuild-guide.md`).
- [ ] Pin the workspace to Fabric Runtime 1.3 (Spark 3.5, Python 3.11) before you create or import any notebook. The kit was rehearsed on that line; Runtime 2.0 was not. The steps are in `04-demo-fabric-e2e\etl\rebuild-guide.md`.
- [ ] Generate the data locally (about 5 seconds, 95 MB): `python fleet_data_generator.py --out data --truth-dir truth --with-drift` in `02-demo-data`; then upload `data` to `Files/raw`. Details: `02-demo-data\README.md`.
- [ ] Import `nb_00` to `nb_03`, attach `lh_fleet` as the default lakehouse of each, run them once in order, and compare the counts with the table in the "Numbers to sanity-check" section below.

Fabric ML and MLOps (about 3 hours)
- [ ] Upload the folder `04-demo-fabric-e2e\ml-mlops\notebooks` to `lh_fleet`, under `Files/code/notebooks`. The ML notebooks import their shared code from there; without it `nb_04` fails on its first import.
- [ ] Import `nb_04` to `nb_08`, the variable library and `pl_fleet_daily`; attach `lh_fleet`; run the chain once (`04-demo-fabric-e2e\ml-mlops\rebuild-guide.md`). The Git folders of the ETL half and of the ML half merge into one workspace repository (`04-demo-fabric-e2e\README.md`).
- [ ] The pipeline JSON already carries the real logical ID of each notebook, so Git sync should bind its activities by itself. Only two placeholders remain: `__OFFICE365_CONNECTION_ID__` and `__ALERT_TO__`; fill them in for your tenant. Real dev, test and prod values are needed only if you run the CI/CD deploy script (`cicd\parameter.yml`).
- [ ] After the Git import, open the pipeline and check that no notebook activity shows as unresolved. If one does, pick the notebook again by hand.
- [ ] If the ETL did not run: `06-demo-foundry-data-agent\fabric-setup\nb_10_load_gold_break_glass.py` restores the `gold` and `ml` tables only. That is enough to show features, scores and drift, but `nb_04` and `nb_07` need the silver tables to re-run.
- [ ] Run the pipeline once and read the notebook exit payload in the activity output inspector; check that the `IfDriftAlert` expression (it reads `activity('RunDriftMonitor').output.result.exitValue`) sees it, and fix the expression if it does not.
- [ ] Create the Activator rule on `ml.drift_report` (`04-demo-fabric-e2e\ml-mlops\drift-alert-recipe.md`) and send yourself one alert. Keep the pipeline trigger **disabled** until this passes.
- [ ] Time the three notebooks on your capacity. If F4 is too slow, resize before Friday, not on Friday.

Laptop (about 1 hour)
- [ ] Create the local venv for the MLflow tour and run it once (`03-demo-mlflow-tour\README.md`). Keep the `summary.json` it writes: it is the fallback for Demo 1.
- [ ] Install fonts check: the deck uses Trebuchet MS, Segoe UI and Consolas. If you present from another machine, use the PDF.

### Thu 22 morning: Azure ML run-through and the data agent (about 6 hours, the waiting overlaps)
Azure ML (about 3 hours hands-on; the endpoint builds in the background)
- [ ] Run the training pipeline, register the model, run the gate, create the online endpoint with the blue deployment (first deployment 10 to 15 minutes, ⚠ planning estimate), invoke it once.
- [ ] Create the green deployment, mirror a share of traffic to it, then roll back. Run the batch endpoint once.
- [ ] Create the drift schedule only if you plan to show it: it is a ⚠ PREVIEW feature and its schema moves.
- [ ] Run the GitHub Actions workflow once with OIDC; keep the green run page open as the proof.

Foundry and the data agent (about 3 hours)
- [ ] Load the gold and ml tables into `lh_fleet`: run the real ETL if time allows, otherwise `06-demo-foundry-data-agent\fabric-setup\nb_10_load_gold_break_glass.py`.
- [ ] Create the data agent `da_fleet_recon`, add the sources, instructions and example queries; publish it; make a **saved copy** you can fall back to (`06-demo-foundry-data-agent\rebuild-guide.md`).
- [ ] Connect it to a Foundry agent `fleet-recon-agent`; ask every question of `06-demo-foundry-data-agent\qa-script.md`; check the refusals; open the trace.

### Thu 22 afternoon: compressed dry run and fallback pack (until the 18:00 freeze)
Do these in order. The freeze is a hard stop: if time runs short, cut from the bottom of the cut list.
- [ ] Every item in the five `VERIFY-BEFORE-FRIDAY.md` files has an answer: **ok**, **changed the slide** or **dropped**. Write the answer next to the item.
- [ ] Put the real labels and numbers you saw into the slide notes (or tell me and I will update the deck).
- [ ] Run each demo once at the timed speed of its short path: Demo 1 (10 min), Demo 2a ETL (15 min), ML and MLOps (18 min), Demo 2b (about 25 min live), Demo 3 (about 50 min). That is about 2 hours 20 minutes; if you cannot fit them all, time the Fabric paths and Demo 3 and walk through the others once.
- [ ] Talk through the core slides at speaking pace and write the real minute marks into `02-slide-timeline.md`.
- [ ] Build the fallback pack on the laptop: the deck as PDF; one screenshot per demo checkpoint; the saved notebook outputs; the saved agent copy; the offline evaluation reports; the local venv with `run_local.py` for each platform.
- [ ] Re-read the preview and deprecation banners: legacy Foundry Fabric tool (deprecates 2026-11-06), the Foundry visual workflow builder (retires 2026-12-01), prompt flow (retires 2027-04-20). If a date moved, change P4.16 and say so.
- [ ] Check that the capacity is not paused, quotas still hold, the endpoint and the environment image still exist, and the alert channel works.
- [ ] **18:00 freeze.** Close the portals you changed things in. No more package or portal updates. Disable automatic updates on the laptop for the day.

### Fri 23: morning pre-flight (arrive early, 07:30 to 08:45)
- [ ] Power, display adapter, second screen for notes, a phone hotspot as the network fallback, do-not-disturb on, notifications off.
- [ ] Sign in to every portal in a **dedicated browser profile** (Fabric, Azure ML Studio, Azure portal, Foundry, GitHub) so no sign-in or multifactor prompt appears on stage.
- [ ] Set the AML cluster `min nodes` to 1 about 30 minutes before Part 3B, and back to 0 after (a warmed cluster starts in 3 to 5 minutes, ⚠ planning estimate).
- [ ] Open the tabs for the first two parts only (list below), then open the rest at each break.
- [ ] Run the smoke notebook in Fabric (any small cell) to wake the Spark pool; check the default lakehouse is `lh_fleet` on every notebook.
- [ ] Open the deck in presenter view, check the timer, and keep the PDF on a USB stick.

Tabs to have open

| Part | Tabs |
|---|---|
| Part 1 | Local MLflow UI and the tour notebooks; the Fabric experiment item `fleet-failure-7d`; AML Studio, Jobs page |
| Part 3A | `ws-fleet-dev`: `nb_00` to `nb_03` then `nb_04` to `nb_08`; the `lh_fleet` table browser; the experiment and the model item; the `pl_fleet_daily` pipeline run; the Monitor view; the Activator rule |
| Part 3B | AML Studio: pipeline run, model registry, online endpoint (traffic split), batch endpoint; the GitHub Actions run; VS Code on `jobs\` |
| Part 4 | The data agent `da_fleet_recon` and its saved copy; the Foundry project (agent playground, tracing); VS Code on `qa-script.md` |

## 4. Per-demo pre-flight files

| Demo | Read this before rehearsing |
|---|---|
| 1. MLflow tour | `03-demo-mlflow-tour\VERIFY-BEFORE-FRIDAY.md`, `run-of-show.md`, `troubleshooting.md` |
| 2a. Fabric ETL | `04-demo-fabric-e2e\etl\VERIFY-BEFORE-FRIDAY.md`, `run-of-show.md`, `troubleshooting.md` |
| 2a. Fabric ML and MLOps | `04-demo-fabric-e2e\ml-mlops\VERIFY-BEFORE-FRIDAY.md`, `run-of-show.md`, `troubleshooting.md` |
| 2b. Azure ML | `05-demo-azureml-e2e\VERIFY-BEFORE-FRIDAY.md`, `run-of-show.md`, `cost-and-cleanup.md`, `troubleshooting.md` |
| 3. Data agent and Foundry | `06-demo-foundry-data-agent\VERIFY-BEFORE-FRIDAY.md`, `run-of-show.md`, `qa-script.md`, `troubleshooting.md` |

## 5. Numbers to sanity-check live

If a count is off, stop and fix it before you present. Counts must match exactly; model metrics may move by about 0.02 between library versions, and live-scored risk bands may differ slightly.

| Check | Expected |
|---|---|
| Bronze telematics rows | 208,900 |
| `silver.telemetry` rows | 207,691 |
| Duplicates removed / late rows / nulled spikes | 1,209 / 2,066 / 217 |
| Fault episodes | 3,459 |
| Reconciliation exceptions | 211 (91 significant with no work order, 30 of them critical) |
| `ml.asset_day_features` rows | 50,876 (49,028 labelled) |
| `ml.failure_risk_score` rows | 264 |
| Risk bands in Part 4 (frozen file loaded as is) | 9 High, 7 Medium, 248 Low |
| Risk bands after a live scoring run in Part 3 | Close to the above but **not guaranteed identical**: bands depend on library versions. Say "about" out loud |
| `ml.drift_report` | 47 combinations: 4 major, 3 moderate, 40 stable |
| Test PR-AUC | hist. gradient boosting about 0.385; logistic about 0.29; rules about 0.07; prevalence about 0.045 |

## 6. Risks and what to do

| Risk | Likelihood | What to do |
|---|---|---|
| Fabric capacity paused or throttled | Medium | Check it on Friday morning; keep a small smoke notebook; know where to resume it |
| A tenant setting is off, so the data agent or Copilot does not appear | Medium | Ask for the settings now; fallback is the saved agent copy and the screenshot pack |
| First online endpoint deployment is slow | High if not pre-built | Create it on Wednesday and show the existing one; keep the 10 to 15 minute build as a talking point |
| Quota refused or too small | Medium | Request now; fallback region or SKU; last resort `run_local.py` and screenshots |
| A preview feature changed since the slides were written | Medium | Rehearse on Thursday; say "preview" out loud; the three dates on P4.16 are your anchor |
| Foundry model throttled (tokens per minute) | Low to medium | Check the quota; use the offline evaluation reports and the saved answers |
| Venue Wi-Fi blocks a portal | Medium | Phone hotspot; local fallback for Part 1 and Part 3B; PDF and screenshots |
| Sign-in or multifactor prompt on stage | Medium | Dedicated browser profile, sign in at 08:00 |
| Secrets in the repo or on a slide | Low | Use environment variables or a key vault; the `truth/` folder never leaves the laptop |
| You run late | High | The cut order in `01-day-plan.md`, section 4 |

## 7. Cost, and cleanup after the day

- Azure ML: planning estimate **USD 3 to 10** of compute for the day (⚠ UNVERIFIED). It depends on endpoint uptime, environment rebuilds and accidental scale-out. The retail anchor for `Standard_DS3_v2` in West Europe was about USD 0.272 per hour on 2026-10-18; other regions are not verified. Details and cleanup commands: `05-demo-azureml-e2e\cost-and-cleanup.md`.
- Fabric: the capacity bills while it runs, per second with a one-minute minimum; pause it after the workshop. An exact euro amount for F2, F4 or F8 in your region is not verified in this kit.
- Foundry: the model deployment bills per token; delete or scale down the deployment after the day.
- After the workshop: delete the online and batch endpoints, delete the Azure ML resource group, pause the Fabric capacity, remove the Foundry deployment, and archive the GitHub repository. Export anything you want to keep first.
