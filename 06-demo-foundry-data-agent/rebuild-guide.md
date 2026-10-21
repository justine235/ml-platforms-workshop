# Rebuild guide

## 1. Starting point

If the gold tables already exist in the lakehouse, skip to step 4. If not, upload the `*.csv` and `*.csv.gz` files of `02-demo-data\reference_out\` (never `02-demo-data\truth\`) to the lakehouse `lh_fleet`, folder `Files/reference_out`, then follow step 3.

## 2. Fabric prerequisites

- Fabric capacity: **F2+** or **P1+ with Fabric enabled** for the data agent. A trial capacity is enough for steps 1 and 3 (the notebooks) but not for step 4.
- Confirm the tenant settings that enable Fabric data agent and any needed cross-geo AI path. **Verify the exact labels in your tenant before Friday.**
- Keep the Fabric workspace and the data sources in the same region/capacity path described in current Learn guidance.

## 3. Load the frozen tables

1. Attach `lh_fleet` (schema-enabled) as the **default lakehouse** of `fabric-setup\nb_10_load_gold_break_glass` and of `nb_11_recon_walkthrough`, then restart the session. Relative paths and `gold.*` / `ml.*` table names resolve against the default lakehouse only.
2. Run all cells of `nb_10_load_gold_break_glass`. It reads `Files/reference_out` and writes each table with `saveAsTable` (overwrite) into the `gold` and `ml` schemas. There is nothing to edit.
3. If the first read reports "path not found" right after the upload, wait about 2 minutes and rerun (file-listing cache; the duration is **UNVERIFIED**).
4. Verify that the printed row counts match the contract for all 11 tables (listed in `README.md`).
5. Confirm `ml.failure_risk_score` shows **264 rows** on **2026-09-30**.
6. Run `nb_11_recon_walkthrough` end to end. Its final cell asserts the reconciliation scorecard computed from `gold.fact_recon_match` (significant episodes 455 / 91 / 11, CRIT 367 / 30 / 2). The precision / recall panel (0.933 / 0.778) is a literal copied from the frozen ground truth; it is shown, not recomputed in Fabric.

## 4. Build the Fabric data agent in the UI

1. In the Fabric workspace, create **New item -> Fabric data agent**.
2. Name it `da_fleet_recon`.
3. Add the lakehouse SQL analytics endpoint as the data source.
4. Select only:
   - `gold.dim_asset`
   - `gold.dim_site`
   - `gold.fact_fault_episode`
   - `gold.fact_recon_exception`
   - `gold.fact_recon_match`
   - `gold.fact_telemetry_daily`
   - `gold.fact_work_order`
   - `gold.agg_recon_monthly`
   - `ml.failure_risk_score`
   - optionally `ml.drift_report`
5. Paste `data-agent\data-source-description.md`.
6. Paste `data-agent\data-source-instructions.md`.
7. Paste `data-agent\agent-instructions.md`.
8. Paste or upload the schema notes from `fabric-setup\schema-descriptions.md`.
9. Import `data-agent\example-queries.json`.
10. Test at least Q11, Q20, Q21, and Q30.
11. Publish the data agent.

Expected duration: **15-20 minutes** if the lakehouse already exists.

## 5. Build the Foundry side

1. Create or open a Foundry resource/project in an EU region that supports Agents and the model you plan to use.
2. Deploy a chat model that exists in the chosen region. Safe workshop candidates from current docs include `gpt-5.4` or `gpt-5.5`; confirm the exact deployment name in your tenant.
3. Ensure the builder identity has at least:
   - **Foundry User** for agent work
   - **Foundry Project Manager** if it must create project connections
4. Create the Fabric IQ / MCP connection path the project will use.
5. Copy `foundry-agent\.env.example` to `.env` and fill the live values.
6. Dry-run first:
   - `python foundry-agent\create_agent.py --dry-run`
7. Create the agent live:
   - `python foundry-agent\create_agent.py`
8. Smoke-test the offline harness:
   - `python foundry-agent\eval_harness.py --agent oracle`
9. Smoke-test the real stack in the portal or your tenant-specific invocation path.

Expected duration once the project exists: **10-15 minutes**.

## 6. End-to-end rehearsal

1. Run `fabric-setup\nb_11_recon_walkthrough`.
2. Ask Q11, Q20, Q21, Q24, and Q30.
3. Keep `qa-script.md` open during the live demo.
