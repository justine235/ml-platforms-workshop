# Part 4 - Microsoft Foundry + Fabric data agent

This folder is the presenter rebuild kit for Part 4 of the workshop: use the reconciled `gold.*` tables and frozen `ml.failure_risk_score` to show (1) what the reconciliation found, (2) how to build a Fabric data agent over those tables, and (3) how to call that agent from Foundry or fall back to the offline harness.

## What is in scope

- **Demo 3a:** reconciliation walk-through on the frozen gold tables
- **Demo 3b:** build the Fabric data agent live in Fabric
- **Demo 3c:** ask scripted questions, including refusal traps
- **Safety net:** offline oracle/naive eval harness (DuckDB over the frozen reference tables, no Fabric needed)

## Architecture

1. `02-demo-data\reference_out\` supplies the frozen `gold.*` and `ml.*` tables.
2. `fabric-setup\nb_10_load_gold_break_glass` reads those CSVs from `Files/reference_out` of the default lakehouse and writes them as Delta tables (`saveAsTable`) into the `gold` and `ml` schemas, then checks the row counts.
3. `fabric-setup\nb_11_recon_walkthrough` is a Spark-only, read-only notebook that tells the reconciliation story on those tables with contract-backed numbers.
4. `data-agent\` holds the exact instructions, descriptions, schema notes, and example queries for the Fabric data agent.
5. `foundry-agent\` holds a dry-run-safe Foundry prompt-agent scaffold plus guardrails, tracing hooks, and the offline evaluation harness.

## Standard vs extended delivery plan

### STANDARD workshop slot inside the 75-minute Part 4 block

- Demo 3a: **15 min**
- Demo 3b: **20 min**
- Demo 3c: **15 min**
- Total live-demo time: **50 min**
- Remaining **25 min**: intro slides, architecture, guardrails/evaluation, recap

### EXTENDED version for a lab or longer slot

- Demo 3a: **25 min**
- Demo 3b: **20 min**
- Demo 3c: **20 min**
- Total live-demo time: **65 min**

See `run-of-show.md` for minute-by-minute standard and extended tables, including what to skip in the standard version.

## Presenter prerequisites

### Fabric

- **Paid Fabric capacity required:** **F2 or higher**, or **Power BI Premium P1 or higher with Fabric enabled**. Learn: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- **Trial limitation:** Fabric trial capacity does **not** support Copilot, Data agent, AI functions, or AI services. Learn: https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial
- **Tenant settings:** enable **Users can use Copilot and other features powered by Azure OpenAI** and **Capacities can be designated as Fabric Copilot capacities**. If the capacity is outside the EU data boundary or the US, also enable the documented cross-geo processing/storage settings. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings
- **Regional note:** choose a region with full Fabric workloads and keep the data agent and its sources on capacities in the same region. West Europe, France Central, Germany West Central, and Sweden Central all show full Fabric workloads. Learn: https://learn.microsoft.com/en-us/fabric/admin/region-availability

### Fabric notebooks (`nb_10`, `nb_11`)

- Upload the `*.csv` and `*.csv.gz` files of `02-demo-data\reference_out\` to the schema-enabled lakehouse `lh_fleet`, folder `Files/reference_out`. Never upload `02-demo-data\truth\` (hidden answer key).
- Attach `lh_fleet` as the **default lakehouse** of both notebooks, then restart the session. The relative path `Files/reference_out` and the table names `gold.*` / `ml.*` resolve against the default lakehouse only.
- Run `nb_10_load_gold_break_glass`, check the printed row counts, then run `nb_11_recon_walkthrough`. No path or setting needs editing.
- If the first read says "path not found" right after the upload, wait about 2 minutes and rerun the cell (file-listing cache; the duration is **UNVERIFIED**).
- A Fabric trial capacity is enough for these two notebooks. The data agent (Demos 3b and 3c) still needs the paid capacity above.
- Expected row counts: `gold.dim_asset` 316, `gold.dim_site` 12, `gold.fact_telemetry_daily` 51,353, `gold.fact_fault_episode` 3,459, `gold.fact_work_order` 2,345, `gold.fact_recon_match` 468, `gold.fact_recon_exception` 211, `gold.agg_recon_monthly` 72, `ml.asset_day_features` 50,876, `ml.failure_risk_score` 264, `ml.drift_report` 47.
- Validation status: both notebooks were run unchanged on a local Spark + Delta session, not in Fabric. `RESULTS.md` lists what that covered and what it did not; the open Fabric checks are in `VERIFY-BEFORE-FRIDAY.md`.

### Foundry

- Foundry project endpoint format: `https://<resource-name>.services.ai.azure.com/api/projects/<project-name>`. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- Build/test role: **Foundry User**. Fabric IQ connection creation role: **Foundry Project Manager**. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- **Fabric IQ** is the current **preview** path for adding published Fabric data agents to Foundry. Learn: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-foundry-fabric-iq
- The legacy **Microsoft Fabric data agent** tool in Foundry is **preview** and **DEPRECATING 2026-11-06**. Learn: https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric

## Pre-flight checklist

### D-5 to D-2

- Provision or confirm a paid Fabric capacity in the target region.
- Confirm tenant settings with a Fabric admin.
- Create/publish a rehearsal Fabric data agent over a throwaway copy of the workshop tables.
- Provision the Foundry project and deploy the chat model to be used on stage.
- Confirm that the same sign-in account can open Fabric and Foundry in the same tenant.

### D-1

- Run `nb_10_load_gold_break_glass` in the rehearsal workspace (CSVs uploaded and `lh_fleet` attached as default lakehouse first, see "Fabric notebooks") and confirm the contract counts.
- Run `nb_11_recon_walkthrough` end to end.
- Re-import `data-agent\example-queries.json`.
- Ask at least Q11, Q20, Q21, Q24, and Q30 in the Fabric data agent UI.
- Dry-run `foundry-agent\create_agent.py --dry-run`.
- Re-run the offline harness and keep the reports in `foundry-agent\reports\`.

### D-0 / pre-room

- Open the notebook, the data-agent configuration UI, `qa-script.md`, and `run-of-show.md`.
- Confirm that the published data agent still appears in Fabric IQ / MCP surfaces.
- Warm the browser session and confirm that the data agent answers one easy question.
- Keep the break-glass path ready: the gold/ml tables already loaded with `nb_10`, `nb_11` open, and the offline oracle harness.

## Break-glass path when the live data agent is unavailable

1. Switch to `fabric-setup\nb_11_recon_walkthrough` (it only reads `gold.*`; if the tables are missing, run `nb_10_load_gold_break_glass` first).
2. Tell the audience the business logic and numbers are unchanged because the tables are frozen from the contract-backed reference output.
3. If Fabric itself is unreachable, the notebooks cannot run (they are Spark-only, with no local mode). Use the offline DuckDB-backed SQL examples (`data-agent\validate_examples.py`) or run:

```powershell
python foundry-agent\eval_harness.py --agent oracle
```

4. If needed, show `foundry-agent\create_agent.py --dry-run` to explain the Foundry wiring without making a live call.

## Cost and capacity notes

- Do **not** quote an exact workshop-day price in slides.
- Safe message: Fabric requires paid capacity; Foundry cost depends on chosen model, tool usage, and background-mode/runtime behavior.
- For discussion, estimate by method only: capacity-hours for Fabric + model tokens/tool calls for Foundry.

## Lab variant: participants build their own agent in 30 minutes

### Prerequisites

- Paid Fabric capacity with the required tenant settings already enabled
- Rehearsal workspace with the frozen `gold.*` and `ml.*` tables already loaded
- Read access to the source tables

### 30-minute plan

1. **5 min** - open the preloaded lakehouse and inspect the curated tables.
2. **10 min** - create a Fabric data agent, add the lakehouse SQL endpoint, and expose only the approved tables.
3. **5 min** - paste the agent instructions, source instructions, description, and schema notes from this folder.
4. **5 min** - import example queries and test one count, one drill-down, and one trap.
5. **5 min** - compare the answer to `qa-script.md`, then publish.

Skip the Foundry layer in the participant lab unless a working Foundry project already exists for every participant.

## File index

- `fabric-setup\`
  - `nb_10_load_gold_break_glass.{py,ipynb}` - load the frozen gold and ML tables from `Files/reference_out` with `saveAsTable` and check the row counts
  - `nb_11_recon_walkthrough.{py,ipynb}` - reconciliation story notebook (Spark-only, read-only)
  - `schema-descriptions.md` - business descriptions for the exposed tables/columns
- `data-agent\`
  - `agent-instructions.md`
  - `data-source-description.md`
  - `data-source-instructions.md`
  - `example-queries.json`
  - `validate_examples.py`
- `foundry-agent\`
  - `create_agent.py`
  - `ask.py`
  - `guardrails.py`
  - `tracing.py`
  - `eval_harness.py`
  - `reports\`
- top-level docs
  - `run-of-show.md`
  - `rebuild-guide.md`
  - `qa-script.md`
  - `troubleshooting.md`
  - `VERIFY-BEFORE-FRIDAY.md`
  - `agent-facts-for-slides.md`
  - `RESULTS.md`

## Local validation commands

Run from the B4 venv:

```powershell
python -m py_compile (Get-ChildItem -Recurse -Filter *.py | ForEach-Object FullName)
ruff check .
pytest tests -q
python data-agent\validate_examples.py
python foundry-agent\eval_harness.py --agent oracle
python foundry-agent\eval_harness.py --agent naive
python -c "import json, pathlib, importlib; root = pathlib.Path('.'); [json.loads(p.read_text(encoding='utf-8')) for p in root.rglob('*.json') if '.pytest_cache' not in str(p) and '.ruff_cache' not in str(p)]; yaml_files = [*root.rglob('*.yml'), *root.rglob('*.yaml')]; yaml = importlib.import_module('yaml') if yaml_files else None; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in yaml_files]"
python -c "import nbformat, pathlib; root = pathlib.Path('fabric-setup'); [nbformat.validate(nbformat.read(p.open('r', encoding='utf-8'), as_version=4)) for p in root.glob('*.ipynb')]"
```

Final executed results are recorded in `RESULTS.md`.

The two notebooks are Spark-only and are not run by the commands above. They were executed unchanged, one after the other, on a local Spark + Delta session; `RESULTS.md` states what that run did and did not cover. Their `.ipynb` files are generated from the percent-format `.py` files (`b4_fleet_demo\notebook_sync.py`); edit the `.py`, regenerate, and rerun `pytest tests -q`, which parses the notebook literals and fails if they drift from the reference data.
