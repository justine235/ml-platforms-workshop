from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .eval_cases import EvalCase


@dataclass
class ScoreResult:
    passed: bool
    details: list[str] = field(default_factory=list)


def _is_close(actual: float, expected: float, tolerance: float) -> bool:
    return math.isclose(float(actual), float(expected), abs_tol=float(tolerance), rel_tol=0.0)


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def _compare_lists(actual: list[Any], expected: list[Any], details: list[str]) -> bool:
    if actual == expected:
        return True
    if sorted(actual) == sorted(expected):
        return True
    details.append(f"list mismatch: actual={actual!r} expected={expected!r}")
    return False


def _compare_asset_rows(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    tolerance_score: float,
    details: list[str],
) -> bool:
    if len(actual) != len(expected):
        details.append(f"row-count mismatch: actual={len(actual)} expected={len(expected)}")
        return False
    for index, (actual_row, expected_row) in enumerate(zip(actual, expected), start=1):
        for key, expected_value in expected_row.items():
            actual_value = actual_row.get(key)
            if isinstance(expected_value, float):
                if not _is_close(actual_value, expected_value, tolerance_score):
                    details.append(
                        f"row {index} field {key} mismatch: actual={actual_value!r} expected={expected_value!r}"
                    )
                    return False
            elif actual_value != expected_value:
                details.append(
                    f"row {index} field {key} mismatch: actual={actual_value!r} expected={expected_value!r}"
                )
                return False
    return True


def score_structured_result(case: EvalCase, actual: dict[str, Any]) -> ScoreResult:
    details: list[str] = []
    expected = case.expected_values
    if not case.answerable:
        answerable = actual.get("answerable")
        refused = actual.get("refused")
        passed = answerable is False or refused is True
        if not passed:
            details.append("expected refusal or unanswerable result")
        return ScoreResult(passed=passed, details=details)

    passed = True
    try:
        if case.case_id == "Q01":
            passed &= actual["total"] == expected["total"]
            for key in ("Active", "Retired", "Disposed"):
                passed &= actual[key] == expected[key]
        elif case.case_id == "Q02":
            passed &= actual["total"] == expected["total"]
            for key, value in expected.items():
                if key != "total":
                    passed &= actual[key] == value
        elif case.case_id == "Q03":
            passed &= actual["count"] == expected["count"]
        elif case.case_id == "Q04":
            passed &= actual["count"] == expected["count"]
            passed &= actual["duplicate_of"] == expected["duplicate_of"]
        elif case.case_id == "Q05":
            passed &= actual["count"] == expected["count"]
            passed &= _compare_lists(actual["work_orders"], expected["work_orders"], details)
        elif case.case_id == "Q06":
            passed &= actual["count"] == expected["count"]
            passed &= _compare_lists(actual["assets"], expected["assets"], details)
        elif case.case_id == "Q07":
            passed &= _compare_lists(actual["stopped_reporting"], expected["stopped_reporting"], details)
            passed &= _compare_lists(actual["never_linked"], expected["never_linked"], details)
        elif case.case_id == "Q08":
            passed &= actual["count"] == expected["count"]
            passed &= actual["records_per_device"] == expected["records_per_device"]
        elif case.case_id == "Q09":
            passed &= actual["work_orders"] == expected["work_orders"]
            passed &= actual["distinct_tags"] == expected["distinct_tags"]
            passed &= _compare_lists(actual["tags"], expected["tags"], details)
        elif case.case_id == "Q10":
            passed &= actual["count"] == expected["count"]
            passed &= _compare_lists(actual["sites"], expected["sites"], details)
        elif case.case_id in {"Q11", "Q12", "Q13", "Q14", "Q15", "Q19", "Q23"}:
            tolerance_key = next(key for key in expected if key.startswith("tolerance_"))
            tolerance = expected[tolerance_key]
            for key, expected_value in expected.items():
                if key.startswith("tolerance_"):
                    continue
                actual_value = actual[key]
                if isinstance(expected_value, float):
                    passed &= _is_close(actual_value, expected_value, tolerance)
                else:
                    passed &= actual_value == expected_value
        elif case.case_id in {"Q16", "Q17"}:
            tolerance = expected["tolerance_hours"] if "tolerance_hours" in expected else expected["tolerance_eur"]
            passed &= _compare_asset_rows(actual["sites"], expected["sites"], tolerance, details)
        elif case.case_id == "Q18":
            passed &= actual["total"] == expected["total"]
            for key in ("NO_FAULT_SIGNAL", "NO_TELEMETRY", "TELEMETRY_STOPPED"):
                passed &= actual[key] == expected[key]
        elif case.case_id == "Q20":
            passed &= actual["asset"] == expected["asset"]
            passed &= _compare_lists(actual["exception_types"], expected["exception_types"], details)
            passed &= actual["last_telemetry_utc"] == expected["last_telemetry_utc"]
        elif case.case_id == "Q21":
            for key in ("High", "Medium", "Low", "top_site_high_count"):
                passed &= actual[key] == expected[key]
            passed &= _compare_lists(actual["top_sites"], expected["top_sites"], details)
        elif case.case_id == "Q22" or case.case_id == "Q24":
            passed &= _compare_asset_rows(actual["assets"], expected["assets"], expected["tolerance_score"], details)
        elif case.case_id == "Q25":
            passed &= actual["count"] == expected["count"]
            passed &= _compare_lists(actual["assets"], expected["assets"], details)
        else:
            passed = actual == expected
            if not passed:
                details.append(f"mismatch: actual={actual!r} expected={expected!r}")
    except KeyError as exc:
        passed = False
        details.append(f"missing key: {exc.args[0]}")

    if not passed and not details:
        details.append(f"actual={actual!r} expected={expected!r}")
    return ScoreResult(passed=passed, details=details)
