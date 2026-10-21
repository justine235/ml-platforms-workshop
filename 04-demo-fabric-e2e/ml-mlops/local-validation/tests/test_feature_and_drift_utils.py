from __future__ import annotations

import pandas as pd

from notebooks.notebook_common import compare_frames_with_tolerance, major_shift_summary


def test_compare_frames_with_tolerance_accepts_small_numeric_deltas() -> None:
    actual = pd.DataFrame(
        [
            {"erp_asset_id": "EQ-00001", "obs_date": "2026-09-30", "split": "score", "temp_mean": 88.1234},
        ]
    )
    expected = pd.DataFrame(
        [
            {"erp_asset_id": "EQ-00001", "obs_date": "2026-09-30", "split": "score", "temp_mean": 88.1234004},
        ]
    )
    result = compare_frames_with_tolerance(
        actual,
        expected,
        key_cols=["erp_asset_id", "obs_date", "split"],
        numeric_cols=["temp_mean"],
        tolerance=1e-6,
    )
    assert result["ok"] is True


def test_major_shift_summary_separates_major_and_expected_moderate() -> None:
    report = pd.DataFrame(
        [
            {"equipment_class": "Excavator", "sensor": "engine_temp_c", "psi": 0.88, "status": "major"},
            {"equipment_class": "Compactor", "sensor": "engine_temp_c", "psi": 0.11, "status": "moderate"},
            {"equipment_class": "Compactor", "sensor": "load_pct", "psi": 0.09, "status": "stable"},
        ]
    )
    major, expected_moderate = major_shift_summary(report)
    assert major == ["Excavator engine_temp_c psi=0.8800"]
    assert expected_moderate == ["Compactor engine_temp_c psi=0.1100"]
