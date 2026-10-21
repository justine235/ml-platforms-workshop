# Q&A cheat sheet: the questions a room of data scientists and data engineers will ask

How to use it: each answer is short enough to say out loud in 20 to 40 seconds. "Proof" tells you where the fact comes from
(`FS-*` = fact sheet in `fact-sheets/`, verified 2026-10-18; `Learn` = a Microsoft Learn page; `Repo` = something you can show in the demo folders).
Anything marked **⚠** is not settled by the documentation: say so, then check it in the tenant (see `VERIFY-BEFORE-FRIDAY.md`).
No exact prices anywhere: say "use the Azure pricing calculator for your region" and show the method (slide A4).

## 1. Choosing a platform

**Q1. Fabric or Azure ML: which one should we standardize on?**
Neither "or". Fabric is strongest when the work is lake-centric and notebook-centric and sits next to Power BI.
Azure ML is the dedicated ML platform for production MLOps: jobs, pipelines, registries, managed endpoints, monitoring.
Most real teams use both: Fabric does the ETL and features, Azure ML trains and serves at scale, scores come back to OneLake.
Show slide P1.17 (five questions) and P1.18 (hybrid pattern). Proof: FS-fabric-ml §G, FS-aml §F.

**Q2. Is Azure ML being replaced by Fabric or by Foundry?**
No. Microsoft positions Azure ML for training, classical and deep ML, endpoints and MLOps; Foundry for agents, models and GenAI;
Fabric for data plus ML inside the lakehouse. What did end: Azure ML CLI v1 support (2025-09-30) and Python SDK v1 support (2026-06-30); prompt flow retires on 2027-04-20 and is not recommended for new work.
Proof: FS-aml §B1 and §F.

**Q3. What about Databricks? We already use it.**
It is not either/or, and we are not here to rank products. MLflow was created at Databricks, so every MLflow skill in this workshop transfers.
Azure Databricks is a first-party Azure service and it reads and writes OneLake through the ABFS endpoint, with documented Unity Catalog federation
and mirroring in both directions. Use appendix A6 (concept mapping) and compare on your own criteria: where the data lives, who builds, how it is served, governance, skills.
Do not claim feature superiority either way. Proof: Learn "Integrate OneLake with Azure Databricks" (page updated 2026-10-13).

**Q4. Could we just run open-source MLflow ourselves?**
Yes, and the first part of Demo 1 does exactly that (local tracking). What you buy with a platform is identity (Entra ID), networking, governance,
managed compute and managed endpoints. Both Fabric and an Azure ML workspace expose MLflow, so the code barely changes. Proof: Repo `03-demo-mlflow-tour`.

**Q5. Is Fabric "real MLflow" or a wrapper?**
Real MLflow APIs for tracking and model logging; Fabric adds first-class workspace items (experiment, ML model) and a UI on top. Proof: FS-fabric-ml §A.

## 2. MLflow details

**Q6. Which MLflow version should I use?**
Fabric Runtime 2.0 ships mlflow-skinny 2.22.0, Runtime 1.3 ships 2.12.2; Fabric documents MLflow 3 support up to 3.1, but you have to install it explicitly.
Azure ML: pin `mlflow<=2.16.2` with `azureml-mlflow`; MLflow 2.17+ and the 3.x LoggedModel changes are not supported by that plugin.
For code that must run in both places, stay on MLflow 2.x APIs: the Demo 1 compatibility shim shows how.
If someone installs MLflow 3 on a laptop: its scikit-learn flavor saves with `skops` by default, `skops` is not installed with MLflow, and tree-based models need their types marked as trusted when they are loaded. The Demo 1 shim handles this. A model exported under MLflow 2.x still loads under 3.x (checked from 2.12.2 to 3.17.0); the reverse direction was not tested **⚠**.
Proof: FS-fabric-ml §A1, FS-aml §0 and §1, `03-demo-mlflow-tour/validation/matrix.md`.

**Q7. Does the registry have stages or aliases?**
Fabric ML models: the docs emphasize model versions and do not document stages or aliases as a Fabric pattern **⚠** (not verified either way). In the Fabric demo the champion is a row in a small `ml.model_pointer` table, updated by `nb_08_promotion_gate`.
Azure ML: MLflow stages exist only through the MLflow SDK; they are not visible in the studio, CLI or SDK v2, and deployment from a stage is not supported. Aliases are not verified in the Azure ML docs **⚠**.
Open-source MLflow (your laptop, Demo 1): both exist. Aliases are the current pattern; stages are deprecated since MLflow 2.9 but still work. Checked locally with a sqlite registry on 2.12.2, 2.16.2, 2.22.0 and 3.17.0. This says nothing about the managed registries above.
The safe pattern on both sides: a model version number, an explicit pointer you control, and a gate in code.
Proof: FS-fabric-ml §A4 and §A6, FS-aml §A1 and Gotchas 2 and 3, `03-demo-mlflow-tour/slide-facts.md` (#9, #17, #18), `03-demo-mlflow-tour/validation/matrix.md`.

**Q8. Can I move a model between Fabric and Azure ML?**
Move the MLflow model folder (the artifacts), not the registry pointers or run history. Demo 1 has an export script and an import check.
Do not rely on MLflow 3 LoggedModel metadata across the two. Proof: FS-aml §E4, Repo `03-demo-mlflow-tour/portability`.

**Q9. Can I log from my laptop or a CI agent into Fabric?**
Yes, with `synapseml-mlflow` and a tracking URI of the form `sds://api.fabric.microsoft.com/v1/workspaces/<workspaceId>/mlflow`. The same mechanism logs from one Fabric workspace to another. Authentication can use `DefaultAzureCredential`, a device code or a client secret; Microsoft documents it as a code-first pattern.
Proof: FS-fabric-ml §A5. **⚠** rehearse the exact URI in your workspace.

**Q10. Does Fabric autologging really switch itself on?**
Yes, in Data Science notebooks, and a workspace setting ("Automatically track machine learning experiments and models") controls it.
Proof: FS-fabric-ml §A3 and §F4.

**Q11. Why log a model with a signature instead of dumping a pickle?**
Fabric `PREDICT` and ML model endpoints require a usable signature. In Azure ML the MLflow model format is what makes no-code deployment possible: no scoring script and no environment to write (packages come from `conda.yaml`), plus lineage and Responsible AI dashboard compatibility.
Proof: FS-fabric-ml §A6, FS-aml §A5 and Q5.

## 3. MLOps

**Q12. How do we promote a model from dev to test to prod in Fabric?**
Git integration and deployment pipelines move the metadata of ML items, not the trained artifacts or model versions. Microsoft's documented pattern for workspace-scoped registries is to download the artifacts and re-log or re-register them in the target workspace. In practice: promote the code and re-train there,
or train in Azure ML and promote through a registry. Demo 2a shows the pattern; slide P2.14 explains the trade-off. Proof: FS-fabric-ml §A5, §D1, §D2, §D7, Repo `04-demo-fabric-e2e/ml-mlops/cicd/README.md`.

**Q13. Does Fabric monitor model drift for us?**
Not in the official docs reviewed. We build it: a PSI drift report (thresholds 0.10 moderate, 0.25 major) written to a table, then a scheduled check with an alert
(`nb_07_drift_monitor`, slides P2.15 and P2.16, recipe in `04-demo-fabric-e2e/ml-mlops/drift-alert-recipe.md`).
Azure ML has managed model monitoring (data drift, prediction drift, data quality, feature attribution drift, model performance) with alerts through Azure ML and Event Grid. The fact sheet does not state a GA badge **⚠**: check it before you promise it.
Proof: FS-fabric-ml §D8 and Q9, FS-aml §B5.

**Q14. What is a sensible promotion gate?**
Both demos use the same rule (slide P2.11): the challenger must beat the champion by at least +0.01 test PR-AUC, and precision at the top 5 percent must not drop by more than 0.02.
It is code and it is versioned: `src/gate.py` in the Azure ML demo, `nb_08_promotion_gate` in the Fabric demo. In Azure ML the production step also sits behind a GitHub Environments approval (`promote-model.yml`, environment `prod`).
Proof: Repo `05-demo-azureml-e2e/src/gate.py`, `04-demo-fabric-e2e/ml-mlops/notebooks/nb_08_promotion_gate.py`.

**Q15. Batch or online scoring?**
Decide by latency and cost. Our use case (corrective work order within 7 days) is a daily batch; an online endpoint is optional and costs money while instances exist.
Fabric ML endpoints are in preview, with a short list of supported model flavors. Azure ML managed online endpoints are documented for production use, with blue/green rollout, traffic split and mirrored traffic; Microsoft recommends more than 3 instances in production, so a 1-instance demo endpoint is a demo-only setup.
Proof: FS-fabric-ml §B3, FS-aml §C1 and §C2.

**Q16. How do you do CI/CD?**
Azure ML: GitHub Actions with OIDC (no client secret stored, only the tenant, client and subscription ids), YAML jobs, Bicep for the infrastructure and a GitHub Environments approval for prod. Fabric: Git integration plus `fabric-cicd` or deployment pipelines.
Proof: FS-aml §D1 to §D3, FS-fabric-ml §D1 to §D3, Repo `05-demo-azureml-e2e/mlops/github-workflows/` and `04-demo-fabric-e2e/ml-mlops/cicd/`. **⚠** the `fabric-cicd` call in the demo repo is not run against a real workspace yet.

**Q17. Why do you split by time and leave a gap?**
A random split leaks the future into training and the metric lies. We purge 7 days between train and valid, because the label looks 7 days ahead. Proof: contract §8, slide P2.9.

## 4. Security, networking, compliance, EU

**Q18. Does our data stay in the EU?**
Fabric: put the capacity in an EU region (West Europe, North Europe, France Central, Germany West Central, Sweden Central and others show all workloads)
and keep the cross-region AI settings off unless you accept that exception. Foundry: it depends on the deployment type. Global deployments can process anywhere;
Data Zone EU processes in the EU; Standard and Regional types stay in the geography. At rest, data stays in the chosen geography for all types.
Proof: FS-fabric-de-rti §E2 and §E5, FS-foundry §A "Deployment types and residency".

**Q19. How do we lock down the network?**
Fabric: Private Link (inbound only), managed private endpoints (outbound, for Data Engineering and Eventstream), trusted workspace access to firewalled storage (F SKU, GA, not on Trial),
workspace outbound access protection. Foundry Agent Service lists Private VNet support in the EU regions. Private Link alone does not secure outbound traffic. Proof: FS-fabric-de-rti §E3, FS-foundry §A.

**Q20. Do row-level and column-level security still apply to the agent?**
Yes: the data agent queries as the signed-in user (Entra ID) and RLS and CLS continue to apply. Sharing the agent does not grant access to the underlying data.
The legacy Foundry tool uses on-behalf-of identity, so every end user needs access, and service principals are not supported there; direct MCP consumption of a published data agent can use a user or a service principal token. Proof: FS-foundry §C, §D, Q5 and Q6.

**Q21. Can we use customer-managed keys?**
Fabric workspace CMK covers Lakehouse, Notebook, Environment, Pipeline and others (Eventhouse is preview); it does not cover Spark temp, shuffle and cache data, and Trial capacities do not support it.
Proof: FS-fabric-de-rti §E4.

**Q22. Audit, lineage, classification?**
Purview audit logs, sensitivity labels through Purview Information Protection, Purview for scanning, lineage beyond Fabric and DLP. Proof: FS-fabric-de-rti §E4.

**Q23. How do we protect an agent from prompt injection and bad answers?**
Layers: grounded tools with a least-privilege identity; Prompt Shields (user prompt attack detection is on by default, document attack detection is off by default and must be enabled; the models are mostly trained and evaluated on English, so test in French);
an evaluation set that includes unanswerable, out-of-scope and guardrail questions (Demo 3c has 30); tracing; and red teaming with the AI Red Teaming Agent (PyRIT-based; cloud runs are region-limited, France Central and Sweden Central are listed). Proof: FS-foundry §E, Repo `06-demo-foundry-data-agent`.

**Q24. What does the EU AI Act mean for us?**
Not legal advice. AI literacy and the first prohibited practices already apply since 2025-02-02; the 2026 Omnibus moved the high-risk deadlines to 2027-12-02 (Annex III) and 2028-08-02 (Annex I).
An internal maintenance-risk model is usually not the high-risk case, but your legal team decides. Proof: FS-foundry §H.

## 5. Cost and capacity

**Q25. What will this cost?**
Method, not prices. Fabric: one shared capacity (F SKU), billed per second with a one-minute minimum, can be paused; usage is smoothed in 30-second windows.
Azure ML: pay per VM hour; the demo cluster scales to zero (`minNodeCount: 0` in the Bicep); online endpoints bill while instances exist, and some SKUs need 20 percent extra reserved quota. Foundry: model tokens plus tool usage, plus hosting for hosted agents.
Exact euro figures for the workshop tenant are not verified **⚠**: use the pricing calculator. Proof: FS-fabric-ml §F2, FS-aml §C3 and §G, FS-foundry §A.

**Q26. Can we rehearse on a Fabric trial?**
Notebooks, experiments, models and pipelines work on Trial. The data agent, Copilot, AI functions, trusted workspace access and CMK do not: Part 4 needs a paid F2 or higher. Proof: FS-fabric-ml §F1.

**Q27. Why is my Fabric job throttled or queued?**
Everything shares one capacity, and usage is evaluated in 30-second windows. Look at the Fabric Capacity Metrics app. Pausing stops throttling immediately, but the remaining smoothed usage is added to the Azure bill at pause time. Size the capacity for the whole room, not for one demo. Proof: FS-fabric-ml §F2.

**Q28. Which Azure ML quotas bite first?**
Endpoint SKU quota (with the extra reservation) and cluster vCPU quota. Request them early; never create the first online deployment live: plan for roughly 10 to 20 minutes for a first deployment **⚠** (planning estimate, not an official figure). Proof: FS-aml §C3 and §G2.

## 6. Data agent and Foundry

**Q29. Is the Fabric data agent production-ready?**
The data agent itself is a mainstream Fabric capability that needs a paid F2 or higher (or Power BI Premium P1+ with Fabric enabled). Its Python SDK is preview, and some sources are preview (graph, ontology, Azure AI Search). Maximum 5 sources.
There is no official latency number, and language support beyond English is not verified either **⚠**: test your French questions before promising anything.
When a published agent is consumed through MCP, answers may leave Fabric's compliance boundary depending on the client. Proof: FS-foundry §D.

**Q30. I saw that the Foundry tool for the Fabric data agent is deprecated. What do we do?**
The legacy tool (preview) is scheduled for deprecation on 2026-11-06. The preferred path is the Fabric IQ tool (preview): published data agents are picked from the OneLake catalog,
you can attach more than one, and each is exposed as an MCP endpoint. Demo 3 keeps a fallback that calls the data agent directly. Proof: FS-foundry §C.

**Q31. Why not a RAG index over the data instead of a data agent?**
For structured analytical data (SQL, KQL, DAX) a data agent writes and runs real queries, so the answer is computed, not retrieved. For manuals and runbooks use Azure AI Search or a knowledge tool.
They complement each other. Proof: FS-foundry Q7.

**Q32. How do you evaluate an agent?**
A fixed question set with expected answers, tracing, and a repeatable score. Demo 3c has 30 scripted questions (answerable, unanswerable, out of scope, guardrail) checked by an eval harness (`foundry-agent/eval_harness.py`). Validated locally: a reference "oracle" passes 30 of 30 and a naive baseline fails them all, so the checks do bite. A run of the real agent in your tenant is part of the rehearsal **⚠**.
In Foundry you can add built-in evaluators (groundedness, relevance, tool-call accuracy; several agent evaluators are still preview) and a CI run with the `microsoft/ai-agent-evals` GitHub Action. Proof: FS-foundry §E, Repo `06-demo-foundry-data-agent/RESULTS.md`.

## 7. About the demo and the data

**Q33. Is the data real?** No. It is synthetic and deterministic (seed 20261023): the same counts on every run. The model is there to show the pipeline, not to claim a business result.

**Q34. The model is only 0.38 PR-AUC. Is that good?** The prevalence is 0.045 and the simple rule gets 0.068, so 0.38 is a real lift; precision at the top 5 percent is what an operations team would use.
Say it honestly: modest signal, useful ranking. Metrics move by about ±0.02 across library versions; counts do not.

**Q35. Can we rebuild everything ourselves?** Yes: every demo folder has a README, a rebuild guide with expected numbers, a run-of-show, a troubleshooting page and a verify list.

## 8. When you do not know

Say: "The documentation does not settle that. I will check it and send the answer after the workshop." Write it on the parking-lot flipchart and keep the promise.
Never improvise a limit, a price or a roadmap date.
