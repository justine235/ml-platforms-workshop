# Microsoft Foundry agents + Fabric data agent + integration fact sheet (verified as of 2026-10-18)

> Scope: Microsoft Foundry agent platform, Fabric data agent, legacy Foundry Fabric tool, new Fabric IQ integration, evaluation/observability, samples, and workshop-ready gotchas. All claims below are sourced; anything not directly verified is marked **UNVERIFIED**.

## A. Foundry naming, architecture, RBAC, regions, deployment types, pricing

### Naming and platform state

- **Current product name is “Microsoft Foundry”** across current Learn docs, SDK quickstarts, RBAC docs, model docs, and agent docs. Many pages note that **Foundry RBAC roles were recently renamed** from **Azure AI User / Owner / Account Owner / Project Manager** to **Foundry User / Owner / Account Owner / Project Manager**; role IDs and permissions are unchanged. **Status: GA naming, rename rollout in progress.** As of 2026-09-16. Source: https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry
- Current Python quickstarts explicitly say code uses **Azure AI Projects 2.x** and is **incompatible with Azure AI Projects 1.x**; for old flows they point to **Foundry (classic)** docs. That is the clearest official signal that **Projects 2.x + “Foundry projects (new)” is the current path**. **Retirement date for hub-based / classic projects: UNVERIFIED** in the fetched sources. As of 2026-09-09 / 2026-09-03. Sources: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent , https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code
- Current project endpoint form is: `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>`. This is the endpoint used by SDK 2.x and current agent quickstarts. **Status: GA.** Source: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- Current resource model in docs is a **Foundry resource + Foundry projects** model, not the older hub/project wording. The RBAC scopes are **Foundry resource**, **Foundry project**, and optionally **agent** scope for endpoint access. **Status: GA.** Source: https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry

### Minimum RBAC you actually need

| Task | Minimum role | Notes |
|---|---|---|
| Build/test agents in a project | **Foundry User** | Least privilege for devs building/testing agents. |
| Create/manage project connections (for example Fabric IQ connection) | **Foundry Project Manager** | Needed to create connection resources in project scope. |
| Call agent endpoints only | **Foundry Agent Consumer** | Least privilege runtime/consumer role. |
| Create projects / manage Foundry resource broadly | **Foundry Account Owner** or **Foundry Owner** | Higher-privilege admin roles. |
| View quota/usage | **Cognitive Services Usages Reader** at subscription | Separate from Foundry roles. |

- **Foundry User** should be assigned to **both the human user and the project managed identity** on the Foundry resource for a basic working setup. Source: https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry
- **Foundry Agent Consumer** exists specifically for identities that only need to call agents, not build them. Source: https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry
- Publishing to **Microsoft Copilot / Teams** also needs **Azure Bot Service Contributor** (or broader Contributor/Owner) on the Azure resource group because Foundry roles do **not** grant Bot Service write/channel permissions. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot

### Regions and Agent Service availability

- **Foundry Agent Service is GA**; some sub-features remain preview. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions
- The key EU regions relevant to this workshop all support **Responses API = Yes** and **Agents = Yes**: **France Central, Germany West Central, Sweden Central, West Europe**. Voice-based agents are also marked Yes in those regions, and **Private VNet = Yes**. As of 2026-09-07 / updated 2026-10-15. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions
- Tool coverage in those EU regions is broad; in particular **Fabric Data Agent**, **MCP**, **OpenAPI**, **SharePoint**, **Web Search**, **Code Interpreter**, **Azure AI Search**, **Function**, and **Agent2Agent** are all marked available in **France Central, Germany West Central, Sweden Central, West Europe** in the tool-by-region table. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions

### Which Azure-sold models are available in EU regions for agents

For Agent Service, the model must be available in-region and compatible with agents. The region table for **Foundry Models sold by Azure** shows the following **Global Standard** models are available in **France Central, Germany West Central, Sweden Central, West Europe**:

- **GPT-4.1 family**: `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`
- **GPT-4o family**: `gpt-4o` (multiple versions), `gpt-4o-mini`
- **GPT-5 family**: `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5-pro`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.4-pro`, `gpt-5.5`, `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`
- **GPT-6 family already present in catalog**: `gpt-6-astra`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-sol`
- **Reasoning families** also visible in EU table: `o1`, `o3`, `o3-mini`, `o4-mini`

Notes:
- This is **region availability**, not “best model” guidance.
- For long-running Fabric IQ questions, Fabric docs explicitly call out **background mode** with models such as **`gpt-5.4`** or **`gpt-5.5`**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- For demos, the safest default is a mainstream chat/reasoning model already supported by your chosen tool pattern in your region; verify in the Foundry portal catalog before the workshop day.

Source for model-region matrix: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability

### Deployment types and residency

- Current deployment types for serverless API: **Global Standard**, **Global Provisioned**, **Global Batch**, **Data Zone Standard**, **Data Zone Provisioned**, **Data Zone Batch**, **Standard**, **Regional Provisioned**, plus **Developer** for fine-tuned evaluation. Source: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types
- **Global**: inference may be processed in **any Azure region**.
- **Data Zone**: inference is processed only within the named **US / EU / APAC** data zone.
- **Standard / Regional Provisioned**: prompts/responses are processed within the customer-specified **Azure geography**; operational processing can still move between regions **within that geography**.
- At-rest data stays in the designated Azure geography for all types, but **inference-path residency differs** by deployment type.
- Official recommendation for most workloads: **start with Global Standard**; it launches first, is usually lowest price, and has widest availability.

Source: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types

### Quotas and pricing basics

- Agent Service docs emphasize service quotas on files, tools, vector stores, messages, tool registrations, etc.; use the quotas/limits page for the current authoritative values because they change. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions
- Pricing is not a single “agent fee”: expect a blend of **model inference** + **tool usage** + for some scenarios managed hosting/runtime costs (hosted agents). The deployment-types page points to Azure OpenAI pricing for token-level detail. Source: https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types
- Practical workshop takeaway: cost-control is mostly about **model choice**, **tool choice**, **background vs synchronous usage**, **retrieval volume**, and whether you use **hosted agents** or only prompt/ephemeral agents.

## B. Foundry Agent Service: API generations, SDKs, minimal working code, tools, identity, hosted agents, publishing

### Where Microsoft is steering developers

- **Persisted prompt agents** are created and versioned through **Foundry projects / agents v1** APIs and SDKs (`AIProjectClient(...).agents.create_version(...)`). Source: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- **Ephemeral/in-process agents** are now built around the **Responses API**, called on the Foundry project endpoint, using either **OpenAI SDK** or **Microsoft Agent Framework** (`FoundryChatClient`). Microsoft calls the Responses API the **single model and tools entry point for Foundry**. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
- So the 2026 picture is:
  - **Old mental model many people still have**: “Assistants-like threads/runs is the main future API.”
  - **Current reality**: **Responses API** is the preferred unified entry point for ephemeral/in-app agents; persisted prompt agents still exist and are created/managed through the projects/agents API.

### Exact Python package versions verified on PyPI (checked 2026-10-18)

| Package | Latest version seen | Upload time (UTC) |
|---|---:|---|
| `azure-ai-projects` | **2.9.0** | 2026-10-17T03:57:26Z |
| `azure-ai-agents` | **1.1.0** | 2025-08-05T19:02:28Z |
| `openai` | **3.35.1** | 2026-10-18T01:06:36Z |
| `azure-identity` | **1.26.0** | 2026-10-01T14:17:49Z |
| `fabric-data-agent-sdk` | **0.1.33a0** | 2026-10-12T20:37:36Z |
| `azure-ai-evaluation` | **1.18.9** | 2026-10-14T18:22:45Z |

### Minimal working code: create a project client and persisted prompt agent

```python
# Source (adapted): https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

FOUNDRY_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"
FOUNDRY_AGENT_NAME = "fleet-agent"

project = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

agent = project.agents.create_version(
    agent_name=FOUNDRY_AGENT_NAME,
    definition=PromptAgentDefinition(
        model="gpt-5-mini",
        instructions="You are a helpful assistant that answers general questions.",
    ),
)
print(agent.id, agent.name, agent.version)
```

### Minimal working code: ask via Responses API (ephemeral agent pattern)

```python
# Source (adapted): https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

FOUNDRY_PROJECT_ENDPOINT = "https://<resource>.services.ai.azure.com/api/projects/<project>"

project = AIProjectClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)
openai = project.get_openai_client()

response = openai.responses.create(
    model="gpt-5-mini",
    input="What is the size of France in square miles?",
)
print(response.output_text)
```

### Minimal working code: print tool-call trace / citations during a streamed response

```python
# Source (adapted from official sample):
# https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/ai/azure-ai-projects/samples/agents/tools/sample_agent_fabric.py
stream_response = openai_client.responses.create(
    tool_choice="required",
    stream=True,
    input=user_input,
)

for event in stream_response:
    if event.type == "response.output_text.delta":
        print(event.delta, end="")
    elif event.type == "response.output_item.done":
        if event.item.type == "message" and event.item.content[-1].type == "output_text":
            for annotation in event.item.content[-1].annotations:
                if annotation.type == "url_citation":
                    print(f"\nCITATION: {annotation.url}")
    elif event.type == "response.completed":
        print("\nFULL:", event.response.output_text)
```

### Tool catalog: verified status snapshot

> Important: I only mark **Preview** when the cited source explicitly says so. For several tools, the fetched sources prove support/availability but do **not** explicitly stamp GA on the tool page I fetched; those are marked **Supported (GA not explicitly verified here)**.

| Tool / capability | Verified status | Evidence |
|---|---|---|
| Fabric IQ | **Public preview** | Explicitly marked preview in Fabric IQ article and SDK/package descriptions. |
| Microsoft Fabric data agent tool (legacy Foundry tool) | **Preview + scheduled deprecation 2026-11-06** | Explicit preview warning + deprecation banner on tool doc. |
| File Search | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| Code Interpreter | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| MCP | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| OpenAPI | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| Function tool / function calling | **Supported (GA not explicitly verified here)** | Listed in stable SDK and samples. |
| Azure Functions tool | **Supported (GA not explicitly verified here)** | Listed in stable SDK package description. |
| Azure AI Search | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| Bing Grounding | **Supported (GA not explicitly verified here)** | Listed in stable SDK and tool/region matrix. |
| Bing Custom Search | **Preview** | Explicit preview label in stable SDK description. |
| SharePoint | **Preview** | Explicit preview label in stable SDK description. |
| Work IQ | **Preview** | Explicit preview label in stable SDK description. |
| Browser Automation | **Preview** | Explicit preview label in stable SDK description. |
| Computer Use | **Preview** | Explicit preview label in stable SDK description. |
| Agent-to-Agent (A2A) | **Supported (GA not explicitly verified here)** | Listed in stable SDK description and tool/region matrix. |
| Hosted agents | **GA service capability** | Full concept doc published without preview banner. |
| Agent identity / Entra agent identity | **Documented current capability; exact GA/preview label not stated on fetched page** | Use with caution in slides. |

Sources: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions , https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents , https://pypi.org/project/azure-ai-projects/

### Identity and auth model for tools

- Foundry now documents **agent identity** as a specialized **Microsoft Entra ID** identity model for agents. Agent Service can do **attended / delegated (OBO)** and **unattended / application-only** flows for downstream services. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity
- Common downstream audience values documented: `https://storage.azure.com`, `https://logic.azure.com`, `https://cosmos.azure.com`, `https://graph.microsoft.com`, `https://vault.azure.net`. Wrong audience => auth failure even if RBAC is correct. Source: same.
- This matters for tools: some tools are naturally **delegated-user** oriented (Fabric data agent via legacy tool), while others can work application-only if the downstream system and connection model support it.

### Hosted agents, playground, Teams/M365

- **Hosted agents** are Microsoft-managed hosting for your own containerized agent code, with scaling, session state, per-session VM isolation, persistent filesystem, and Responses / Invocations / WebSocket protocol choices. **Status: GA concept doc, not preview.** Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents
- **Visual workflows** in Foundry are **Preview** and the product page explicitly says they are **retiring on 2026-12-01**. Microsoft says: for new workflows, use **Microsoft Agent Framework**. For workshop slides, that means “multi-agent orchestration exists, but the no-code Foundry workflow builder is not the long-term anchor.” Source: https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow
- **Agent playground** remains the standard place to configure and test prompt agents in portal; current Fabric IQ walkthrough uses the **Playground** tab with sections **Model**, **Instructions**, **Tools**, **Knowledge**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- **Publish to Microsoft Copilot / Teams** is supported from the Foundry portal. Caveats: not supported from portal when the project disables public network access; for that you must use REST and enable the Activity route. Publishing also creates/uses **Azure Bot Service** artifacts. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot

## C. Fabric data agent as a Foundry tool

### Legacy path: Microsoft Fabric data agent tool (deprecated soon)

- Official page: **Use the Microsoft Fabric data agent with Foundry agents**. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
- **Status**: **Preview**, and **scheduled for deprecation on 2026-11-06**. This is the most important date for slide builders to know.
- Prereqs:
  - Published Fabric data agent
  - Paid **F2+** or **P1+ with Fabric enabled**
  - Fabric cross-geo AI tenant settings if needed
  - Foundry and Fabric in **same tenant**
  - Fabric data agent and its sources on capacities in the **same region**
  - Foundry users need at least **Foundry User**; also need underlying Fabric permissions
- Portal connection setup uses `workspace_id` and `artifact_id` from the Fabric data agent URL, then creates a **project connection** in Foundry.
- REST connection creation uses ARM API `2025-04-01-preview` with `workspace_id` and `artifact_id` under `credentials.keys`.

### Verified Python class names for the legacy tool

```python
# Source (adapted):
# https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
# and official sample:
# https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/ai/azure-ai-projects/samples/agents/tools/sample_agent_fabric.py
from azure.ai.projects.models import (
    PromptAgentDefinition,
    MicrosoftFabricPreviewTool,
    FabricDataAgentToolParameters,
    ToolProjectConnection,
)

tool = MicrosoftFabricPreviewTool(
    fabric_dataagent_preview=FabricDataAgentToolParameters(
        project_connections=[
            ToolProjectConnection(project_connection_id=FABRIC_PROJECT_CONNECTION_ID)
        ]
    )
)
```

### Legacy auth model and implications

- The legacy integration uses **identity passthrough / On-Behalf-Of**. The Fabric query runs as the **signed-in user**.
- Therefore **every end user** must have access to the Fabric data agent and underlying data sources or the tool call fails.
- The doc is explicit: **service principal authentication isn’t supported for the Fabric data agent** in this legacy tool integration.
- Implication: this path is poor for fully headless daemon apps.

Source: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric

### Typical runtime behavior / trace

- The official sample uses `tool_choice="required"`, streams the response, prints `response.output_text.delta`, and inspects `response.output_item.done` for **URL citations** on the final `output_text`. This is the clearest official trace pattern to reuse in demos. Source: official sample above.

### New path: Fabric IQ tool (preferred)

- Official Fabric doc: **Consume Fabric data agent from Microsoft Foundry via Fabric IQ (preview)**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- What changed versus the old path:
  - Pick published data agents from **OneLake Catalog** by name; no manual workspace/artifact ID lookup in portal.
  - **More than one** data agent can be added to a Foundry agent.
  - Each published data agent is exposed as an **MCP endpoint** / tool.
- Required roles in Foundry for this path:
  - Build/test agent: **Foundry User**
  - Create Fabric IQ connection: **Foundry Project Manager**
- Same-tenant + same signed-in account guidance is explicit.
- For long-running questions, the doc explicitly recommends selecting a model supporting **Background mode**, for example `gpt-5.4` or `gpt-5.5`, then enabling **Background mode** in model parameters.
- Code-based addition uses the **Fabric IQ** tool docs rather than the old Fabric preview tool; the Fabric article points developers to `/azure/foundry/agents/how-to/tools/fabric-iq` for current code samples.

## D. Fabric data agent itself

### Status and prerequisites

- Fabric data agent itself is available as a mainstream Fabric capability; however surrounding APIs/SDKs remain mixed maturity. The **Python SDK is explicitly preview**. Source: https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk
- Capacity/license prerequisite: **paid F2 or higher** Fabric capacity, or **Power BI Premium P1 or higher with Fabric enabled**. Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Must enable **cross-geo processing and cross-geo storing for AI** where required. Source: same.

### Supported sources and limits

- Supported categories and native query modes:
  - **SQL**: Lakehouse, Data Warehouse, SQL Database, Mirrored Databases → **NL2SQL / T-SQL**
  - **Eventhouse KQL database** → **NL2KQL / KQL**
  - **Power BI semantic models** → **NL2DAX / DAX** via XMLA endpoint
  - **Graph model (preview)** → **GQL**
  - **Ontology (preview)** → semantic layer that routes to source-native SQL/KQL/DAX
  - **Azure AI Search index (preview)** → unstructured retrieval with citations
- **Maximum 5 data sources** in any combination.
- SQL schema selection can include tables/views/functions; KQL can include tables/materialized views/functions/shortcuts; semantic model support is mainly shaped through **Prep for AI**.

Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources

### Creation and configuration UX

- Create from Fabric workspace: **+ New Item** → **Fabric data agent**. Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Exact configuration areas called out in docs:
  - **Explorer** (schema/object selection)
  - **Data agent instructions**
  - **Data source instructions**
  - **Data source description**
  - **Data source example queries**
  - **Schema object descriptions (Preview)**
  - **Topics (Preview)** for SQL preview runtime
- Recommended agent-instructions markdown template uses sections: `## Objective`, `## Data sources`, `## Key terminology`, `## Response guidelines`, `## Handling common topics`.
- Recommended data-source-instructions template uses: `## General knowledge`, `## Table descriptions`, `## When asked about`.

Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configurations

### Best-practice prompt patterns to copy into the demo

- Keep selected schema tight; don’t expose irrelevant tables.
- Put business rules, join logic, table grain, fiscal calendar, date logic, authoritative-table guidance in **data source instructions**.
- Use **schema object descriptions** for ambiguous names/codes/units/dates.
- Use **example queries** for join-heavy logic, relative dates, ranking/windowing, and domain-specific calculations.
- For time-based questions, explicitly document whether dates mean submission/completion/fulfillment, timezone assumptions, and fiscal-vs-calendar logic.

Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configuration-best-practices

### Security and sharing behavior

- In-product chat uses Fabric-managed identity flow; you do **not** bring an Azure OpenAI key.
- Data access runs under the user’s **Microsoft Entra ID** identity and their source permissions.
- For **semantic models**, **Read** permission is enough for querying via data agent; **Build** isn’t required for this scenario.
- Sharing the data agent does **not** automatically grant underlying data source permissions.
- Cross-tenant shared OneLake data can be queried through accepted shortcuts; governance remains with the consumer tenant’s policies.

Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent

### Runtime limits / caveats that matter for demos

- A published data agent becomes an **MCP server** exposing **a single MCP tool**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
- MCP client must speak actual MCP over streamable HTTP (`initialize` → `tools/list` → `tools/call`); a generic HTTP client won’t work. Source: same.
- Data agent responses consumed via MCP may leave Fabric’s compliance boundary depending on the client/orchestrator. Source: same.
- Long-running requests can use the MCP **tasks** extension (`tasks/get`, `tasks/cancel`). Source: same.
- The doc set I fetched does **not** give one authoritative latency number; present latency as workload-dependent, especially for multi-source or large scans. **Typical latency: UNVERIFIED**.
- Supported languages for NL experience were **not explicitly verified** in fetched sources; don’t overclaim multilingual parity. **Language support beyond English: UNVERIFIED**.

### SDK and API usage

- SDK package: **`fabric-data-agent-sdk`**. **Status: preview / alpha package.** Source: https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk and PyPI
- The SDK is **management plane**, not the preferred runtime query surface.
- Current runtime guidance is **Responses API / MCP**, not the older Assistants pattern.

#### Minimal management-plane snippet

```python
# Source (adapted): https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk
from fabric.dataagent.client import create_data_agent

agent = create_data_agent(
    data_agent_name="Quickstart data agent",
    workspace_id="<workspace-id>",
)
agent.update_settings(ai_instructions="<your agent instructions>")
agent.add_staging_datasource(
    artifact_name_or_id="<datasource-id>",
    workspace_id_or_name="<workspace-id>",
)
agent.publish_staging(description="Initial publish")
```

#### Minimal MCP runtime snippet

```python
# Source (adapted): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
import asyncio
from azure.identity import AzureCliCredential
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

credential = AzureCliCredential()
workspace_id = "<workspace-id>"
data_agent_id = "<data-agent-id>"
mcp_url = f"https://api.fabric.microsoft.com/v1/mcp/workspaces/{workspace_id}/dataagents/{data_agent_id}/agent"

async def query(question: str):
    token = credential.get_token("https://api.fabric.microsoft.com/.default")
    headers = {"Authorization": f"Bearer {token.token}"}
    async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool = tools.tools[0]
            arg_name = next(iter(tool.inputSchema["properties"]))
            result = await session.call_tool(tool.name, {arg_name: question})
            print("\n".join(block.text for block in result.content if block.type == "text"))

asyncio.run(query("What is total revenue?"))
```

## E. Evaluation, tracing, red teaming, guardrails, CI

### Built-in evaluators relevant to agents

Foundry’s evaluation stack includes agent-specific evaluators in addition to generic RAG/safety ones.

- Agent-specific / tool-use evaluators verified in docs include: **Task Adherence (preview)**, **Task Completion (preview)**, **Intent Resolution (preview)**, **Tool Call Accuracy**, **Tool Selection**, **Tool Input Accuracy**, **Tool Output Utilization**, **Tool Call Success**, **Output Quality (preview)**, **Tool Use Quality (preview)**, **Rubric (preview)**.
- RAG / quality / safety evaluators also include items such as **Groundedness**, **Relevance**, **Indirect Attack**, **Sensitive Data Leakage**, etc.

Source basis: Foundry evaluation docs + package version verified at PyPI: https://pypi.org/project/azure-ai-evaluation/

### Minimal `azure-ai-evaluation` pattern

```python
# Source basis: package docs / Foundry eval docs
from azure.ai.evaluation import evaluate

result = evaluate(
    data="golden.jsonl",
    evaluators={
        # Fill with built-in evaluator configs per current Foundry eval docs
    },
)
print(result)
```

> Use a **JSONL golden dataset** of `input` / expected-or-reference fields plus whatever evaluator-specific mappings your selected evaluator needs. Exact evaluator wiring changes quickly; copy from the current Foundry evaluator docs or `microsoft/ai-agent-evals` sample before coding.

### Tracing / observability

- Responses calls through the **project endpoint** flow into project tracing/monitoring/identity configuration. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
- For Fabric-data-agent-from-Foundry, the Fabric article points to a dedicated observability page to inspect which Fabric sources were queried and timing details. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq

### Continuous eval and red teaming

- **AI Red Teaming Agent** is officially documented in Foundry and uses **PyRIT** + Foundry risk/safety evaluators. It supports agentic risks such as **prohibited actions**, **sensitive data leakage**, and **task adherence** in cloud red-teaming runs. Source: https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent
- Cloud red teaming for agentic risks is region-limited; the article names **France Central** and **Sweden Central** among supported regions. Source: same.

### Guardrails

- **Prompt Shields** are current Microsoft Foundry terminology for prompt-attack / document-attack detection, powered by **Azure AI Content Safety**.
- **User prompt attack detection** is enabled by default in Foundry guardrails; **document attack detection** is off by default and must be enabled.
- Docs warn that performance is best-validated per language; models are primarily trained/evaluated on English. This is highly relevant for a French customer workshop.

Source: https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/content-filter-prompt-shields

### CI/CD pattern

- Official GitHub Action path still exists via **`microsoft/ai-agent-evals`**.
- Key inputs documented in official eval action docs include: `azure-ai-project-endpoint`, `deployment-name`, `data-path`, `agent-ids`, optional `baseline-agent-id`.
- This is the cleanest workshop answer for “what is your AgentOps CI story?”

## F. Foundry knowledge / unstructured side

- For unstructured content, the cleanest Fabric-side story is now **Azure AI Search index as a Fabric data agent source (preview)**; the data agent can retrieve chunks and return answers with citations when URL/file-path fields are present. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- On the Foundry side, Responses on the project endpoint can also expose platform tools like **file search**, **SharePoint**, **WorkIQ**, **Fabric IQ**, etc. The project endpoint is what unlocks project-scoped data/tooling beyond a plain Azure OpenAI endpoint. Source: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
- Workshop recommendation: keep **structured enterprise truth** in Fabric data agents; keep **manuals/runbooks/unstructured SOPs** in Azure AI Search / Foundry knowledge tools, then orchestrate both from one Foundry agent.

## G. Official samples worth basing the demo on

1. **Official legacy Foundry Fabric-tool sample (Python)**
   - Repo/path: `Azure/azure-sdk-for-python/sdk/ai/azure-ai-projects/samples/agents/tools/sample_agent_fabric.py`
   - Why use it: verifies the old tool class names and streaming trace/citation pattern.
2. **Fabric Data Agent SDK samples**
   - Repo/path: `microsoft/fabric-samples/docs-samples/data-science/data-agent-sdk/...`
   - Especially useful:
     - `responses-api/responses-api-notebook.ipynb`
     - `Fabric-DataAgent-Automation-Library-sample.ipynb`
     - `Fabric-DataAgent-Evaluation-sample.ipynb`
     - `Fabric-DataAgent-OpenAI-Client-sample.ipynb`
   - Why use them: they show the post-Assistants world and management-plane/runtime split.
3. **Foundry prompt-agent quickstart**
   - Use for the persisted-agent scaffolding.
4. **Foundry Responses API quickstart**
   - Use when you want the same demo logic in app code without a persisted agent.

### Recommended demo build strategy

- **Do not start from the legacy Fabric tool** unless you specifically want to show the near-deprecated path.
- Preferred 2026 architecture for the workshop demo:
  1. Build/publish one or more **Fabric data agents** over the curated gold tables.
  2. Expose them to Foundry via **Fabric IQ (preview)**.
  3. Use a Foundry prompt agent or ephemeral Responses-based agent to orchestrate Fabric IQ + any unstructured knowledge tool.
  4. Keep a separate code sample slide showing the **legacy MicrosoftFabricPreviewTool** only as migration context.

## H. EU AI Act cheat-sheet (not legal advice, <=150 words)

**Not legal advice.** The base AI Act is **Regulation (EU) 2024/1689**. Initial rules including the **AI system definition**, **AI literacy**, and a **limited set of prohibited practices** started applying on **2025-02-02**. In 2026, the **AI Omnibus** entered into force and pushed the main deadlines for high-risk systems: **Annex III high-risk systems now apply from 2027-12-02**; **Annex I high-risk AI embedded in regulated products now applies from 2028-08-02**. The Omnibus also simplified some SME/SMC obligations and adjusted literacy/governance mechanics, but it did **not** erase the already-applicable early obligations. For enterprise copilots/agents, the practical message is: literacy and prohibited-practice hygiene were already live; the heaviest high-risk compliance clocks were deferred. Sources: European Commission Digital Strategy “First rules … now applicable”, “AI Omnibus enters force”, and EUR-Lex AI Act / Omnibus texts.

## Gotchas & limits

- **Biggest 2026 change**: the old Foundry **Microsoft Fabric data agent tool is being deprecated on 2026-11-06**; use **Fabric IQ** for new work.
- **Projects SDK 2.x / Foundry projects (new)** is the active path; **Projects 1.x / classic docs** are legacy compatibility docs.
- Legacy Fabric tool requires **delegated user/OBO**; **service principals are not supported** there.
- Fabric data agent MCP consumption can use **user or service principal token**, but the client must speak **real MCP**, not ad-hoc REST.
- Data agent source limit is **5** sources.
- For semantic models via data agent, **Read** is enough; **Build** is not required for querying.
- Long-running multi-source questions: turn on **Background mode** for a capable model in Foundry.
- Fabric data agent + sources must stay on capacities in the **same region**.
- Prompt Shields are strongest when validated in the app’s real languages; docs explicitly warn that training/evaluation is primarily on **English**.

## Questions a skeptical data scientist / data engineer would ask

1. **Is Foundry still just “Azure AI Foundry” renamed?**  
   Official docs now use **Microsoft Foundry**; role names were also renamed. Some old names still appear during rollout.

2. **Are persisted agents dead because Responses exists?**  
   No. Persisted prompt agents still exist and are managed through the projects/agents APIs. But **Responses API** is now the preferred unified entry point for ephemeral/in-app agents.

3. **Can I still demo the old Fabric tool?**  
   Yes, but it is **preview** and officially **scheduled for deprecation on 2026-11-06**.

4. **Can one Foundry agent call multiple Fabric data agents now?**  
   Yes—through **Fabric IQ**. That is one of the main reasons to prefer it over the old Fabric tool.

5. **Can I use a service principal for Foundry ↔ Fabric data agent integration?**  
   **Not for the legacy Fabric tool**; it requires delegated user/OBO. For direct Fabric MCP consumption, docs say the token can represent a **user or service principal**.

6. **Will row-level/column-level security still apply?**  
   Yes. The docs explicitly say RLS/CLS continue to apply, especially for semantic models.

7. **Does Fabric data agent replace Azure AI Search for manuals/runbooks?**  
   No. Fabric data agent is strongest for **structured analytical sources**. Unstructured retrieval is either **Azure AI Search as a Fabric source (preview)** or a separate Foundry knowledge tool path.

8. **Do I need Build permission on Power BI semantic models for the demo?**  
   No for data-agent querying; **Read** is sufficient in this scenario.

9. **Can I assume EU data residency just because I deployed in France Central?**  
   Not if you chose **Global** deployment types. Use **Data Zone EU** or geography-scoped types when residency matters.

## Sources

- Microsoft Foundry RBAC (2026-09-16; updated 2026-09-22): https://learn.microsoft.com/en-us/azure/foundry/concepts/rbac-foundry
- Foundry prompt-agent quickstart (2026-09-09; updated 2026-10-15): https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- Foundry Responses API quickstart (2026-07-07; updated 2026-10-15): https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/responses-api
- Foundry SDK quickstart (2026-09-03): https://learn.microsoft.com/en-us/azure/foundry/quickstarts/get-started-code
- Agent Service quotas/regions/tools (2026-09-07; updated 2026-10-15): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions
- Foundry model deployment types (2026-08-06): https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types
- Azure-sold model region availability (2026-09-03): https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability
- Foundry model lifecycle/support policy (2026-07-24): https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements
- Agent identity concepts (2026-08-21; updated 2026-09-24): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-identity
- Hosted agents concept (2026-09-11; updated 2026-09-29): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents
- Workflow builder (Preview; retiring 2026-12-01) (2026-07-31; updated 2026-10-08): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/workflow
- Publish to Microsoft Copilot / Teams (2026-09-23): https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot
- Legacy Fabric tool in Foundry (2026-09-14; updated 2026-10-14): https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric
- Fabric IQ integration from Fabric docs (2026-08-26): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- Create a Fabric data agent (2026-05-20; updated 2026-09-29): https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Add data sources to Fabric data agent (2026-08-31; updated 2026-09-30): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- Data agent configurations (2026-08-31; updated 2026-09-29): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configurations
- Data agent best practices (2026-08-27): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configuration-best-practices
- Fabric data agent MCP server (2026-09-03): https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
- Fabric data agent Python SDK (preview) (2026-06-24; updated 2026-10-14): https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk
- Prompt Shields (2026-09-08; updated 2026-09-18): https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/content-filter-prompt-shields
- AI Red Teaming Agent (2026-08-19): https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent
- Official Azure SDK sample for legacy Fabric tool: https://raw.githubusercontent.com/Azure/azure-sdk-for-python/main/sdk/ai/azure-ai-projects/samples/agents/tools/sample_agent_fabric.py
- Official Fabric samples repo (responses-api notebook path): https://raw.githubusercontent.com/microsoft/fabric-samples/main/docs-samples/data-science/data-agent-sdk/responses-api/responses-api-notebook.ipynb
- PyPI package metadata checked 2026-10-18: https://pypi.org/project/azure-ai-projects/ , https://pypi.org/project/azure-ai-agents/ , https://pypi.org/project/openai/ , https://pypi.org/project/azure-identity/ , https://pypi.org/project/fabric-data-agent-sdk/ , https://pypi.org/project/azure-ai-evaluation/
- EU AI Act base regulation (EUR-Lex): https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- European Commission: first AI Act rules applicable: https://digital-strategy.ec.europa.eu/en/news/first-rules-artificial-intelligence-act-are-now-applicable
- European Commission: AI Omnibus enters force: https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force
- European Commission: AI literacy Q&A: https://digital-strategy.ec.europa.eu/en/faqs/ai-literacy-questions-answers
