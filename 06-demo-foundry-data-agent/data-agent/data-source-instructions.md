Use this source as a **read-only analytical lakehouse** for the Contoso Fleet reconciliation workshop.

- Prefer `gold.*` for reconciliation and maintenance questions.
- Prefer `ml.failure_risk_score` for risk-band questions in Part 4.
- Use `gold.agg_recon_monthly` for site or month trends before scanning detailed fact tables.
- Join through `erp_asset_id` for asset-level analysis and `site_code` for site-level analysis.
- Treat `fact_recon_exception` as the curated record of what went wrong; do not try to infer exceptions from raw facts unless the question explicitly asks for supporting evidence.
- Treat `fact_recon_match.delta_hours` as the official signed delay from first fault record to work-order opening.
- Do not infer unsupported business entities such as operators, fuel cost, safety incidents, or future forecasts.
