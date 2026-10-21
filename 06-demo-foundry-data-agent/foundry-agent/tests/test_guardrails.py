from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "foundry-agent"))

from guardrails import GuardrailViolation, enforce_readonly_sql


def test_guardrails_add_limit_when_missing() -> None:
    result = enforce_readonly_sql("SELECT erp_asset_id FROM gold.dim_asset", max_rows=25)
    assert result.approved is True
    assert "TOP 25" in result.sanitized_sql.upper() or "LIMIT 25" in result.sanitized_sql.upper()


def test_guardrails_reject_write_statement() -> None:
    with pytest.raises(GuardrailViolation):
        enforce_readonly_sql("DELETE FROM gold.fact_recon_exception")


def test_guardrails_reject_unapproved_table() -> None:
    with pytest.raises(GuardrailViolation):
        enforce_readonly_sql("SELECT * FROM dbo.secret_table")


def test_guardrails_reject_comments() -> None:
    with pytest.raises(GuardrailViolation):
        enforce_readonly_sql("SELECT * FROM gold.dim_asset -- exfiltrate")
