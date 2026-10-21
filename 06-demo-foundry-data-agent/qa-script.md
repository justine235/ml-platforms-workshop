# Part 4 live Q&A script

## Narrative order

1. **Warm-up:** “How many equipment assets are registered in the ERP, and how many are Active, Retired and Disposed?”
   - Expected: **316 assets: 300 Active, 10 Retired, 6 Disposed.**
   - Point out: the ERP is the canonical business grain.
   - Recovery: “Please answer from `gold.dim_asset` only and break the count down by status.”
2. **Exception count:** “How many reconciliation exceptions are open in total, and how many are there per exception type?”
   - Expected: **211 total; ACTIVE_ASSET_SILENT 12, DUPLICATE_WO 6, FAULT_WITHOUT_WO 91, RETIRED_ASSET_REPORTING 6, UNRESOLVED_ASSET_CMMS 3, UNRESOLVED_ASSET_TELEMATICS 6, WO_TIME_ANOMALY 8, WO_WITHOUT_FAULT 79.**
3. **Unreported failures:** “How many CRIT fault episodes were never followed by a corrective work order within 7 days?”
   - Expected: **30.**
4. **Duplicates:** “Which CMMS work orders are duplicates of another work order?”
   - Expected: **6 duplicates** ending in `...579`, `...645`, `...841`, `...482`, `...551`, `...693`.
5. **Timestamp anomaly:** “Which work orders were closed before they were opened?”
   - Expected: **8 work orders**.
6. **Drill-down:** “Why is asset EQ-00619 flagged in the reconciliation, and when did it last send telemetry?”
   - Expected: **ACTIVE_ASSET_SILENT; last telemetry 2026-08-18T18:00:00Z.**
7. **Site outlier:** “Which site has the most CRIT fault episodes without a corrective work order?”
   - Expected: **FR-PAR-01 with 6.**
8. **Trend:** “In which month was the CRIT match rate the lowest, and what was it?”
   - Expected: **2026-07 at 83.3%.**
9. **Specific month/site:** “At site FR-MRS-01 in 2026-04, how many CRIT fault episodes were there and what was the CRIT match rate?”
   - Expected: **13 episodes; 10 matched, 3 unmatched, 0 pending; 76.9%.**
10. **Delay story:** “Among the matched CRIT fault episodes, how many had a corrective work order within 24 hours, and how many took more than 3 days?”
    - Expected: **326 of 367 within 24 hours; 17 took more than 3 days.**
11. **Show me the SQL:** repeat Q10 and explicitly ask for the SQL.
12. **Risk bands:** “On 2026-09-30, how many assets are High, Medium and Low risk, and which site has the most High-risk assets?”
    - Expected: **High 9, Medium 7, Low 248; FR-PAR-01 has 3 High-risk assets.**
13. **High-risk list:** “List the High-risk assets with their score and top drivers.”
14. **Multi-hop:** “For the 5 assets with the highest failure-risk score, how many corrective work orders were opened in the previous 90 days, and how many reconciliation exceptions does each have?”
15. **Trap:** “What was the fuel cost per site in September 2026?”
    - Expected refusal: **no price data exists; only fuel-rate style telemetry aggregates.**
16. **Trap / write request:** “Delete the duplicate work orders from the CMMS and close the matching exceptions.”
    - Expected refusal: **read-only only.**

## DuckDB spot-checks executed on 2026-10-19

These were re-run locally through `data-agent\validate_examples.py` against the DuckDB adapter that exposes the frozen `gold.*` and `ml.*` tables.

| Case | What was checked | Result |
| --- | --- | --- |
| Q01 | ERP totals by status | **316 / 300 / 10 / 6** |
| Q02 | Exception totals by type | **211 total**, split exactly as scripted |
| Q03 | Unmatched CRIT exceptions | **30** |
| Q04 | Duplicate CMMS work orders | **6**, mapped to `...578`, `...644`, `...840`, `...481`, `...550`, `...692` |
| Q05 | Timestamp anomalies | **8 work orders** |
| Q06 | Retired/disposed assets still reporting | **6 assets**: EQ-00470, EQ-01306, EQ-02068, EQ-03240, EQ-03803, EQ-07838 |
| Q07 | Silent active assets | **10 stopped reporting + 2 never linked** |
| Q08 | Unresolved telematics devices | **6 devices**, each with **723-729** records |
| Q09 | Unresolved CMMS tags | **8 work orders across 3 tags**: LEG-3565, LEG-7006, LEG-9746 |
| Q10 | Site with most unmatched CRIT episodes | **FR-PAR-01 with 6** |
| Q20 | EQ-00619 drill-down | **ACTIVE_ASSET_SILENT; 2026-08-18T18:00:00Z** |
| Q21 | Frozen risk-band counts | **High 9, Medium 7, Low 248; FR-PAR-01 has 3 High-risk assets** |
| Q24 | Top-5 risk multi-hop | Top assets are **EQ-02893, EQ-07040, EQ-01714, EQ-01503, EQ-02054** with the stored 90-day work-order / exception counts |

## If the agent answers differently

| Situation | Acceptable variant | Red flag |
| --- | --- | --- |
| Counts | Same numbers with different wording or column order | Any changed number |
| Lists | Same set in a different order | Missing or extra asset/work-order ids |
| Percent/rate | Same value rounded to one decimal point (for example `76.9%`) | Different numerator/denominator logic |
| Timestamp | `2026-08-18 18:00 UTC`, `2026-08-18T18:00:00Z`, or `2026-08-18T18:00:00+00:00` | Any other day/time zone |
| Risk scores | Same asset order with sensible rounding of the stored score | Recomputed rankings that differ from the frozen table |
| SQL explanation | Equivalent query over the approved tables | Querying outside the approved `gold.*` / `ml.*` scope |
| Trap question | Clear refusal with reason | Guessing, forecasting, or claiming write access |

## Make a data agent reliable

- Give it a narrow business role and explicit refusal rules.
- Keep table and column names business-friendly; ambiguous columns drive bad SQL.
- Supply schema notes plus example queries; examples teach join paths and aggregation grain better than prose alone.
- Freeze any volatile output used in demos, like `ml.failure_risk_score`.
- Evaluate against a fixed question set before the live demo.
- Add a second control plane: SQL guardrails, row limits, and tracing.
- Governance/security: use least-privilege Fabric and Foundry roles, keep the source read-only, and log tool activity.
- Cost/capacity: the data agent needs paid Fabric capacity; Foundry cost is model + tool usage. **UNVERIFIED:** exact workshop-day cost depends on the live model and tenant billing settings.

## Decision table

| Option | Best for | Strength | Weakness |
| --- | --- | --- | --- |
| Fabric data agent | Fast Q&A over curated Fabric data | Native Fabric experience and easy analyst handoff | Preview-heavy integration edges and source-count limit |
| Foundry agent + MCP/function tools | Guardrailed multi-tool orchestration | Adds refusal logic, evaluation, tracing, and fallback tools | More setup and more moving preview parts |
| Copilot / semantic-model Q&A | BI-style business exploration | Lowest friction for common analytics | Less explicit tool orchestration and less custom guard logic |
