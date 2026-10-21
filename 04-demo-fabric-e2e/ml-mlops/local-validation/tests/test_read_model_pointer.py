from __future__ import annotations

import pytest

from notebooks.notebook_common import NotebookContext, model_pointer_schema, read_model_pointer


class AnalysisException(Exception):
    """Same class name as pyspark's AnalysisException (pyspark is not installed in the local runs)."""


class _FakeReader:
    def __init__(self, error: Exception):
        self._error = error

    def table(self, _name: str):
        raise self._error


class _FakeSpark:
    def __init__(self, error: Exception):
        self.read = _FakeReader(error)


def _fabric_context(tmp_path, error: Exception) -> NotebookContext:
    return NotebookContext(
        mode="fabric",
        reference_dir=tmp_path,
        artifact_dir=tmp_path,
        output_dir=tmp_path,
        spark=_FakeSpark(error),
    )


def test_missing_pointer_table_means_no_pointer_yet(tmp_path):
    spark_style = AnalysisException("[TABLE_OR_VIEW_NOT_FOUND] The table or view `ml`.`model_pointer` cannot be found.")
    message_only = RuntimeError("Table ml.model_pointer does not exist")
    for error in (spark_style, message_only):
        frame = read_model_pointer(_fabric_context(tmp_path, error))
        assert frame.empty
        assert list(frame.columns) == model_pointer_schema()


def test_unrelated_read_errors_are_not_swallowed(tmp_path):
    with pytest.raises(RuntimeError, match="connection reset"):
        read_model_pointer(_fabric_context(tmp_path, RuntimeError("connection reset by peer")))
