# Troubleshooting

## The data agent gives the wrong number

- Re-ask with the exact wording from `qa-script.md`.
- Check whether it drifted to `fact_fault_episode` when `agg_recon_monthly` was the better source.
- If a risk answer changed, confirm it used `ml.failure_risk_score` and not a re-derived score.

## The data agent answers a trap instead of refusing

- Tighten the pasted instructions first.
- Re-import the example queries.
- Confirm the selected tables do not accidentally imply the missing concept.

## Fabric/Foundry integration issues

- Confirm the data agent is **published**; the MCP path is for the published agent.
- Confirm Foundry and Fabric are in the same tenant and follow the current region guidance.
- Re-check the project connection and workspace/data-agent ids in `.env`.

## Live tenant uncertainty

- Use `create_agent.py --dry-run` if the preview tool wiring changed.
- Fall back to the Fabric UI demo plus the offline oracle harness if the Foundry preview path is temporarily unstable.

## nb_10 / nb_11 cannot find the files or the tables

- "Path not found" for `Files/reference_out`: check that `lh_fleet` is attached as the **default lakehouse** of the notebook and that the session was restarted after attaching it. Then check that the CSVs sit directly in `Files/reference_out`, not in a sub-folder.
- "Path not found" right after an upload: wait about 2 minutes and rerun the cell (file-listing cache; the duration is **UNVERIFIED**).
- "Table or view not found: gold.<table>" in `nb_11`: `nb_10` has not completed in this lakehouse, or `nb_11` has another default lakehouse. Rerun `nb_10` and check its printed row counts.
- Row counts that differ from the contract: re-upload the complete `02-demo-data\reference_out\` CSV set and rerun `nb_10`; it overwrites the tables.
- A new table is missing from the data agent's source picker: the lakehouse SQL analytics endpoint may not have synced yet. Wait, then refresh (the delay is **UNVERIFIED**).

## Local validation issues

- If `validate_examples.py` fails, fix the example query before changing the expected answer.
- If notebook validation fails, or `pytest` reports that a `.ipynb` is not generated from its `.py`, regenerate the `.ipynb` files from the percent scripts with `b4_fleet_demo\notebook_sync.py` (`percent_script_to_notebook`). Never edit the `.ipynb` by hand.
- If `pytest` fails in guardrails, inspect SQLGlot parser changes first.
