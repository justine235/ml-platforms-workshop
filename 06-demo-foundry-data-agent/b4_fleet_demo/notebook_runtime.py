from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import duckdb
import pandas as pd

from .reference_data import (
    GROUND_TRUTH,
    TABLE_SPECS,
    create_local_session,
    expected_row_count,
    iter_table_specs,
)


def detect_mode() -> str:
    requested = os.getenv("B4_NOTEBOOK_MODE", "").strip().lower()
    if requested in {"fabric", "local"}:
        return requested
    try:
        import pyspark  # noqa: F401
    except ImportError:
        return "local"
    return "fabric"


@dataclass
class NotebookContext:
    mode: str
    duckdb_connection: duckdb.DuckDBPyConnection | None = None
    spark: Any | None = None

    def sql(self, query: str) -> pd.DataFrame:
        if self.mode == "fabric":
            return self.spark.sql(query).toPandas()
        return self.duckdb_connection.execute(query).fetchdf()

    def display(self, query: str, limit: int | None = None) -> pd.DataFrame:
        sql_text = query.strip().rstrip(";")
        if limit is not None:
            sql_text = f"{sql_text}\nLIMIT {limit}"
        frame = self.sql(sql_text)
        print(frame.to_string(index=False))
        return frame

    def create_or_replace_table(self, table_name: str, frame: pd.DataFrame) -> None:
        if self.mode == "fabric":
            schema_name, bare_name = table_name.split(".", 1)
            self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            self.spark.createDataFrame(frame).write.mode("overwrite").saveAsTable(f"{schema_name}.{bare_name}")
            return
        schema_name, _ = table_name.split(".", 1)
        self.duckdb_connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        self.duckdb_connection.register("_temp_frame", frame)
        self.duckdb_connection.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM _temp_frame")
        self.duckdb_connection.unregister("_temp_frame")


def make_context() -> NotebookContext:
    mode = detect_mode()
    if mode == "fabric":
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        return NotebookContext(mode="fabric", spark=spark)
    return NotebookContext(mode="local", duckdb_connection=create_local_session())


def assert_row_counts(context: NotebookContext) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for spec in iter_table_specs():
        actual = int(context.sql(f"SELECT COUNT(*) AS row_count FROM {spec.fq_name}").iloc[0]["row_count"])
        expected = expected_row_count(spec.table_name)
        if actual != expected:
            raise AssertionError(f"{spec.fq_name}: expected {expected}, found {actual}")
        results.append({"table": spec.fq_name, "expected": expected, "actual": actual})
    return results


def materialize_local_tables(context: NotebookContext) -> list[dict[str, Any]]:
    if context.mode != "local":
        return []
    results: list[dict[str, Any]] = []
    for spec in TABLE_SPECS:
        frame = context.sql(f"SELECT * FROM {spec.fq_name}")
        context.create_or_replace_table(spec.fq_name, frame)
        results.append({"table": spec.fq_name, "rows": len(frame)})
    return results


def ground_truth_json() -> str:
    return json.dumps(GROUND_TRUTH, indent=2)
