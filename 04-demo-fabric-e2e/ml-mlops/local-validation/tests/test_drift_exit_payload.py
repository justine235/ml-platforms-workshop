from __future__ import annotations

import json
from pathlib import Path

from notebooks.notebook_common import NotebookContext


def _local_context() -> NotebookContext:
    # notebook_exit() in local mode only needs `mode`; the other dataclass fields are
    # unused by that method, so dummy paths are fine here.
    here = Path(__file__).resolve().parent
    return NotebookContext(mode="local", reference_dir=here, artifact_dir=here, output_dir=here)


def test_drift_exit_payload_round_trips_and_has_status() -> None:
    """nb_07's IfDriftAlert branches on this exact payload shape in the pipeline JSON:
    @equals(json(activity('RunDriftMonitor').output.result.exitValue).status, 'alert').
    This guards the two things that expression depends on: the exit value is valid JSON,
    and it has a top-level "status" key with value "alert" or "ok"."""
    summary = {
        "status": "alert",
        "major_shift_count": 4,
        "moderate_shift_count": 3,
        "major_shifts": ["engine_temp_c:Excavator"],
        "expected_moderate_shifts": ["engine_temp_c:Paver"],
    }
    rendered = _local_context().notebook_exit(summary)

    parsed = json.loads(rendered)
    assert parsed["status"] == "alert"


def test_drift_exit_payload_ok_status_also_round_trips() -> None:
    summary = {"status": "ok", "major_shift_count": 0, "moderate_shift_count": 2}
    rendered = _local_context().notebook_exit(summary)

    parsed = json.loads(rendered)
    assert parsed["status"] == "ok"
