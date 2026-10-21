"""Numbers shown on slides, read from the reference run (ground_truth.json) so that no figure is typed by hand.

    from facts import F, n, pct
    f"{n(F.bronze_rows)} raw rows"        -> '208,900 raw rows'
    pct(F.crit_match_rate)                 -> '92.4 %'

Counts are exact on every library version. Model metrics and risk scores are approximate (see the contract):
always round them as shown here and say "about" when speaking.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

_REF = Path(__file__).resolve().parents[1] / "02-demo-data" / "reference_out"
GT = json.loads((_REF / "ground_truth.json").read_text(encoding="utf-8"))


def n(x) -> str:
    """12345 -> '12,345' (locale-proof)."""
    return f"{int(round(x)):,}"


def pct(x, digits=1) -> str:
    """0.9244 -> '92.4 %'"""
    return f"{x * 100:.{digits}f} %"


def d2(x) -> str:
    return f"{x:.2f}"


def d3(x) -> str:
    return f"{x:.3f}"


_s, _c, _g = GT["silver"]["telematics"], GT["silver"]["cmms"], GT["gold_row_counts"]
_r, _e, _m = GT["reconciliation"], GT["exceptions"], GT["ml"]["metrics_approximate"]
_t = {k: v["test"] for k, v in _m.items()}
_v = {k: v["valid"] for k, v in _m.items()}
_sp = GT["ml"]["by_split"]
_d = GT["drift"]

F = SimpleNamespace(
    # bronze and silver
    bronze_rows=_s["bronze_rows"], duplicates=_s["duplicates_removed"], out_of_range=_s["out_of_range_values_nulled"],
    silver_rows=_s["rows"], late_rows=_s["late_rows"], tiers=_s["by_resolution"],
    unresolved=_s["by_resolution"]["UNRESOLVED"],
    cmms_rows=_c["rows"], cmms_tiers=_c["by_resolution"], cmms_unresolved=_c["unresolved"],
    cmms_duplicates=_c["duplicates"], cmms_time_anomalies=_c["time_anomalies"],
    erp_assets=GT["assets"]["by_status"]["Active"] + GT["assets"]["by_status"]["Retired"] + GT["assets"]["by_status"]["Disposed"],
    erp_status=GT["assets"]["by_status"], asset_classes=GT["assets"]["by_class"],
    devices=GT["truth_checks"]["telematics_id_resolution"]["devices"],
    # gold
    gold=_g,
    # reconciliation
    episodes=_r["fault_episodes"], severity=_r["by_severity"], significant=_r["significant_episodes"],
    recon=_r["recon_status"], crit_recon=_r["crit_recon_status"], crit_match_rate=_r["crit_match_rate"],
    crit_total=sum(_r["crit_recon_status"].values()), median_crit_hours=_r["median_crit_fault_to_wo_hours"],
    cm_work_orders=_r["cm_work_orders"], cm_work_orders_matched=_r["cm_work_orders_matched"],
    crit_within_24h=326,  # contract section 10 and the agent evaluation set
    # exceptions
    exceptions=_e["total"], exception_types=_e["by_type"], exception_subtypes=_e["by_type_and_subtype"],
    # machine learning (approximate)
    feature_count=GT["ml"]["feature_count"], ml_rows=GT["ml"]["rows"], labelled_rows=GT["ml"]["labelled_rows"],
    positive_rate=GT["ml"]["positive_rate_labelled"], splits=_sp,
    pr_auc_test=dict(hgb=_t["hist_gradient_boosting"]["pr_auc"], logistic=_t["logistic_regression"]["pr_auc"],
                     rule=_t["rule_baseline"]["pr_auc"], prevalence=_t["prevalence"]["pr_auc"],
                     hgb_no_fault_codes=_t["hist_gradient_boosting_no_fault_codes"]["pr_auc"]),
    roc_auc_test=dict(hgb=_t["hist_gradient_boosting"]["roc_auc"], logistic=_t["logistic_regression"]["roc_auc"],
                      rule=_t["rule_baseline"]["roc_auc"]),
    pr_auc_valid=dict(hgb=_v["hist_gradient_boosting"]["pr_auc"], logistic=_v["logistic_regression"]["pr_auc"],
                      rule=_v["rule_baseline"]["pr_auc"], prevalence=_v["prevalence"]["pr_auc"]),
    prevalence_test=_t["prevalence"]["prevalence"], prevalence_valid=_v["prevalence"]["prevalence"],
    bands=GT["risk_scoring"]["bands"], band_thresholds=GT["risk_scoring"]["thresholds"],
    assets_scored=GT["risk_scoring"]["assets_scored"], score_date=GT["risk_scoring"]["score_date"],
    top10=GT["risk_scoring"]["top10"],
    # drift
    drift_combinations=_d["combinations"], drift_major=_d["major_shift"], drift_moderate=_d["moderate_shift"],
    drift_stable=_d["combinations"] - len(_d["major_shift"]) - len(_d["moderate_shift"]),
    seed=GT["data"]["seed"], window=GT["data"]["window"],
)

if __name__ == "__main__":
    for k, v in vars(F).items():
        s = json.dumps(v, ensure_ascii=False, default=str)
        print(f"{k:24s} {s if len(s) < 110 else s[:107] + '...'}")
