from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import sqlglot

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from b4_fleet_demo import create_local_session, load_eval_cases, score_structured_result

EXAMPLE_QUERIES_PATH = Path(__file__).with_name("example-queries.json")


def load_examples() -> list[dict[str, Any]]:
    return json.loads(EXAMPLE_QUERIES_PATH.read_text(encoding="utf-8"))


def transpile_tsql(tsql: str) -> str:
    return sqlglot.transpile(tsql, read="tsql", write="duckdb")[0]


def dataframe_to_records(connection: duckdb.DuckDBPyConnection, sql_text: str) -> list[dict[str, Any]]:
    return connection.execute(sql_text).fetchdf().to_dict(orient="records")


def structure_result(case_id: str, rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if mode == "refuse":
        return {"answerable": False, "refused": True}
    row = rows[0] if rows else {}
    if case_id in {"Q01", "Q02", "Q03", "Q11", "Q12", "Q13", "Q14", "Q15", "Q18", "Q19"}:
        return row
    if case_id == "Q04":
        return {
            "count": len(rows),
            "duplicate_of": {record["work_order"]: record["duplicate_of"] for record in rows},
        }
    if case_id == "Q05":
        return {"count": len(rows), "work_orders": [record["work_order"] for record in rows]}
    if case_id == "Q06":
        return {"count": len(rows), "assets": [record["erp_asset_id"] for record in rows]}
    if case_id == "Q07":
        return {
            "stopped_reporting": [
                record["erp_asset_id"] for record in rows if record["subtype"] == "STOPPED_REPORTING"
            ],
            "never_linked": [
                record["erp_asset_id"] for record in rows if record["subtype"] == "NO_LINKED_TELEMETRY"
            ],
        }
    if case_id == "Q08":
        return {
            "count": len(rows),
            "records_per_device": {record["device_id"]: int(record["n_records"]) for record in rows},
        }
    if case_id == "Q09":
        return {
            "work_orders": int(row["work_orders"]),
            "distinct_tags": int(row["distinct_tags"]),
            "tags": row["tags_csv"].split(","),
        }
    if case_id == "Q10":
        return {"sites": [row["site_code"]], "count": int(row["count"])}
    if case_id == "Q16":
        return {"sites": rows}
    if case_id == "Q17":
        return {"sites": rows}
    if case_id == "Q20":
        timestamp = pd.Timestamp(row["last_telemetry_utc"])
        return {
            "asset": row["asset"],
            "exception_types": sorted({record["exception_type"] for record in rows}),
            "last_telemetry_utc": timestamp.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    if case_id == "Q21":
        return {
            "High": int(row["High"]),
            "Medium": int(row["Medium"]),
            "Low": int(row["Low"]),
            "top_sites": [row["top_site"]],
            "top_site_high_count": int(row["top_site_high_count"]),
        }
    if case_id == "Q22":
        return {"assets": rows}
    if case_id == "Q23":
        return {"classes": [row["equipment_class"]], "share_percent": row["share_percent"]}
    if case_id == "Q24":
        return {"assets": rows}
    if case_id == "Q25":
        return {"count": len(rows), "assets": [record["erp_asset_id"] for record in rows]}
    raise KeyError(f"Unsupported case id {case_id}")


def validate_examples() -> tuple[bool, list[dict[str, Any]]]:
    examples = {example["id"]: example for example in load_examples()}
    cases = load_eval_cases()
    connection = create_local_session()
    results: list[dict[str, Any]] = []
    try:
        for case in cases:
            example = examples[case.case_id]
            mode = example["mode"]
            sql_text = ""
            rows: list[dict[str, Any]] = []
            if mode == "sql":
                sql_text = transpile_tsql(example["tsql"])
                rows = dataframe_to_records(connection, sql_text)
            actual = structure_result(case.case_id, rows, mode)
            score = score_structured_result(case, actual)
            results.append(
                {
                    "id": case.case_id,
                    "mode": mode,
                    "passed": score.passed,
                    "details": score.details,
                    "duckdb_sql": sql_text,
                    "actual": actual,
                }
            )
    finally:
        connection.close()
    return all(result["passed"] for result in results), results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate data-agent example queries against the frozen eval set.")
    parser.parse_args()
    passed, results = validate_examples()
    print(json.dumps(results, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
