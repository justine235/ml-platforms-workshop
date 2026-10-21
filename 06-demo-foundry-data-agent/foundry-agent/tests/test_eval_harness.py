from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "foundry-agent"))

from eval_harness import run_harness


def test_oracle_agent_scores_perfectly() -> None:
    payload = run_harness("oracle")
    assert payload["summary"]["pass_rate"] == 1.0


def test_naive_agent_fails() -> None:
    payload = run_harness("naive")
    assert payload["summary"]["pass_rate"] < 1.0
