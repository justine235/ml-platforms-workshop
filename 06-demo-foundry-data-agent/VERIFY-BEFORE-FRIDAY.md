# VERIFY-BEFORE-FRIDAY

Be strict here: this stack mixes GA services with preview integration paths.

## Must verify in the live tenant

1. **Fabric UI field limits** for:
   - Data agent instructions
   - Data source instructions
   - Data source description
   - Example-query import or paste size
2. **Tenant settings and exact labels** for:
   - **Users can use Copilot and other features powered by Azure OpenAI**
   - **Capacities can be designated as Fabric Copilot capacities**
   - The two cross-geo processing/storage settings if the capacity is outside the EU data boundary and the US
3. **Fabric IQ / OneLake Catalog** path in Foundry:
   - exact tool label in the current portal
   - whether the published data agent still appears exactly as rehearsed
4. **Published MCP details** in Fabric:
   - exact MCP tool name
   - exact settings-tab labels
   - whether the downloaded `mcp.json` still matches the rehearsal client config
5. **Legacy Foundry Fabric tool**:
   - preview banner still present
   - deprecation date still shown as **2026-11-06**
6. **Foundry trace surfacing**:
   - exact Application Insights / tracing path in the chosen project
   - whether content recording defaults changed
7. **Regional reality check**:
   - the chosen Fabric capacity region and the workspace/data-source region are still aligned
   - the chosen Foundry region still exposes the planned model and required agent features
8. **Notebook behaviour in Fabric** (`nb_10_load_gold_break_glass`, `nb_11_recon_walkthrough`; both were validated only on a local Spark + Delta session, never in Fabric; see `RESULTS.md`):
   - which Spark runtime the workshop workspace uses: the local session was close to Runtime 1.3 (Spark 3.5.6 vs 3.5, Delta 3.2.1 vs 3.2, Python 3.11). Per Learn (checked 2026-10-21) Runtime 1.3 is in the end-of-support-announced stage and Runtime 2.0 (Spark 4.1, Delta 4.2, Python 3.13) is the GA runtime. The notebooks were **not** run on Runtime 2.0 (**UNVERIFIED**): rehearse on the runtime the workspace will actually use
   - `lh_fleet` attached as the **default lakehouse** (schema-enabled) is enough for the relative `Files/reference_out` path and for `saveAsTable("gold.<table>")`, and the session was restarted after attaching it
   - how long after the CSV upload the first read can fail with "path not found" (file-listing cache); the "about 2 minutes" written in the notebook is **UNVERIFIED**
   - the lakehouse SQL analytics endpoint lists the new `gold.*` and `ml.*` tables, and after how long, before the data-agent source is added (**UNVERIFIED**)
   - `saveAsTable` with `mode("overwrite")` and `overwriteSchema` works as is on the Fabric runtime (the local session needed a harness-only Spark setting for it; the Fabric runtime is expected not to need it, **UNVERIFIED**)
   - `nb_10` prints the 11 contract row counts and `nb_11` reaches its final assertions without error

## Known unverified or environment-specific items

- `fabric-data-agent-sdk` still does not fit cleanly into the same venv as `azure-ai-projects==2.9.0` because of the `openai` major-version split.
- `AIProjectClient.from_connection_string` is **not** present in the installed `azure-ai-projects==2.9.0`; this code uses the verified `AIProjectClient(endpoint=..., credential=...)` constructor instead.
- The live agent invocation path in `foundry-agent\ask.py` remains deliberately dry-run-first because preview runtime wiring differs by tenant/project setup.
- Exact UI character limits for the Fabric instruction fields are still **UNVERIFIED** from Learn alone; verify directly in the current Fabric UI before quoting them out loud.
- Exact Foundry portal button labels for Fabric IQ can shift during preview rollout; rehearse them in the exact tenant on Thursday.
