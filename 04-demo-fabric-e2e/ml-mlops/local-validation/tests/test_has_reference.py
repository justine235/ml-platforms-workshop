from __future__ import annotations

import pandas as pd


def test_has_reference_true_when_file_present(tmp_path):
    from notebooks.notebook_common import make_local_context

    ref_dir = tmp_path / "reference_out"
    ref_dir.mkdir()
    pd.DataFrame({"a": [1, 2]}).to_csv(ref_dir / "sample.csv", index=False)
    context = make_local_context(reference_dir=ref_dir, output_dir=tmp_path / "out")

    assert context.has_reference("sample") is True
    assert context.has_reference("missing_table") is False


def test_nb04_nb06_nb07_skip_cleanly_without_reference_files(tmp_path):
    """Mirrors what a real Fabric workspace sees: no reference_out files at all."""
    from notebooks.notebook_common import make_local_context

    context = make_local_context(reference_dir=tmp_path / "no_such_dir", output_dir=tmp_path / "out")
    assert context.has_reference("ml_asset_day_features") is False
    assert context.has_reference("drift_report") is False
    assert context.has_reference("ml_failure_risk_score") is False