"""Shared ML core for the Contoso Fleet workshop (pandas + scikit-learn only).

The same code trains the same model on a laptop, in a Fabric notebook and in an Azure ML job.
Platform-specific parts (tracking URI, where files live, model registration) stay OUTSIDE this file.

    from fleet_ml_core import load_features, train_and_evaluate, mlflow_metrics
    df = load_features("ml_asset_day_features.csv.gz")
    model, metrics = train_and_evaluate(df)          # metrics["test"]["pr_auc"] is about 0.38

Contract: 02-demo-data/scenario-contract.md section 8 (label, 42 features, purged time splits, models, reason codes).
Dependencies: numpy, pandas, scikit-learn. No MLflow import here on purpose.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LABEL = "fail_next_7d"
SPLIT_COL = "split"
ID_COLS = ["erp_asset_id", "obs_date", "day"]
BASE_COLS = ["temp_mean", "temp_max", "oil_mean", "oil_min", "hyd_mean", "hyd_min", "vib_mean", "vib_max", "fuel_mean", "load_mean", "idle_mean",
             "n_readings", "run_share", "engine_hours"]
FEATURES = (BASE_COLS + ["warn_cnt_1d", "crit_cnt_1d", "warn_cnt_7d", "crit_cnt_7d", "warn_cnt_14d"]
            + ["%s_mean_%dd" % (s, n) for s in ("temp", "oil", "hyd", "vib") for n in (3, 7, 14)]
            + ["%s_trend" % s for s in ("temp", "oil", "hyd", "vib")] + ["temp_max_7d", "vib_max_7d"]
            + ["days_since_last_pm", "days_since_last_cm", "cm_count_90d", "equipment_class_code", "asset_age_years"])
NO_FAULT_FEATURES = [c for c in FEATURES if not c.startswith(("warn_cnt", "crit_cnt"))]
MODEL_KINDS = ("prevalence", "logistic_regression", "hist_gradient_boosting")
HGB_PARAMS = dict(max_iter=300, learning_rate=0.06, max_leaf_nodes=24, l2_regularization=1.0, early_stopping=False, random_state=0)
LR_PARAMS = dict(C=0.5, max_iter=2000)
HIGH_RISK, MEDIUM_RISK = 0.30, 0.10
TRAIN_SPLITS = ("train",)
FINAL_FIT_SPLITS = ("train", "gap", "valid", "test")      # final refit: every labelled day after the warm-up
METRIC_KEYS = ("valid_pr_auc", "valid_roc_auc", "test_pr_auc", "test_roc_auc", "test_precision_at_top5pct", "test_recall_at_top5pct")


def load_features(path) -> pd.DataFrame:
    """Read ml_asset_day_features (.csv or .csv.gz). Numeric columns are float, ids/dates are strings."""
    df = pd.read_csv(path, dtype={"erp_asset_id": str, "obs_date": str, SPLIT_COL: str})
    missing = [c for c in FEATURES + [LABEL, SPLIT_COL] if c not in df.columns]
    if missing:
        raise ValueError("feature table is missing columns: %s" % missing)
    return df


def get_split(df: pd.DataFrame, *names: str) -> pd.DataFrame:
    """Rows of one or more splits (warmup, train, gap, valid, test, unlabeled, score). Never re-split: the purge gap is in the column."""
    return df[df[SPLIT_COL].isin(names)]


def make_model(kind: str = "hist_gradient_boosting", **overrides):
    """Return an unfitted scikit-learn estimator. `overrides` replace default hyper-parameters (used by sweeps)."""
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    if kind == "prevalence":
        return DummyClassifier(strategy="prior")
    if kind == "logistic_regression":
        p = {**LR_PARAMS, **overrides}
        return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), LogisticRegression(**p))
    if kind == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(**{**HGB_PARAMS, **overrides})
    raise ValueError("unknown model kind %r, expected one of %s" % (kind, MODEL_KINDS))


def eval_scores(y, s) -> dict:
    """PR-AUC, ROC-AUC and precision/recall among the 5 % riskiest asset-days."""
    from sklearn.metrics import average_precision_score, roc_auc_score
    y, s = np.asarray(y, dtype=float), np.asarray(s, dtype=float)
    top = np.argsort(-s, kind="stable")[: max(1, int(round(0.05 * len(y))))]
    return {"rows": len(y), "positives": int(y.sum()), "prevalence": round(float(y.mean()), 4),
            "pr_auc": round(float(average_precision_score(y, s)), 4), "roc_auc": round(float(roc_auc_score(y, s)), 4),
            "precision_at_top5pct": round(float(y[top].mean()), 4), "recall_at_top5pct": round(float(y[top].sum() / y.sum()), 4)}


def rule_baseline_scores(d: pd.DataFrame) -> np.ndarray:
    """The 'no ML' rule: any CRIT fault in 7 days, or 2+ WARN faults. A maintenance planner could write it in an afternoon."""
    return ((d["crit_cnt_7d"] > 0) | (d["warn_cnt_7d"] >= 2)).astype(float).to_numpy()


def train_and_evaluate(df: pd.DataFrame, kind: str = "hist_gradient_boosting", features=None, **overrides):
    """Fit on the train split, evaluate on valid and test. Returns (fitted_model, {"valid": {...}, "test": {...}})."""
    features = list(features or FEATURES)
    tr = get_split(df, *TRAIN_SPLITS)
    model = make_model(kind, **overrides).fit(tr[features], tr[LABEL])
    metrics = {}
    for name in ("valid", "test"):
        part = get_split(df, name)
        metrics[name] = eval_scores(part[LABEL], model.predict_proba(part[features])[:, 1])
    return model, metrics


def mlflow_metrics(metrics: dict) -> dict:
    """The six metric names used everywhere in the workshop (MLflow, Fabric experiment, AML job, CI gate)."""
    flat = {"valid_pr_auc": metrics["valid"]["pr_auc"], "valid_roc_auc": metrics["valid"]["roc_auc"],
            "test_pr_auc": metrics["test"]["pr_auc"], "test_roc_auc": metrics["test"]["roc_auc"],
            "test_precision_at_top5pct": metrics["test"]["precision_at_top5pct"], "test_recall_at_top5pct": metrics["test"]["recall_at_top5pct"]}
    return {k: float(flat[k]) for k in METRIC_KEYS}


def fit_final_model(df: pd.DataFrame, kind: str = "hist_gradient_boosting", features=None, **overrides):
    """Refit on every labelled day after the warm-up (train + gap + valid + test) before scoring the latest day."""
    features = list(features or FEATURES)
    lab = get_split(df, *FINAL_FIT_SPLITS)
    return make_model(kind, **overrides).fit(lab[features], lab[LABEL])


def risk_band(score: float) -> str:
    return "High" if score >= HIGH_RISK else "Medium" if score >= MEDIUM_RISK else "Low"


def reason_codes(s: pd.DataFrame) -> list:
    """Rule-based 'why is it flagged' labels (readable by a planner). NOT model attributions: say so out loud."""
    rules = [("CRIT_FAULT_7D", s["crit_cnt_7d"] >= 1), ("REPEATED_WARNINGS", s["warn_cnt_7d"] >= 3), ("ENGINE_TEMP_RISING", s["temp_trend"] >= 3.0),
             ("OIL_PRESSURE_FALLING", s["oil_trend"] <= -10.0), ("HYDRAULIC_PRESSURE_FALLING", s["hyd_trend"] <= -8.0),
             ("VIBRATION_RISING", s["vib_trend"] >= 0.3), ("PM_OVERDUE", s["days_since_last_pm"] >= 90)]
    flags = np.column_stack([m.to_numpy() for _, m in rules])
    out = []
    for row in flags:
        names = [n for (n, _), on in zip(rules, row) if on][:3]
        out.append(";".join(names) or "NO_STRONG_SIGNAL")
    return out


def score_latest(df: pd.DataFrame, model, features=None, model_version: str = "dev") -> pd.DataFrame:
    """Score the `score` split (the latest day). Same columns as ml.failure_risk_score except site_code / equipment_class (join dim_asset)."""
    features = list(features or FEATURES)
    s = get_split(df, "score").copy()
    s["risk_score"] = model.predict_proba(s[features])[:, 1]
    s["risk_band"] = [risk_band(v) for v in s["risk_score"]]
    s["top_drivers"] = reason_codes(s)
    s = s.sort_values(["risk_score", "erp_asset_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
    s["risk_rank"], s["risk_score"] = np.arange(1, len(s) + 1), s["risk_score"].round(4)
    s["score_date"], s["model_version"] = s["obs_date"], model_version
    return s[["score_date", "erp_asset_id", "risk_score", "risk_band", "risk_rank", "top_drivers", "model_version"]]


def psi(ref, cur, bins: int = 10) -> float:
    """Population Stability Index vs the reference deciles: < 0.10 stable, 0.10-0.25 moderate shift, > 0.25 major shift."""
    ref, cur = np.asarray(ref, dtype=float), np.asarray(cur, dtype=float)
    ref, cur = ref[~np.isnan(ref)], cur[~np.isnan(cur)]
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r, c = (np.clip(np.histogram(x, edges)[0] / len(x), 1e-4, None) for x in (ref, cur))
    return float(np.sum((c - r) * np.log(c / r)))


def psi_status(v: float) -> str:
    return "major" if v > 0.25 else "moderate" if v > 0.10 else "stable"


def psi_table(ref: pd.DataFrame, cur: pd.DataFrame, group_col: str = "equipment_class", sensors=None) -> pd.DataFrame:
    """PSI per group x sensor between two frames of RUN readings. Same columns as reference_out/drift_report.csv."""
    sensors = list(sensors or ["engine_temp_c", "oil_pressure_kpa", "hydraulic_pressure_bar", "vibration_mm_s", "fuel_rate_lph", "load_pct"])
    rows = []
    for g in sorted(set(ref[group_col].dropna())):
        r, n = ref[ref[group_col] == g], cur[cur[group_col] == g]
        for sensor in sensors:
            a, b = r[sensor].to_numpy(dtype=float), n[sensor].to_numpy(dtype=float)
            if len(a) == 0 or len(b) == 0 or np.isnan(a).all() or np.isnan(b).all():
                continue
            v = psi(a, b)
            rows.append({group_col: g, "sensor": sensor, "psi": round(v, 4), "ref_mean": round(float(np.nanmean(a)), 3), "new_mean": round(float(np.nanmean(b)), 3),
                         "ref_rows": len(r), "new_rows": len(n), "status": psi_status(v)})
    return pd.DataFrame(rows)
