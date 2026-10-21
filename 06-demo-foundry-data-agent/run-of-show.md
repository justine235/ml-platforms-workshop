# Part 4 run of show

## STANDARD version for the 75-minute workshop block

This is the version that fits the slide budget for Part 4.

| Minute | Segment | What is on screen | What to do / say | Standard or extended |
| ---: | --- | --- | --- | --- |
| 0-10 | Frame the problem | Slides P4.0-P4.6 | Three messy systems, one reconciled gold layer, one frozen risk table, one read-only agent. | Both |
| 10-25 | **Demo 3a - reconciliation walk-through (15 min)** | `fabric-setup\nb_11_recon_walkthrough` | Show exception counts, the CRIT story, the monthly trend, and EQ-00619. Keep the headline simple: **326 of 367 matched CRIT episodes got a corrective work order within 24 hours**. | **Standard** |
| 25-45 | **Demo 3b - build the Fabric data agent live (20 min)** | Fabric data-agent UI | Create the agent, add the source, select the approved tables, paste the instructions/description/schema notes, import the examples, test, publish. | **Standard** |
| 45-60 | **Demo 3c - questions from easy to tricky (15 min)** | Data-agent chat + `qa-script.md` | Ask the warm-up, exception, drill-down, risk, and trap questions. Read the generated SQL aloud once. | **Standard** |
| 60-70 | Foundry layer, guardrails, evaluation | `foundry-agent\create_agent.py`, `foundry-agent\reports\oracle-eval.md`, `foundry-agent\red-team-prompts.md` | Show the dry-run scaffolding, explain read-only guardrails, and mention the offline oracle/naive comparison. | Both |
| 70-75 | Wrap-up | Closing slides | Preview/deprecation dates, break-glass path, and recap. | Both |

## EXTENDED version for a lab or longer slot

Use this when the live-demo budget is longer than 50 minutes.

| Minute | Segment | What is on screen | What to add beyond the standard version |
| ---: | --- | --- | --- |
| 0-10 | Frame the problem | Slides P4.0-P4.6 | Same as standard. |
| 10-35 | **Demo 3a - reconciliation walk-through (25 min)** | `fabric-setup\nb_11_recon_walkthrough` | Add the resolution-tier table, one example row per exception type, and the truth-check precision/recall discussion. |
| 35-55 | **Demo 3b - build the Fabric data agent live (20 min)** | Fabric data-agent UI | Same as standard. |
| 55-75 | **Demo 3c - questions from easy to tricky (20 min)** | Data-agent chat + `qa-script.md` | Add one extra multi-hop risk question and one extra trap. |
| 75-85 | Foundry layer, guardrails, evaluation | Foundry dry-run + reports | Same as standard, with more time for red-team prompts. |

## What to skip in the STANDARD version

- In Demo 3a, skip the per-resolution deep dive and the precision/recall truth-check discussion unless asked.
- In Demo 3b, keep one prebuilt `da_fleet_recon` draft as a safety net and skip optional polishing such as extra descriptions for unused tables.
- In Demo 3c, ask only one multi-hop question and two traps.
- Keep Foundry to dry-run scaffolding plus evaluation summary; do not attempt a risky live code-based invocation unless rehearsed in the exact tenant.

## Pre-built before the session

- Gold/ml tables already loaded by `nb_10_load_gold_break_glass` (or the `reference_out` CSVs uploaded to `lh_fleet` `Files/reference_out`, with `lh_fleet` attached as the default lakehouse, ready for `nb_10`)
- A prebuilt copy of `da_fleet_recon` saved as the safety net
- Foundry project/resource and chat model already provisioned
- Offline oracle and naive eval reports already generated in `foundry-agent\reports\`

## Keep visible on stage

- `qa-script.md`
- `fabric-setup\nb_11_recon_walkthrough`
- Fabric data-agent configuration UI
- `foundry-agent\create_agent.py`
- `foundry-agent\red-team-prompts.md`
- `VERIFY-BEFORE-FRIDAY.md`
