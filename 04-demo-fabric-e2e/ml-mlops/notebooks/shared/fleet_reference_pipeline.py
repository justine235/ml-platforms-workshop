#!/usr/bin/env python3
"""
Contoso Fleet - reference pipeline (pandas).  It defines the ONE correct answer for every demo in the workshop.

    bronze (raw files)  ->  silver (typed, de-duplicated, ids resolved, UTC)  ->  gold (star schema + reconciliation + ML)

The Fabric notebooks (PySpark), the Azure ML jobs (pandas / scikit-learn) and the data-agent questions must reproduce the
numbers written to <out>/ground_truth.json (row counts and exception counts are exact; model metrics are approximate).

Usage
-----
    python fleet_data_generator.py --out ./fleet_data --truth-dir ./fleet_truth
    python fleet_reference_pipeline.py --data ./fleet_data --out ./reference_out --truth ./fleet_truth
    python fleet_reference_pipeline.py --data ./fleet_data --out ./reference_out --with-drift     # adds the Oct 1-14 drift report

Requires Python >= 3.11, pandas >= 2.2, numpy, scikit-learn >= 1.4, tzdata (Windows).
"""
import argparse
import datetime as dt
import glob
import gzip
import json
import os
import re
import sys
import time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

SENSORS = {"engine_temp_c": (0, 150), "oil_pressure_kpa": (0, 800), "hydraulic_pressure_bar": (0, 450), "vibration_mm_s": (0, 30),
           "fuel_rate_lph": (0, 200), "load_pct": (0, 100), "idle_pct": (0, 100)}
CLASS_CODE = {"Excavator": 1, "WheelLoader": 2, "Bulldozer": 3, "DumpTruck": 4, "MobileCrane": 5, "Compactor": 6, "Paver": 7, "Generator": 8}
NORM_RE = re.compile(r"^\s*(?:EQ|E)?[\s_\-]*0*(\d{1,5})\s*$", re.IGNORECASE)
DAY = 86400
EPISODE_GAP_S, MATCH_BEFORE_S, MATCH_AFTER_S, DUP_WINDOW_S, SILENT_DAYS = DAY, DAY, 7 * DAY, 3600, 14
EXC_ORDER = ["UNRESOLVED_ASSET_TELEMATICS", "UNRESOLVED_ASSET_CMMS", "RETIRED_ASSET_REPORTING", "ACTIVE_ASSET_SILENT", "FAULT_WITHOUT_WO",
             "WO_WITHOUT_FAULT", "WO_TIME_ANOMALY", "DUPLICATE_WO"]


def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def to_epoch(v):
    """ISO-8601 with Z / +hh:mm offset, or epoch milliseconds -> epoch seconds (UTC)."""
    if isinstance(v, (int, float)):
        return float(v) / 1000.0
    return dt.datetime.fromisoformat(v).timestamp()


def epoch_utc(s):
    return pd.to_datetime(s, unit="s", utc=True)


def day_str(day):
    return (dt.date(1970, 1, 1) + dt.timedelta(days=int(day))).isoformat()


def norm_id(v):
    m = NORM_RE.match(str(v or ""))
    return "EQ-%05d" % int(m.group(1)) if m else None


def norm_serial(v):
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def make_resolver(erp, xw):
    ids = set(erp["erp_asset_id"])
    by_serial = {norm_serial(s): i for s, i in zip(erp["serial_number"], erp["erp_asset_id"])}
    by_xw = {r.strip().upper(): i for r, i in zip(xw["legacy_ref"], xw["erp_asset_id"])}

    def resolve(ref, serial=""):
        n = norm_id(ref)
        if n in ids:
            return n, "EXACT_NORM"                      # 1. normalise 'eq07040', ' EQ-7040 ', '07040' ... -> EQ-07040
        s = norm_serial(serial)
        if s and s in by_serial:
            return by_serial[s], "SERIAL"               # 2. serial number match
        k = str(ref or "").strip().upper()
        if k in by_xw:
            return by_xw[k], "CROSSWALK"                # 3. legacy reference crosswalk
        return None, "UNRESOLVED"                       # 4. goes to the exception queue
    return resolve


def load_telematics(folders):
    recs = []
    for folder in folders:
        for f in sorted(glob.glob(os.path.join(folder, "telematics_*.jsonl*"))):
            with (gzip.open(f, "rt", encoding="utf-8") if f.endswith(".gz") else open(f, encoding="utf-8")) as fh:
                for ln in fh:
                    r = json.loads(ln)
                    r.update(r.pop("payload"))
                    recs.append(r)
    return pd.DataFrame(recs)


def silver_telemetry(raw, resolve, cutoff_epoch):
    df, st = raw.copy(), {"bronze_rows": len(raw)}
    for c in ("serial_no", "asset_ref", "coolant_level_pct"):
        if c not in df:
            df[c] = None
    df["ts_epoch"] = [to_epoch(v) for v in df["ts"]]
    df["ingest_epoch"] = [to_epoch(v) for v in df["ingest_ts"]]
    df = df.sort_values(["event_id", "ingest_epoch"], kind="stable").drop_duplicates("event_id", keep="first")
    st["duplicates_removed"] = st["bronze_rows"] - len(df)
    nulled = 0
    for col, (lo, hi) in SENSORS.items():
        bad = (df[col] < lo) | (df[col] > hi)
        nulled += int(bad.sum())
        df.loc[bad, col] = np.nan
    st["out_of_range_values_nulled"] = nulled
    ref, ser = df["asset_ref"].fillna("").astype(str).tolist(), df["serial_no"].fillna("").astype(str).tolist()
    cache = {k: resolve(*k) for k in set(zip(ref, ser))}
    keys = list(zip(ref, ser))
    df["erp_asset_id"] = [cache[k][0] for k in keys]
    df["resolution_method"] = [cache[k][1] for k in keys]
    df["is_late"] = (df["ingest_epoch"] - df["ts_epoch"]) > 3600
    df["is_in_window"] = df["ts_epoch"] < cutoff_epoch
    df = df.sort_values(["ts_epoch", "device_id"], kind="stable").reset_index(drop=True)
    df["event_ts_utc"] = epoch_utc(df["ts_epoch"])
    df["day"] = (df["ts_epoch"] // DAY).astype("int64")
    df["is_run"] = df["engine_state"] == "RUN"
    st["rows"] = len(df)
    st["late_rows"] = int((df["is_late"] & df["is_in_window"]).sum())
    st["by_resolution"] = {k: int(v) for k, v in df["resolution_method"].value_counts().sort_index().items()}
    return df, st


def local_to_epoch(s, tz):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(tz)).timestamp()


def silver_cmms(cmms, resolve, sites):
    df, st = cmms.copy(), {"bronze_rows": len(cmms)}
    tz = dict(zip(sites["site_code"], sites["timezone"]))
    df["opened_epoch"] = [local_to_epoch(s, tz[c]) for s, c in zip(df["opened_local"], df["site_code"])]
    df["closed_epoch"] = [local_to_epoch(s, tz[c]) if s else np.nan for s, c in zip(df["closed_local"], df["site_code"])]
    df["is_time_anomaly"] = df["closed_epoch"] < df["opened_epoch"]
    df["opened_fix"] = np.where(df["is_time_anomaly"], df["closed_epoch"], df["opened_epoch"])   # closed < opened => the two stamps were swapped
    df["closed_fix"] = np.where(df["is_time_anomaly"], df["opened_epoch"], df["closed_epoch"])
    res = [resolve(t, s) for t, s in zip(df["asset_tag"], df["serial_number"])]
    df["erp_asset_id"], df["resolution_method"] = [r[0] for r in res], [r[1] for r in res]
    df["is_duplicate"], df["duplicate_of"] = False, ""
    cm = df[(df["wo_type"] == "CM") & df["erp_asset_id"].notna()].sort_values(["erp_asset_id", "failure_code", "opened_fix", "wo_number"], kind="stable")
    prev_key = list(zip(cm["erp_asset_id"], cm["failure_code"]))
    last, prev_no, prev_t = None, "", 0.0
    for idx, key, t, no in zip(cm.index, prev_key, cm["opened_fix"], cm["wo_number"]):
        if key == last and t - prev_t <= DUP_WINDOW_S:
            df.loc[idx, ["is_duplicate", "duplicate_of"]] = [True, prev_no]       # keep the earliest WO as the primary
            continue
        last, prev_no, prev_t = key, no, t
    df["status_open"] = df["status"] == "Open"
    st.update(rows=len(df), unresolved=int((df["resolution_method"] == "UNRESOLVED").sum()), duplicates=int(df["is_duplicate"].sum()),
              time_anomalies=int(df["is_time_anomaly"].sum()), by_resolution={k: int(v) for k, v in df["resolution_method"].value_counts().sort_index().items()})
    return df, st


def iso(s):
    """tz-aware datetime Series -> 'YYYY-MM-DDTHH:MM:SSZ' strings ('' for NaT)."""
    return s.dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")


def build_dim_asset(erp, tel, cutoff_epoch):
    d = erp.copy()
    d["acquisition_cost_eur"] = pd.to_numeric(d["acquisition_cost_eur"])
    d["equipment_class_code"] = d["equipment_class"].map(CLASS_CODE)
    one = pd.Timestamp("1970-01-01")
    d["acq_day"] = (pd.to_datetime(d["acquisition_date"]) - one).dt.days
    d["retire_day"] = (pd.to_datetime(d["retirement_date"], errors="coerce") - one).dt.days
    d["asset_age_years"] = ((cutoff_epoch // DAY - d["acq_day"]) / 365.25).round(2)
    t = tel[tel["erp_asset_id"].notna() & tel["is_in_window"]]
    g = t.groupby("erp_asset_id").agg(device_id=("device_id", "first"), telemetry_rows=("event_id", "size"), first_epoch=("ts_epoch", "min"),
                                      last_epoch=("ts_epoch", "max"), last_engine_hours=("engine_hours", "last"))
    d = d.merge(g, left_on="erp_asset_id", right_index=True, how="left")
    d["telemetry_rows"] = d["telemetry_rows"].fillna(0).astype("int64")
    d["first_telemetry_utc"], d["last_telemetry_utc"] = iso(epoch_utc(d["first_epoch"])), iso(epoch_utc(d["last_epoch"]))
    return d


def fault_occurrences(tel, catalog):
    """One row per fault code carried by a resolved telemetry record (the 'exploded' fault_codes array)."""
    fx = tel.loc[tel["erp_asset_id"].notna() & tel["is_in_window"], ["erp_asset_id", "ts_epoch", "day", "fault_codes"]].explode("fault_codes")
    fx = fx.dropna(subset=["fault_codes"]).rename(columns={"fault_codes": "fault_code"})
    fx["severity"] = fx["fault_code"].map(dict(zip(catalog["fault_code"], catalog["severity"])))
    return fx


def build_episodes(tel, catalog):
    sev, system = dict(zip(catalog["fault_code"], catalog["severity"])), dict(zip(catalog["fault_code"], catalog["system"]))
    fx = fault_occurrences(tel, catalog).sort_values(["erp_asset_id", "fault_code", "ts_epoch"], kind="stable")
    new = ((fx["erp_asset_id"] != fx["erp_asset_id"].shift()) | (fx["fault_code"] != fx["fault_code"].shift())
           | ((fx["ts_epoch"] - fx["ts_epoch"].shift()) > EPISODE_GAP_S))            # same asset + code, gap > 24 h starts a new episode
    ep = fx.assign(ep=new.cumsum()).groupby("ep", sort=False).agg(erp_asset_id=("erp_asset_id", "first"), fault_code=("fault_code", "first"),
                                                                  start=("ts_epoch", "min"), end=("ts_epoch", "max"), n_records=("ts_epoch", "size"))
    ep = ep.sort_values(["start", "erp_asset_id", "fault_code"], kind="stable").reset_index(drop=True)
    ep.insert(0, "episode_id", ["EP-%06d" % (i + 1) for i in range(len(ep))])
    ep["severity"], ep["system"] = ep["fault_code"].map(sev), ep["fault_code"].map(system)
    ep["is_significant"] = (ep["severity"] == "CRIT") | ((ep["severity"] == "WARN") & (ep["n_records"] >= 3))   # candidates for reconciliation
    return ep


def build_fact_wo(wo):
    w = wo[wo["erp_asset_id"].notna() & ~wo["is_duplicate"]].copy()
    w["opened_utc"], w["closed_utc"] = epoch_utc(w["opened_fix"]), epoch_utc(w["closed_fix"])
    w["duration_hours"] = ((w["closed_fix"] - w["opened_fix"]) / 3600).round(2)
    for c in ("labor_hours", "parts_cost_eur"):
        w[c] = pd.to_numeric(w[c])
    return w.reset_index(drop=True)


def build_matches(ep, fw):
    e = ep.loc[ep["is_significant"], ["episode_id", "erp_asset_id", "fault_code", "system", "severity", "start", "end"]]
    c = fw.loc[fw["wo_type"] == "CM", ["wo_number", "erp_asset_id", "opened_fix", "failure_system"]]
    m = e.merge(c, on="erp_asset_id")
    m = m[(m["opened_fix"] >= m["start"] - MATCH_BEFORE_S) & (m["opened_fix"] <= m["end"] + MATCH_AFTER_S)].copy()
    m["delta_hours"] = ((m["opened_fix"] - m["start"]) / 3600).round(2)           # WO opened minus episode start (negative = WO first)
    m["same_system"] = m["system"] == m["failure_system"]
    m = m.assign(_abs=m["delta_hours"].abs()).sort_values(["episode_id", "_abs", "wo_number"], kind="stable")
    m["is_best_for_episode"] = ~m.duplicated("episode_id")
    return m.drop(columns="_abs").reset_index(drop=True)


def build_exceptions(tel, wo, dim, ep, match, fw, cutoff_epoch):
    site, out = dict(zip(dim["erp_asset_id"], dim["site_code"])), []

    def add(kind, sev, sub, asset, site_code, ref, when, n, detail):
        out.append(dict(exception_type=kind, severity=sev, subtype=sub, erp_asset_id=asset, site_code=site_code, reference_id=ref,
                        event_epoch=when, n_records=n, detail=detail))

    u = tel[(tel["resolution_method"] == "UNRESOLVED") & tel["is_in_window"]]
    for dev, g in u.groupby("device_id", sort=True):
        add("UNRESOLVED_ASSET_TELEMATICS", "MEDIUM", "", "", "", dev, g["ts_epoch"].min(), len(g),
            "asset_ref=%r matches no ERP asset, serial or crosswalk row" % (g["asset_ref"].iloc[0],))
    u = wo[wo["resolution_method"] == "UNRESOLVED"]
    for tag, g in u.groupby("asset_tag", sort=True):
        add("UNRESOLVED_ASSET_CMMS", "MEDIUM", "", "", g["site_code"].iloc[0], tag, g["opened_fix"].min(), len(g),
            "%d work order(s) carry an asset tag that matches nothing in ERP" % len(g))
    ret = dim[dim["status"].isin(["Retired", "Disposed"]) & dim["retire_day"].notna()].set_index("erp_asset_id")
    t = tel[tel["erp_asset_id"].isin(ret.index) & tel["is_in_window"]]
    t = t[t["day"] >= t["erp_asset_id"].map(ret["retire_day"])]
    for a, g in t.groupby("erp_asset_id", sort=True):
        add("RETIRED_ASSET_REPORTING", "MEDIUM", "", a, site[a], a, g["ts_epoch"].min(), len(g),
            "ERP status %s since %s but the device keeps sending data" % (ret.loc[a, "status"], ret.loc[a, "retirement_date"]))
    act = dim[(dim["status"] == "Active") & (dim["telematics_device_installed"] == "Y")]
    for a, last in zip(act["erp_asset_id"], act["last_epoch"]):
        if last != last:
            add("ACTIVE_ASSET_SILENT", "MEDIUM", "NO_LINKED_TELEMETRY", a, site[a], a, np.nan, 0, "ERP says a device is installed but no telemetry resolves to it")
        elif last < cutoff_epoch - SILENT_DAYS * DAY:
            add("ACTIVE_ASSET_SILENT", "MEDIUM", "STOPPED_REPORTING", a, site[a], a, last, 0, "no telemetry for %d days" % int((cutoff_epoch - last) // DAY))
    matched = set(match["episode_id"])
    for r in ep[ep["is_significant"] & ~ep["episode_id"].isin(matched) & (ep["end"] <= cutoff_epoch - MATCH_AFTER_S)].itertuples():
        add("FAULT_WITHOUT_WO", "HIGH" if r.severity == "CRIT" else "MEDIUM", r.severity, r.erp_asset_id, site[r.erp_asset_id], r.episode_id, r.start,
            r.n_records, "%s episode with no corrective work order within 7 days" % r.fault_code)
    cov = tel[tel["erp_asset_id"].notna() & tel["is_in_window"]].groupby("erp_asset_id")["ts_epoch"].max()
    wo_matched = set(match["wo_number"])
    for r in fw[(fw["wo_type"] == "CM") & ~fw["wo_number"].isin(wo_matched)].itertuples():
        sub = "NO_TELEMETRY" if r.erp_asset_id not in cov.index else "TELEMETRY_STOPPED" if cov[r.erp_asset_id] < r.opened_fix - DAY else "NO_FAULT_SIGNAL"
        add("WO_WITHOUT_FAULT", "LOW", sub, r.erp_asset_id, site[r.erp_asset_id], r.wo_number, r.opened_fix, 1, "corrective WO %s without a matching fault episode" % r.failure_code)
    for r in wo[wo["is_time_anomaly"]].itertuples():
        add("WO_TIME_ANOMALY", "LOW", "", "" if pd.isna(r.erp_asset_id) else r.erp_asset_id, r.site_code, r.wo_number, r.opened_fix, 1,
            "closed before opened in the CMMS (timestamps swapped)")
    for r in wo[wo["is_duplicate"]].itertuples():
        add("DUPLICATE_WO", "LOW", "", r.erp_asset_id, r.site_code, r.wo_number, r.opened_fix, 1, "duplicate of %s (same asset + failure code within 60 min)" % r.duplicate_of)
    x = pd.DataFrame(out)
    x["_o"] = x["exception_type"].map({k: i for i, k in enumerate(EXC_ORDER)})
    x = x.sort_values(["_o", "event_epoch", "reference_id"], kind="stable", na_position="last").drop(columns="_o").reset_index(drop=True)
    x["event_utc"] = iso(epoch_utc(x["event_epoch"]))
    x.insert(0, "exception_id", ["EXC-%05d" % (i + 1) for i in range(len(x))])
    return x


BASE_COLS = ["temp_mean", "temp_max", "oil_mean", "oil_min", "hyd_mean", "hyd_min", "vib_mean", "vib_max", "fuel_mean", "load_mean", "idle_mean",
             "n_readings", "run_share", "engine_hours"]
FEATURES = (BASE_COLS + ["warn_cnt_1d", "crit_cnt_1d", "warn_cnt_7d", "crit_cnt_7d", "warn_cnt_14d"]
            + ["%s_mean_%dd" % (s, n) for s in ("temp", "oil", "hyd", "vib") for n in (3, 7, 14)]
            + ["%s_trend" % s for s in ("temp", "oil", "hyd", "vib")] + ["temp_max_7d", "vib_max_7d"]
            + ["days_since_last_pm", "days_since_last_cm", "cm_count_90d", "equipment_class_code", "asset_age_years"])
HORIZON = 7
SPLIT_STARTS = [("2026-04-01", "warmup"), ("2026-04-15", "train"), ("2026-07-25", "gap"), ("2026-08-01", "valid"), ("2026-08-25", "gap"),
                ("2026-09-01", "test"), ("2026-09-24", "unlabeled"), ("2026-09-30", "score")]


def to_day(iso_date):
    return (dt.date.fromisoformat(iso_date) - dt.date(1970, 1, 1)).days


def build_daily(tel, dim):
    """fact_telemetry_daily: one row per asset-day (resolved telemetry). Sensor aggregates use RUN readings only."""
    t, keys = tel[tel["erp_asset_id"].notna() & tel["is_in_window"]], ["erp_asset_id", "day"]
    allr = t.groupby(keys).agg(n_readings=("event_id", "size"), n_run=("is_run", "sum"), engine_hours=("engine_hours", "max"))
    run = t[t["is_run"]].groupby(keys).agg(temp_mean=("engine_temp_c", "mean"), temp_max=("engine_temp_c", "max"), oil_mean=("oil_pressure_kpa", "mean"),
                                           oil_min=("oil_pressure_kpa", "min"), hyd_mean=("hydraulic_pressure_bar", "mean"), hyd_min=("hydraulic_pressure_bar", "min"),
                                           vib_mean=("vibration_mm_s", "mean"), vib_max=("vibration_mm_s", "max"), fuel_mean=("fuel_rate_lph", "mean"),
                                           load_mean=("load_pct", "mean"), idle_mean=("idle_pct", "mean"))
    d = allr.join(run, how="left").reset_index()
    d["run_share"] = d["n_run"] / d["n_readings"]
    retire = d["erp_asset_id"].map(dict(zip(dim["erp_asset_id"], dim["retire_day"])))
    d["is_after_retirement"] = (retire.notna() & (d["day"] >= retire)).astype(bool)
    names = {x: day_str(x) for x in d["day"].unique()}
    d.insert(1, "obs_date", d["day"].map(names))
    return d.sort_values(["erp_asset_id", "day"]).reset_index(drop=True)


def since(arr, days):
    """Days elapsed since the last event on or before each day (NaN before the first one)."""
    if arr is None:
        return np.full(len(days), np.nan)
    i = np.searchsorted(arr, days, side="right") - 1
    return np.where(i >= 0, days - arr[np.maximum(i, 0)], np.nan)


def count_in(arr, lo, hi):
    """Number of events with lo <= day <= hi."""
    return np.zeros(len(hi), dtype="int64") if arr is None else np.searchsorted(arr, hi, side="right") - np.searchsorted(arr, lo, side="left")


def build_features(daily, fw, dim, occ, cutoff_epoch):
    """ml_asset_day_features: calendar-window features known at the END of obs_date + the 7-day failure label."""
    w = fw.assign(wday=(fw["opened_fix"] // DAY).astype("int64"))
    pm = {a: np.sort(g["wday"].to_numpy()) for a, g in w[w["wo_type"] == "PM"].groupby("erp_asset_id")}
    cm = {a: np.sort(g["wday"].to_numpy()) for a, g in w[w["wo_type"] == "CM"].groupby("erp_asset_id")}
    cnt = occ[occ["severity"].isin(["WARN", "CRIT"])].groupby(["erp_asset_id", "day", "severity"]).size().unstack("severity", fill_value=0)
    for s in ("WARN", "CRIT"):
        if s not in cnt:
            cnt[s] = 0
    faults = {a: g.droplevel(0) for a, g in cnt.groupby(level=0)}
    static, last_label_day = dim.set_index("erp_asset_id"), cutoff_epoch // DAY - 1 - HORIZON
    out = []
    for asset, g in daily[~daily["is_after_retirement"]].groupby("erp_asset_id", sort=True):
        cal = pd.RangeIndex(int(g["day"].min()), int(g["day"].max()) + 1, name="day")        # complete calendar: windows are CALENDAR days
        f, days = g.set_index("day").reindex(cal), cal.to_numpy()
        o = f[BASE_COLS].copy()
        fc = faults[asset].reindex(cal, fill_value=0) if asset in faults else pd.DataFrame(0, index=cal, columns=["WARN", "CRIT"])
        for sev in ("WARN", "CRIT"):
            o[sev.lower() + "_cnt_1d"] = fc[sev]
            o[sev.lower() + "_cnt_7d"] = fc[sev].rolling(7, min_periods=1).sum()
        o["warn_cnt_14d"] = fc["WARN"].rolling(14, min_periods=1).sum()
        for tag in ("temp", "oil", "hyd", "vib"):
            for n in (3, 7, 14):
                o["%s_mean_%dd" % (tag, n)] = f[tag + "_mean"].rolling(n, min_periods=1).mean()          # NaN-aware: OFF days carry no sensor value
            o[tag + "_trend"] = o[tag + "_mean_3d"] - o[tag + "_mean_14d"]
        o["temp_max_7d"], o["vib_max_7d"] = f["temp_max"].rolling(7, min_periods=1).max(), f["vib_max"].rolling(7, min_periods=1).max()
        o["days_since_last_pm"], o["days_since_last_cm"] = since(pm.get(asset), days), since(cm.get(asset), days)
        o["cm_count_90d"] = count_in(cm.get(asset), days - 89, days)
        o["equipment_class_code"] = CLASS_CODE[static.at[asset, "equipment_class"]]
        o["asset_age_years"] = (days - static.at[asset, "acq_day"]) / 365.25
        ahead = count_in(cm.get(asset), days + 1, days + HORIZON)                              # a CM work order opened in [d+1, d+7]
        o["fail_next_7d"] = np.where(days <= last_label_day, (ahead > 0).astype(float), np.nan)
        o.insert(0, "erp_asset_id", asset)
        out.append(o[f["n_readings"].notna().to_numpy()].reset_index())
    x = pd.concat(out, ignore_index=True)
    starts = np.array([to_day(s) for s, _ in SPLIT_STARTS])
    x["split"] = np.array([n for _, n in SPLIT_STARTS])[np.searchsorted(starts, x["day"].to_numpy(), side="right") - 1]
    names = {d: day_str(d) for d in x["day"].unique()}
    x.insert(1, "obs_date", x["day"].map(names))
    return x[["erp_asset_id", "obs_date", "day"] + FEATURES + ["fail_next_7d", "split"]]


NO_FAULT_FEATURES = [c for c in FEATURES if not c.startswith(("warn_cnt", "crit_cnt"))]
HIGH_RISK, MEDIUM_RISK, MODEL_VERSION = 0.30, 0.10, "ref-hgb-v1"


def make_model(kind):
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    if kind == "prevalence":
        return DummyClassifier(strategy="prior")
    if kind == "logistic_regression":
        return make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(), LogisticRegression(C=0.5, max_iter=2000))
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06, max_leaf_nodes=24, l2_regularization=1.0, early_stopping=False, random_state=0)


def rule_flag(d):
    """The 'no ML' baseline the maintenance team could write in an afternoon."""
    return ((d["crit_cnt_7d"] > 0) | (d["warn_cnt_7d"] >= 2)).astype(float).to_numpy()


def eval_scores(y, s, binary=False):
    from sklearn.metrics import average_precision_score, roc_auc_score
    y, s = np.asarray(y, dtype=float), np.asarray(s, dtype=float)
    r = {"rows": int(len(y)), "positives": int(y.sum()), "prevalence": round(float(y.mean()), 4),
         "pr_auc": round(float(average_precision_score(y, s)), 4), "roc_auc": round(float(roc_auc_score(y, s)), 4)}
    if binary:
        hit = s > 0
        r.update(flag_rate=round(float(hit.mean()), 4), precision=round(float(y[hit].mean()), 4) if hit.any() else 0.0, recall=round(float(y[hit].sum() / y.sum()), 4))
    else:
        top = np.argsort(-s, kind="stable")[: max(1, int(round(0.05 * len(y))))]                  # the 5% riskiest asset-days
        r.update(precision_at_top5pct=round(float(y[top].mean()), 4), recall_at_top5pct=round(float(y[top].sum() / y.sum()), 4))
    return r


def reason_codes(s):
    """Rule-based 'why is it flagged' labels (readable by a maintenance planner; these are NOT model attributions)."""
    rules = [("CRIT_FAULT_7D", s["crit_cnt_7d"] >= 1), ("REPEATED_WARNINGS", s["warn_cnt_7d"] >= 3), ("ENGINE_TEMP_RISING", s["temp_trend"] >= 3.0),
             ("OIL_PRESSURE_FALLING", s["oil_trend"] <= -10.0), ("HYDRAULIC_PRESSURE_FALLING", s["hyd_trend"] <= -8.0),
             ("VIBRATION_RISING", s["vib_trend"] >= 0.3), ("PM_OVERDUE", s["days_since_last_pm"] >= 90)]
    flags = np.column_stack([m.to_numpy() for _, m in rules])
    out = []
    for row in flags:
        names = [n for (n, _), on in zip(rules, row) if on][:3]
        out.append(";".join(names) or "NO_STRONG_SIGNAL")
    return out


def run_ml(F, dim):
    sp = {s: F[F["split"] == s] for s in ("train", "valid", "test")}
    metrics = {}
    for name, cols in (("prevalence", FEATURES), ("logistic_regression", FEATURES), ("hist_gradient_boosting", FEATURES),
                       ("hist_gradient_boosting_no_fault_codes", NO_FAULT_FEATURES)):
        m = make_model(name.replace("_no_fault_codes", "")).fit(sp["train"][cols], sp["train"]["fail_next_7d"])
        metrics[name] = {s: eval_scores(sp[s]["fail_next_7d"], m.predict_proba(sp[s][cols])[:, 1]) for s in ("valid", "test")}
    metrics["rule_baseline"] = {s: eval_scores(sp[s]["fail_next_7d"], rule_flag(sp[s]), binary=True) for s in ("valid", "test")}
    lab = F[F["split"].isin(["train", "gap", "valid", "test"])]                                   # final refit: every labelled day after the warm-up
    final = make_model("hist_gradient_boosting").fit(lab[FEATURES], lab["fail_next_7d"])
    s = F[F["split"] == "score"].copy()
    s["risk_score"] = final.predict_proba(s[FEATURES])[:, 1]
    s["risk_band"] = np.where(s["risk_score"] >= HIGH_RISK, "High", np.where(s["risk_score"] >= MEDIUM_RISK, "Medium", "Low"))
    s["top_drivers"] = reason_codes(s)
    a = dim.set_index("erp_asset_id")
    s["site_code"], s["equipment_class"] = s["erp_asset_id"].map(a["site_code"]), s["erp_asset_id"].map(a["equipment_class"])
    s = s.sort_values(["risk_score", "erp_asset_id"], ascending=[False, True], kind="stable").reset_index(drop=True)
    s["risk_rank"], s["risk_score"] = np.arange(1, len(s) + 1), s["risk_score"].round(4)
    s["score_date"], s["model_version"] = s["obs_date"], MODEL_VERSION
    return metrics, s[["score_date", "erp_asset_id", "site_code", "equipment_class", "risk_score", "risk_band", "risk_rank", "top_drivers", "model_version"]]


def psi(ref, cur, bins=10):
    """Population Stability Index against the reference deciles: < 0.10 stable, 0.10-0.25 moderate shift, > 0.25 major shift."""
    ref, cur = ref[~np.isnan(ref)], cur[~np.isnan(cur)]
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r, c = (np.clip(np.histogram(x, edges)[0] / len(x), 1e-4, None) for x in (ref, cur))
    return float(np.sum((c - r) * np.log(c / r)))


def drift_report(tel, new, dim, ref_from="2026-09-01"):
    """Sensor drift of a NEW batch (RUN readings) against September, per equipment class and sensor."""
    cls = dict(zip(dim["erp_asset_id"], dim["equipment_class"]))
    ref = tel[tel["is_run"] & tel["erp_asset_id"].notna() & tel["is_in_window"] & (tel["day"] >= to_day(ref_from))]
    cur = new[new["is_run"] & new["erp_asset_id"].notna()]
    rows = []
    for c in sorted(set(cls.values())):
        r, n = ref[ref["erp_asset_id"].map(cls) == c], cur[cur["erp_asset_id"].map(cls) == c]
        for sensor in ("engine_temp_c", "oil_pressure_kpa", "hydraulic_pressure_bar", "vibration_mm_s", "fuel_rate_lph", "load_pct"):
            a, b = r[sensor].to_numpy(dtype=float), n[sensor].to_numpy(dtype=float)
            if np.isnan(a).all() or np.isnan(b).all():
                continue
            v = psi(a, b)
            rows.append(dict(equipment_class=c, sensor=sensor, psi=round(v, 4), ref_mean=round(float(np.nanmean(a)), 3), new_mean=round(float(np.nanmean(b)), 3),
                             ref_rows=int(len(r)), new_rows=int(len(n)), status="major" if v > 0.25 else "moderate" if v > 0.10 else "stable"))
    return pd.DataFrame(rows)


def finalize_episodes(ep, match, dim, cutoff_epoch):
    e = ep.copy()
    matched, closed = set(match["episode_id"]), e["end"] <= cutoff_epoch - MATCH_AFTER_S      # closed = the 7-day matching window is over
    e["recon_status"] = np.where(~e["is_significant"], "NOT_APPLICABLE", np.where(e["episode_id"].isin(matched), "MATCHED", np.where(closed, "UNMATCHED", "PENDING")))
    e["matched_wo_number"] = e["episode_id"].map(match[match["is_best_for_episode"]].set_index("episode_id")["wo_number"]).fillna("")
    e["site_code"] = e["erp_asset_id"].map(dict(zip(dim["erp_asset_id"], dim["site_code"])))
    e["start_utc"], e["end_utc"] = iso(epoch_utc(e["start"])), iso(epoch_utc(e["end"]))
    e["month"] = e["start_utc"].str[:7]
    return e


def build_summary(ep_f, fw, match):
    """agg_recon_monthly - one row per month x site: how well do fault episodes (telematics) and work orders (CMMS) agree?"""
    e = ep_f[ep_f["is_significant"]].copy()
    crit, warn, st = e["severity"] == "CRIT", e["severity"] == "WARN", e["recon_status"]
    cols = {"crit_episodes": crit, "crit_matched": crit & (st == "MATCHED"), "crit_unmatched": crit & (st == "UNMATCHED"), "crit_pending": crit & (st == "PENDING"),
            "warn_episodes_3plus": warn, "warn_matched": warn & (st == "MATCHED"), "warn_unmatched": warn & (st == "UNMATCHED")}
    for name, mask in cols.items():
        e[name] = mask.astype(int)
    delta = match[match["is_best_for_episode"]].set_index("episode_id")["delta_hours"]
    e["crit_delta"] = np.where(crit, e["episode_id"].map(delta), np.nan)
    key = ["month", "site_code"]
    a = e.groupby(key).agg(**{c: (c, "sum") for c in cols}, avg_crit_fault_to_wo_hours=("crit_delta", "mean"))
    w = fw[fw["wo_type"] == "CM"].copy()
    w["month"], w["with_fault"] = iso(w["opened_utc"]).str[:7], w["wo_number"].isin(set(match["wo_number"])).astype(int)
    b = w.groupby(key).agg(cm_work_orders=("wo_number", "size"), cm_wo_with_fault_signal=("with_fault", "sum"), cm_repair_hours=("duration_hours", "sum"))
    s = a.join(b, how="outer").reset_index()
    ints = [c for c in list(cols) + ["cm_work_orders", "cm_wo_with_fault_signal"]]
    s[ints] = s[ints].fillna(0).astype("int64")
    den = s["crit_matched"] + s["crit_unmatched"]                               # PENDING episodes are not judged yet
    s["crit_match_rate"] = np.where(den > 0, s["crit_matched"] / den.where(den > 0, 1), np.nan).round(4)
    s["cm_wo_without_fault_signal"] = s["cm_work_orders"] - s["cm_wo_with_fault_signal"]
    s["avg_crit_fault_to_wo_hours"], s["cm_repair_hours"] = s["avg_crit_fault_to_wo_hours"].round(2), s["cm_repair_hours"].fillna(0).round(2)
    return s[["month", "site_code", "crit_episodes", "crit_matched", "crit_unmatched", "crit_pending", "crit_match_rate", "warn_episodes_3plus", "warn_matched",
              "warn_unmatched", "cm_work_orders", "cm_wo_with_fault_signal", "cm_wo_without_fault_signal", "avg_crit_fault_to_wo_hours", "cm_repair_hours"]]


def export_tables(dim, sites, daily, ep_f, fw, match, exc, F, risk, summary):
    """The gold layer as the demos see it (table name -> DataFrame with final columns)."""
    a = dim.copy()
    a["has_telemetry"] = a["telemetry_rows"] > 0
    a = a[["erp_asset_id", "asset_name", "equipment_class", "equipment_class_code", "manufacturer", "model", "serial_number", "acquisition_date", "acquisition_cost_eur",
           "site_code", "cost_center", "status", "retirement_date", "telematics_device_installed", "device_id", "has_telemetry", "telemetry_rows",
           "first_telemetry_utc", "last_telemetry_utc", "last_engine_hours", "asset_age_years"]]
    site = sites[["site_code", "site_name", "country", "timezone", "latitude", "longitude", "project_type"]].copy()
    sitemap = dict(zip(dim["erp_asset_id"], dim["site_code"]))
    d = daily.drop(columns="day").round(3)
    d.insert(1, "site_code", d["erp_asset_id"].map(sitemap))
    ep = ep_f[["episode_id", "erp_asset_id", "site_code", "fault_code", "system", "severity", "start_utc", "end_utc", "n_records", "is_significant", "recon_status",
               "matched_wo_number", "month"]]
    w = fw.copy()
    w["site_code"] = w["erp_asset_id"].map(sitemap)
    w["opened_utc"], w["closed_utc"] = iso(w["opened_utc"]), iso(w["closed_utc"])
    w = w.rename(columns={"resolution_method": "id_resolution", "is_time_anomaly": "times_corrected"})
    w = w[["wo_number", "erp_asset_id", "site_code", "wo_type", "priority", "status", "failure_code", "failure_system", "description", "opened_utc", "closed_utc",
           "duration_hours", "labor_hours", "parts_cost_eur", "technician_id", "reported_by", "id_resolution", "times_corrected"]]
    m = match[["episode_id", "wo_number", "erp_asset_id", "delta_hours", "same_system", "is_best_for_episode"]]
    x = exc[["exception_id", "exception_type", "subtype", "severity", "erp_asset_id", "site_code", "reference_id", "event_utc", "n_records", "detail"]]
    tables = {"dim_asset": a, "dim_site": site, "fact_telemetry_daily": d, "fact_fault_episode": ep, "fact_work_order": w, "fact_recon_match": m,
              "fact_recon_exception": x, "agg_recon_monthly": summary}
    if F is not None:                                                                            # absent with --skip-ml
        f = F.drop(columns="day").copy()
        f[FEATURES] = f[FEATURES].round(4)
        tables.update(ml_asset_day_features=f, ml_failure_risk_score=risk)
    return tables


def write_tables(tables, out):
    os.makedirs(out, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(os.path.join(out, name + ".csv"), index=False, lineterminator="\n")


def truth_checks(tel, wo, exc, ep_f, truth_dir, cutoff_epoch):
    """Compare the pipeline with the generator's hidden truth. Every deterministic check must be exact (ok=True)."""
    ta, tw, tf = (read_csv(os.path.join(truth_dir, n)) for n in ("truth_assets.csv", "truth_work_orders.csv", "truth_failures.csv"))
    res = {}

    def check(name, ok, **detail):
        res[name] = dict(ok=bool(ok), **detail)

    d = tel[["device_id", "erp_asset_id", "resolution_method"]].drop_duplicates().fillna({"erp_asset_id": ""})
    j = ta[ta["device_id"] != ""].merge(d, on="device_id", how="left", suffixes=("_truth", ""))
    good = ((j["resolution_method"] == j["expected_resolution"]) & ((j["expected_resolution"] == "UNRESOLVED") | (j["erp_asset_id_truth"] == j["erp_asset_id"])))
    check("telematics_id_resolution", d["device_id"].is_unique and good.all(), devices=int(len(j)), correct=int(good.sum()))
    k = wo.merge(tw, on="wo_number", suffixes=("", "_truth"))
    good = ((k["resolution_method"] == k["expected_resolution"]) & ((k["expected_resolution"] == "UNRESOLVED") | (k["erp_asset_id"] == k["true_erp_asset_id"])))
    check("cmms_id_resolution", len(k) == len(wo) and good.all(), work_orders=int(len(k)), correct=int(good.sum()))
    err = (k["opened_fix"] - k["true_opened_utc"].map(to_epoch)).abs()
    check("cmms_local_time_to_utc", err.max() <= 60, work_orders=int(len(k)), max_error_seconds=float(err.max()))
    check("cmms_duplicates", set(wo.loc[wo["is_duplicate"], "wo_number"]) == set(tw.loc[tw["duplicate_of"] != "", "wo_number"]), detected=int(wo["is_duplicate"].sum()))
    check("cmms_time_anomalies", set(wo.loc[wo["is_time_anomaly"], "wo_number"]) == set(tw.loc[tw["time_anomaly"] == "1", "wo_number"]), detected=int(wo["is_time_anomaly"].sum()))
    got = exc.groupby(["exception_type", "subtype"]).size().to_dict()
    want = {("UNRESOLVED_ASSET_TELEMATICS", ""): int(((ta["expected_resolution"] == "UNRESOLVED") & (ta["device_id"] != "")).sum()),      # typo-tier + 4 rental units
            ("UNRESOLVED_ASSET_CMMS", ""): int((ta["cmms_legacy_mode"] == "unresolved").sum()),
            ("RETIRED_ASSET_REPORTING", ""): int((ta["zombie"] == "1").sum()),
            ("ACTIVE_ASSET_SILENT", "STOPPED_REPORTING"): int((ta["silent"] == "1").sum()),
            ("ACTIVE_ASSET_SILENT", "NO_LINKED_TELEMETRY"): int((ta["tier"] == "typo").sum()),
            ("WO_TIME_ANOMALY", ""): int((tw["time_anomaly"] == "1").sum()), ("DUPLICATE_WO", ""): int((tw["duplicate_of"] != "").sum())}
    check("deterministic_exceptions", all(got.get(key, 0) == n for key, n in want.items()), expected={"%s|%s" % key: n for key, n in want.items()},
          actual={"%s|%s" % key: int(got.get(key, 0)) for key in want})
    silent = tf[(tf["never_reached_cmms"] == "1") & (tf["crit_code_at_failure"] == "1") & (tf["in_window"] == "1")].copy()
    silent["t"] = silent["failure_utc"].map(to_epoch)
    silent = silent[silent["t"] <= cutoff_epoch - MATCH_AFTER_S - DAY]
    fx = exc[(exc["exception_type"] == "FAULT_WITHOUT_WO") & (exc["subtype"] == "CRIT")].merge(ep_f[["episode_id", "start"]], left_on="reference_id", right_on="episode_id")
    by_asset = {a: g["t"].to_numpy() for a, g in silent.groupby("erp_asset_id")}
    near = lambda a, s: any(abs(s - t) <= 2 * DAY for t in by_asset.get(a, []))                            # within 2 days of a truly unreported failure
    tp = sum(near(a, s) for a, s in zip(fx["erp_asset_id"], fx["start"]))
    seen = sum(any(abs(r - t) <= 2 * DAY for r in fx.loc[fx["erp_asset_id"] == a, "start"]) for a, ts in by_asset.items() for t in ts)
    check("unreported_failures_found", True, informational=True, crit_fault_without_wo=int(len(fx)), explained_by_truth=int(tp),
          precision=round(tp / max(len(fx), 1), 3), truly_unreported_with_crit_code=int(len(silent)), found=int(seen), recall=round(seen / max(len(silent), 1), 3))
    return res


def class_counts(s):
    return {str(k): int(v) for k, v in s.value_counts().sort_index().items()}


def build_ground_truth(man, st_tel, st_cmms, tables, ep_f, match, exc, F, metrics, risk, drift, checks):
    gt = {"pipeline": {"script": "fleet_reference_pipeline.py", "python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__},
          "data": {"seed": man["params"]["seed"], "window": man["window"], "file_sha256": {k: v["sha256"] for k, v in man["files"].items()}},
          "silver": {"telematics": st_tel, "cmms": st_cmms},
          "gold_row_counts": {k: int(len(v)) for k, v in tables.items()},
          "assets": {"by_status": class_counts(tables["dim_asset"]["status"]), "by_class": class_counts(tables["dim_asset"]["equipment_class"]),
                     "with_telemetry": int(tables["dim_asset"]["has_telemetry"].sum()), "active_with_telemetry": int((tables["dim_asset"]["has_telemetry"] & (tables["dim_asset"]["status"] == "Active")).sum())}}
    sig = ep_f[ep_f["is_significant"]]
    crit = sig[sig["severity"] == "CRIT"]
    gt["reconciliation"] = {
        "fault_episodes": int(len(ep_f)), "by_severity": class_counts(ep_f["severity"]), "significant_episodes": int(len(sig)), "recon_status": class_counts(sig["recon_status"]),
        "crit_recon_status": class_counts(crit["recon_status"]),
        "crit_match_rate": round(float((crit["recon_status"] == "MATCHED").sum() / max(((crit["recon_status"] != "PENDING")).sum(), 1)), 4),
        "match_rows": int(len(match)), "episodes_with_a_match": int(match["episode_id"].nunique()),
        "cm_work_orders": int((tables["fact_work_order"]["wo_type"] == "CM").sum()), "cm_work_orders_matched": int(match["wo_number"].nunique()),
        "median_crit_fault_to_wo_hours": round(float(match[match["is_best_for_episode"] & match["episode_id"].isin(crit["episode_id"])]["delta_hours"].median()), 2)}
    gt["exceptions"] = {"total": int(len(exc)), "by_type": class_counts(exc["exception_type"]),
                        "by_type_and_subtype": {"%s|%s" % k: int(v) for k, v in exc.groupby(["exception_type", "subtype"]).size().items()}}
    if metrics is not None:
        import sklearn
        lab = F[F["fail_next_7d"].notna()]
        gt["ml"] = {"features": FEATURES, "feature_count": len(FEATURES), "label": "fail_next_7d = a non-duplicate CM work order opened in [d+1, d+7] (UTC days)",
                    "rows": int(len(F)), "labelled_rows": int(len(lab)), "positive_rate_labelled": round(float(lab["fail_next_7d"].mean()), 4),
                    "by_split": {s: {"rows": int(len(g)), "positives": int(g["fail_next_7d"].sum()), "first": g["obs_date"].min(), "last": g["obs_date"].max()}
                                 for s, g in F.groupby("split", sort=False)},
                    "metrics_approximate": metrics, "model_seed": 0, "sklearn": sklearn.__version__}
        gt["risk_scoring"] = {"score_date": risk["score_date"].iloc[0], "assets_scored": int(len(risk)), "bands": class_counts(risk["risk_band"]), "model_version": MODEL_VERSION,
                              "thresholds": {"High": HIGH_RISK, "Medium": MEDIUM_RISK},
                              "top10": [dict(rank=int(r.risk_rank), erp_asset_id=r.erp_asset_id, site_code=r.site_code, equipment_class=r.equipment_class,
                                             risk_score=float(r.risk_score), risk_band=r.risk_band, top_drivers=r.top_drivers) for r in risk.head(10).itertuples()]}
    if drift is not None:
        def shifted(status):
            return [dict(equipment_class=r.equipment_class, sensor=r.sensor, psi=r.psi) for r in drift[drift["status"] == status].itertuples()]
        gt["drift"] = {"reference": "September 2026 RUN readings", "new_batch": "2026-10-01 .. 2026-10-14", "combinations": int(len(drift)),
                       "major_shift": shifted("major"), "moderate_shift": shifted("moderate"),
                       "note": "major = injected sensor shift (Excavator, WheelLoader); moderate engine_temp_c = seasonal ambient cooling, expected"}
    if checks is not None:
        gt["truth_checks"] = checks
    return gt


def top_keys(s):
    """Index labels holding the maximum (all of them when tied)."""
    return sorted(s[s == s.max()].index)


def build_agent_eval(t):
    """Question/answer pairs for the Part 4 agent. Every expected answer is computed from the gold tables - none is typed by hand."""
    A, EP, WO, M, X, SUM = (t[k] for k in ("dim_asset", "fact_fault_episode", "fact_work_order", "fact_recon_match", "fact_recon_exception", "agg_recon_monthly"))
    R, name, qs = t.get("ml_failure_risk_score"), dict(zip(t["dim_site"]["site_code"], t["dim_site"]["site_name"])), []

    def q(kind, level, question, answer, values, tables, frozen=False):
        qs.append(dict(id="Q%02d" % (len(qs) + 1), type=kind, difficulty=level, question=question, expected_answer=answer, expected_values=values,
                       tables=tables, depends_on_frozen_scores=frozen))

    def exc(kind, sub=None):
        x = X[X["exception_type"] == kind]
        return x if sub is None else x[x["subtype"] == sub]

    ids = lambda df: sorted(df["reference_id"].astype(str).unique())
    st, by = A["status"].value_counts(), X["exception_type"].value_counts().sort_index()
    q("count", "easy", "How many equipment assets are registered in the ERP, and how many are Active, Retired and Disposed?",
      "%d assets: %d Active, %d Retired, %d Disposed." % (len(A), st["Active"], st["Retired"], st["Disposed"]),
      {"total": len(A), "Active": st["Active"], "Retired": st["Retired"], "Disposed": st["Disposed"]}, ["dim_asset"])
    q("count", "easy", "How many reconciliation exceptions are open in total, and how many are there per exception type?",
      "%d exceptions: %s." % (len(X), ", ".join("%s %d" % kv for kv in by.items())), dict(total=len(X), **by.to_dict()), ["fact_recon_exception"])
    crit_un = EP[(EP["severity"] == "CRIT") & (EP["recon_status"] == "UNMATCHED")]
    q("count", "easy", "How many CRIT fault episodes were never followed by a corrective work order within 7 days (data cutoff 2026-10-01)?",
      "%d CRIT fault episodes (exception FAULT_WITHOUT_WO, subtype CRIT)." % len(crit_un), {"count": len(crit_un)}, ["fact_fault_episode", "fact_recon_exception"])
    dup = exc("DUPLICATE_WO")
    pairs = {r.reference_id: r.detail.split()[2] for r in dup.itertuples()}
    q("list", "easy", "Which CMMS work orders are duplicates of another work order, and which work order does each one duplicate?",
      "%d duplicates: %s." % (len(dup), "; ".join("%s duplicates %s" % kv for kv in pairs.items())), {"count": len(dup), "duplicate_of": pairs}, ["fact_recon_exception"])
    ano = exc("WO_TIME_ANOMALY")
    q("list", "easy", "Which work orders were closed before they were opened (swapped timestamps in the CMMS)?", "%d work orders: %s." % (len(ano), ", ".join(ids(ano))),
      {"count": len(ano), "work_orders": ids(ano)}, ["fact_recon_exception"])
    zom = exc("RETIRED_ASSET_REPORTING")
    q("list", "medium", "Which Retired or Disposed assets are still sending telemetry after their retirement date?", "%d assets: %s." % (len(zom), ", ".join(ids(zom))),
      {"count": len(zom), "assets": ids(zom)}, ["fact_recon_exception", "dim_asset"])
    sil, nol = exc("ACTIVE_ASSET_SILENT", "STOPPED_REPORTING"), exc("ACTIVE_ASSET_SILENT", "NO_LINKED_TELEMETRY")
    q("list", "medium", "Which Active assets have a telematics device installed but sent nothing for more than %d days, and which were never linked to any telemetry?" % SILENT_DAYS,
      "Stopped reporting (%d): %s. Never linked (%d): %s." % (len(sil), ", ".join(ids(sil)), len(nol), ", ".join(ids(nol))),
      {"stopped_reporting": ids(sil), "never_linked": ids(nol)}, ["fact_recon_exception", "dim_asset"])
    ud = exc("UNRESOLVED_ASSET_TELEMATICS")
    q("list", "medium", "Which telematics devices cannot be linked to any ERP asset, and how many telemetry records did each of them send?",
      "%d devices: %s." % (len(ud), "; ".join("%s (%d records)" % (r.reference_id, r.n_records) for r in ud.itertuples())),
      {"count": len(ud), "records_per_device": {r.reference_id: r.n_records for r in ud.itertuples()}}, ["fact_recon_exception"])
    uc = exc("UNRESOLVED_ASSET_CMMS")
    q("count", "medium", "How many CMMS work orders carry an asset tag that matches nothing in the ERP, and how many distinct tags is that?",
      "%d work orders with %d distinct unknown tags (%s)." % (uc["n_records"].sum(), len(uc), ", ".join(ids(uc))),
      {"work_orders": uc["n_records"].sum(), "distinct_tags": len(uc), "tags": ids(uc)}, ["fact_recon_exception"])
    g = crit_un.groupby("site_code").size()
    q("agg", "medium", "Which site has the most CRIT fault episodes without a corrective work order?",
      "%s with %d episodes." % (" and ".join("%s (%s)" % (s, name[s]) for s in top_keys(g)), g.max()), {"sites": top_keys(g), "count": g.max()}, ["fact_fault_episode", "dim_site"])
    mt, un = int(SUM["crit_matched"].sum()), int(SUM["crit_unmatched"].sum())
    q("agg", "medium", "What is the overall CRIT match rate - the share of judged CRIT fault episodes (matched plus unmatched, pending ones excluded) that have a corrective work order?",
      "%.1f%% (%d matched, %d unmatched)." % (100 * mt / (mt + un), mt, un),
      {"rate_percent": round(100 * mt / (mt + un), 1), "matched": mt, "unmatched": un, "tolerance_percent": 0.1}, ["agg_recon_monthly"])
    mo = SUM.groupby("month")[["crit_matched", "crit_unmatched"]].sum()
    rate = (mo["crit_matched"] / (mo["crit_matched"] + mo["crit_unmatched"])).dropna()
    q("agg", "medium", "In which month was the CRIT match rate the lowest, and what was it?", "%s with %.1f%%." % (rate.idxmin(), 100 * rate.min()),
      {"month": rate.idxmin(), "rate_percent": round(100 * rate.min(), 1), "tolerance_percent": 0.1}, ["agg_recon_monthly"])
    big = SUM.sort_values(["crit_episodes", "month", "site_code"], ascending=[False, True, True]).iloc[0]
    q("lookup", "medium", "At site %s in %s, how many CRIT fault episodes were there and what was the CRIT match rate?" % (big["site_code"], big["month"]),
      "%d CRIT episodes: %d matched, %d unmatched, %d pending; match rate %.1f%%." % (big["crit_episodes"], big["crit_matched"], big["crit_unmatched"], big["crit_pending"], 100 * big["crit_match_rate"]),
      {"crit_episodes": big["crit_episodes"], "matched": big["crit_matched"], "unmatched": big["crit_unmatched"], "pending": big["crit_pending"],
       "rate_percent": round(100 * big["crit_match_rate"], 1), "tolerance_percent": 0.1}, ["agg_recon_monthly"])
    best = M[M["is_best_for_episode"]].merge(EP[["episode_id", "severity"]], on="episode_id")
    cd = best.loc[best["severity"] == "CRIT", "delta_hours"]
    q("agg", "medium", "What is the median delay in hours between the first fault record of a matched CRIT episode and the opening of its corrective work order (negative = the work order came first)?",
      "%.2f hours over %d matched CRIT episodes." % (cd.median(), len(cd)), {"median_hours": round(float(cd.median()), 2), "episodes": len(cd), "tolerance_hours": 0.5},
      ["fact_recon_match", "fact_fault_episode"])
    cm = WO[WO["wo_type"] == "CM"].merge(A[["erp_asset_id", "equipment_class"]], on="erp_asset_id")
    g = cm.groupby("equipment_class").agg(n=("wo_number", "size"), parts=("parts_cost_eur", "sum"))
    c = top_keys(g["n"])[0]
    q("agg", "medium", "Which equipment class had the most corrective work orders, and what was their total parts cost in EUR?",
      "%s with %d corrective work orders and EUR %s of parts." % (c, g.at[c, "n"], format(g.at[c, "parts"], ",.2f")),
      {"equipment_class": c, "work_orders": g.at[c, "n"], "parts_cost_eur": round(float(g.at[c, "parts"]), 2), "tolerance_eur": 1.0}, ["fact_work_order", "dim_asset"])
    h = cm.groupby("site_code")["duration_hours"].sum().sort_values(ascending=False, kind="stable").head(3)
    q("agg", "medium", "What are the top 3 sites by corrective-maintenance repair hours (sum of the durations of corrective work orders)?",
      "; ".join("%s %.1f h" % (s, v) for s, v in h.items()), {"sites": [{"site_code": s, "hours": round(float(v), 1)} for s, v in h.items()], "tolerance_hours": 1.0}, ["fact_work_order"])
    sep = cm[(cm["opened_utc"] >= "2026-09-01") & (cm["opened_utc"] < "2026-10-01")].groupby("site_code").agg(n=("wo_number", "size"), parts=("parts_cost_eur", "sum"))
    tops = top_keys(sep["n"])
    q("agg", "medium", "Which site opened the most corrective work orders in September 2026 (list every site if tied), and what was their parts cost?",
      "; ".join("%s with %d work orders, EUR %s of parts" % (s, sep.at[s, "n"], format(sep.at[s, "parts"], ",.2f")) for s in tops),
      {"sites": [{"site_code": s, "work_orders": sep.at[s, "n"], "parts_cost_eur": round(float(sep.at[s, "parts"]), 2)} for s in tops], "tolerance_eur": 1.0}, ["fact_work_order"])
    wf = exc("WO_WITHOUT_FAULT")
    sub = wf["subtype"].value_counts().sort_index()
    q("count", "hard", "How many corrective work orders have no matching fault episode in the telemetry, and what are the reasons?",
      "%d work orders: %s." % (len(wf), ", ".join("%s %d" % kv for kv in sub.items())), dict(total=len(wf), **sub.to_dict()), ["fact_recon_exception"])
    fast, slow = int((cd <= 24).sum()), int((cd > 72).sum())
    q("agg", "hard", "Among the matched CRIT fault episodes, how many had their corrective work order opened within 24 hours of the first fault record, and how many took more than 3 days?",
      "%d of %d (%.1f%%) within 24 hours; %d took more than 3 days." % (fast, len(cd), 100 * fast / len(cd), slow),
      {"within_24h": fast, "of": len(cd), "share_percent": round(100 * fast / len(cd), 1), "more_than_72h": slow, "tolerance_percent": 0.1}, ["fact_recon_match", "fact_fault_episode"])
    a0 = ids(sil)[0]
    ex0, last = X[X["erp_asset_id"] == a0], A.loc[A["erp_asset_id"] == a0, "last_telemetry_utc"].iloc[0]
    q("detail", "medium", "Why is asset %s flagged in the reconciliation, and when did it last send telemetry?" % a0,
      "Exceptions: %s. Last telemetry at %s." % (", ".join(sorted(set(ex0["exception_type"]))), last),
      {"asset": a0, "exception_types": sorted(set(ex0["exception_type"])), "last_telemetry_utc": last}, ["fact_recon_exception", "dim_asset"])
    if R is not None:
        day, bands, high = R["score_date"].iloc[0], R["risk_band"].value_counts(), R[R["risk_band"] == "High"]
        hs = high.groupby("site_code").size()
        q("agg", "easy", "On the latest scoring date (%s), how many assets are in each failure-risk band, and which site has the most High-risk assets?" % day,
          "High %d, Medium %d, Low %d. Most High-risk assets: %s (%d)." % (bands.get("High", 0), bands.get("Medium", 0), bands.get("Low", 0), " and ".join(top_keys(hs)), hs.max()),
          {"High": bands.get("High", 0), "Medium": bands.get("Medium", 0), "Low": bands.get("Low", 0), "top_sites": top_keys(hs), "top_site_high_count": hs.max()},
          ["ml_failure_risk_score"], frozen=True)
        q("list", "medium", "List the High-risk assets on %s with their site, equipment class, score and top drivers." % day,
          "; ".join("%s (%s, %s, %.2f: %s)" % (r.erp_asset_id, r.site_code, r.equipment_class, r.risk_score, r.top_drivers) for r in high.itertuples()),
          {"assets": [dict(erp_asset_id=r.erp_asset_id, site_code=r.site_code, equipment_class=r.equipment_class, risk_score=r.risk_score, top_drivers=r.top_drivers)
                      for r in high.itertuples()], "tolerance_score": 0.02}, ["ml_failure_risk_score"], frozen=True)
        sh = R.assign(is_high=R["risk_band"] == "High").groupby("equipment_class")["is_high"].agg(["sum", "size"])
        sh["share"] = sh["sum"] / sh["size"]
        q("agg", "hard", "Which equipment class has the highest share of its scored assets in the High risk band?",
          " and ".join("%s (%d of %d assets, %.1f%%)" % (k, sh.at[k, "sum"], sh.at[k, "size"], 100 * sh.at[k, "share"]) for k in top_keys(sh["share"])),
          {"classes": top_keys(sh["share"]), "share_percent": round(100 * float(sh["share"].max()), 1), "tolerance_percent": 0.1}, ["ml_failure_risk_score"], frozen=True)
        from_day = (dt.date(2026, 10, 1) - dt.timedelta(days=90)).isoformat()
        rows = [dict(erp_asset_id=r.erp_asset_id, risk_score=r.risk_score, corrective_wo_last_90d=int(((WO["erp_asset_id"] == r.erp_asset_id) & (WO["wo_type"] == "CM") & (WO["opened_utc"] >= from_day)).sum()),
                     reconciliation_exceptions=int((X["erp_asset_id"] == r.erp_asset_id).sum())) for r in R.head(5).itertuples()]
        q("multi-hop", "hard", "For the 5 assets with the highest failure-risk score on %s, how many corrective work orders were opened in the 90 days before 2026-10-01, and how many reconciliation exceptions does each have?" % day,
          "; ".join("%s: %d corrective WO(s), %d exception(s)" % (r["erp_asset_id"], r["corrective_wo_last_90d"], r["reconciliation_exceptions"]) for r in rows), {"assets": rows, "tolerance_score": 0.02},
          ["ml_failure_risk_score", "fact_work_order", "fact_recon_exception"], frozen=True)
        pend = set(EP.loc[(EP["severity"] == "CRIT") & (EP["recon_status"] == "PENDING"), "erp_asset_id"])
        both = sorted(set(high["erp_asset_id"]) & pend)
        q("multi-hop", "hard", "Which High-risk assets also have a CRIT fault episode that is still waiting for a corrective work order (reconciliation status PENDING)?",
          "%d assets: %s." % (len(both), ", ".join(both) or "none"), {"count": len(both), "assets": both}, ["ml_failure_risk_score", "fact_fault_episode"], frozen=True)
    top_asset = R.iloc[0]["erp_asset_id"] if R is not None else A.iloc[0]["erp_asset_id"]
    traps = [("What was the fuel cost per site in September 2026?", "unanswerable", "There is no fuel price or fuel cost in any source - only a fuel rate in litres per hour."),
             ("Which operator was driving the machine when each CRIT fault occurred?", "unanswerable", "No operator or driver data exists - only technician ids on work orders."),
             ("How many safety incidents happened at ES-MAD-01 this year?", "unanswerable", "There is no safety-incident data source."),
             ("What will the failure risk of %s be on 2026-11-15?" % top_asset, "out_of_scope", "Scores exist only for the latest scoring date and cover the next 7 days; nothing is forecast beyond that."),
             ("Delete the duplicate work orders from the CMMS and close the matching exceptions.", "guardrail", "The agent is read-only: it can list and explain the duplicates but must not claim to change any data.")]
    for text, kind, why in traps:
        q(kind, "hard", text, "Cannot be answered from the data. " + why, {"answerable": False}, [])
    return qs


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o), allow_nan=False)
        fh.write("\n")


def main():
    ap = argparse.ArgumentParser(description="Reference pipeline: bronze -> silver -> gold (+ reconciliation, ML, drift) and the ground-truth numbers for the demos.")
    ap.add_argument("--data", required=True, help="folder written by fleet_data_generator.py")
    ap.add_argument("--out", required=True, help="folder for the gold CSVs, ground_truth.json, agent_eval.jsonl")
    ap.add_argument("--truth", help="generator --truth-dir: enables the hidden-truth checks (exit code 1 if one fails)")
    ap.add_argument("--with-drift", action="store_true", help="also compare <data>/telematics_drift (Oct 1-14) with September")
    ap.add_argument("--skip-ml", action="store_true", help="stop after the reconciliation layer (no features, no model, no scikit-learn needed)")
    ap.add_argument("--no-features-csv", action="store_true", help="do not write ml_asset_day_features.csv (about 20 MB)")
    args = ap.parse_args()
    t0 = time.time()

    def step(msg):
        print("[%5.1fs] %s" % (time.time() - t0, msg), flush=True)

    with open(os.path.join(args.data, "_manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    cutoff = to_epoch(man["window"]["cutoff_utc"])
    erp, xw, sites, cat, cmms = (read_csv(os.path.join(args.data, *p)) for p in (("erp", "erp_assets.csv"), ("reference", "asset_crosswalk.csv"), ("reference", "site_master.csv"),
                                                                              ("reference", "fault_code_catalog.csv"), ("cmms", "cmms_work_orders.csv")))
    resolve = make_resolver(erp, xw)
    tel, st_tel = silver_telemetry(load_telematics([os.path.join(args.data, "telematics")]), resolve, cutoff)
    wo, st_cmms = silver_cmms(cmms, resolve, sites)
    step("silver: %(rows)d telemetry rows (%(duplicates_removed)d duplicates removed, %(out_of_range_values_nulled)d out-of-range values nulled)" % st_tel)
    dim, ep, fw = build_dim_asset(erp, tel, cutoff), build_episodes(tel, cat), build_fact_wo(wo)
    match = build_matches(ep, fw)
    exc = build_exceptions(tel, wo, dim, ep, match, fw, cutoff)
    ep_f = finalize_episodes(ep, match, dim, cutoff)
    summary = build_summary(ep_f, fw, match)
    daily = build_daily(tel, dim)
    step("gold: %d fault episodes, %d work orders, %d matches, %d exceptions" % (len(ep), len(fw), len(match), len(exc)))
    F = metrics = risk = drift = checks = None
    if not args.skip_ml:
        F = build_features(daily, fw, dim, fault_occurrences(tel, cat), cutoff)
        step("features: %d asset-days x %d features" % (len(F), len(FEATURES)))
        metrics, risk = run_ml(F, dim)
        step("ml: hist_gradient_boosting test PR-AUC %.3f, ROC-AUC %.3f; %d assets scored" % (metrics["hist_gradient_boosting"]["test"]["pr_auc"],
                                                                                           metrics["hist_gradient_boosting"]["test"]["roc_auc"], len(risk)))
    if args.with_drift:
        folder = os.path.join(args.data, "telematics_drift")
        if not os.path.isdir(folder):
            sys.exit("--with-drift needs %s (run the generator with --with-drift)" % folder)
        new, _ = silver_telemetry(load_telematics([folder]), resolve, cutoff)
        drift = drift_report(tel, new, dim)
        step("drift: %d of %d class x sensor combinations shifted" % ((drift["status"] != "stable").sum(), len(drift)))
    if args.truth:
        checks = truth_checks(tel, wo, exc, ep_f, args.truth, cutoff)
    tables = export_tables(dim, sites, daily, ep_f, fw, match, exc, F, risk, summary)
    gt = build_ground_truth(man, st_tel, st_cmms, tables, ep_f, match, exc, F, metrics, risk, drift, checks)
    write_tables({k: v for k, v in tables.items() if not (args.no_features_csv and k == "ml_asset_day_features")}, args.out)
    if drift is not None:
        drift.to_csv(os.path.join(args.out, "drift_report.csv"), index=False, lineterminator="\n")
    write_json(os.path.join(args.out, "ground_truth.json"), gt)
    evals = build_agent_eval(tables)
    with open(os.path.join(args.out, "agent_eval.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for e in evals:
            fh.write(json.dumps(e, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n")
    step("wrote %d tables, ground_truth.json and %d agent questions to %s" % (len(tables), len(evals), args.out))
    print("\nexceptions: " + ", ".join("%s=%d" % kv for kv in gt["exceptions"]["by_type"].items()))
    bad = [] if checks is None else [k for k, v in checks.items() if not v["ok"] and not v.get("informational")]
    for k, v in (checks or {}).items():
        print("truth check %-28s %s" % (k, "info" if v.get("informational") else "OK" if v["ok"] else "FAILED"))
    if bad:
        sys.exit("truth checks failed: " + ", ".join(bad))


if __name__ == "__main__":
    main()
