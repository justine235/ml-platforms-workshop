# %% [markdown]
# # nb_11_recon_walkthrough
#
# Fabric-native, Spark-only, read-only walkthrough for the Part 4 live demo. Run
# `nb_10_load_gold_break_glass` first, in the same lakehouse, so that the `gold.*` tables exist.
# This notebook has no local/offline branch and does not import `b4_fleet_demo`: the few expected
# values it needs (resolution tiers, the precision/recall check) are literal, copied from the
# scenario contract / `reference_out/ground_truth.json`, and are covered by the same drift-guard
# test as nb_10 (`tests/test_nb10_nb11_literals.py`).

# %%
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()


def show_sql(title: str, query: str) -> pd.DataFrame:
    print(f"\n## {title}\n")
    print(query.strip())
    frame = spark.sql(query).toPandas()
    print(frame.to_string(index=False))
    return frame


# %% [markdown]
# ## 1. What are the three sources and why was reconciliation needed?
#
# - **Telematics logs** give daily runtime and fault episodes keyed by messy `asset_ref` values and device ids.
# - **CMMS work orders** describe maintenance actions, sometimes with duplicate work orders or swapped timestamps.
# - **ERP asset register** is the business system of record and provides the canonical `erp_asset_id`.
#
# The same machine can appear under a telematics device id, an ERP identifier, or a legacy CMMS tag. The Part 3
# ETL resolved that into one business grain and surfaced the mismatches as explicit exceptions.

# %% [markdown]
# ## 2. Resolution tiers and counts
#
# Literal from `reference_out/ground_truth.json` -> `silver.telematics.by_resolution` /
# `silver.cmms.by_resolution` (these are ETL silver-stage facts, not reloaded by nb_10, so there is
# no gold table to query them from here).

# %%
RESOLUTION_TIERS = {
    "telematics": {"EXACT_NORM": 196810, "SERIAL": 4350, "CROSSWALK": 2180, "UNRESOLVED": 4351},
    "cmms": {"EXACT_NORM": 2305, "SERIAL": 28, "CROSSWALK": 18, "UNRESOLVED": 8},
}

resolution_tiers = pd.DataFrame(
    [
        {"source": source, "tier": tier, "rows": rows}
        for source, tiers in RESOLUTION_TIERS.items()
        for tier, rows in tiers.items()
    ]
)
print(resolution_tiers.to_string(index=False))

# %% [markdown]
# ## 3. Exception counts, with one real row for every exception type

# %%
exception_counts = show_sql(
    "Exception counts",
    """
    SELECT exception_type, COUNT(*) AS exception_count
    FROM gold.fact_recon_exception
    GROUP BY exception_type
    ORDER BY exception_type
    """,
)

# %%
exception_examples = show_sql(
    "One example row per exception type",
    """
    WITH ranked AS (
        SELECT
            exception_type,
            subtype,
            erp_asset_id,
            site_code,
            reference_id,
            detail,
            ROW_NUMBER() OVER (PARTITION BY exception_type ORDER BY reference_id) AS rn
        FROM gold.fact_recon_exception
    )
    SELECT exception_type, subtype, erp_asset_id, site_code, reference_id, detail
    FROM ranked
    WHERE rn = 1
    ORDER BY exception_type
    """,
)

# %% [markdown]
# ## 4. The CRIT story: match rate and response speed
#
# This is the headline operational message of the demo:
# - There are 557 significant episodes (CRIT, plus WARN with at least 3 records): 455 matched,
#   91 unmatched, 11 pending (no work order yet, but the 7-day window is still open).
# - There are 399 CRIT episodes in total: 367 matched, 30 unmatched, 2 pending.
# - 326 of the 367 matched CRIT episodes got a work order within 24 hours.
# - 17 matched CRIT episodes took more than 3 days.
# - 30 CRIT episodes never got a corrective work order inside the 7-day window.

# %%
EXPECTED_RECON_STATUS = {"MATCHED": (455, 367), "UNMATCHED": (91, 30), "PENDING": (11, 2)}

scorecard = show_sql(
    "Significant episodes by reconciliation status",
    """
    SELECT
        recon_status,
        COUNT(*) AS significant_episodes,
        SUM(CASE WHEN severity = 'CRIT' THEN 1 ELSE 0 END) AS crit_episodes
    FROM gold.fact_fault_episode
    WHERE is_significant = TRUE
    GROUP BY recon_status
    ORDER BY CASE recon_status WHEN 'MATCHED' THEN 1 WHEN 'UNMATCHED' THEN 2 ELSE 3 END
    """,
)

# %%
crit_story = show_sql(
    "Matched CRIT episodes within 24 hours vs. more than 3 days",
    """
    SELECT
        SUM(CASE WHEN m.delta_hours >= 0 AND m.delta_hours <= 24 THEN 1 ELSE 0 END) AS within_24h,
        COUNT(*) AS matched_crit_episodes,
        SUM(CASE WHEN m.delta_hours > 72 THEN 1 ELSE 0 END) AS more_than_72h
    FROM gold.fact_recon_match AS m
    INNER JOIN gold.fact_fault_episode AS e ON e.episode_id = m.episode_id
    WHERE m.is_best_for_episode = TRUE AND e.severity = 'CRIT'
    """,
)

# %% [markdown]
# ## 5. Monthly match-rate trend from `agg_recon_monthly`

# %%
monthly_trend = show_sql(
    "Monthly CRIT trend",
    """
    SELECT
        month,
        SUM(crit_matched) AS crit_matched,
        SUM(crit_unmatched) AS crit_unmatched,
        SUM(crit_pending) AS crit_pending,
        ROUND(100.0 * SUM(crit_matched) / NULLIF(SUM(crit_matched) + SUM(crit_unmatched), 0), 1) AS crit_match_rate_percent
    FROM gold.agg_recon_monthly
    GROUP BY month
    ORDER BY month
    """,
)

# %% [markdown]
# ## 6. Asset drill-down used in the live Q&A: EQ-00619

# %%
eq_00619 = show_sql(
    "EQ-00619 reconciliation drill-down",
    """
    SELECT
        a.erp_asset_id,
        a.site_code,
        a.status,
        a.device_id,
        a.last_telemetry_utc,
        e.exception_type,
        e.subtype,
        e.detail
    FROM gold.dim_asset AS a
    LEFT JOIN gold.fact_recon_exception AS e
        ON e.erp_asset_id = a.erp_asset_id
    WHERE a.erp_asset_id = 'EQ-00619'
    ORDER BY e.exception_type
    """,
)

# %% [markdown]
# ## 7. Honest detection quality for "real unreported failures"
#
# The synthetic truth says this exception logic is useful but not perfect, so we say that explicitly
# in the demo. Literal from `reference_out/ground_truth.json` ->
# `truth_checks.unreported_failures_found`.

# %%
UNREPORTED_FAILURES_FOUND = {
    "ok": True,
    "informational": True,
    "crit_fault_without_wo": 30,
    "explained_by_truth": 28,
    "precision": 0.933,
    "truly_unreported_with_crit_code": 36,
    "found": 28,
    "recall": 0.778,
}

quality = pd.DataFrame([UNREPORTED_FAILURES_FOUND])
print(quality.to_string(index=False))

# %%
assert float(quality.loc[0, "precision"]) == 0.933
assert float(quality.loc[0, "recall"]) == 0.778
assert {
    row.recon_status: (int(row.significant_episodes), int(row.crit_episodes))
    for row in scorecard.itertuples()
} == EXPECTED_RECON_STATUS
print("Walkthrough checks align with the frozen truth set.")
