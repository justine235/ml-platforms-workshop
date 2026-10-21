# Part 4 facts for slides

## Contract / ground-truth facts (verified locally on 2026-10-19)

- ERP population: **316 assets = 300 Active + 10 Retired + 6 Disposed**. Source: `02-demo-data\scenario-contract.md` §10 and `reference_out\ground_truth.json`.
- Reconciliation exceptions: **211 total**. Source: `02-demo-data\scenario-contract.md` §10 and `reference_out\ground_truth.json`.
- Significant fault episodes: **455 MATCHED + 91 UNMATCHED + 11 PENDING = 557**. Source: `02-demo-data\scenario-contract.md` §10 and `reference_out\ground_truth.json`.
- CRIT fault episodes: **367 MATCHED + 30 UNMATCHED + 2 PENDING = 399**. Source: `02-demo-data\scenario-contract.md` §10 and `reference_out\ground_truth.json`.
- Demo 3a story: **326 of the 367 matched CRIT episodes** got a corrective work order within **24 hours**; **17** took **more than 3 days**. Source: validated locally from `gold.fact_recon_match` + `gold.fact_fault_episode` on 2026-10-19.
- Frozen risk table on **2026-09-30**: **264 assets**, split into **High 9 / Medium 7 / Low 248**. Source: `02-demo-data\scenario-contract.md` §8 and `reference_out\ground_truth.json`.
- Top 5 frozen risk assets: **EQ-02893, EQ-07040, EQ-01714, EQ-01503, EQ-02054**. Source: `02-demo-data\scenario-contract.md` §8 and local DuckDB spot-check Q24 on 2026-10-19.

## Learn-verified platform facts (re-verified on 2026-10-19)

- Fabric data agents require **paid F2 or higher Fabric capacity**, or **Power BI Premium P1 or higher with Fabric enabled**. Learn: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Fabric trial capacity does **not** support **Copilot**, **Data agent**, **AI functions**, or **AI services**. Learn: https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial
- A Fabric data agent supports **up to 5 data sources**. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- Current documented data-source categories are **SQL (lakehouse, warehouse, SQL database, mirrored databases)**, **Eventhouse KQL database**, **Power BI semantic model**, **Graph (PREVIEW)**, **Ontology (PREVIEW)**, and **Azure AI Search index (PREVIEW)**. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- A **published** Fabric data agent becomes an **MCP server** that exposes **a single MCP tool**. The documented URL shape is `https://api.fabric.microsoft.com/v1/mcp/workspaces/{WorkspaceId}/dataagents/{DataAgentId}/agent`. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
- Fabric data-agent tenant settings to confirm live: **Users can use Copilot and other features powered by Azure OpenAI** and **Capacities can be designated as Fabric Copilot capacities**. Extra cross-geo processing/storage switches are required only when the capacity is outside the EU data boundary and the US. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings
- West Europe, France Central, Germany West Central, and Sweden Central all show **all Fabric workloads = Yes** in the current Fabric region table. Learn: https://learn.microsoft.com/en-us/fabric/admin/region-availability
- Foundry Agent Service is **GA**; some sub-features remain preview. The current region matrix shows **Responses API = Yes** and **Agents = Yes** for **France Central, Germany West Central, Sweden Central, and West Europe**. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions
- Foundry project endpoint format is `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>`. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- Persisted prompt agents are created with `AIProjectClient(...).agents.create_version(agent_name=..., definition=PromptAgentDefinition(...))`. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- The Responses API is the recommended unified entry point for **ephemeral** Foundry agents, and `AIProjectClient.get_openai_client()` is the documented Python route to that surface. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api and https://pypi.org/project/azure-ai-projects/
- **Fabric IQ** in Foundry is **PREVIEW** and is the current replacement path for published Fabric data agents in Foundry. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- The legacy Foundry **Microsoft Fabric data agent** tool is **PREVIEW** and **DEPRECATING 2026-11-06**. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
- Foundry workflows / visual workflow builder are **PREVIEW** and retire on **2026-12-01**. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow
- Prompt flow in Foundry / Azure Machine Learning retires on **2027-04-20**. Learn: https://learn.microsoft.com/en-us/azure/machine-learning/prompt-flow/overview-what-is-prompt-flow?view=azureml-api-2
- Latest PyPI versions checked on 2026-10-19: **azure-ai-projects 2.9.0**, **openai 3.35.1**, **fabric-data-agent-sdk 0.1.33a0**. PyPI: https://pypi.org/project/azure-ai-projects/ , https://pypi.org/project/openai/ , https://pypi.org/project/fabric-data-agent-sdk/

## Still unverified in Learn or only confirmable in a live tenant

- **UNVERIFIED:** exact current UI character limits for **Data agent instructions**, **Data source instructions**, **Data source description**, and the practical example-query upload limit are not clearly stated in the current Learn pages; verify in the live Fabric UI and keep the exact number off the slides until checked.
- **UNVERIFIED:** exact portal labels and placement for Fabric IQ connection setup can shift with preview updates; rehearse in the live tenant.
- **UNVERIFIED:** the exact Foundry Application Insights / trace surfacing path should be checked in the target project before Friday.
