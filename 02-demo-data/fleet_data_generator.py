#!/usr/bin/env python3
"""
Contoso Fleet - synthetic data generator for the ML / MLOps / Agents workshop.

Scenario: a construction-equipment fleet with three operational sources
(telematics JSONL, CMMS work orders CSV, ERP asset register CSV) whose asset
identifiers are deliberately inconsistent.  Equipment failures drive BOTH the
sensor precursors in telematics and the corrective work orders in the CMMS, so
the same data supports (1) ETL + reconciliation, (2) failure prediction and
(3) an agent that answers questions on top of the reconciled data.

Determinism: numpy *legacy* RandomState (stream-stable across numpy versions)
+ stdlib only.  The same command line yields byte-identical files on any
machine.  The base window is identical with or without --with-drift.

Usage
-----
    python fleet_data_generator.py --out ./fleet_data
    python fleet_data_generator.py --out ./fleet_data --with-drift --gzip
    python fleet_data_generator.py --out ./fleet_data --truth-dir ./fleet_truth   # tests only

Outputs (under --out)
---------------------
    reference/site_master.csv  fault_code_catalog.csv  asset_crosswalk.csv
    erp/erp_assets.csv
    cmms/cmms_work_orders.csv
    telematics/telematics_YYYY-MM.jsonl[.gz]
    telematics_drift/telematics_2026-10.jsonl[.gz]      (only with --with-drift)
    _manifest.json                                       (params, counts, sha256)

All company, site and manufacturer names are fictional.
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import sys
import time
import uuid
from collections import Counter
from types import SimpleNamespace

import numpy as np

SEED = 20261023
DEFAULT_START = "2026-04-01"
DEFAULT_ASSETS = 300
DEFAULT_DAYS = 183            # 2026-04-01 .. 2026-09-30
EXT_DAYS = 14                 # always simulated after the window (drift period)
UTC = dt.timezone.utc
SLOTS_PER_DAY = 4             # readings at 00, 06, 12, 18 UTC
BASE_HAZARD = 0.0085          # tuned: ~1.5 failures / asset / 183 days
FW_COOLANT = (2, 4, 0)        # firmware >= 2.4.0 adds coolant_level_pct ...
COOLANT_FROM = dt.date(2026, 7, 1)  # ... from this date (schema evolution demo)

# (code, name, country, timezone, std_utc_offset_h, lat, lon, project_type, weight, hazard_mult)
SITES = [
    ("FR-PAR-01", "Paris Ring Road Upgrade", "FR", "Europe/Paris", 1, 48.8566, 2.3522, "Road", 0.14, 1.00),
    ("FR-LYS-01", "Lyon Metro Extension", "FR", "Europe/Paris", 1, 45.7640, 4.8357, "Metro", 0.08, 0.95),
    ("FR-MRS-01", "Marseille Port Terminal", "FR", "Europe/Paris", 1, 43.2965, 5.3698, "Port", 0.09, 1.20),
    ("DE-MUC-01", "Munich Rail Hub", "DE", "Europe/Berlin", 1, 48.1351, 11.5820, "Rail", 0.08, 0.90),
    ("DE-HAM-01", "Hamburg Quay Wall", "DE", "Europe/Berlin", 1, 53.5511, 9.9937, "Quay", 0.08, 1.10),
    ("BE-ANR-01", "Antwerp Tunnel Works", "BE", "Europe/Brussels", 1, 51.2194, 4.4025, "Tunnel", 0.07, 1.00),
    ("GB-MAN-01", "Manchester Airport Link", "GB", "Europe/London", 0, 53.4808, -2.2426, "Airport", 0.08, 1.15),
    ("GB-BHM-01", "Birmingham Interchange", "GB", "Europe/London", 0, 52.4862, -1.8904, "Interchange", 0.07, 0.90),
    ("ES-MAD-01", "Madrid Solar Plant Foundations", "ES", "Europe/Madrid", 1, 40.4168, -3.7038, "Energy", 0.09, 1.25),
    ("NL-RTM-01", "Rotterdam Flood Barrier", "NL", "Europe/Amsterdam", 1, 51.9244, 4.4777, "Flood barrier", 0.08, 1.00),
    ("CH-ZRH-01", "Zurich Base Tunnel", "CH", "Europe/Zurich", 1, 47.3769, 8.5417, "Tunnel", 0.06, 0.85),
    ("PT-LIS-01", "Lisbon Harbour Bridge", "PT", "Europe/Lisbon", 0, 38.7223, -9.1393, "Bridge", 0.08, 1.05),
]

MANUFACTURERS = ["Kestrel Heavy", "Ironvale", "Terrain Dynamics", "Norland Machinery", "Altis Equipment"]
MFR_PREFIX = ["KES", "IRO", "TER", "NOR", "ALT"]

# share = fleet mix, hz = failure-hazard multiplier, load/idle = typical load% / idle%
# temp/oil/hyd/vib/fuel = healthy baselines (deg C / kPa / bar / mm/s / L/h); hyd=None -> no hydraulics
CLASSES = {
    "Excavator":   dict(code=1, abbr="EXC", share=.22, hz=1.15, cost=(180e3, 420e3), temp=88, oil=390, hyd=230, vib=2.4, fuel=24, load=60, idle=22,
                        models=[(0, "KX-220"), (1, "IV-340"), (2, "TD-290")]),
    "WheelLoader": dict(code=2, abbr="WHL", share=.14, hz=1.00, cost=(150e3, 300e3), temp=86, oil=380, hyd=210, vib=2.0, fuel=19, load=65, idle=20,
                        models=[(0, "KL-180"), (3, "NM-L40"), (4, "AL-950")]),
    "Bulldozer":   dict(code=3, abbr="DOZ", share=.08, hz=1.10, cost=(220e3, 450e3), temp=90, oil=400, hyd=200, vib=2.8, fuel=26, load=70, idle=15,
                        models=[(1, "IV-D7"), (2, "TD-D65"), (0, "KB-850")]),
    "DumpTruck":   dict(code=4, abbr="DMP", share=.16, hz=1.00, cost=(200e3, 500e3), temp=87, oil=410, hyd=190, vib=1.9, fuel=30, load=58, idle=25,
                        models=[(3, "NM-DT35"), (4, "AL-T45"), (0, "KD-40")]),
    "MobileCrane": dict(code=5, abbr="CRN", share=.08, hz=0.80, cost=(350e3, 900e3), temp=84, oil=370, hyd=250, vib=1.4, fuel=16, load=45, idle=35,
                        models=[(2, "TD-MC60"), (4, "AL-MC90"), (1, "IV-MC45")]),
    "Compactor":   dict(code=6, abbr="CMP", share=.10, hz=0.85, cost=(90e3, 200e3), temp=85, oil=360, hyd=170, vib=3.4, fuel=12, load=55, idle=18,
                        models=[(3, "NM-C12"), (0, "KC-130"), (4, "AL-R11")]),
    "Paver":       dict(code=7, abbr="PAV", share=.06, hz=0.90, cost=(250e3, 500e3), temp=86, oil=375, hyd=200, vib=2.6, fuel=21, load=50, idle=20,
                        models=[(1, "IV-P90"), (3, "NM-P70")]),
    "Generator":   dict(code=8, abbr="GEN", share=.16, hz=0.70, cost=(25e3, 120e3), temp=82, oil=350, hyd=None, vib=1.2, fuel=14, load=62, idle=10,
                        models=[(4, "AL-G250"), (0, "KG-400"), (2, "TD-G150")]),
}
CLASS_NAMES = list(CLASSES)

SYSTEM_ORDER = ["ENG", "HYD", "ELEC", "COOL", "TRN", "UND", "STR"]
FAIL_SYSTEMS = {
    "ENG": ["ENG-OVERHEAT", "ENG-OILPRESS"], "HYD": ["HYD-LEAK", "HYD-PUMP"],
    "ELEC": ["ELEC-ECU", "ELEC-ALT"], "COOL": ["COOL-PUMP", "COOL-LEAK"],
    "TRN": ["TRN-SLIP", "TRN-OVERHEAT"], "UND": ["UND-TRACK"], "STR": ["STR-CRACK"],
}
FAIL_SYSTEM_OF = {c: s for s, cs in FAIL_SYSTEMS.items() for c in cs}
# probability of the failing system, per equipment class (order = SYSTEM_ORDER)
CLASS_SYSTEM_W = {
    "Excavator":   [.22, .34, .08, .12, .00, .20, .04],
    "WheelLoader": [.20, .25, .08, .12, .28, .00, .07],
    "Bulldozer":   [.22, .15, .06, .12, .20, .22, .03],
    "DumpTruck":   [.26, .12, .10, .14, .30, .00, .08],
    "MobileCrane": [.15, .35, .15, .05, .10, .00, .20],
    "Compactor":   [.25, .30, .10, .15, .10, .00, .10],
    "Paver":       [.20, .30, .12, .10, .10, .15, .03],
    "Generator":   [.45, .00, .30, .25, .00, .00, .00],
}
# sensor shift at full precursor severity: (temp degC, oil kPa, hyd bar, vib mm/s, coolant %)
AMPL = {
    "ENG": (14, -70, 0, 0.8, 0), "HYD": (0, 0, -60, 1.1, 0), "ELEC": (3, -5, 0, 0.3, 0),
    "COOL": (18, -25, 0, 0.0, -35), "TRN": (7, -35, 0, 2.0, 0), "UND": (0, 0, 0, 2.6, 0),
    "STR": (0, 0, 0, 1.5, 0),
}
FAULT_CATALOG = [  # code, system, severity, description, recommended action
    ("P0217", "ENG", "WARN", "Engine coolant over-temperature", "Check coolant level and radiator airflow"),
    ("P0524", "ENG", "WARN", "Engine oil pressure low", "Check oil level, filter and pump"),
    ("P0218", "ENG", "CRIT", "Engine over-temperature protection active", "Stop machine, inspect cooling circuit"),
    ("H1201", "HYD", "WARN", "Hydraulic pressure below target", "Inspect hoses, fittings and pump"),
    ("H1305", "HYD", "WARN", "Hydraulic oil temperature high", "Check cooler and oil level"),
    ("H1210", "HYD", "CRIT", "Hydraulic pressure loss", "Stop machine, inspect for leaks"),
    ("E3304", "ELEC", "WARN", "Alternator voltage out of range", "Test alternator and battery"),
    ("E3401", "ELEC", "INFO", "CAN bus communication retry", "Monitor; reseat connectors if frequent"),
    ("E3310", "ELEC", "CRIT", "ECU communication lost", "Stop machine, diagnose ECU"),
    ("C2105", "COOL", "WARN", "Coolant level low", "Top up coolant, inspect for leaks"),
    ("C2110", "COOL", "CRIT", "Coolant pump failure", "Stop machine, replace pump"),
    ("T4410", "TRN", "WARN", "Transmission oil temperature high", "Check oil level and cooler"),
    ("T4420", "TRN", "CRIT", "Transmission clutch slip detected", "Stop machine, inspect transmission"),
    ("U5501", "UND", "WARN", "Track tension out of range", "Adjust track tension, inspect rollers"),
    ("U5510", "UND", "CRIT", "Undercarriage vibration limit exceeded", "Stop machine, inspect undercarriage"),
    ("S6601", "STR", "WARN", "Structural stress threshold exceeded", "Inspect boom / frame welds"),
    ("S6610", "STR", "CRIT", "Structural integrity alarm", "Stop machine, structural inspection"),
    ("G0001", "GEN", "INFO", "Service interval approaching", "Schedule preventive maintenance"),
    ("G0101", "GEN", "INFO", "Fuel level low", "Refuel"),
    ("G0202", "GEN", "INFO", "Operator seat belt not fastened", "Remind operator"),
]
WARN_CODES = {s: [c[0] for c in FAULT_CATALOG if c[1] == s and c[2] == "WARN"] for s in SYSTEM_ORDER}
CRIT_CODE = {s: [c[0] for c in FAULT_CATALOG if c[1] == s and c[2] == "CRIT"][0] for s in SYSTEM_ORDER}
INFO_CODES = [c[0] for c in FAULT_CATALOG if c[2] == "INFO"]

CM_TEXT = {
    "ENG-OVERHEAT": ["Engine overheating under load, operator shut machine down",
                     "High coolant temperature alarm, machine derated then stopped"],
    "ENG-OILPRESS": ["Low engine oil pressure warning, engine stopped", "Oil pressure drop at idle, suspected pump wear"],
    "HYD-LEAK": ["Hydraulic oil leak at boom cylinder hose", "Visible hydraulic leak, pressure dropping during lift"],
    "HYD-PUMP": ["Main hydraulic pump noisy and weak, slow implement response", "Hydraulic pump failure, no pressure at implement"],
    "ELEC-ECU": ["ECU communication fault, machine will not start", "Intermittent ECU reset, dashboard lost power"],
    "ELEC-ALT": ["Alternator not charging, battery voltage low", "Alternator belt failure, charging warning on"],
    "COOL-PUMP": ["Coolant pump failure, engine temperature rising fast", "Water pump seal leaking, coolant loss"],
    "COOL-LEAK": ["Coolant leak at radiator hose", "Radiator leak found, coolant level low alarm"],
    "TRN-SLIP": ["Transmission slipping under load", "Clutch pack slip, loss of drive in 2nd gear"],
    "TRN-OVERHEAT": ["Transmission oil overheating, machine stopped", "Transmission temperature alarm after long haul"],
    "UND-TRACK": ["Track tension lost / worn rollers, machine unsafe to move", "Track chain damage found, undercarriage vibration"],
    "STR-CRACK": ["Crack found on boom / frame weld, machine tagged out", "Structural crack at pivot bracket, out of service"],
}
PM_TEXT = ["Scheduled preventive maintenance: oil and filters changed, greasing done",
           "PM service completed per OEM schedule, fluids topped up",
           "Preventive maintenance: belts and hoses inspected, filters replaced"]
INSP_TEXT = ["Routine safety inspection, no findings", "Weekly walk-around inspection OK",
             "Inspection: minor seep noted, monitor", "Pre-shift inspection completed, all checks passed",
             "Inspection: tyre/track wear within limits"]

FIRMWARES = ["2.1.4", "2.2.0", "2.3.1", "2.4.0", "2.4.2"]
REF_STYLES = ["EQ-%05d", "eq%05d", "EQ_%05d", "%05d", "EQ-%d", " EQ-%05d "]   # telematics asset_ref formats
REF_STYLE_P = [.68, .10, .07, .06, .05, .04]
TAG_STYLES = ["E%05d", "EQ%05d", "EQ %05d", "EQ-%05d"]                           # CMMS asset_tag formats
TAG_STYLE_P = [.45, .30, .15, .10]
TS_STYLE_P = [.80, .15, .05]                                                      # Z / local offset / epoch-ms


def scaled(k, n, base=DEFAULT_ASSETS):
    """Scale an injected-anomaly count with fleet size (exactly k when n == 300)."""
    return max(1, int(round(k * n / base)))


def ri(rs, lo, hi, size=None):
    """Platform-stable bounded integers (always int64)."""
    r = rs.randint(lo, hi, size=size, dtype=np.int64)
    return int(r) if size is None else r


def epoch_of(d):
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


def _last_sunday(y, m):
    d = dt.date(y, m, 31)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)


def _dst_window(y):
    """EU summer time: last Sunday of March -> last Sunday of October, both at 01:00 UTC."""
    return epoch_of(_last_sunday(y, 3)) + 3600, epoch_of(_last_sunday(y, 10)) + 3600


def local_offset_hours(std_h, epoch_s):
    t = np.asarray(epoch_s, dtype=np.int64)
    off = np.full(t.shape, std_h, dtype=np.int64)
    for y in range(dt.datetime.fromtimestamp(int(t.min()), UTC).year, dt.datetime.fromtimestamp(int(t.max()), UTC).year + 1):
        a, b = _dst_window(y)
        off += ((t >= a) & (t < b)).astype(np.int64)
    return off


def iso_z(epoch_s):
    t = np.asarray(epoch_s, dtype=np.int64).astype("datetime64[s]")
    return [s + "Z" for s in np.datetime_as_string(t, unit="s").tolist()]


def iso_local(epoch_s, offs_h):
    t, o = np.asarray(epoch_s, dtype=np.int64), np.asarray(offs_h, dtype=np.int64)
    base = np.datetime_as_string((t + o * 3600).astype("datetime64[s]"), unit="s").tolist()
    return [b + ("%s%02d:00" % ("+" if h >= 0 else "-", abs(h))) for b, h in zip(base, o.tolist())]


def local_wo_string(epoch_s, std_h):
    """CMMS timestamps are local wall-clock strings 'YYYY-MM-DD HH:MM' (no offset)."""
    o = int(local_offset_hours(std_h, [epoch_s])[0])
    return dt.datetime.fromtimestamp(epoch_s + o * 3600, UTC).strftime("%Y-%m-%d %H:%M")


def new_asset(**kw):
    base = dict(erp_id=None, in_erp=True, status="Active", retire=None, has_dev=True, device_id=None, firmware=FIRMWARES[0],
                ts_style=0, asset_ref=None, serial_in=False, dev_end=None, tier="normal", legacy=None, leg_tag=None,
                zombie=False, silent=False, serial=None, acq=None, cost=None, mfr=None, model=None)
    base.update(kw)
    return SimpleNamespace(**base)


def build_population(master, n_active, start, days):
    """ERP assets + devices + identifier 'tiers' (see scenario-contract.md); returns (assets, rentals, crosswalk_rows)."""
    n_ret, n_dis = scaled(10, n_active), scaled(6, n_active)
    n = n_active + n_ret + n_dis
    cls_idx = master.choice(len(CLASS_NAMES), size=n, p=[CLASSES[c]["share"] for c in CLASS_NAMES])
    age = master.uniform(0.4, 9.5, n)
    order = np.argsort(-age, kind="stable")                       # oldest assets get the lowest ids
    cls_idx, age = cls_idx[order], age[order]
    ids = np.sort(master.choice(np.arange(100, 9000), size=n, replace=False))
    site_idx = master.choice(len(SITES), size=n, p=[s[8] for s in SITES])
    perm = master.permutation(n).tolist()
    dis_set, ret_list = set(perm[:n_dis]), perm[n_dis:n_dis + n_ret]
    ret_set, zombie_set = set(ret_list), set(ret_list[:scaled(6, n_active)])
    active = [i for i in range(n) if i not in dis_set and i not in ret_set]
    nodev = set(master.choice(active, size=min(scaled(24, n_active), len(active)), replace=False).tolist())
    pool = master.permutation([i for i in active if i not in nodev]).tolist()
    cur = [0]

    def take(m):
        out = pool[cur[0]:cur[0] + m]
        cur[0] += m
        return out

    silent_set = set(take(scaled(10, n_active)))
    serial_tier, xw_tier, typo_tier = take(scaled(6, n_active)), take(scaled(3, n_active)), take(scaled(2, n_active))
    n_ls, n_lx, n_lu = scaled(5, n_active), scaled(4, n_active), scaled(3, n_active)
    legacy = take(n_ls + n_lx + n_lu)
    leg_mode = {i: ("serial" if k < n_ls else "crosswalk" if k < n_ls + n_lx else "unresolved") for k, i in enumerate(legacy)}
    used = {"serial": set(), "dev": set(), "tag": set(), "ref": set()}

    def uniq(kind, draw):
        while True:
            v = draw()
            if v not in used[kind]:
                used[kind].add(v)
                return v

    assets, xw = [], []
    for i in range(n):
        cname = CLASS_NAMES[int(cls_idx[i])]
        c = CLASSES[cname]
        mi, model = c["models"][ri(master, 0, len(c["models"]))]
        acq = start - dt.timedelta(days=int(round(float(age[i]) * 365.25)))
        serial = uniq("serial", lambda: "SN-%s-%02d-%06d" % (MFR_PREFIX[mi], acq.year % 100, ri(master, 100000, 1000000)))
        cost = float(np.round(master.uniform(c["cost"][0], c["cost"][1]), -2))
        status = "Disposed" if i in dis_set else "Retired" if i in ret_set else "Active"
        retire = None
        if status == "Disposed":
            retire = start - dt.timedelta(days=ri(master, 30, 400))
        elif status == "Retired":
            retire = start + dt.timedelta(days=ri(master, 45, max(46, days - 30)))
        has_dev = i not in nodev and status != "Disposed"
        dev_id = uniq("dev", lambda: "TLM-%06X" % ri(master, 0x100000, 0xFFFFFF)) if has_dev else None
        fw = FIRMWARES[int(master.choice(len(FIRMWARES), p=[.15, .20, .25, .25, .15]))]
        ts_style = int(master.choice(3, p=TS_STYLE_P))
        ref_style = int(master.choice(len(REF_STYLES), p=REF_STYLE_P))
        dev_end = None
        if i in silent_set:
            dev_end = days - ri(master, 15, 61)
        elif status == "Retired" and i not in zombie_set:
            dev_end = (retire - start).days
        a = new_asset(idx=i, erp_id=int(ids[i]), cls=cname, mfr=MANUFACTURERS[mi], model=model, serial=serial, acq=acq, cost=cost,
                      site=SITES[int(site_idx[i])], status=status, retire=retire, age0=float(age[i]), has_dev=has_dev,
                      device_id=dev_id, firmware=fw, ts_style=ts_style, dev_end=dev_end, zombie=i in zombie_set,
                      silent=i in silent_set, asset_ref=REF_STYLES[ref_style] % int(ids[i]))
        eq = "EQ-%05d" % a.erp_id
        if i in serial_tier:
            a.tier, a.serial_in = "serial", True
            a.asset_ref = None if serial_tier.index(i) % 2 == 0 else ""
        elif i in xw_tier:
            a.tier, a.asset_ref = "crosswalk", uniq("ref", lambda: "FLT-%04d" % ri(master, 1000, 10000))
            xw.append((a.asset_ref, eq, "Telematics fleet number", "Re-keyed during 2024 device migration"))
        elif i in typo_tier:
            a.tier, a.asset_ref = "typo", "EQ-%05d" % uniq("ref", lambda: ri(master, 9100, 9990))   # number never exists in ERP
        if i in leg_mode:
            a.legacy, a.leg_tag = leg_mode[i], uniq("tag", lambda: "LEG-%04d" % ri(master, 1000, 10000))
            if a.legacy == "crosswalk":
                xw.append((a.leg_tag, eq, "CMMS legacy tag", "Pre-2020 CMMS asset tag"))
        assets.append(a)
    for a in [x for x in assets if x.status == "Disposed"][:2]:       # decoy rows: mapped but never used
        xw.append((uniq("tag", lambda: "LEG-%04d" % ri(master, 1000, 10000)), "EQ-%05d" % a.erp_id, "CMMS legacy tag",
                   "Asset disposed - mapping kept for audit"))
    rentals = []
    for k in range(scaled(4, n_active)):
        cname = CLASS_NAMES[ri(master, 0, len(CLASS_NAMES))]
        rentals.append(new_asset(idx=n + k, in_erp=False, status="Rental", cls=cname, site=SITES[ri(master, 0, len(SITES))],
                                 age0=float(master.uniform(0.5, 4.0)), tier="rental",
                                 device_id=uniq("dev", lambda: "TLM-%06X" % ri(master, 0x100000, 0xFFFFFF)),
                                 firmware=FIRMWARES[ri(master, 0, len(FIRMWARES))],
                                 asset_ref=uniq("ref", lambda: "RNT-%04d" % ri(master, 1000, 10000))))
    for a in assets + rentals:
        a.cdef = CLASSES[a.cls]
    seeds = ri(master, 1, 2 ** 31 - 1, size=len(assets) + len(rentals))
    for k, a in enumerate(assets + rentals):
        a.seed = int(seeds[k])
    return assets, rentals, xw


P_WK, P_SAT, P_SUN = np.array([.04, .90, .90, .45]), np.array([.02, .35, .30, .05]), np.array([.01, .08, .06, .02])
PARTS_BASE = {"ENG": 3500, "HYD": 2800, "ELEC": 1500, "COOL": 1800, "TRN": 6500, "UND": 8000, "STR": 12000}


def make_timeline(start, days):
    D = days + EXT_DAYS
    T = D * SLOTS_PER_DAY
    slot = np.arange(T, dtype=np.int64)
    day = slot // SLOTS_PER_DAY
    t0 = epoch_of(start)
    return SimpleNamespace(D=D, T=T, days=days, t0=t0, slot=slot, day=day, epoch=t0 + day * 86400 + (slot % SLOTS_PER_DAY) * 6 * 3600,
                           wd=(start.weekday() + day) % 7, yday=start.timetuple().tm_yday, start=start, cache={})


def _schedule(rs, first_hi, mean, sd, lo, hi, D):
    """Event days: first U(0, first_hi), then every ~N(mean, sd) days clipped to [lo, hi]."""
    out, p = [], float(rs.uniform(0, first_hi))
    while p < D:
        out.append(p)
        p += float(np.clip(rs.normal(mean, sd), lo, hi))
    return out


def _tag(a, rs):
    r, style = rs.random_sample(), int(rs.choice(len(TAG_STYLES), p=TAG_STYLE_P))
    if a.legacy and r < 0.60:
        return a.leg_tag, (a.serial if a.legacy == "serial" else "")
    return TAG_STYLES[style] % a.erp_id, ""


def plan_asset(a, tl, base_hazard=BASE_HAZARD):
    """Personality, PM/inspection schedule, failures (hazard model) and the work orders they generate."""
    rs = np.random.RandomState(a.seed)
    c, D = a.cdef, tl.D
    p = SimpleNamespace(rs=rs, frailty=float(rs.gamma(4.0, 0.25)), use=float(rs.uniform(0.75, 1.15)),
                        off_temp=float(rs.normal(0, 2.0)), off_oil=float(rs.normal(0, 15.0)),
                        off_hyd=float(rs.normal(0, 8.0)), off_vib=float(rs.normal(0, 0.15)), fails=[], wos=[])
    end_day = D if a.status in ("Active", "Rental") else (0 if a.status == "Disposed" else (a.retire - tl.start).days)
    days_arr = np.arange(D)
    pm_days = _schedule(rs, 90, 90, 12, 60, 120, D)
    insp_days = _schedule(rs, 45, 45, 10, 25, 70, D)
    last_pm = np.full(D, -1e9)
    for d0 in pm_days:
        last_pm[int(d0):] = d0
    pm_mult = 0.55 + 0.45 * np.clip((days_arr - last_pm) / 45.0, 0.0, 1.0)
    hazard = np.minimum(base_hazard * c["hz"] * (0.8 + 0.06 * (a.age0 + days_arr / 365.25)) * p.frailty * a.site[9] * pm_mult, 0.2)
    hazard[end_day:] = 0.0
    u_fail, w, down_until = rs.random_sample(D), np.array(CLASS_SYSTEM_W[a.cls]), -1
    for d in range(D):
        if d <= down_until or u_fail[d] >= hazard[d]:
            continue
        sysn = SYSTEM_ORDER[int(rs.choice(len(SYSTEM_ORDER), p=w))]
        code = FAIL_SYSTEMS[sysn][ri(rs, 0, len(FAIL_SYSTEMS[sysn]))]
        tf = tl.t0 + d * 86400 + int(rs.uniform(7.0, 17.0) * 3600)
        dd = ri(rs, 1, 5)
        down_end = tf + dd * 86400 + ri(rs, 0, 12 * 3600)
        f = dict(day=d, tf=tf, system=sysn, code=code, dd=dd, down_end=down_end, precursor=bool(rs.random_sample() > 0.15),
                 L=ri(rs, 3, 10), crit=bool(rs.random_sample() < 0.85), silent=bool(rs.random_sample() < 0.07),
                 late=bool(rs.random_sample() < 0.05))
        gap = ri(rs, 3 * 86400, 6 * 86400) if f["late"] else int(rs.uniform(0.25, 4.0) * 3600)
        f["wo_open"] = tf + gap
        f["wo_close"] = f["wo_open"] + int(max(4 * 3600, (down_end - f["wo_open"]) * rs.uniform(0.7, 1.0)))
        f["sf"] = int(np.searchsorted(tl.epoch, tf, side="right")) - 1
        p.fails.append(f)
        down_until = (down_end - tl.t0) // 86400
        if a.in_erp and not f["silent"]:
            tag, ser = _tag(a, rs)
            p.wos.append(dict(type="CM", open=f["wo_open"], close=f["wo_close"], code=code, system=sysn, tag=tag, serial=ser,
                              prio=["P1", "P2", "P3"][int(rs.choice(3, p=[.45, .40, .15]))],
                              text=CM_TEXT[code][ri(rs, 0, 2)], labor=round(dd * float(rs.uniform(5, 14)), 1),
                              parts=round(PARTS_BASE[sysn] * float(rs.lognormal(0, 0.5)), 2),
                              reporter="OP-%04d" % ri(rs, 1000, 2000)))
    if a.in_erp:
        for kind, sched, hrs, prio in (("PM", pm_days, (2, 7), "P3"), ("INSP", insp_days, (1, 3), "P4")):
            for d0 in sched:
                if int(d0) >= end_day:
                    continue
                op = tl.t0 + int(d0) * 86400 + ri(rs, 6, 10) * 3600
                dur = ri(rs, hrs[0], hrs[1]) * 3600
                tag, ser = _tag(a, rs)
                p.wos.append(dict(type=kind, open=op, close=op + dur, code="", system="", tag=tag, serial=ser, prio=prio,
                                  text=(PM_TEXT if kind == "PM" else INSP_TEXT)[ri(rs, 0, 3 if kind == "PM" else 5)],
                                  labor=round(dur / 3600.0 * float(rs.uniform(1.0, 2.2)), 1),
                                  parts=round(float(rs.uniform(180, 900)), 2) if kind == "PM" else (
                                      round(float(rs.uniform(20, 150)), 2) if rs.random_sample() < 0.10 else 0.0),
                                  reporter=""))
    for wo in p.wos:
        wo["tech"] = "TECH-%03d" % (SITES.index(a.site) * 10 + ri(rs, 1, 9))
    return p


STATES = ("OFF", "IDLE", "RUN")


def simulate_readings(a, tl, p, with_drift):
    """Vectorised 6-hourly readings for one asset (state, sensors with failure precursors, fault codes, anomalies)."""
    rs, c, T = p.rs, a.cdef, tl.T
    hr = tl.slot % SLOTS_PER_DAY
    gen = a.cls == "Generator"
    pr = np.where(tl.wd < 5, P_WK[hr], np.where(tl.wd == 5, P_SAT[hr], P_SUN[hr]))
    pr = np.full(T, 0.80) if gen else np.clip(pr * p.use, 0.0, 0.97)
    pi = (1.0 - pr) * (0.10 if gen else 0.18)
    u = rs.random_sample(T)
    state = np.where(u < pr, 2, np.where(u < pr + pi, 1, 0)).astype(np.int8)
    for f in p.fails:
        state[(tl.epoch > f["tf"]) & (tl.epoch <= f["down_end"])] = 0    # machine down after a breakdown
        state[f["sf"]] = 2                                                # ... and running when it happens
    run, idle, on = state == 2, state == 1, state > 0
    season = 2.5 * np.sin(2 * np.pi * (tl.yday + tl.day - 110) / 365.0)
    load = np.clip(rs.normal(c["load"], 12, T), 0, 100)
    idle_pct = np.clip(rs.normal(c["idle"], 5, T), 0, 100)
    temp = c["temp"] + p.off_temp + season + 0.08 * (load - c["load"]) + rs.normal(0, 2.5, T)
    oil = c["oil"] + p.off_oil + rs.normal(0, 15, T)
    hyd = (c["hyd"] or 0) + p.off_hyd + rs.normal(0, 6, T)
    vib = np.maximum(0.05, c["vib"] + p.off_vib + rs.normal(0, 0.25, T))
    fuel = np.maximum(0.5, c["fuel"] * (0.5 + 0.5 * load / c["load"]) + rs.normal(0, 1.5, T))
    cool = 93.0 + rs.normal(0, 1.5, T)
    temp, oil, hyd = np.where(idle, temp - 10, temp), np.where(idle, oil - 40, oil), np.where(idle, hyd * 0.35, hyd)
    vib, fuel, load = np.where(idle, vib * 0.35, vib), np.where(idle, fuel * 0.25, fuel), np.where(idle, load * 0.1, load)
    idle_pct = np.where(idle, np.clip(idle_pct + 55, 0, 100), idle_pct)
    fc = {}

    def add(i, code):
        lst = fc.setdefault(int(i), [])
        if code not in lst:
            lst.append(code)

    valid = [s for s, wgt in zip(SYSTEM_ORDER, CLASS_SYSTEM_W[a.cls]) if wgt > 0]
    for f in p.fails:                                                     # precursors: ramp (i/L)^1.3 on sensors + fault codes
        uw, uc, cw = rs.random_sample(T), rs.random_sample(T), ri(rs, 0, 1000, T)
        if f["precursor"]:
            onset = f["tf"] - f["L"] * 86400
            x = np.clip((tl.epoch - onset) / float(f["tf"] - onset), 0.0, 1.0)
            inwin = (tl.epoch >= onset) & (tl.epoch <= f["tf"])
            sev = np.where(inwin, x ** 1.3, 0.0) * run
            d_t, d_o, d_h, d_v, d_c = AMPL[f["system"]]
            temp, oil, hyd, vib, cool = temp + d_t * sev, oil + d_o * sev, hyd + d_h * sev, vib + d_v * sev, cool + d_c * sev
            wc = WARN_CODES[f["system"]]
            for i in np.nonzero(run & inwin & (uw < 0.04 + 0.45 * sev))[0]:
                add(i, wc[int(cw[i]) % len(wc)])
            for i in np.nonzero(run & inwin & (uc < 0.25 * np.maximum(0.0, sev - 0.55)))[0]:
                add(i, CRIT_CODE[f["system"]])
        if f["crit"]:
            add(f["sf"], CRIT_CODE[f["system"]])
    for _ in range(int(rs.poisson(tl.D / 90.0))):                          # false-alarm episodes (WARN only)
        d0, dur, sysn = ri(rs, 0, tl.D), ri(rs, 1, 4), valid[ri(rs, 0, len(valid))]
        wc = WARN_CODES[sysn]
        for i in np.nonzero(run & (tl.day >= d0) & (tl.day < d0 + dur) & (rs.random_sample(T) < 0.35))[0]:
            add(i, wc[int(i) % len(wc)])
    iso, si = run & (rs.random_sample(T) < 0.002), ri(rs, 0, len(valid), T)   # isolated WARN readings
    for i in np.nonzero(iso)[0]:
        wc = WARN_CODES[valid[int(si[i])]]
        add(i, wc[int(i) % len(wc)])
    info, ii = on & (rs.random_sample(T) < 0.015), ri(rs, 0, len(INFO_CODES), T)
    for i in np.nonzero(info)[0]:
        add(i, INFO_CODES[int(ii[i])])
    if with_drift and a.cls in ("Excavator", "WheelLoader"):               # data-drift period: hotter + shakier
        m = run & (tl.day >= tl.days)
        vib, temp = np.where(m, vib * 1.35, vib), np.where(m, temp + 4.0, temp)
    hyd = np.full(T, np.nan) if c["hyd"] is None else hyd
    eh = a.age0 * float(rs.uniform(1200, 2000)) + np.cumsum(np.where(run, 4.0, np.where(idle, 1.5, 0.0)))
    lat = a.site[5] + float(rs.normal(0, 0.006)) + np.where(on, rs.normal(0, 0.0004, T), 0.0)
    lon = a.site[6] + float(rs.normal(0, 0.008)) + np.where(on, rs.normal(0, 0.0004, T), 0.0)
    sens = [np.where(on, x, np.nan) for x in (temp, oil, hyd, vib, fuel, load, idle_pct)]
    u_sp, k_sp, u_nl, k_nl = rs.random_sample(T), ri(rs, 0, 5, T), rs.random_sample(T), ri(rs, 0, 5, T)
    spk, nul = np.zeros(T, dtype=bool), np.zeros(T, dtype=bool)
    for k in range(5):                                                      # 0.2% sentinel spikes, 1% null sensor values
        m = (u_sp < 0.002) & (k_sp == k) & on & ~np.isnan(sens[k])
        spk |= m
        sens[k] = np.where(m, 999.0, sens[k])
        m = (u_nl < 0.01) & (k_nl == k) & on & ~np.isnan(sens[k])
        nul |= m
        sens[k] = np.where(m, np.nan, sens[k])
    fw = tuple(int(x) for x in a.firmware.split("."))
    miss, dup, late = rs.random_sample(T) < 0.01, rs.random_sample(T) < 0.006, rs.random_sample(T) < 0.01
    late_h, delay, ids = rs.uniform(1, 36, T), rs.uniform(60, 180, T), rs.bytes(16 * T)
    active = (tl.day < a.dev_end) if a.dev_end is not None else np.ones(T, dtype=bool)
    return SimpleNamespace(state=state, sens=sens, cool=np.where(on, cool, np.nan), eh=eh, lat=lat, lon=lon, fc=fc, spk=spk, nul=nul,
                           cool_on=np.full(T, fw >= FW_COOLANT) & (tl.epoch >= epoch_of(COOLANT_FROM)), active=active, miss=miss,
                           dup=dup, late=late, late_h=late_h, delay=delay, ids=ids)


def _col(arr, nd):
    return [None if v != v else round(v, nd) for v in arr.tolist()]


def emit_events(a, tl, R, with_drift):
    """Serialise one device's readings to JSON lines; returns ([(epoch, device_id, line)], stats)."""
    std = a.site[4]
    if "z" not in tl.cache:
        tl.cache["z"], tl.cache["ms"] = iso_z(tl.epoch), (tl.epoch * 1000).tolist()
    if std not in tl.cache:
        tl.cache[std] = iso_local(tl.epoch, local_offset_hours(std, tl.epoch))
    ts = (tl.cache["z"], tl.cache[std], tl.cache["ms"])[a.ts_style]
    in_scope = (tl.day < tl.days) | with_drift
    emit = R.active & ~R.miss & in_scope
    ing_epoch = tl.epoch + np.where(R.late, (R.late_h * 3600).astype(np.int64), R.delay.astype(np.int64))
    ing, ing2 = iso_z(ing_epoch), iso_z(ing_epoch + 30)
    names = ("engine_temp_c", "oil_pressure_kpa", "hydraulic_pressure_bar", "vibration_mm_s", "fuel_rate_lph", "load_pct", "idle_pct")
    cols = [_col(s, d) for s, d in zip(R.sens, (1, 1, 1, 2, 1, 1, 1))]
    eh, lat, lon, cool = _col(R.eh, 1), _col(R.lat, 5), _col(R.lon, 5), _col(R.cool, 1)
    out = []
    for i in np.nonzero(emit)[0].tolist():
        pl = {"engine_state": STATES[int(R.state[i])], "engine_hours": eh[i]}
        for nm, col in zip(names, cols):
            pl[nm] = col[i]
        pl["fault_codes"] = sorted(R.fc.get(i, []))
        pl["lat"], pl["lon"] = lat[i], lon[i]
        if R.cool_on[i]:
            pl["coolant_level_pct"] = cool[i]
        ev = {"event_id": str(uuid.UUID(bytes=R.ids[16 * i:16 * i + 16], version=4)), "device_id": a.device_id,
              "asset_ref": a.asset_ref, "ts": ts[i], "ingest_ts": ing[i], "firmware": a.firmware}
        if a.serial_in:
            ev["serial_no"] = a.serial
        ev["payload"] = pl
        ep = int(tl.epoch[i])
        out.append((ep, a.device_id, json.dumps(ev, separators=(",", ":"))))
        if R.dup[i]:
            ev["ingest_ts"] = ing2[i]
            out.append((ep, a.device_id, json.dumps(ev, separators=(",", ":"))))
    base = tl.day < tl.days
    stats = dict(events=int((emit & base).sum()), duplicate_events=int((emit & R.dup & base).sum()),
                 missing_readings=int((R.active & R.miss & base).sum()), sensor_spikes=int((emit & R.spk & base).sum()),
                 null_sensor_values=int((emit & R.nul & base).sum()), late_ingest=int((emit & R.late & base).sum()))
    return out, stats


def build_cmms(assets, plans, tl, days, n_active, seed):
    """Merge per-asset work orders, inject duplicates + time anomalies, number them chronologically."""
    cutoff = tl.t0 + days * 86400
    rows = [dict(wo, a=a, dup_of=None, anomaly=False) for a, p in zip(assets, plans) for wo in p.wos if wo["open"] < cutoff]
    rows.sort(key=lambda r: (r["open"], r["a"].idx, r["type"]))
    rs = np.random.RandomState(seed + 17)
    cands = [i for i, r in enumerate(rows) if r["type"] == "CM" and r["open"] + 3300 < cutoff]
    dups = []
    for k in rs.choice(len(cands), size=min(scaled(6, n_active), len(cands)), replace=False).tolist():
        src = rows[cands[k]]
        d = dict(src, dup_of=src, open=src["open"] + ri(rs, 300, 3300), reporter="OP-%04d" % ri(rs, 2000, 3000))
        d["close"] = max(src["close"], d["open"] + 3600)
        if not src["tag"].startswith("LEG-"):
            d["tag"] = TAG_STYLES[ri(rs, 0, len(TAG_STYLES))] % src["a"].erp_id
        dups.append(d)
    rows += dups
    rows.sort(key=lambda r: (r["open"], r["a"].idx, r["type"]))
    year = dt.datetime.fromtimestamp(tl.t0, UTC).year
    for k, r in enumerate(rows):
        r["no"] = "WO-%d-%06d" % (year, 100001 + k)
    for r in rows:
        r["t_open"], r["t_close"] = r["open"], r["close"]                           # truth, before the anomaly swap
    dup_ids = {id(r["dup_of"]) for r in rows if r["dup_of"] is not None}
    ok = [i for i, r in enumerate(rows) if r["close"] < cutoff and r["dup_of"] is None and id(r) not in dup_ids]
    for k in rs.choice(len(ok), size=min(scaled(8, n_active), len(ok)), replace=False).tolist():
        r = rows[ok[k]]
        r["open"], r["close"], r["anomaly"] = r["close"], r["open"], True          # closed < opened
    return rows, cutoff


def cmms_resolution(r):
    a = r["a"]
    if r["tag"].startswith("LEG-"):
        return {"serial": "SERIAL", "crosswalk": "CROSSWALK"}.get(a.legacy, "UNRESOLVED")
    return "EXACT_NORM"


def csv_lines(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().splitlines()


def write_lines(path, lines, gz=False):
    """Write UTF-8 lines; returns (written_path, line_count, sha256 of the *uncompressed* bytes)."""
    h, n, out = hashlib.sha256(), 0, path + (".gz" if gz else "")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as raw:
        f = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) if gz else raw
        for ln in lines:
            b = (ln + "\n").encode("utf-8")
            h.update(b)
            f.write(b)
            n += 1
        if gz:
            f.close()
    return out, n, h.hexdigest()


def erp_rows(assets):
    rows = []
    for a in sorted(assets, key=lambda x: x.erp_id):
        rows.append(["EQ-%05d" % a.erp_id, "%s %s %s" % (a.mfr, a.model, a.cls), a.cls, a.mfr, a.model, a.serial, a.acq.isoformat(),
                     "%.2f" % a.cost, a.site[0], "CC-%s-%s" % (a.site[0], a.cdef["abbr"]), a.status,
                     a.retire.isoformat() if a.retire else "", "Y" if a.has_dev else "N"])
    return rows


ERP_HEADER = ["erp_asset_id", "asset_name", "equipment_class", "manufacturer", "model", "serial_number", "acquisition_date",
              "acquisition_cost_eur", "site_code", "cost_center", "status", "retirement_date", "telematics_device_installed"]
CMMS_HEADER = ["wo_number", "asset_tag", "serial_number", "site_code", "wo_type", "priority", "status", "failure_code", "failure_system",
               "description", "opened_local", "closed_local", "labor_hours", "parts_cost_eur", "technician_id", "reported_by"]


def cmms_csv_rows(rows, cutoff):
    out = []
    for r in rows:
        std, closed = r["a"].site[4], r["close"] < cutoff
        out.append([r["no"], r["tag"], r["serial"], r["a"].site[0], r["type"], r["prio"], "Closed" if closed else "Open", r["code"],
                    r["system"], r["text"], local_wo_string(r["open"], std), local_wo_string(r["close"], std) if closed else "",
                    "%.1f" % r["labor"], "%.2f" % r["parts"], r["tech"], r["reporter"]])
    return out


class Out:
    """Writes files under a root folder and records (rows, sha256) per file for the manifest."""

    def __init__(self, root, gz=False):
        self.root, self.gz, self.files = root, gz, {}

    def csv(self, rel, header, rows):
        _, n, h = write_lines(os.path.join(self.root, rel), csv_lines(header, rows))
        self.files[rel] = {"rows": n - 1, "sha256": h}

    def jsonl(self, rel, lines):
        _, n, h = write_lines(os.path.join(self.root, rel), lines, self.gz)
        self.files[rel + (".gz" if self.gz else "")] = {"rows": n, "sha256": h}


_MONTHS = {}


def month_of(ep):
    d = ep // 86400
    if d not in _MONTHS:
        _MONTHS[d] = dt.datetime.fromtimestamp(ep, UTC).strftime("%Y-%m")
    return _MONTHS[d]


TEL_RES = {"normal": "EXACT_NORM", "serial": "SERIAL", "crosswalk": "CROSSWALK", "typo": "UNRESOLVED", "rental": "UNRESOLVED"}


def summarize(args, assets, rentals, plans, rows, xw, tstats, days):
    everyone = assets + rentals
    base_f = [(a, f) for a, p in zip(everyone, plans) for f in p.fails if f["day"] < days]
    st = Counter(a.status for a in assets)
    population = dict(
        erp_assets=len(assets), active=st["Active"], retired=st["Retired"], disposed=st["Disposed"], rental_devices_not_in_erp=len(rentals),
        devices=sum(1 for a in everyone if a.has_dev), active_without_device=sum(1 for a in assets if a.status == "Active" and not a.has_dev),
        zombie_assets_still_reporting=sum(1 for a in assets if a.zombie), silent_devices=sum(1 for a in assets if a.silent),
        retired_stopped_reporting=sum(1 for a in assets if a.status == "Retired" and a.has_dev and not a.zombie),
        telematics_id_tiers=dict(Counter(a.tier for a in everyone if a.has_dev)),
        cmms_legacy_tag_assets=dict(Counter(a.legacy for a in assets if a.legacy)), crosswalk_rows=len(xw),
        equipment_classes=dict(Counter(a.cls for a in assets)))
    injected = dict(
        telematics={k: int(tstats[k]) for k in sorted(tstats)},
        telematics_unresolvable_devices=sum(1 for a in everyone if a.has_dev and a.tier in ("typo", "rental")),
        cmms=dict(rows=len(rows), by_type=dict(Counter(r["type"] for r in rows)), duplicate_pairs=sum(1 for r in rows if r["dup_of"] is not None),
                  time_anomalies=sum(1 for r in rows if r["anomaly"]), asset_resolution=dict(Counter(cmms_resolution(r) for r in rows))))
    n_eq = sum(1 for a in everyone if a.status in ("Active", "Rental"))
    failures = dict(
        in_window=len(base_f), assets_with_failure=len({a.idx for a, _ in base_f}),
        per_active_asset=round(sum(1 for a, _ in base_f if a.status in ("Active", "Rental")) / max(1, n_eq), 3),
        with_sensor_precursor=sum(1 for _, f in base_f if f["precursor"]), critical_code_at_failure=sum(1 for _, f in base_f if f["crit"]),
        never_reached_cmms=sum(1 for a, f in base_f if f["silent"] and a.in_erp), wo_opened_3_to_6_days_late=sum(1 for _, f in base_f if f["late"]))
    return population, injected, failures


def generate(args):
    start = dt.date.fromisoformat(args.start)
    n_active, days = args.assets, args.days
    master = np.random.RandomState(args.seed)
    assets, rentals, xw = build_population(master, n_active, start, days)
    everyone = assets + rentals
    tl = make_timeline(start, days)
    plans = [plan_asset(a, tl, args.base_hazard) for a in everyone]
    rows, cutoff = build_cmms(everyone, plans, tl, days, n_active, args.seed)

    o = Out(args.out, args.gzip)
    o.csv("reference/site_master.csv", ["site_code", "site_name", "country", "timezone", "utc_offset_standard_h", "latitude", "longitude",
                                        "project_type"], [list(s[:8]) for s in SITES])
    o.csv("reference/fault_code_catalog.csv", ["fault_code", "system", "severity", "description", "recommended_action"],
          [list(c) for c in FAULT_CATALOG])
    o.csv("reference/asset_crosswalk.csv", ["legacy_ref", "erp_asset_id", "source_system", "note"], [list(r) for r in sorted(xw)])
    o.csv("erp/erp_assets.csv", ERP_HEADER, erp_rows(assets))
    o.csv("cmms/cmms_work_orders.csv", CMMS_HEADER, cmms_csv_rows(rows, cutoff))

    events, tstats = [], Counter()
    for a, p in zip(everyone, plans):
        if a.has_dev:
            ev, st = emit_events(a, tl, simulate_readings(a, tl, p, args.with_drift), args.with_drift)
            events += ev
            tstats.update(st)
    events.sort(key=lambda e: (e[0], e[1]))
    base, drift = {}, {}
    for ep, _, line in events:
        (drift if ep >= cutoff else base).setdefault(month_of(ep), []).append(line)
    for m in sorted(base):
        o.jsonl("telematics/telematics_%s.jsonl" % m, base[m])
    for m in sorted(drift):
        o.jsonl("telematics_drift/telematics_%s.jsonl" % m, drift[m])

    population, injected, failures = summarize(args, assets, rentals, plans, rows, xw, tstats, days)
    manifest = dict(
        generator="fleet_data_generator.py", format_version=1,
        params=dict(seed=args.seed, assets=n_active, start=args.start, days=days, with_drift=bool(args.with_drift), gzip=bool(args.gzip)),
        window=dict(start=start.isoformat(), end=(start + dt.timedelta(days=days - 1)).isoformat(), cutoff_utc=iso_z([cutoff])[0],
                    drift=(dict(start=(start + dt.timedelta(days=days)).isoformat(),
                                end=(start + dt.timedelta(days=days + EXT_DAYS - 1)).isoformat()) if args.with_drift else None)),
        population=population, injected=injected, failures=failures, files=o.files)
    if args.truth_dir:
        write_truth(args.truth_dir, everyone, plans, rows, days)
    with open(os.path.join(args.out, "_manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    return manifest


def write_truth(root, everyone, plans, rows, days):
    """Hidden ground truth for tests and the reference-pipeline self-check (never shown to participants)."""
    o = Out(root)
    eq = lambda a: "EQ-%05d" % a.erp_id if a.in_erp else ""
    o.csv("truth_assets.csv", ["erp_asset_id", "device_id", "tier", "expected_resolution", "emitted_asset_ref", "serial_in_payload", "status",
                               "equipment_class", "site_code", "zombie", "silent", "device_last_day", "cmms_legacy_tag", "cmms_legacy_mode"],
          [[eq(a), a.device_id or "", a.tier, TEL_RES[a.tier] if a.has_dev else "", a.asset_ref or "", int(a.serial_in), a.status, a.cls,
            a.site[0], int(a.zombie), int(a.silent), "" if a.dev_end is None else a.dev_end, a.leg_tag or "", a.legacy or ""] for a in everyone])
    o.csv("truth_work_orders.csv", ["wo_number", "true_erp_asset_id", "expected_resolution", "wo_type", "failure_code", "duplicate_of",
                                    "time_anomaly", "true_opened_utc", "true_closed_utc"],
          [[r["no"], eq(r["a"]), cmms_resolution(r), r["type"], r["code"], r["dup_of"]["no"] if r["dup_of"] is not None else "",
            int(r["anomaly"]), iso_z([r["t_open"]])[0], iso_z([r["t_close"]])[0]] for r in rows])
    wo_of = {(r["a"].idx, r["code"], r["t_open"]): r["no"] for r in rows if r["type"] == "CM" and r["dup_of"] is None}
    o.csv("truth_failures.csv", ["erp_asset_id", "device_id", "failure_utc", "failure_system", "failure_code", "sensor_precursor",
                                 "precursor_days", "crit_code_at_failure", "downtime_days", "back_in_service_utc", "never_reached_cmms",
                                 "wo_opened_late", "wo_number", "in_window"],
          [[eq(a), a.device_id or "", iso_z([f["tf"]])[0], f["system"], f["code"], int(f["precursor"]), f["L"] if f["precursor"] else "",
            int(f["crit"]), f["dd"], iso_z([f["down_end"]])[0], int(f["silent"]), int(f["late"]),
            wo_of.get((a.idx, f["code"], f["wo_open"]), ""), int(f["day"] < days)] for a, p in zip(everyone, plans) for f in p.fails])


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Generate the Contoso Fleet synthetic data set (telematics + CMMS + ERP + reference).")
    ap.add_argument("--out", default="./fleet_data", help="output folder (default ./fleet_data)")
    ap.add_argument("--assets", type=int, default=DEFAULT_ASSETS, help="active ERP assets (default 300; anomaly counts scale with it)")
    ap.add_argument("--start", default=DEFAULT_START, help="first day of the window, YYYY-MM-DD (default 2026-04-01)")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="window length in days (default 183)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--with-drift", action="store_true", help="also write 14 days of drifted telemetry to telematics_drift/")
    ap.add_argument("--gzip", action="store_true", help="gzip the telematics files (deterministic, mtime=0)")
    ap.add_argument("--truth-dir", help="write the hidden ground-truth files here (tests only)")
    ap.add_argument("--base-hazard", type=float, default=BASE_HAZARD, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.assets < 30 or args.days < 60:
        ap.error("--assets must be >= 30 and --days >= 60")
    return args


def main(argv=None):
    args = parse_args(argv)
    t0 = time.time()
    m = generate(args)
    rows = sum(v["rows"] for k, v in m["files"].items() if k.startswith("telematics"))
    print("Generated %d ERP assets, %d telematics rows, %d work orders in %.1fs -> %s"
          % (m["population"]["erp_assets"], rows, m["injected"]["cmms"]["rows"], time.time() - t0, os.path.abspath(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
