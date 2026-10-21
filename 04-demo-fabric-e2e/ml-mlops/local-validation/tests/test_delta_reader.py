"""Unit tests for the Delta reader in local-validation/integration_etl_to_ml.py (synthetic tables: no ETL output needed)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

_SPEC = importlib.util.spec_from_file_location("integration_etl_to_ml", Path(__file__).resolve().parents[1] / "integration_etl_to_ml.py")
etl_check = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(etl_check)

SCHEMA = json.dumps({"type": "struct", "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}]})


def _write_part(table_dir: Path, name: str, ids: list[int]) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"id": pa.array(ids, type=pa.int64())}), table_dir / name)


def _commit(table_dir: Path, version: int, *actions: dict) -> None:
    log = table_dir / "_delta_log"
    log.mkdir(parents=True, exist_ok=True)
    (log / ("%020d.json" % version)).write_text("\n".join(json.dumps(action) for action in actions) + "\n", encoding="utf-8")


def _meta(partitions: list[str] | None = None) -> dict:
    return {"metaData": {"id": "t", "format": {"provider": "parquet"}, "schemaString": SCHEMA, "partitionColumns": partitions or [], "configuration": {}}}


def _add(name: str, **extra) -> dict:
    return {"add": {"path": name, "size": 1, "modificationTime": 0, "dataChange": True, **extra}}


def test_overwrite_reads_only_the_active_files(tmp_path: Path) -> None:
    table = tmp_path / "t"
    _write_part(table, "part-0.parquet", [1, 2])
    _write_part(table, "part-1.parquet", [3])
    _commit(table, 0, _meta(), _add("part-0.parquet"))
    _commit(table, 1, {"remove": {"path": "part-0.parquet", "dataChange": True}}, _add("part-1.parquet"))
    assert etl_check.read_delta_table(table)["id"].tolist() == [3]


def test_checkpoint_plus_a_newer_commit(tmp_path: Path) -> None:
    table = tmp_path / "t"
    for index in range(3):
        _write_part(table, "part-%d.parquet" % index, [index])
    log = table / "_delta_log"
    log.mkdir()
    meta_type = pa.struct([("schemaString", pa.string()), ("partitionColumns", pa.list_(pa.string())), ("configuration", pa.map_(pa.string(), pa.string()))])
    checkpoint = pa.table(
        {
            "add": pa.array([{"path": "part-0.parquet"}, {"path": "part-1.parquet"}, None], type=pa.struct([("path", pa.string())])),
            "metaData": pa.array([None, None, {"schemaString": SCHEMA, "partitionColumns": [], "configuration": []}], type=meta_type),
        }
    )
    pq.write_table(checkpoint, log / ("%020d.checkpoint.parquet" % 1))
    (log / "_last_checkpoint").write_text(json.dumps({"version": 1, "size": 3}), encoding="utf-8")
    _commit(table, 2, _add("part-2.parquet"))  # commits 0 and 1 are gone, as after a log cleanup
    assert sorted(etl_check.read_delta_table(table)["id"].tolist()) == [0, 1, 2]


def test_partitioned_tables_and_deletion_vectors_are_refused(tmp_path: Path) -> None:
    partitioned = tmp_path / "partitioned"
    _write_part(partitioned, "part-0.parquet", [1])
    _commit(partitioned, 0, _meta(["day"]), _add("part-0.parquet"))
    with pytest.raises(NotImplementedError):
        etl_check.read_delta_table(partitioned)
    with_vector = tmp_path / "vector"
    _write_part(with_vector, "part-0.parquet", [1])
    _commit(with_vector, 0, _meta(), _add("part-0.parquet", deletionVector={"storageType": "u", "pathOrInlineDv": "x", "sizeInBytes": 1, "cardinality": 1}))
    with pytest.raises(NotImplementedError):
        etl_check.read_delta_table(with_vector)


def test_a_log_that_does_not_start_at_version_zero_is_an_error(tmp_path: Path) -> None:
    table = tmp_path / "t"
    _write_part(table, "part-0.parquet", [1])
    _commit(table, 5, _meta(), _add("part-0.parquet"))
    with pytest.raises(ValueError):
        etl_check.read_delta_table(table)


def test_arrays_dates_and_timestamps_come_back_as_spark_to_pandas_gives_them(tmp_path: Path) -> None:
    table = tmp_path / "t"
    table.mkdir()
    pq.write_table(
        pa.table(
            {
                "codes": pa.array([["E101", "E202"], None, []], type=pa.list_(pa.string())),
                "day": pa.array([dt.date(2026, 9, 1), dt.date(2026, 9, 2), None], type=pa.date32()),
                "seen": pa.array([dt.datetime(2026, 9, 1, 12), None, dt.datetime(2026, 9, 3)], type=pa.timestamp("ns")),
            }
        ),
        table / "part-0.parquet",
    )
    _commit(table, 0, _meta(), _add("part-0.parquet"))
    frame = etl_check.read_delta_table(table)
    assert frame["codes"].tolist() == [["E101", "E202"], None, []]
    assert isinstance(frame["codes"].iloc[0], list)
    assert isinstance(frame["day"].iloc[0], dt.date)
    assert str(frame["seen"].dtype) == "datetime64[ns]"


def test_a_table_without_active_files_returns_its_columns(tmp_path: Path) -> None:
    table = tmp_path / "t"
    _commit(table, 0, _meta())
    frame = etl_check.read_delta_table(table)
    assert frame.empty
    assert list(frame.columns) == ["id"]


def test_url_encoded_paths_in_the_log_are_decoded(tmp_path: Path) -> None:
    table = tmp_path / "t"
    _write_part(table, "part 0.parquet", [7])
    _commit(table, 0, _meta(), _add("part%200.parquet"))
    assert etl_check.read_delta_table(table)["id"].tolist() == [7]


def test_resolve_tables_root_accepts_the_artifacts_lakehouse_and_tables_folders(tmp_path: Path) -> None:
    tables = tmp_path / "artifacts" / "lh_fleet" / "Tables"
    (tables / "silver" / "telemetry" / "_delta_log").mkdir(parents=True)
    for start in (tmp_path / "artifacts", tmp_path / "artifacts" / "lh_fleet", tables):
        assert etl_check.resolve_tables_root(start) == tables
    with pytest.raises(FileNotFoundError):
        etl_check.resolve_tables_root(tmp_path / "missing")
