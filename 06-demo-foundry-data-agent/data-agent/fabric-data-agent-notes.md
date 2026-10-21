# Fabric data-agent notes

## What the platform can do today

- A Fabric data agent can answer natural-language questions over selected Fabric data sources and generate SQL on the user's behalf. Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- A published Fabric data agent can be exposed as an **MCP server**, and the published endpoint exposes a **single MCP tool**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
- The Foundry-side Fabric IQ integration is the current preview path for consuming a published Fabric data agent from Foundry. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq

## Verified limits and prerequisites

- Capacity/license prerequisite: **paid F2 or higher** Fabric capacity, or **Power BI Premium P1 or higher with Fabric enabled**. Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- A data agent supports **up to 5 data sources**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- Source types documented in current Learn pages include **lakehouse, warehouse, semantic model, KQL database/Eventhouse-family source, mirrored database, ontology, Graph, and Azure AI Search index** depending on feature path. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources
- Topics support up to **1,000,000 characters**. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configurations
- REST create-item `description` is limited to **256 characters**. Source: https://learn.microsoft.com/en-us/rest/api/fabric/dataagent/items/create-data-agent

## Security and identity

- Fabric data agents are **read-only analytical experiences**; operational writes are not their job. Source: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- The MCP endpoint uses Fabric authentication and the documented audience is `https://api.fabric.microsoft.com/.default`. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-mcp-server
- The Foundry preview article describes identity passthrough and Fabric-side observability for the published agent. Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq

## What is still moving

- **Fabric IQ in Foundry is preview.** Source: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- The Python package **`fabric-data-agent-sdk`** is preview/alpha and currently awkward to combine with the `azure-ai-projects==2.9.0` stack used here. Source: https://learn.microsoft.com/en-us/fabric/data-science/fabric-data-agent-sdk
- **UNVERIFIED:** the exact current UI character limits for agent instructions, data-source instructions, and data-source description were not clearly stated in the fetched Learn pages; confirm them in the live Fabric UI before Friday.
